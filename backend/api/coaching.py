import threading

from fastapi import APIRouter, HTTPException

from .. import coach, db
from ..schemas.requests import ChatRequest

router = APIRouter()

# in-process coaching job tracking: game_id -> {"done", "total", "label", "error"}
_coach_jobs: dict[int, dict] = {}


@router.post("/api/games/{game_id}/coach")
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


@router.get("/api/games/{game_id}/coach/status")
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


@router.get("/api/games/{game_id}/position/{ply}/explanation")
def get_position_explanation(game_id: int, ply: int):
    try:
        return coach.explain_current_move(game_id, ply)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"coach error: {e}")


@router.post("/api/games/{game_id}/chat")
def chat_about_game(game_id: int, req: ChatRequest):
    try:
        return coach.answer_game_question(
            game_id,
            req.question,
            ply=req.ply,
            history=[message.model_dump() for message in req.history],
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"coach error: {e}")
