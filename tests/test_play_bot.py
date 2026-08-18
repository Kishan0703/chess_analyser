import sqlite3

import chess
import pytest

from backend import db, play


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


def test_difficulty_presets_have_hybrid_defaults():
    assert play.DIFFICULTY_PRESETS["beginner"] == {
        "label": "Beginner", "skill_level": 2, "move_time_ms": 80, "randomness": 0.55
    }
    assert play.DIFFICULTY_PRESETS["master"]["skill_level"] == 18
    assert play.DIFFICULTY_PRESETS["master"]["randomness"] == 0.0


def test_new_game_creates_white_to_move_session(monkeypatch):
    conn = make_conn()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    result = play.new_game("white", "club")

    assert result["player_color"] == "white"
    assert result["difficulty"] == "club"
    assert result["status"] == "active"
    assert result["fen"] == chess.STARTING_FEN
    assert result["legal_moves"]


def test_apply_player_move_rejects_illegal_move(monkeypatch):
    conn = make_conn()
    bot_game_id = db.create_bot_game(conn, {
        "player_color": "white",
        "difficulty": "club",
        "advanced": play.DIFFICULTY_PRESETS["club"],
        "pgn": "",
        "fen": chess.STARTING_FEN,
        "status": "active",
        "result": "*",
    })
    conn.commit()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    with pytest.raises(ValueError, match="illegal move"):
        play.apply_player_move(bot_game_id, {"from": "e2", "to": "e5"})


def test_apply_player_move_returns_bot_reply_from_injected_selector(monkeypatch):
    conn = make_conn()
    bot_game_id = db.create_bot_game(conn, {
        "player_color": "white",
        "difficulty": "club",
        "advanced": play.DIFFICULTY_PRESETS["club"],
        "pgn": "",
        "fen": chess.STARTING_FEN,
        "status": "active",
        "result": "*",
    })
    conn.commit()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    result = play.apply_player_move(
        bot_game_id,
        {"from": "e2", "to": "e4"},
        bot_selector=lambda board, advanced: chess.Move.from_uci("e7e5"),
    )

    assert result["last_player_move"]["san"] == "e4"
    assert result["last_bot_move"]["san"] == "e5"
    assert result["status"] == "active"
    assert " e5" in result["pgn"]
