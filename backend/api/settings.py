from fastapi import APIRouter

from .. import settings
from ..schemas.requests import SettingsUpdate

router = APIRouter()


@router.get("/api/settings")
def get_settings():
    cfg = settings.load()
    cfg["anthropic_api_key"] = bool(cfg["anthropic_api_key"])
    cfg["gemini_api_key"] = bool(cfg["gemini_api_key"])
    return cfg


@router.put("/api/settings")
def put_settings(update: SettingsUpdate):
    cfg = settings.save(update.model_dump(exclude_none=True))
    cfg["anthropic_api_key"] = bool(cfg["anthropic_api_key"])
    cfg["gemini_api_key"] = bool(cfg["gemini_api_key"])
    return cfg
