"""SQLite schema and access helpers.

Schema is designed so cross-game profiling (phase 3) is a GROUP BY over
`themes` and `moves.classification`, not a migration.
"""
from .storage.bot_games import (
    create_bot_game,
    get_bot_game,
    mark_bot_game_saved,
    update_bot_game,
)
from .storage.cache import (
    get_candidate_cache,
    get_moment_cache,
    get_summary_cache,
    save_candidate_cache,
    save_moment_cache,
    save_summary_cache,
)
from .storage.connection import DB_PATH, connect
from .storage.games import (
    _apply_user_color,
    get_game,
    insert_game,
    list_games,
    save_coach,
    save_engine_pass,
)
from .storage.migrations import migrate
from .storage.profile import get_profile
from .storage.schema import INITIAL_SCHEMA

SCHEMA = INITIAL_SCHEMA


def init_db() -> None:
    with connect() as conn:
        migrate(conn)
