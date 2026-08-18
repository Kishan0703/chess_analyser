"""SQLite schema and access helpers.

Schema is designed so cross-game profiling (phase 3) is a GROUP BY over
`themes` and `moves.classification`, not a migration.
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "chesscoach.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL DEFAULT 'chess.com',
    source_url TEXT UNIQUE,
    pgn TEXT NOT NULL,
    white TEXT, black TEXT,
    white_elo INTEGER, black_elo INTEGER,
    result TEXT, eco TEXT, opening TEXT,
    time_control TEXT, played_at TEXT,
    user_color TEXT,                -- 'white' | 'black' (relative to configured user)
    engine_analyzed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS moves (
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    ply INTEGER NOT NULL,           -- 1-based half-move number
    san TEXT NOT NULL,
    uci TEXT NOT NULL,
    fen_after TEXT NOT NULL,
    eval_cp INTEGER,                -- white-POV centipawns after the move
    eval_mate INTEGER,              -- white-POV mate distance after the move (overrides eval_cp)
    best_uci TEXT,                  -- engine best move in the position before this move
    best_san TEXT,
    best_line TEXT,                 -- SAN pv of the best line, space separated
    classification TEXT,            -- best/good/inaccuracy/mistake/blunder
    win_pct_loss REAL,              -- mover's win% lost by this move vs engine best
    PRIMARY KEY (game_id, ply)
);

CREATE TABLE IF NOT EXISTS analyses (
    game_id INTEGER PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,
    commentary TEXT NOT NULL,       -- JSON blob from the coach
    model TEXT,
    input_tokens INTEGER, output_tokens INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS themes (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,             -- controlled vocabulary, e.g. 'isolated-queen-pawn'
    side TEXT,                      -- 'user' | 'opponent' | 'both'
    severity TEXT,                  -- 'minor' | 'significant' | 'decisive'
    ply_start INTEGER, ply_end INTEGER,
    note TEXT
);
CREATE INDEX IF NOT EXISTS idx_themes_slug ON themes(slug);

CREATE TABLE IF NOT EXISTS engine_candidate_cache (
    cache_key TEXT PRIMARY KEY,
    fen TEXT NOT NULL,
    candidates_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS moment_explanation_cache (
    cache_key TEXT PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    ply INTEGER NOT NULL,
    output_json TEXT NOT NULL,
    model TEXT,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_moment_explanation_cache_game
    ON moment_explanation_cache(game_id, ply);

CREATE TABLE IF NOT EXISTS summary_cache (
    cache_key TEXT PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    output_json TEXT NOT NULL,
    model TEXT,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_summary_cache_game ON summary_cache(game_id);
"""


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


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
        where = "WHERE lower(g.white) = ? OR lower(g.black) = ?"
        name = username.strip().lower()
        params.extend([name, name])
    params.append(limit)
    rows = conn.execute(
        f"""SELECT g.id, g.white, g.black, g.white_elo, g.black_elo, g.result, g.eco,
                  g.opening, g.time_control, g.played_at, g.user_color, g.engine_analyzed,
                  g.source_url,
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


def get_profile(conn: sqlite3.Connection, username: str | None = None,
                limit_games: int = 200) -> dict:
    name = username.strip().lower() if username else None
    user_where = ""
    user_params: list = []
    if name:
        user_where = "WHERE lower(g.white) = ? OR lower(g.black) = ?"
        user_params = [name, name]

    games = [dict(r) for r in conn.execute(
        f"""SELECT g.*,
                  EXISTS(SELECT 1 FROM analyses a WHERE a.game_id = g.id) AS coached
           FROM games g
           {user_where}
           ORDER BY g.played_at DESC
           LIMIT ?""",
        [*user_params, limit_games],
    ).fetchall()]

    game_ids = [g["id"] for g in games]
    if not game_ids:
        return {
            "summary": {
                "games": 0, "analyzed": 0, "coached": 0, "wins": 0, "losses": 0,
                "draws": 0, "unknown_results": 0, "blunders": 0, "mistakes": 0, "inaccuracies": 0,
                "avg_win_pct_loss": 0.0,
            },
            "move_quality": [],
            "themes": [],
            "openings": [],
            "recent": [],
        }

    analyzed_games = [g for g in games if g.get("engine_analyzed")]
    analyzed_game_ids = [g["id"] for g in analyzed_games]

    def user_color_for(g: dict) -> str | None:
        if name == (g.get("white") or "").lower():
            return "white"
        if name == (g.get("black") or "").lower():
            return "black"
        return g.get("user_color")

    def is_user_move(ply: int, color: str | None) -> bool:
        if color is None:
            return True
        return (color == "white") == (ply % 2 == 1)

    def result_for(g: dict) -> str:
        result = g.get("result")
        color = user_color_for(g)
        if result == "1/2-1/2":
            return "draw"
        if result == "1-0" and color == "white":
            return "win"
        if result == "1-0" and color == "black":
            return "loss"
        if result == "0-1" and color == "black":
            return "win"
        if result == "0-1" and color == "white":
            return "loss"
        return "unknown"

    moves_by_game: dict[int, list[dict]] = {gid: [] for gid in analyzed_game_ids}
    if analyzed_game_ids:
        placeholders = ",".join("?" for _ in analyzed_game_ids)
        for r in conn.execute(
            f"""SELECT game_id, ply, classification, win_pct_loss
                FROM moves
                WHERE game_id IN ({placeholders})""",
            analyzed_game_ids,
        ):
            moves_by_game[r["game_id"]].append(dict(r))

    classifications = {"blunder": 0, "mistake": 0, "inaccuracy": 0, "best": 0, "great": 0,
                       "brilliant": 0, "good": 0}
    losses = []
    for g in analyzed_games:
        color = user_color_for(g)
        for m in moves_by_game[g["id"]]:
            if not is_user_move(m["ply"], color):
                continue
            cls = m.get("classification")
            if cls in classifications:
                classifications[cls] += 1
            if cls in {"blunder", "mistake", "inaccuracy"} and m.get("win_pct_loss") is not None:
                losses.append(float(m["win_pct_loss"]))

    theme_rows = []
    if analyzed_game_ids:
        theme_rows = [dict(r) for r in conn.execute(
            f"""SELECT slug,
                      COUNT(*) AS count,
                      SUM(CASE WHEN severity = 'decisive' THEN 1 ELSE 0 END) AS decisive,
                      SUM(CASE WHEN severity = 'significant' THEN 1 ELSE 0 END) AS significant,
                      SUM(CASE WHEN severity = 'minor' THEN 1 ELSE 0 END) AS minor
                FROM themes
                WHERE game_id IN ({placeholders})
                  AND (side IS NULL OR side IN ('user', 'both'))
                GROUP BY slug
                ORDER BY count DESC, slug ASC
                LIMIT 12""",
            analyzed_game_ids,
        ).fetchall()]

    openings = []
    for opening in sorted({g.get("opening") or g.get("eco") or "Unknown" for g in analyzed_games}):
        group = [g for g in analyzed_games if (g.get("opening") or g.get("eco") or "Unknown") == opening]
        opening_losses = []
        for g in group:
            color = user_color_for(g)
            for m in moves_by_game[g["id"]]:
                if (is_user_move(m["ply"], color)
                        and m.get("classification") in {"blunder", "mistake", "inaccuracy"}
                        and m.get("win_pct_loss") is not None):
                    opening_losses.append(float(m["win_pct_loss"]))
        openings.append({
            "opening": opening,
            "games": len(group),
            "wins": sum(1 for g in group if result_for(g) == "win"),
            "losses": sum(1 for g in group if result_for(g) == "loss"),
            "draws": sum(1 for g in group if result_for(g) == "draw"),
            "avg_loss": round(sum(opening_losses) / len(opening_losses), 1) if opening_losses else 0.0,
        })
    openings.sort(key=lambda o: (o["losses"], o["avg_loss"], o["games"]), reverse=True)

    themes_by_game: dict[int, list[str]] = {gid: [] for gid in analyzed_game_ids}
    if analyzed_game_ids:
        for r in conn.execute(
            f"""SELECT game_id, slug FROM themes
                WHERE game_id IN ({placeholders})
                  AND (side IS NULL OR side IN ('user', 'both'))
                ORDER BY slug""",
            analyzed_game_ids,
        ):
            themes_by_game[r["game_id"]].append(r["slug"])

    recent = []
    for g in analyzed_games[:10]:
        color = user_color_for(g)
        user_moves = [m for m in moves_by_game[g["id"]] if is_user_move(m["ply"], color)]
        opponent = g.get("black") if color == "white" else g.get("white")
        recent.append({
            "game_id": g["id"],
            "played_at": g.get("played_at"),
            "opponent": opponent or "",
            "result": result_for(g),
            "blunders": sum(1 for m in user_moves if m.get("classification") == "blunder"),
            "mistakes": sum(1 for m in user_moves if m.get("classification") == "mistake"),
            "themes": themes_by_game[g["id"]][:4],
        })

    return {
        "summary": {
            "games": len(games),
            "analyzed": sum(1 for g in games if g.get("engine_analyzed")),
            "coached": sum(1 for g in games if g.get("coached")),
            "wins": sum(1 for g in games if result_for(g) == "win"),
            "losses": sum(1 for g in games if result_for(g) == "loss"),
            "draws": sum(1 for g in games if result_for(g) == "draw"),
            "unknown_results": sum(1 for g in games if result_for(g) == "unknown"),
            "blunders": classifications["blunder"],
            "mistakes": classifications["mistake"],
            "inaccuracies": classifications["inaccuracy"],
            "avg_win_pct_loss": round(sum(losses) / len(losses), 1) if losses else 0.0,
        },
        "move_quality": [
            {"classification": cls, "count": count}
            for cls, count in classifications.items()
            if count
        ],
        "themes": theme_rows,
        "openings": openings[:8],
        "recent": recent,
    }


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
