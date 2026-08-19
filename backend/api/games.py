from fastapi import APIRouter, HTTPException

from .. import chesscom, db, settings
from ..schemas.requests import ImportRequest

router = APIRouter()


@router.post("/api/import")
def import_games(req: ImportRequest):
    username = req.username or settings.load()["chesscom_username"]
    if not username:
        raise HTTPException(400, "No chess.com username configured")
    try:
        return chesscom.import_games(username, months=req.months)
    except chesscom.ChessComImportError as e:
        raise HTTPException(e.status_code, str(e))
    except Exception as e:
        raise HTTPException(502, f"chess.com import failed: {e}")


@router.get("/api/games")
def games(limit: int = 200):
    username = settings.load().get("chesscom_username")
    with db.connect() as conn:
        return db.list_games(conn, limit, username=username)


@router.get("/api/profile")
def profile():
    username = settings.load().get("chesscom_username")
    with db.connect() as conn:
        return db.get_profile(conn, username=username)


@router.get("/api/games/{game_id}")
def game(game_id: int):
    username = settings.load().get("chesscom_username")
    with db.connect() as conn:
        result = db.get_game(conn, game_id, username=username)
    if result is None:
        raise HTTPException(404, "game not found")
    return result
