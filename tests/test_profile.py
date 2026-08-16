import sqlite3

from backend import db


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(db.SCHEMA)
    return conn


def insert_game(conn, game_id, white, black, result, opening, played_at, user_color):
    conn.execute(
        """INSERT INTO games
           (id, source, source_url, pgn, white, black, result, opening, played_at, user_color, engine_analyzed)
           VALUES (?, 'chess.com', ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
        (game_id, f"https://game/{game_id}", "1. e4 e5 *", white, black, result, opening, played_at, user_color),
    )


def insert_move(conn, game_id, ply, classification, loss):
    conn.execute(
        """INSERT INTO moves
           (game_id, ply, san, uci, fen_after, classification, win_pct_loss)
           VALUES (?, ?, 'e4', 'e2e4', 'fen', ?, ?)""",
        (game_id, ply, classification, loss),
    )


def test_profile_counts_user_results_move_quality_themes_and_openings():
    conn = make_conn()
    insert_game(conn, 1, "kishan", "rival1", "1-0", "Italian Game", "2026-01-01 12:00:00", "white")
    insert_game(conn, 2, "rival2", "kishan", "1-0", "Sicilian Defense", "2026-01-02 12:00:00", "black")
    insert_move(conn, 1, 1, "best", 0)
    insert_move(conn, 1, 3, "mistake", 21.5)
    insert_move(conn, 2, 2, "blunder", 34.0)
    insert_move(conn, 2, 4, "inaccuracy", 12.0)
    conn.execute(
        "INSERT INTO analyses (game_id, commentary, model, input_tokens, output_tokens) VALUES (1, '{}', 'qwen', 10, 5)"
    )
    conn.execute(
        "INSERT INTO themes (game_id, slug, side, severity, ply_start, ply_end, note) VALUES (1, 'weak-king', 'user', 'decisive', 3, 3, 'king exposed')"
    )
    conn.commit()

    profile = db.get_profile(conn, username="kishan")

    assert profile["summary"]["games"] == 2
    assert profile["summary"]["analyzed"] == 2
    assert profile["summary"]["coached"] == 1
    assert profile["summary"]["wins"] == 1
    assert profile["summary"]["losses"] == 1
    assert profile["summary"]["draws"] == 0
    assert profile["summary"]["blunders"] == 1
    assert profile["summary"]["mistakes"] == 1
    assert profile["summary"]["inaccuracies"] == 1
    assert profile["summary"]["avg_win_pct_loss"] == 22.5
    assert profile["move_quality"][0] == {"classification": "blunder", "count": 1}
    assert profile["themes"][0]["slug"] == "weak-king"
    assert profile["themes"][0]["decisive"] == 1
    assert profile["openings"][0]["opening"] == "Sicilian Defense"
    assert profile["openings"][0]["losses"] == 1
    assert profile["recent"][0]["game_id"] == 2
    assert profile["recent"][0]["opponent"] == "rival2"
