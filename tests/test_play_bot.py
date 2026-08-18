import sqlite3

from backend import db


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(db.SCHEMA)
    return conn


def test_bot_game_storage_round_trips_session_state():
    conn = make_conn()
    bot_game_id = db.create_bot_game(conn, {
        "player_color": "white",
        "difficulty": "club",
        "advanced": {"skill_level": 8, "move_time_ms": 250, "randomness": 0.25},
        "pgn": "",
        "fen": "start",
        "status": "active",
        "result": "*",
    })

    loaded = db.get_bot_game(conn, bot_game_id)

    assert loaded["id"] == bot_game_id
    assert loaded["player_color"] == "white"
    assert loaded["difficulty"] == "club"
    assert loaded["advanced"] == {"skill_level": 8, "move_time_ms": 250, "randomness": 0.25}
    assert loaded["fen"] == "start"
    assert loaded["status"] == "active"
    assert loaded["result"] == "*"


def test_bot_game_update_replaces_mutable_state():
    conn = make_conn()
    bot_game_id = db.create_bot_game(conn, {
        "player_color": "black",
        "difficulty": "beginner",
        "advanced": {"skill_level": 2, "move_time_ms": 80, "randomness": 0.6},
        "pgn": "",
        "fen": "start",
        "status": "active",
        "result": "*",
    })

    db.update_bot_game(conn, bot_game_id, {
        "pgn": "1. e4 e5 *",
        "fen": "after",
        "status": "active",
        "result": "*",
    })

    loaded = db.get_bot_game(conn, bot_game_id)
    assert loaded["pgn"] == "1. e4 e5 *"
    assert loaded["fen"] == "after"
