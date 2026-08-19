"""SQLite persistence helpers for local bot game sessions."""
import json
import sqlite3


def create_bot_game(conn: sqlite3.Connection, payload: dict) -> int:
    cur = conn.execute(
        """INSERT INTO bot_games
           (player_color, difficulty, advanced_json, pgn, fen, status, result)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            payload["player_color"],
            payload["difficulty"],
            json.dumps(payload["advanced"], sort_keys=True),
            payload.get("pgn", ""),
            payload["fen"],
            payload.get("status", "active"),
            payload.get("result", "*"),
        ),
    )
    return cur.lastrowid


def get_bot_game(conn: sqlite3.Connection, bot_game_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM bot_games WHERE id = ?", (bot_game_id,)).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["advanced"] = json.loads(data.pop("advanced_json"))
    return data


def update_bot_game(conn: sqlite3.Connection, bot_game_id: int, payload: dict) -> None:
    conn.execute(
        """UPDATE bot_games
           SET pgn = ?, fen = ?, status = ?, result = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (payload["pgn"], payload["fen"], payload["status"], payload["result"], bot_game_id),
    )


def mark_bot_game_saved(conn: sqlite3.Connection, bot_game_id: int, saved_game_id: int) -> None:
    conn.execute(
        """UPDATE bot_games
           SET saved_game_id = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (saved_game_id, bot_game_id),
    )
