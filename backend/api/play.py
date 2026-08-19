from fastapi import APIRouter, HTTPException

from .. import play
from ..schemas.requests import BotGameCreate, BotMoveRequest

router = APIRouter()


@router.post("/api/play/bot/games")
def create_bot_game(req: BotGameCreate):
    try:
        advanced = req.advanced.model_dump(exclude_none=True, exclude_unset=True) if req.advanced else None
        return play.new_game(req.player_color, req.difficulty, advanced)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"bot game error: {e}")


@router.get("/api/play/bot/games/{bot_game_id}")
def get_bot_game(bot_game_id: int):
    try:
        return play.get_game(bot_game_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.post("/api/play/bot/games/{bot_game_id}/move")
def play_bot_move(bot_game_id: int, req: BotMoveRequest):
    try:
        return play.apply_player_move(
            bot_game_id,
            {"from": req.from_square, "to": req.to, "promotion": req.promotion},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"bot move error: {e}")


@router.post("/api/play/bot/games/{bot_game_id}/save")
def save_bot_game(bot_game_id: int):
    try:
        return play.save_to_game(bot_game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/api/play/bot/games/{bot_game_id}/resign")
def resign_bot_game(bot_game_id: int):
    try:
        return play.resign_game(bot_game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/api/play/bot/games/{bot_game_id}/draw-offer")
def offer_bot_draw(bot_game_id: int):
    try:
        return play.offer_draw(bot_game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
