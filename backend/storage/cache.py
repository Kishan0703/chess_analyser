"""SQLite persistence helpers for cached engine and model results."""
import json
import sqlite3


def get_candidate_cache(conn: sqlite3.Connection, cache_key: str) -> list[dict] | None:
    row = conn.execute(
        "SELECT candidates_json FROM engine_candidate_cache WHERE cache_key = ?",
        (cache_key,),
    ).fetchone()
    return json.loads(row["candidates_json"]) if row else None


def save_candidate_cache(conn: sqlite3.Connection, cache_key: str, fen: str,
                         candidates: list[dict]) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO engine_candidate_cache
           (cache_key, fen, candidates_json)
           VALUES (?, ?, ?)""",
        (cache_key, fen, json.dumps(candidates, sort_keys=True)),
    )


def get_moment_cache(conn: sqlite3.Connection, cache_key: str) -> dict | None:
    row = conn.execute(
        """SELECT output_json, model, input_tokens, output_tokens
           FROM moment_explanation_cache
           WHERE cache_key = ?""",
        (cache_key,),
    ).fetchone()
    if row is None:
        return None
    return {
        "output": json.loads(row["output_json"]),
        "model": row["model"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
    }


def save_moment_cache(conn: sqlite3.Connection, cache_key: str, game_id: int, ply: int,
                      output: dict, model: str, input_tokens: int, output_tokens: int) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO moment_explanation_cache
           (cache_key, game_id, ply, output_json, model, input_tokens, output_tokens)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (cache_key, game_id, ply, json.dumps(output, sort_keys=True), model,
         input_tokens, output_tokens),
    )


def get_summary_cache(conn: sqlite3.Connection, cache_key: str) -> dict | None:
    row = conn.execute(
        """SELECT output_json, model, input_tokens, output_tokens
           FROM summary_cache
           WHERE cache_key = ?""",
        (cache_key,),
    ).fetchone()
    if row is None:
        return None
    return {
        "output": json.loads(row["output_json"]),
        "model": row["model"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
    }


def save_summary_cache(conn: sqlite3.Connection, cache_key: str, game_id: int,
                       output: dict, model: str, input_tokens: int, output_tokens: int) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO summary_cache
           (cache_key, game_id, output_json, model, input_tokens, output_tokens)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (cache_key, game_id, json.dumps(output, sort_keys=True), model,
         input_tokens, output_tokens),
    )
