INITIAL_SCHEMA = """
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

CREATE TABLE IF NOT EXISTS bot_games (
    id INTEGER PRIMARY KEY,
    player_color TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    advanced_json TEXT NOT NULL,
    pgn TEXT NOT NULL DEFAULT '',
    fen TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    result TEXT NOT NULL DEFAULT '*',
    saved_game_id INTEGER REFERENCES games(id) ON DELETE SET NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_bot_games_status ON bot_games(status, updated_at);
"""
