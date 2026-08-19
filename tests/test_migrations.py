import sqlite3

from backend.storage.migrations import CURRENT_SCHEMA_VERSION, migrate


def test_migrate_creates_latest_schema():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    migrate(conn)

    version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == CURRENT_SCHEMA_VERSION
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"games", "moves", "analyses", "themes", "bot_games"}.issubset(tables)


def test_migrate_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    migrate(conn)
    migrate(conn)

    assert conn.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION
