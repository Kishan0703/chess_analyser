"""SQLite persistence helpers for imported and locally saved games."""
import json
import sqlite3


def insert_game(conn: sqlite3.Connection, g: dict) -> int | None:
    """Insert a game; returns new id, or None if the source_url already exists."""
    try:
        cur = conn.execute(
            """INSERT INTO games (source, source_url, pgn, white, black, white_elo,
                   black_elo, result, eco, opening, time_control, played_at, user_color)
               VALUES (:source, :source_url, :pgn, :white, :black, :white_elo,
                   :black_elo, :result, :eco, :opening, :time_control, :played_at, :user_color)""",
            g,
        )
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None


def _apply_user_color(game: dict, username: str | None) -> dict:
    if game.get("source") == "local-bot":
        return game
    if not username:
        return game
    name = username.strip().lower()
    if name == (game.get("white") or "").lower():
        game["user_color"] = "white"
    elif name == (game.get("black") or "").lower():
        game["user_color"] = "black"
    else:
        game["user_color"] = None
    return game


def list_games(conn: sqlite3.Connection, limit: int = 200,
               username: str | None = None) -> list[dict]:
    params: list = []
    where = ""
    if username:
        where = "WHERE lower(g.white) = ? OR lower(g.black) = ? OR g.source = 'local-bot'"
        name = username.strip().lower()
        params.extend([name, name])
    params.append(limit)
    rows = conn.execute(
        f"""SELECT g.id, g.white, g.black, g.white_elo, g.black_elo, g.result, g.eco,
                  g.opening, g.time_control, g.played_at, g.user_color, g.engine_analyzed,
                  g.source, g.source_url,
                  EXISTS(SELECT 1 FROM analyses a WHERE a.game_id = g.id) AS coached
           FROM games g {where} ORDER BY g.played_at DESC LIMIT ?""",
        params,
    ).fetchall()
    return [_apply_user_color(dict(r), username) for r in rows]


def get_game(conn: sqlite3.Connection, game_id: int,
             username: str | None = None) -> dict | None:
    row = conn.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
    if row is None:
        return None
    game = _apply_user_color(dict(row), username)
    game["moves"] = [
        dict(r) for r in conn.execute(
            "SELECT * FROM moves WHERE game_id = ? ORDER BY ply", (game_id,)
        )
    ]
    analysis = conn.execute(
        "SELECT * FROM analyses WHERE game_id = ?", (game_id,)
    ).fetchone()
    game["coach"] = json.loads(analysis["commentary"]) if analysis else None
    game["themes"] = [
        dict(r) for r in conn.execute(
            "SELECT * FROM themes WHERE game_id = ? ORDER BY ply_start", (game_id,)
        )
    ]
    return game


def save_engine_pass(conn: sqlite3.Connection, game_id: int, moves: list[dict]) -> None:
    conn.execute("DELETE FROM moves WHERE game_id = ?", (game_id,))
    conn.executemany(
        """INSERT INTO moves (game_id, ply, san, uci, fen_after, eval_cp, eval_mate,
               best_uci, best_san, best_line, classification, win_pct_loss)
           VALUES (:game_id, :ply, :san, :uci, :fen_after, :eval_cp, :eval_mate,
               :best_uci, :best_san, :best_line, :classification, :win_pct_loss)""",
        moves,
    )
    conn.execute("UPDATE games SET engine_analyzed = 1 WHERE id = ?", (game_id,))


def save_coach(conn: sqlite3.Connection, game_id: int, commentary: dict,
               model: str, input_tokens: int, output_tokens: int) -> None:
    conn.execute(
        """INSERT OR REPLACE INTO analyses (game_id, commentary, model, input_tokens, output_tokens)
           VALUES (?, ?, ?, ?, ?)""",
        (game_id, json.dumps(commentary), model, input_tokens, output_tokens),
    )
    conn.execute("DELETE FROM themes WHERE game_id = ?", (game_id,))
    for t in commentary.get("themes", []):
        conn.execute(
            """INSERT INTO themes (game_id, slug, side, severity, ply_start, ply_end, note)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (game_id, t.get("slug"), t.get("side"), t.get("severity"),
             t.get("ply_start"), t.get("ply_end"), t.get("note")),
        )
