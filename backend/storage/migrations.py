import sqlite3

from .schema import INITIAL_SCHEMA

CURRENT_SCHEMA_VERSION = 1


def _version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn: sqlite3.Connection) -> None:
    version = _version(conn)
    if version == 0:
        conn.executescript(INITIAL_SCHEMA)
        _set_version(conn, CURRENT_SCHEMA_VERSION)
        return
    if version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {version} is newer than app version "
            f"{CURRENT_SCHEMA_VERSION}"
        )
