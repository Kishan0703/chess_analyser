import httpx
from fastapi import APIRouter

from .. import db, engine, settings

router = APIRouter()


@router.get("/api/onboarding")
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
        "stockfish_path": cfg.get("stockfish_path") or "",
        "stockfish_found": False,
        "stockfish_error": "",
    }
    try:
        engine.resolve_engine_path(cfg)
        out["stockfish_found"] = True
    except Exception as e:
        out["stockfish_error"] = str(e)
    if provider == "ollama":
        try:
            base = cfg["ollama_url"].rstrip("/")
            response = httpx.get(f"{base}/api/tags", timeout=2.5)
            response.raise_for_status()
            out["ollama_reachable"] = True
            names = [model.get("name", "") for model in response.json().get("models", [])]
            want = cfg.get("ollama_model") or ""
            out["ollama_model_present"] = any(
                name == want or name.split(":")[0] == want.split(":")[0]
                for name in names
            )
        except Exception:
            pass
    return out
