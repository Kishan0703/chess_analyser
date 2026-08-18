# Human vs Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline human-vs-Stockfish play mode with hybrid difficulty controls, then let finished bot games enter the existing analyze and coach workflow.

**Architecture:** Add a backend `backend/play.py` module that owns bot game sessions, legal move validation, Stockfish move selection, and conversion of finished sessions into normal local games. Add FastAPI endpoints under `/api/play/bot/*`, then add a new React `Play vs Bot` view that reuses `chess.js` and `react-chessboard` for the board while treating the backend as authoritative.

**Tech Stack:** Python 3.12, FastAPI, SQLite, python-chess, Stockfish via `chess.engine`, React 19, Vite, chess.js, react-chessboard, pytest.

**Spec:** Conversation-approved hybrid design: simple difficulty presets (`Beginner`, `Casual`, `Club`, `Strong`, `Master`) plus an optional advanced panel exposing Stockfish skill level, bot move time, and randomness.

## Global Constraints

- Works offline once Stockfish and the app are installed; no Chess.com or hosted LLM dependency is required for play.
- Stockfish is the only bot move source; LLMs must not choose chess moves.
- The server is authoritative for legality, bot replies, status, and PGN persistence.
- Finished bot games must save into the existing `games` table with `source = 'local-bot'` so existing `analyze` and `coach` endpoints work unchanged.
- Do not push. Commit after each suitable completed phase.
- Preserve existing imported-game analysis and coaching behavior.

---

## File Structure

- Create `backend/play.py`: bot session domain logic, difficulty presets, legal move handling, Stockfish bot move selection, PGN export, save-to-games helper.
- Modify `backend/db.py`: add `bot_games` table and helpers for creating, reading, updating, and saving bot sessions.
- Modify `backend/app.py`: add request models and `/api/play/bot/*` routes.
- Create `tests/test_play_bot.py`: unit tests for presets, legal move flow, bot move selection via injected fake engine, game save behavior, and API route behavior.
- Modify `frontend/src/api.js`: add bot-play API methods.
- Modify `frontend/src/App.jsx`: add `Play vs Bot` navigation and route.
- Create `frontend/src/components/BotPlay.jsx`: offline play UI, difficulty controls, board, move list, game actions, save/analyze handoff.
- Modify `frontend/src/index.css`: responsive layout and controls for the bot play screen.

---

### Task 1: Bot Game Storage

**Files:**
- Modify: `backend/db.py`
- Test: `tests/test_play_bot.py`

**Interfaces:**
- Produces: `db.create_bot_game(conn, payload: dict) -> int`
- Produces: `db.get_bot_game(conn, bot_game_id: int) -> dict | None`
- Produces: `db.update_bot_game(conn, bot_game_id: int, payload: dict) -> None`

- [ ] **Step 1: Write the failing tests**

```python
import json
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py::test_bot_game_storage_round_trips_session_state tests/test_play_bot.py::test_bot_game_update_replaces_mutable_state -q`

Expected: FAIL with `AttributeError` for missing `create_bot_game`.

- [ ] **Step 3: Implement storage schema and helpers**

Add to `SCHEMA` in `backend/db.py`:

```sql
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
```

Add helpers:

```python
def create_bot_game(conn: sqlite3.Connection, payload: dict) -> int:
    cur = conn.execute(
        """INSERT INTO bot_games
           (player_color, difficulty, advanced_json, pgn, fen, status, result)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            payload["player_color"],
            payload["difficulty"],
            json.dumps(payload["advanced"], sort_keys=True),
            payload.get("pgn", ""),
            payload["fen"],
            payload.get("status", "active"),
            payload.get("result", "*"),
        ),
    )
    return cur.lastrowid


def get_bot_game(conn: sqlite3.Connection, bot_game_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM bot_games WHERE id = ?", (bot_game_id,)).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["advanced"] = json.loads(data.pop("advanced_json"))
    return data


def update_bot_game(conn: sqlite3.Connection, bot_game_id: int, payload: dict) -> None:
    conn.execute(
        """UPDATE bot_games
           SET pgn = ?, fen = ?, status = ?, result = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (payload["pgn"], payload["fen"], payload["status"], payload["result"], bot_game_id),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py -q`

Expected: PASS for the two storage tests.

- [ ] **Step 5: Commit**

```bash
git add backend/db.py tests/test_play_bot.py
git commit -m "feat: store bot play sessions"
```

---

### Task 2: Bot Play Domain Logic

**Files:**
- Create: `backend/play.py`
- Test: `tests/test_play_bot.py`

**Interfaces:**
- Consumes: DB helpers from Task 1.
- Produces: `DIFFICULTY_PRESETS: dict[str, dict]`
- Produces: `new_game(player_color: str, difficulty: str, advanced: dict | None = None) -> dict`
- Produces: `apply_player_move(bot_game_id: int, move: dict, bot_selector: Callable | None = None) -> dict`
- Produces: `serialize_board_state(session: dict, board: chess.Board) -> dict`

- [ ] **Step 1: Write the failing tests**

```python
import chess

from backend import db, play


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py -q`

Expected: FAIL with `ImportError` or `AttributeError` for missing `backend.play`.

- [ ] **Step 3: Implement `backend/play.py`**

Use `chess.Board`, `chess.pgn.Game`, and the existing `engine.resolve_engine_path()` helper. Keep bot move selection injectable so tests do not spawn Stockfish.

```python
DIFFICULTY_PRESETS = {
    "beginner": {"label": "Beginner", "skill_level": 2, "move_time_ms": 80, "randomness": 0.55},
    "casual": {"label": "Casual", "skill_level": 5, "move_time_ms": 150, "randomness": 0.35},
    "club": {"label": "Club", "skill_level": 8, "move_time_ms": 250, "randomness": 0.20},
    "strong": {"label": "Strong", "skill_level": 13, "move_time_ms": 500, "randomness": 0.08},
    "master": {"label": "Master", "skill_level": 18, "move_time_ms": 900, "randomness": 0.0},
}
```

Implement:

```python
def _legal_moves(board: chess.Board) -> list[dict]:
    return [
        {"uci": move.uci(), "from": chess.square_name(move.from_square),
         "to": chess.square_name(move.to_square),
         "promotion": chess.piece_symbol(move.promotion) if move.promotion else None,
         "san": board.san(move)}
        for move in board.legal_moves
    ]
```

Implement move status:

```python
def _status_for(board: chess.Board) -> tuple[str, str]:
    if board.is_checkmate():
        return "finished", "1-0" if board.turn == chess.BLACK else "0-1"
    if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
        return "finished", "1/2-1/2"
    return "active", "*"
```

Implement bot selection:

```python
def choose_bot_move(board: chess.Board, advanced: dict) -> chess.Move:
    cfg = settings.load()
    sf = chess.engine.SimpleEngine.popen_uci(str(engine.resolve_engine_path(cfg)))
    try:
        try:
            sf.configure({"Skill Level": int(advanced["skill_level"])})
        except Exception:
            pass
        multipv = 1 if float(advanced["randomness"]) <= 0 else 3
        infos = sf.analyse(
            board,
            chess.engine.Limit(time=int(advanced["move_time_ms"]) / 1000),
            multipv=multipv,
        )
        if isinstance(infos, dict):
            infos = [infos]
        moves = [info["pv"][0] for info in infos if info.get("pv")]
        return _pick_ranked_move(moves, float(advanced["randomness"]))
    finally:
        sf.quit()
```

Use deterministic `_pick_ranked_move()` for tests by avoiding randomness when `randomness == 0`; for non-zero randomness use `random.random()` to occasionally pick the second or third legal candidate.

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/play.py tests/test_play_bot.py
git commit -m "feat: add bot play engine"
```

---

### Task 3: Save Bot Games Into Existing Analysis Flow

**Files:**
- Modify: `backend/db.py`
- Modify: `backend/play.py`
- Test: `tests/test_play_bot.py`

**Interfaces:**
- Consumes: `db.insert_game()`
- Produces: `play.save_to_game(bot_game_id: int) -> dict`
- Produces: `db.mark_bot_game_saved(conn, bot_game_id: int, saved_game_id: int) -> None`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py::test_save_to_game_creates_local_bot_game_for_analysis -q`

Expected: FAIL with missing `save_to_game`.

- [ ] **Step 3: Implement save helpers**

Add to `backend/db.py`:

```python
def mark_bot_game_saved(conn: sqlite3.Connection, bot_game_id: int, saved_game_id: int) -> None:
    conn.execute(
        """UPDATE bot_games
           SET saved_game_id = ?, updated_at = datetime('now')
           WHERE id = ?""",
        (saved_game_id, bot_game_id),
    )
```

Add to `backend/play.py`:

```python
def save_to_game(bot_game_id: int) -> dict:
    with db.connect() as conn:
        session = db.get_bot_game(conn, bot_game_id)
        if session is None:
            raise ValueError("bot game not found")
        if session.get("saved_game_id"):
            return {"game_id": session["saved_game_id"]}
        game_id = db.insert_game(conn, {
            "source": "local-bot",
            "source_url": f"local-bot:{bot_game_id}",
            "pgn": session["pgn"],
            "white": "You" if session["player_color"] == "white" else "ChessCoach Bot",
            "black": "ChessCoach Bot" if session["player_color"] == "white" else "You",
            "white_elo": None,
            "black_elo": None,
            "result": session["result"],
            "eco": None,
            "opening": "Bot practice",
            "time_control": "offline",
            "played_at": None,
            "user_color": session["player_color"],
        })
        if game_id is None:
            row = conn.execute(
                "SELECT id FROM games WHERE source_url = ?", (f"local-bot:{bot_game_id}",)
            ).fetchone()
            game_id = row["id"]
        db.mark_bot_game_saved(conn, bot_game_id, game_id)
        conn.commit()
        return {"game_id": game_id}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/db.py backend/play.py tests/test_play_bot.py
git commit -m "feat: save bot games for analysis"
```

---

### Task 4: Bot Play API

**Files:**
- Modify: `backend/app.py`
- Test: `tests/test_play_bot.py`

**Interfaces:**
- Consumes: `play.new_game()`, `play.apply_player_move()`, `play.save_to_game()`
- Produces: `POST /api/play/bot/games`
- Produces: `GET /api/play/bot/games/{bot_game_id}`
- Produces: `POST /api/play/bot/games/{bot_game_id}/move`
- Produces: `POST /api/play/bot/games/{bot_game_id}/save`

- [ ] **Step 1: Write failing API tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py::test_bot_play_api_starts_game tests/test_play_bot.py::test_bot_play_api_maps_illegal_move_to_400 -q`

Expected: FAIL with missing routes or missing `app_module.play`.

- [ ] **Step 3: Implement API models and routes**

Modify imports:

```python
from . import chesscom, coach, db, engine, play, settings
```

Add models:

```python
class BotGameCreate(BaseModel):
    player_color: str = "white"
    difficulty: str = "club"
    advanced: dict | None = None


class BotMoveRequest(BaseModel):
    from_square: str = Field(alias="from")
    to: str
    promotion: str | None = None
```

Add routes before the static mount:

```python
@app.post("/api/play/bot/games")
def create_bot_game(req: BotGameCreate):
    try:
        return play.new_game(req.player_color, req.difficulty, req.advanced)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"bot game error: {e}")


@app.get("/api/play/bot/games/{bot_game_id}")
def get_bot_game(bot_game_id: int):
    try:
        return play.get_game(bot_game_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/api/play/bot/games/{bot_game_id}/move")
def play_bot_move(bot_game_id: int, req: BotMoveRequest):
    try:
        return play.apply_player_move(
            bot_game_id,
            {"from": req.from_square, "to": req.to, "promotion": req.promotion},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"bot move error: {e}")


@app.post("/api/play/bot/games/{bot_game_id}/save")
def save_bot_game(bot_game_id: int):
    try:
        return play.save_to_game(bot_game_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest tests/test_play_bot.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app.py tests/test_play_bot.py
git commit -m "feat: expose bot play api"
```

---

### Task 5: Frontend API and Navigation

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/App.jsx`
- Create: `frontend/src/components/BotPlay.jsx`

**Interfaces:**
- Consumes: `/api/play/bot/*` routes from Task 4.
- Produces: `api.createBotGame()`, `api.getBotGame()`, `api.playBotMove()`, `api.saveBotGame()`
- Produces: app route `#/play`

- [ ] **Step 1: Add frontend API methods**

Modify `frontend/src/api.js`:

```javascript
createBotGame: (payload) =>
  request('/api/play/bot/games', { method: 'POST', body: JSON.stringify(payload) }),
getBotGame: (id) => request(`/api/play/bot/games/${id}`),
playBotMove: (id, move) =>
  request(`/api/play/bot/games/${id}/move`, { method: 'POST', body: JSON.stringify(move) }),
saveBotGame: (id) =>
  request(`/api/play/bot/games/${id}/save`, { method: 'POST' }),
```

- [ ] **Step 2: Add route and nav item**

Modify `NAV_ITEMS` in `frontend/src/App.jsx`:

```javascript
{ view: { name: 'play' }, id: 'play', icon: '04', label: 'Play vs Bot' },
```

Modify `viewFromLocation()`:

```javascript
if (name === 'play') return { name: 'play' }
```

Modify `hashForView()`:

```javascript
if (view.name === 'play') return '#/play'
```

Render:

```jsx
{view.name === 'play' && (
  <BotPlay onOpenGame={(id) => navigate({ name: 'game', id })} />
)}
```

- [ ] **Step 3: Create a minimal `BotPlay` shell**

Create `frontend/src/components/BotPlay.jsx`:

```jsx
export default function BotPlay({ onOpenGame }) {
  return (
    <section className="bot-play">
      <div className="section-head">
        <div>
          <p className="eyebrow">Offline practice</p>
          <h1>Play vs Bot</h1>
        </div>
      </div>
      <div className="status-line">Choose a side and difficulty to start a local Stockfish game.</div>
    </section>
  )
}
```

- [ ] **Step 4: Run frontend build**

Run: `cd frontend && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api.js frontend/src/App.jsx frontend/src/components/BotPlay.jsx
git commit -m "feat: add bot play navigation"
```

---

### Task 6: Play vs Bot UI

**Files:**
- Modify: `frontend/src/components/BotPlay.jsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: frontend API methods from Task 5.
- Produces: playable UI with difficulty presets, advanced toggle, board move handling, game status, move list, save/analyze button.

- [ ] **Step 1: Implement state and controls**

In `BotPlay.jsx`, use:

```javascript
const PRESETS = {
  beginner: { label: 'Beginner', skill_level: 2, move_time_ms: 80, randomness: 0.55 },
  casual: { label: 'Casual', skill_level: 5, move_time_ms: 150, randomness: 0.35 },
  club: { label: 'Club', skill_level: 8, move_time_ms: 250, randomness: 0.2 },
  strong: { label: 'Strong', skill_level: 13, move_time_ms: 500, randomness: 0.08 },
  master: { label: 'Master', skill_level: 18, move_time_ms: 900, randomness: 0 },
}
```

State:

```javascript
const [playerColor, setPlayerColor] = useState('white')
const [difficulty, setDifficulty] = useState('club')
const [advancedOpen, setAdvancedOpen] = useState(false)
const [advanced, setAdvanced] = useState(PRESETS.club)
const [session, setSession] = useState(null)
const [busy, setBusy] = useState(false)
const [error, setError] = useState('')
```

- [ ] **Step 2: Implement start game**

```javascript
const startGame = async () => {
  setBusy(true)
  setError('')
  try {
    const next = await api.createBotGame({ player_color: playerColor, difficulty, advanced })
    setSession(next)
  } catch (e) {
    setError(e.message)
  } finally {
    setBusy(false)
  }
}
```

- [ ] **Step 3: Implement board move handler**

Use `react-chessboard` `onPieceDrop`:

```javascript
const onPieceDrop = async (sourceSquare, targetSquare, piece) => {
  if (!session || busy || session.status !== 'active') return false
  setBusy(true)
  setError('')
  try {
    const promotion = piece?.[1]?.toLowerCase() === 'p' &&
      (targetSquare.endsWith('8') || targetSquare.endsWith('1')) ? 'q' : undefined
    const next = await api.playBotMove(session.id, {
      from: sourceSquare,
      to: targetSquare,
      promotion,
    })
    setSession(next)
    return true
  } catch (e) {
    setError(e.message)
    return false
  } finally {
    setBusy(false)
  }
}
```

- [ ] **Step 4: Implement save and analyze handoff**

```javascript
const saveAndAnalyze = async () => {
  if (!session) return
  setBusy(true)
  try {
    const result = await api.saveBotGame(session.id)
    onOpenGame(result.game_id)
  } catch (e) {
    setError(e.message)
  } finally {
    setBusy(false)
  }
}
```

- [ ] **Step 5: Style the screen**

Add `.bot-play`, `.bot-play-layout`, `.bot-controls`, `.bot-board`, `.difficulty-grid`, `.advanced-panel`, `.bot-move-list`, and `.bot-actions` to `frontend/src/index.css`. Use the existing dashboard/card visual language, 8px or smaller border radii, responsive two-column layout on desktop and one-column on mobile.

- [ ] **Step 6: Run frontend build**

Run: `cd frontend && npm run build`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/BotPlay.jsx frontend/src/index.css
git commit -m "feat: build bot play screen"
```

---

### Task 7: End-to-End Verification

**Files:**
- Modify only files needed to fix failures found during verification.

**Interfaces:**
- Consumes all previous tasks.
- Produces verified offline play flow.

- [ ] **Step 1: Run backend tests**

Run: `/usr/bin/env PYTHONPATH=. .venv/bin/pytest -q`

Expected: PASS.

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && npm run build`

Expected: PASS.

- [ ] **Step 3: Manual smoke test locally**

Run backend and frontend using the project’s normal dev commands. In the browser:

1. Open `Play vs Bot`.
2. Start as White on `Beginner`.
3. Play `e2-e4`.
4. Confirm the bot replies and the board updates.
5. Toggle Advanced, change skill level and move time, start a new game.
6. Finish or save the game.
7. Confirm saved game opens in the existing game viewer.
8. Run Analyze on the saved bot game.

- [ ] **Step 4: Commit verification fixes if any**

```bash
git add backend/play.py backend/app.py backend/db.py tests/test_play_bot.py frontend/src/api.js frontend/src/App.jsx frontend/src/components/BotPlay.jsx frontend/src/index.css
git commit -m "fix: polish bot play flow"
```

Only run this commit if Step 1-3 changed one or more of those files.

---

## Self-Review

- Spec coverage: The plan covers offline play, hybrid difficulty, Stockfish bot moves, game persistence, existing analyze/coach handoff, UI, API, and tests.
- Placeholder scan: No implementation step depends on unresolved placeholders.
- Type consistency: Backend route names, API method names, and frontend consumer names match across tasks.
