from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import db
from .api import analysis, coaching, games, onboarding, play, settings


def create_app() -> FastAPI:
    app = FastAPI(title="ChessCoach")
    db.init_db()
    app.include_router(settings.router)
    app.include_router(onboarding.router)
    app.include_router(games.router)
    app.include_router(analysis.router)
    app.include_router(coaching.router)
    app.include_router(play.router)

    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
