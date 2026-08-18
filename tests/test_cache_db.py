import sqlite3

from backend import db


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(db.SCHEMA)
    conn.execute(
        """INSERT INTO games
           (id, source_url, pgn, white, black, result, user_color)
           VALUES (1, 'https://game/1', '1. e4 e5 *', 'kishan', 'rival', '*', 'white')"""
    )
    return conn


def test_candidate_cache_round_trips_json_and_replaces_existing_value():
    conn = make_conn()
    first = [{"move": "e4", "eval_cp": 20, "eval_mate": None, "line": "e4 e5"}]
    second = [{"move": "d4", "eval_cp": 15, "eval_mate": None, "line": "d4 d5"}]

    db.save_candidate_cache(conn, "candidate-key", "start-fen", first)
    db.save_candidate_cache(conn, "candidate-key", "start-fen", second)

    assert db.get_candidate_cache(conn, "candidate-key") == second
    row = conn.execute(
        "SELECT fen, candidates_json FROM engine_candidate_cache WHERE cache_key = ?",
        ("candidate-key",),
    ).fetchone()
    assert row["fen"] == "start-fen"
    assert '"d4"' in row["candidates_json"]


def test_moment_cache_round_trips_model_output_and_token_counts():
    conn = make_conn()
    output = {"title": "Missed break", "explanation": "You needed c4."}

    db.save_moment_cache(conn, "moment-key", 1, 7, output, "qwen3:8b", 44, 12)

    assert db.get_moment_cache(conn, "moment-key") == {
        "output": output,
        "model": "qwen3:8b",
        "input_tokens": 44,
        "output_tokens": 12,
    }


def test_summary_cache_round_trips_summary_payload():
    conn = make_conn()
    summary = {
        "opening_summary": "You reached an isolated queen pawn structure.",
        "themes": [{"slug": "isolated-queen-pawn", "side": "user"}],
        "takeaways": ["Review IQP plans."],
    }

    db.save_summary_cache(conn, "summary-key", 1, summary, "qwen3:8b", 70, 20)

    assert db.get_summary_cache(conn, "summary-key") == {
        "output": summary,
        "model": "qwen3:8b",
        "input_tokens": 70,
        "output_tokens": 20,
    }
