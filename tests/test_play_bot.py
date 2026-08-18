import sqlite3

import chess
import pytest

from backend import db, play


def test_bot_play_api_starts_game(monkeypatch):
    from fastapi.testclient import TestClient
    from backend import app as app_module

    monkeypatch.setattr(app_module.play, "new_game", lambda player_color, difficulty, advanced=None: {
        "id": 12, "player_color": player_color, "difficulty": difficulty, "advanced": advanced or {},
        "fen": chess.STARTING_FEN, "legal_moves": [], "status": "active", "result": "*", "pgn": "",
    })

    client = TestClient(app_module.app)
    response = client.post("/api/play/bot/games", json={"player_color": "white", "difficulty": "club"})

    assert response.status_code == 200
    assert response.json()["id"] == 12
    assert response.json()["difficulty"] == "club"


def test_bot_play_api_maps_illegal_move_to_400(monkeypatch):
    from fastapi.testclient import TestClient
    from backend import app as app_module

    def raise_illegal(*args, **kwargs):
        raise ValueError("illegal move")

    monkeypatch.setattr(app_module.play, "apply_player_move", raise_illegal)

    client = TestClient(app_module.app)
    response = client.post("/api/play/bot/games/12/move", json={"from": "e2", "to": "e5"})

    assert response.status_code == 400
    assert response.json()["detail"] == "illegal move"


def test_bot_play_api_rejects_invalid_advanced_settings():
    from fastapi.testclient import TestClient
    from backend import app as app_module

    client = TestClient(app_module.app)
    response = client.post("/api/play/bot/games", json={
        "player_color": "white",
        "difficulty": "club",
        "advanced": {"skill_level": 8, "move_time_ms": 0, "randomness": 0.2},
    })

    assert response.status_code == 422


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


def test_new_game_rejects_out_of_range_advanced_settings(monkeypatch):
    conn = make_conn()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    with pytest.raises(ValueError, match="skill_level must be between 0 and 20"):
        play.new_game("white", "club", {"skill_level": 99})

    assert conn.execute("SELECT COUNT(*) AS c FROM bot_games").fetchone()["c"] == 0


def test_get_game_returns_serialized_persisted_session(monkeypatch):
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

    result = play.get_game(bot_game_id)

    assert result["id"] == bot_game_id
    assert result["fen"] == chess.STARTING_FEN
    assert result["status"] == "active"
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


def test_save_to_game_creates_local_bot_game_for_analysis(monkeypatch):
    conn = make_conn()
    bot_game_id = db.create_bot_game(conn, {
        "player_color": "white",
        "difficulty": "club",
        "advanced": play.DIFFICULTY_PRESETS["club"],
        "pgn": '[Event "ChessCoach Bot Game"]\n\n1. e4 e5 *',
        "fen": "after",
        "status": "finished",
        "result": "*",
    })
    conn.commit()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    result = play.save_to_game(bot_game_id)

    assert result["game_id"] > 0
    saved = db.get_game(conn, result["game_id"], username="You")
    assert saved["source"] == "local-bot"
    assert saved["white"] == "You"
    assert saved["black"] == "ChessCoach Bot"
    assert saved["user_color"] == "white"


def test_save_to_game_rejects_active_bot_game(monkeypatch):
    conn = make_conn()
    bot_game_id = db.create_bot_game(conn, {
        "player_color": "white",
        "difficulty": "club",
        "advanced": play.DIFFICULTY_PRESETS["club"],
        "pgn": "1. e4 e5 *",
        "fen": "after",
        "status": "active",
        "result": "*",
    })
    conn.commit()

    class ConnCtx:
        def __enter__(self): return conn
        def __exit__(self, *args): return False

    monkeypatch.setattr(play.db, "connect", lambda: ConnCtx())

    with pytest.raises(ValueError, match="bot game is not finished"):
        play.save_to_game(bot_game_id)


def test_local_bot_games_keep_saved_user_color_with_configured_username():
    conn = make_conn()
    game_id = db.insert_game(conn, {
        "source": "local-bot",
        "source_url": "local-bot:test",
        "pgn": "1. e4 e5 *",
        "white": "You",
        "black": "ChessCoach Bot",
        "white_elo": None,
        "black_elo": None,
        "result": "*",
        "eco": None,
        "opening": "Bot practice",
        "time_control": "offline",
        "played_at": None,
        "user_color": "white",
    })

    game = db.get_game(conn, game_id, username="ConfiguredChesscomUser")
    games = db.list_games(conn, username="ConfiguredChesscomUser")

    assert game["user_color"] == "white"
    assert any(g["id"] == game_id and g["user_color"] == "white" for g in games)
