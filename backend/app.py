"""FastAPI app: API routes + static frontend."""
import threading
from pathlib import Path

import chess
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import chesscom, coach, db, engine, settings

app = FastAPI(title="ChessCoach")
db.init_db()

# in-process engine job tracking: game_id -> {"done": n, "total": n, "error": str|None}
_jobs: dict[int, dict] = {}
# in-process coaching job tracking: game_id -> {"done", "total", "label", "error"}
_coach_jobs: dict[int, dict] = {}


class ImportRequest(BaseModel):
    username: str | None = None
    months: int = 3


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    ply: int = 0
    history: list[ChatMessage] = Field(default_factory=list)


class SettingsUpdate(BaseModel):
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    chesscom_username: str | None = None
    claude_model: str | None = None
    gemini_model: str | None = None
    gemini_fallback_models: str | None = None
    engine_movetime_ms: int | None = None
    engine_multipv: int | None = None
    engine_threads: int | None = None
    # Coach provider settings — without these declared, Pydantic silently drops
    # them from the request and the Ollama model selection never reaches save().
    coach_provider: str | None = None
    ollama_url: str | None = None
    ollama_model: str | None = None


@app.get("/api/settings")
def get_settings():
    cfg = settings.load()
    # don't ship raw keys back to the UI; just whether they're set
    cfg["anthropic_api_key"] = bool(cfg["anthropic_api_key"])
    cfg["gemini_api_key"] = bool(cfg["gemini_api_key"])
    return cfg


@app.put("/api/settings")
def put_settings(update: SettingsUpdate):
    cfg = settings.save(update.model_dump(exclude_none=True))
    cfg["anthropic_api_key"] = bool(cfg["anthropic_api_key"])
    cfg["gemini_api_key"] = bool(cfg["gemini_api_key"])
    return cfg


@app.post("/api/import")
def import_games(req: ImportRequest):
    username = req.username or settings.load()["chesscom_username"]
    if not username:
        raise HTTPException(400, "No chess.com username configured")
    try:
        return chesscom.import_games(username, months=req.months)
    except chesscom.ChessComImportError as e:
        raise HTTPException(e.status_code, str(e))
    except Exception as e:  # surface chess.com errors readably
        raise HTTPException(502, f"chess.com import failed: {e}")


@app.get("/api/onboarding")
def onboarding():
    """Live setup state for the first-run checklist: prerequisites + data milestones."""
    cfg = settings.load()
    provider = cfg.get("coach_provider", "ollama")
    username = (cfg.get("chesscom_username") or "").strip().lower()
    user_filter = "WHERE lower(white) = ? OR lower(black) = ?" if username else ""
    user_params = (username, username) if username else ()
    with db.connect() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM games {user_filter}", user_params
        ).fetchone()["c"]
        analyzed = conn.execute(
            f"""SELECT COUNT(*) AS c FROM games
                {'WHERE engine_analyzed = 1 AND (lower(white) = ? OR lower(black) = ?)' if username else 'WHERE engine_analyzed = 1'}""",
            user_params,
        ).fetchone()["c"]
        coached = conn.execute(
            f"""SELECT COUNT(DISTINCT a.game_id) AS c
                FROM analyses a
                JOIN games g ON g.id = a.game_id
                {('WHERE lower(g.white) = ? OR lower(g.black) = ?') if username else ''}""",
            user_params,
        ).fetchone()["c"]

    out = {
        "coach_provider": provider,
        "chesscom_username": cfg.get("chesscom_username") or "",
        "games": total,
        "engine_analyzed": analyzed,
        "coached": coached,
        "ollama_model": cfg.get("ollama_model"),
        "ollama_reachable": False,
        "ollama_model_present": False,
        "claude_key_set": bool(cfg.get("anthropic_api_key")),
        "gemini_key_set": bool(cfg.get("gemini_api_key")),
    }
    if provider == "ollama":
        try:
            base = cfg["ollama_url"].rstrip("/")
            r = httpx.get(f"{base}/api/tags", timeout=2.5)
            r.raise_for_status()
            out["ollama_reachable"] = True
            names = [m.get("name", "") for m in r.json().get("models", [])]
            want = (cfg.get("ollama_model") or "")
            out["ollama_model_present"] = any(
                n == want or n.split(":")[0] == want.split(":")[0] for n in names)
        except Exception:
            pass  # unreachable -> stays False, the checklist surfaces the fix
    return out


@app.get("/api/games")
def games(limit: int = 200):
    username = settings.load().get("chesscom_username")
    with db.connect() as conn:
        return db.list_games(conn, limit, username=username)


@app.get("/api/games/{game_id}")
def game(game_id: int):
    username = settings.load().get("chesscom_username")
    with db.connect() as conn:
        g = db.get_game(conn, game_id, username=username)
    if g is None:
        raise HTTPException(404, "game not found")
    return g


@app.post("/api/games/{game_id}/analyze")
def analyze(game_id: int):
    if game_id in _jobs and _jobs[game_id].get("error") is None \
            and _jobs[game_id]["done"] < _jobs[game_id]["total"]:
        return {"status": "already_running"}
    progress = {"done": 0, "total": 1, "error": None}
    _jobs[game_id] = progress

    def run():
        try:
            engine.analyze_game(game_id, progress)
        except Exception as e:
            progress["error"] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return {"status": "started"}


@app.get("/api/games/{game_id}/analyze/status")
def analyze_status(game_id: int):
    job = _jobs.get(game_id)
    if job is None:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT engine_analyzed FROM games WHERE id = ?", (game_id,)
            ).fetchone()
        done = bool(row and row["engine_analyzed"])
        return {"status": "done" if done else "not_started"}
    if job["error"]:
        return {"status": "error", "error": job["error"]}
    if job["done"] >= job["total"]:
        return {"status": "done"}
    return {"status": "running", "done": job["done"], "total": job["total"]}


@app.post("/api/games/{game_id}/coach")
def coach_game(game_id: int):
    job = _coach_jobs.get(game_id)
    if job and job.get("error") is None and job["done"] < job["total"]:
        return {"status": "already_running"}
    progress = {"done": 0, "total": 1, "label": "Starting…", "error": None}
    _coach_jobs[game_id] = progress

    def run():
        try:
            coach.coach_game(game_id, progress)
        except Exception as e:
            progress["error"] = str(e)

    threading.Thread(target=run, daemon=True).start()
    return {"status": "started"}


@app.get("/api/games/{game_id}/coach/status")
def coach_status(game_id: int):
    job = _coach_jobs.get(game_id)
    if job is None:
        with db.connect() as conn:
            row = conn.execute(
                "SELECT EXISTS(SELECT 1 FROM analyses WHERE game_id = ?) AS c", (game_id,)
            ).fetchone()
        return {"status": "done" if row and row["c"] else "not_started"}
    if job["error"]:
        return {"status": "error", "error": job["error"]}
    if job["done"] >= job["total"]:
        return {"status": "done"}
    return {"status": "running", "done": job["done"], "total": job["total"],
            "label": job.get("label", "")}


@app.get("/api/games/{game_id}/bestline/{ply}")
def get_deep_bestline(game_id: int, ply: int):
    """Return Stockfish's full PV from the position just before `ply` was played."""
    with db.connect() as conn:
        if ply <= 1:
            fen = chess.STARTING_FEN
        else:
            row = conn.execute(
                "SELECT fen_after FROM moves WHERE game_id = ? AND ply = ?",
                (game_id, ply - 1)
            ).fetchone()
            if row is None:
                raise HTTPException(404, "position not found — run engine analysis first")
            fen = row["fen_after"]

    try:
        sans = engine.get_bestline(fen)
    except Exception as e:
        raise HTTPException(500, f"engine error: {e}")

    return {"fen": fen, "sans": sans}


@app.get("/api/games/{game_id}/position/{ply}")
def get_position_analysis(game_id: int, ply: int):
    """Return top engine candidates for the position currently shown at `ply`."""
    if ply < 0:
        raise HTTPException(400, "ply must be non-negative")

    with db.connect() as conn:
        game_row = conn.execute("SELECT id FROM games WHERE id = ?", (game_id,)).fetchone()
        if game_row is None:
            raise HTTPException(404, "game not found")

        if ply == 0:
            fen = chess.STARTING_FEN
        else:
            row = conn.execute(
                "SELECT fen_after FROM moves WHERE game_id = ? AND ply = ?",
                (game_id, ply)
            ).fetchone()
            if row is None:
                raise HTTPException(404, "position not found — run engine analysis first")
            fen = row["fen_after"]

    board = chess.Board(fen)
    cfg = settings.load()
    try:
        candidates = engine.batch_candidates(
            [fen],
            multipv=cfg.get("engine_multipv", 3),
            movetime_ms=cfg.get("engine_movetime_ms", 150),
        ).get(fen, [])
    except Exception as e:
        raise HTTPException(500, f"engine error: {e}")

    for cand in candidates:
        cp = cand.get("eval_cp")
        if cp is None:
            cand["white_win_pct"] = None
            cand["side_to_move_win_pct"] = None
            continue
        white_wp = engine.win_pct(cp)
        cand["white_win_pct"] = round(white_wp, 1)
        cand["side_to_move_win_pct"] = round(
            white_wp if board.turn == chess.WHITE else 100 - white_wp, 1
        )

    return {
        "fen": fen,
        "ply": ply,
        "side_to_move": "white" if board.turn == chess.WHITE else "black",
        "candidates": candidates,
    }


@app.post("/api/games/{game_id}/chat")
def chat_about_game(game_id: int, req: ChatRequest):
    try:
        return coach.answer_game_question(
            game_id,
            req.question,
            ply=req.ply,
            history=[m.model_dump() for m in req.history],
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"coach error: {e}")


# Serve the built frontend (must be mounted last so /api wins)
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if DIST.exists():
    app.mount("/", StaticFiles(directory=DIST, html=True), name="frontend")
