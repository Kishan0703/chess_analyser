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


def test_new_game_as_black_persists_injected_bot_opening(monkeypatch):
    conn = make_conn()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    result = play.new_game(
        "black",
        "club",
        bot_selector=lambda board, advanced: chess.Move.from_uci("e2e4"),
    )

    stored = db.get_bot_game(conn, result["id"])
    assert result["player_color"] == "black"
    assert result["last_bot_move"]["san"] == "e4"
    assert result["pgn"] == "1. e4 *"
    assert chess.Board(result["fen"]).turn == chess.BLACK
    assert stored["pgn"] == result["pgn"]
    assert stored["fen"] == result["fen"]


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


def test_apply_player_move_rebuilds_pgn_history_for_draw_claim(monkeypatch):
    conn = make_conn()
    pgn = "1. Nf3 Nf6 2. Ng1 Ng8 3. Nf3 Nf6 4. Ng1 *"
    board = chess.Board()
    for uci in ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1"]:
        board.push_uci(uci)
    bot_game_id = db.create_bot_game(conn, {
        "player_color": "black",
        "difficulty": "club",
        "advanced": play.DIFFICULTY_PRESETS["club"],
        "pgn": pgn,
        "fen": board.fen(),
        "status": "active",
        "result": "*",
    })
    conn.commit()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    def unexpected_bot_move(board, advanced):
        raise AssertionError("draw claim must finish before a bot reply")

    result = play.apply_player_move(
        bot_game_id,
        {"from": "f6", "to": "g8"},
        bot_selector=unexpected_bot_move,
    )

    assert result["status"] == "finished"
    assert result["result"] == "1/2-1/2"
    assert result["last_bot_move"] is None
