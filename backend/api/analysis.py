import threading

import chess
from fastapi import APIRouter, HTTPException

from .. import db, engine, settings

router = APIRouter()

# in-process engine job tracking: game_id -> {"done": n, "total": n, "error": str|None}
_jobs: dict[int, dict] = {}


@router.post("/api/games/{game_id}/analyze")
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


@router.get("/api/games/{game_id}/analyze/status")
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


@router.get("/api/games/{game_id}/bestline/{ply}")
def get_deep_bestline(game_id: int, ply: int):
    """Return Stockfish's full PV from the position just before `ply` was played."""
    with db.connect() as conn:
        if ply <= 1:
            fen = chess.STARTING_FEN
        else:
            row = conn.execute(
                "SELECT fen_after FROM moves WHERE game_id = ? AND ply = ?",
                (game_id, ply - 1),
            ).fetchone()
            if row is None:
                raise HTTPException(404, "position not found — run engine analysis first")
            fen = row["fen_after"]

    try:
        sans = engine.get_bestline(fen)
    except Exception as e:
        raise HTTPException(500, f"engine error: {e}")

    return {"fen": fen, "sans": sans}


@router.get("/api/games/{game_id}/position/{ply}")
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
                (game_id, ply),
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

    for candidate in candidates:
        cp = candidate.get("eval_cp")
        if cp is None:
            candidate["white_win_pct"] = None
            candidate["side_to_move_win_pct"] = None
            continue
        white_wp = engine.win_pct(cp)
        candidate["white_win_pct"] = round(white_wp, 1)
        candidate["side_to_move_win_pct"] = round(
            white_wp if board.turn == chess.WHITE else 100 - white_wp, 1
        )

    return {
        "fen": fen,
        "ply": ply,
        "side_to_move": "white" if board.turn == chess.WHITE else "black",
        "candidates": candidates,
    }
