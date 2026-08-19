# ChessCoach Repo Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize ChessCoach for maintainability by adding a safe SQLite migration path, splitting backend responsibilities, and migrating the frontend from JavaScript/JSX to TypeScript/TSX.

**Architecture:** Keep the app local-first with FastAPI, SQLite, and Vite React. Make the smallest structural changes that create durable boundaries: API routers, storage modules, migration scripts, typed frontend API contracts, and feature-oriented frontend folders.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, pytest, React, Vite, TypeScript, ESLint.

**Spec:** This plan is the source-of-truth modernization spec. No separate design doc exists yet.

## Global Constraints

- Do not replace SQLite with Postgres; the app is local-first and SQLite is the right default.
- Do not convert backend persistence to SQLAlchemy in this pass; use the existing `sqlite3` style.
- Preserve current API behavior and response shapes unless a task explicitly updates tests and frontend consumers.
- Keep migration work backward-compatible with existing `chesscoach.db` files.
- Frontend React components use `.tsx`; non-React frontend modules use `.ts`.
- Keep changes phased and independently testable.
- Avoid unrelated redesign, styling changes, or product behavior changes.

---

## Target Structure

```text
backend/
  main.py                  # FastAPI app creation, startup, static mount
  app.py                   # Temporary compatibility shim importing app from main
  api/
    __init__.py
    settings.py            # /api/settings
    onboarding.py          # /api/onboarding
    games.py               # /api/games, game detail, import
    analysis.py            # engine analysis endpoints and job status
    coaching.py            # coaching, explanations, chat
    play.py                # bot play endpoints
  schemas/
    __init__.py
    requests.py            # Pydantic request models
  storage/
    __init__.py
    connection.py          # DB_PATH, connect()
    migrations.py          # PRAGMA user_version migration runner
    schema.py              # latest schema constants
    games.py               # game queries and writes
    profile.py             # training profile aggregation
    cache.py               # candidate/moment/summary cache helpers
    bot_games.py           # bot game persistence
```

```text
frontend/src/
  app/
    App.tsx                # shell and navigation
    routes.ts              # hash route parsing/building
  api/
    client.ts              # typed request helper
    chesscoach.ts          # typed API methods
  types/
    api.ts                 # shared frontend response/request types
  features/
    games/
    analysis/
    profile/
    settings/
    play/
  shared/
    components/
    theme.ts
```

## Task 1: Add SQLite Migration Infrastructure

**Files:**
- Create: `backend/storage/__init__.py`
- Create: `backend/storage/connection.py`
- Create: `backend/storage/schema.py`
- Create: `backend/storage/migrations.py`
- Modify: `backend/db.py`
- Test: `tests/test_migrations.py`

**Interfaces:**
- Produces: `backend.storage.connection.connect() -> sqlite3.Connection`
- Produces: `backend.storage.migrations.migrate(conn: sqlite3.Connection) -> None`
- Produces: `backend.storage.migrations.CURRENT_SCHEMA_VERSION: int`
- Consumes: existing SQL from `backend/db.py`

- [ ] **Step 1: Write migration tests**

Create `tests/test_migrations.py`:

```python
import sqlite3

from backend.storage.migrations import CURRENT_SCHEMA_VERSION, migrate


def test_migrate_creates_latest_schema():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    migrate(conn)

    version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == CURRENT_SCHEMA_VERSION
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert {"games", "moves", "analyses", "themes", "bot_games"}.issubset(tables)


def test_migrate_is_idempotent():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    migrate(conn)
    migrate(conn)

    assert conn.execute("PRAGMA user_version").fetchone()[0] == CURRENT_SCHEMA_VERSION
```

- [ ] **Step 2: Run the failing migration tests**

Run: `.venv/bin/python -m pytest tests/test_migrations.py -v`

Expected: FAIL because `backend.storage.migrations` does not exist.

- [ ] **Step 3: Add storage package and migration runner**

Create `backend/storage/connection.py`:

```python
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "chesscoach.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

Move the current schema SQL from `backend/db.py` into `backend/storage/schema.py` as `INITIAL_SCHEMA`.

Create `backend/storage/migrations.py`:

```python
import sqlite3

from .schema import INITIAL_SCHEMA

CURRENT_SCHEMA_VERSION = 1


def _version(conn: sqlite3.Connection) -> int:
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _set_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn: sqlite3.Connection) -> None:
    version = _version(conn)
    if version == 0:
        conn.executescript(INITIAL_SCHEMA)
        _set_version(conn, CURRENT_SCHEMA_VERSION)
        return
    if version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {version} is newer than app version "
            f"{CURRENT_SCHEMA_VERSION}"
        )
```

Update `backend/db.py`:

```python
from .storage.connection import DB_PATH, connect
from .storage.migrations import migrate


def init_db() -> None:
    with connect() as conn:
        migrate(conn)
```

- [ ] **Step 4: Run migration tests**

Run: `.venv/bin/python -m pytest tests/test_migrations.py -v`

Expected: PASS.

- [ ] **Step 5: Run existing backend tests**

Run: `.venv/bin/python -m pytest tests -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/db.py backend/storage tests/test_migrations.py
git commit -m "chore: add sqlite migration infrastructure"
```

## Task 2: Split FastAPI App Into Routers

**Files:**
- Create: `backend/main.py`
- Create: `backend/api/*.py`
- Create: `backend/schemas/requests.py`
- Modify: `backend/app.py`
- Test: `tests/test_api_routes.py`

**Interfaces:**
- Produces: `backend.main.app`
- Produces: `backend.app.app` compatibility import
- Consumes: existing endpoint paths under `/api/*`

- [ ] **Step 1: Write route smoke tests**

Create `tests/test_api_routes.py`:

```python
from fastapi.testclient import TestClient

from backend.app import app


def test_settings_route_available():
    client = TestClient(app)
    response = client.get("/api/settings")
    assert response.status_code == 200


def test_openapi_contains_existing_routes():
    client = TestClient(app)
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/games" in paths
    assert "/api/profile" in paths
    assert "/api/play/bot/games" in paths
```

- [ ] **Step 2: Run route smoke tests before refactor**

Run: `.venv/bin/python -m pytest tests/test_api_routes.py -v`

Expected: PASS before moving code.

- [ ] **Step 3: Move request models**

Create `backend/schemas/requests.py` and move these classes from `backend/app.py`:

```python
ImportRequest
ChatMessage
ChatRequest
SettingsUpdate
BotAdvancedSettings
BotGameCreate
BotMoveRequest
```

- [ ] **Step 4: Create routers**

Split endpoint functions from `backend/app.py` into these modules with `router = APIRouter()`:

```text
backend/api/settings.py      -> /api/settings
backend/api/onboarding.py    -> /api/onboarding
backend/api/games.py         -> /api/import, /api/games, /api/profile, /api/games/{game_id}
backend/api/analysis.py      -> /api/games/{game_id}/analyze, status, bestline, position
backend/api/coaching.py      -> /api/games/{game_id}/coach, explanation, chat
backend/api/play.py          -> /api/play/bot/*
```

Keep `_jobs` in `backend/api/analysis.py`. Keep `_coach_jobs` in `backend/api/coaching.py`.

- [ ] **Step 5: Add app factory**

Create `backend/main.py`:

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import db
from .api import analysis, coaching, games, onboarding, play, settings


def create_app() -> FastAPI:
    app = FastAPI(title="ChessCoach")
    db.init_db()
    app.include_router(settings.router)
    app.include_router(onboarding.router)
    app.include_router(games.router)
    app.include_router(analysis.router)
    app.include_router(coaching.router)
    app.include_router(play.router)

    dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if dist.exists():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
```

Replace `backend/app.py` with:

```python
from .main import app
```

- [ ] **Step 6: Run API tests**

Run: `.venv/bin/python -m pytest tests/test_api_routes.py tests -v`

Expected: PASS.

- [ ] **Step 7: Verify server import path still works**

Run: `.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8421`

Expected: Uvicorn starts without import errors. Stop the server after verification.

- [ ] **Step 8: Commit**

```bash
git add backend/app.py backend/main.py backend/api backend/schemas tests/test_api_routes.py
git commit -m "refactor: split fastapi routes"
```

## Task 3: Split Backend Persistence Modules

**Files:**
- Create: `backend/storage/games.py`
- Create: `backend/storage/profile.py`
- Create: `backend/storage/cache.py`
- Create: `backend/storage/bot_games.py`
- Modify: `backend/db.py`
- Test: existing `tests/test_cache_db.py`, `tests/test_profile.py`, `tests/test_play_bot.py`

**Interfaces:**
- Preserve public `backend.db` function names during this task.
- Move implementation into storage modules and re-export from `backend/db.py`.

- [ ] **Step 1: Run persistence tests before refactor**

Run: `.venv/bin/python -m pytest tests/test_cache_db.py tests/test_profile.py tests/test_play_bot.py -v`

Expected: PASS before moving code.

- [ ] **Step 2: Move bot game helpers**

Move these functions from `backend/db.py` to `backend/storage/bot_games.py`:

```python
create_bot_game
get_bot_game
update_bot_game
mark_bot_game_saved
```

Import and re-export them from `backend/db.py`.

- [ ] **Step 3: Move game helpers**

Move these functions to `backend/storage/games.py`:

```python
insert_game
_apply_user_color
list_games
get_game
save_engine_pass
save_coach
```

Import and re-export them from `backend/db.py`.

- [ ] **Step 4: Move profile aggregation**

Move `get_profile` to `backend/storage/profile.py`.

Import and re-export it from `backend/db.py`.

- [ ] **Step 5: Move cache helpers**

Move these functions to `backend/storage/cache.py`:

```python
get_candidate_cache
save_candidate_cache
get_moment_cache
save_moment_cache
get_summary_cache
save_summary_cache
```

Import and re-export them from `backend/db.py`.

- [ ] **Step 6: Run persistence tests after each move**

Run after each step above:

```bash
.venv/bin/python -m pytest tests/test_cache_db.py tests/test_profile.py tests/test_play_bot.py -v
```

Expected: PASS after every move.

- [ ] **Step 7: Run full backend suite**

Run: `.venv/bin/python -m pytest tests -v`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/db.py backend/storage tests
git commit -m "refactor: split sqlite storage modules"
```

## Task 4: Add TypeScript Tooling

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/eslint.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Modify: `frontend/vite.config.js`

**Interfaces:**
- Produces: `npm run typecheck`
- Keeps existing `npm run dev`, `npm run build`, and `npm run lint`

- [ ] **Step 1: Add TypeScript dependencies**

Run:

```bash
cd frontend
npm install -D typescript @types/node typescript-eslint
```

- [ ] **Step 2: Add TypeScript config**

Create `frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "allowJs": true,
    "checkJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.js"]
}
```

- [ ] **Step 3: Add script**

In `frontend/package.json`, add:

```json
"typecheck": "tsc --noEmit"
```

- [ ] **Step 4: Verify tooling**

Run:

```bash
cd frontend
npm run typecheck
npm run build
```

Expected: both commands pass while existing `.js` and `.jsx` files still exist.

- [ ] **Step 5: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/tsconfig.json frontend/tsconfig.node.json frontend/eslint.config.js frontend/vite.config.js
git commit -m "chore: add frontend typescript tooling"
```

## Task 5: Type the Frontend API Boundary

**Files:**
- Create: `frontend/src/types/api.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/chesscoach.ts`
- Modify: `frontend/src/api.js`
- Modify: frontend imports that consume `api`

**Interfaces:**
- Produces: `export const api` from `frontend/src/api/chesscoach.ts`
- Produces: request/response types in `frontend/src/types/api.ts`

- [ ] **Step 1: Create API types**

Create `frontend/src/types/api.ts` with initial shared types:

```ts
export type MoveClassification =
  | 'best'
  | 'great'
  | 'brilliant'
  | 'good'
  | 'inaccuracy'
  | 'mistake'
  | 'blunder'

export interface GameSummary {
  id: number
  white: string | null
  black: string | null
  white_elo: number | null
  black_elo: number | null
  result: string | null
  eco: string | null
  opening: string | null
  time_control: string | null
  played_at: string | null
  user_color: 'white' | 'black' | null
  engine_analyzed: 0 | 1 | boolean
  source: string
  source_url: string | null
  coached: 0 | 1 | boolean
}

export interface GameMove {
  game_id: number
  ply: number
  san: string
  uci: string
  fen_after: string
  eval_cp: number | null
  eval_mate: number | null
  best_uci: string | null
  best_san: string | null
  best_line: string | null
  classification: MoveClassification | string | null
  win_pct_loss: number | null
}

export interface GameDetail extends GameSummary {
  pgn: string
  moves: GameMove[]
  coach: unknown | null
  themes: unknown[]
}

export interface SettingsPayload {
  anthropic_api_key?: string | boolean | null
  gemini_api_key?: string | boolean | null
  chesscom_username?: string | null
  claude_model?: string | null
  gemini_model?: string | null
  gemini_fallback_models?: string | null
  engine_movetime_ms?: number | null
  engine_multipv?: number | null
  engine_threads?: number | null
  stockfish_path?: string | null
  coach_provider?: string | null
  ollama_url?: string | null
  ollama_model?: string | null
}

export interface JobStatus {
  status: 'not_started' | 'started' | 'already_running' | 'running' | 'done' | 'error'
  done?: number
  total?: number
  label?: string
  error?: string
}
```

- [ ] **Step 2: Create typed request helper**

Create `frontend/src/api/client.ts`:

```ts
export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? detail
    } catch {
      // Keep HTTP status text when the backend does not return JSON.
    }
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}
```

- [ ] **Step 3: Create typed API object**

Create `frontend/src/api/chesscoach.ts` using the same method names from `api.js`, returning typed promises for settings, games, game detail, and job statuses first. Use `unknown` for coach report shapes until those are typed in a later task.

- [ ] **Step 4: Replace imports**

Change imports from:

```js
import { api } from '../api.js'
```

to:

```ts
import { api } from '../api/chesscoach'
```

- [ ] **Step 5: Remove old API module**

Delete `frontend/src/api.js` after all imports use `frontend/src/api/chesscoach.ts`.

- [ ] **Step 6: Verify**

Run:

```bash
cd frontend
npm run typecheck
npm run build
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/src frontend/package.json frontend/package-lock.json
git commit -m "refactor: type frontend api client"
```

## Task 6: Convert React Shell and Utilities to TypeScript

**Files:**
- Move: `frontend/src/App.jsx` to `frontend/src/app/App.tsx`
- Move: `frontend/src/main.jsx` to `frontend/src/main.tsx`
- Move: `frontend/src/theme.js` to `frontend/src/shared/theme.ts`
- Move: `frontend/src/timeControl.js` to `frontend/src/shared/timeControl.ts`
- Move: `frontend/src/botPlayMoves.js` to `frontend/src/features/play/botPlayMoves.ts`
- Modify: related imports
- Test: existing frontend tests

**Interfaces:**
- React components use `.tsx`.
- Pure helpers use `.ts`.

- [ ] **Step 1: Move pure helpers first**

Move non-React helper files to `.ts`:

```text
frontend/src/timeControl.js -> frontend/src/shared/timeControl.ts
frontend/src/theme.js -> frontend/src/shared/theme.ts
frontend/src/botPlayMoves.js -> frontend/src/features/play/botPlayMoves.ts
```

Update imports in tests and components.

- [ ] **Step 2: Move app shell**

Move:

```text
frontend/src/App.jsx -> frontend/src/app/App.tsx
frontend/src/main.jsx -> frontend/src/main.tsx
```

Update `main.tsx` import to:

```ts
import App from './app/App'
```

- [ ] **Step 3: Add route types**

Create `frontend/src/app/routes.ts`:

```ts
export type AppView =
  | { name: 'list' }
  | { name: 'profile' }
  | { name: 'settings' }
  | { name: 'play' }
  | { name: 'game'; id: string }
```

Move `viewFromLocation()` and `hashForView()` from `App.tsx` into `routes.ts`.

- [ ] **Step 4: Verify**

Run:

```bash
cd frontend
npm run typecheck
npm run build
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src
git commit -m "refactor: convert frontend shell to typescript"
```

## Task 7: Convert Feature Components to TSX

**Files:**
- Move: `frontend/src/components/*.jsx` into feature folders as `.tsx`
- Modify: imports and props
- Test: frontend build and typecheck

**Interfaces:**
- Components with JSX use `.tsx`.
- Component props get explicit interfaces.

- [ ] **Step 1: Convert settings and profile**

Move:

```text
frontend/src/components/Settings.jsx -> frontend/src/features/settings/Settings.tsx
frontend/src/components/Profile.jsx -> frontend/src/features/profile/Profile.tsx
```

Add prop interfaces:

```ts
interface ProfileProps {
  onOpenGame: (id: number | string) => void
}
```

- [ ] **Step 2: Convert games and analysis**

Move:

```text
frontend/src/components/GameList.jsx -> frontend/src/features/games/GameList.tsx
frontend/src/components/GameView.jsx -> frontend/src/features/games/GameView.tsx
frontend/src/components/MoveList.jsx -> frontend/src/features/analysis/MoveList.tsx
frontend/src/components/EvalGraph.jsx -> frontend/src/features/analysis/EvalGraph.tsx
frontend/src/components/CoachPanel.jsx -> frontend/src/features/analysis/CoachPanel.tsx
frontend/src/components/PositionAnalysis.jsx -> frontend/src/features/analysis/PositionAnalysis.tsx
frontend/src/components/GameChat.jsx -> frontend/src/features/analysis/GameChat.tsx
```

- [ ] **Step 3: Convert play**

Move:

```text
frontend/src/components/BotPlay.jsx -> frontend/src/features/play/BotPlay.tsx
```

- [ ] **Step 4: Convert shared UI**

Move:

```text
frontend/src/components/InfoTip.jsx -> frontend/src/shared/components/InfoTip.tsx
frontend/src/components/Onboarding.jsx -> frontend/src/shared/components/Onboarding.tsx
frontend/src/components/ThemePicker.jsx -> frontend/src/shared/components/ThemePicker.tsx
```

- [ ] **Step 5: Verify after each feature group**

Run after each group:

```bash
cd frontend
npm run typecheck
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/src
git commit -m "refactor: convert frontend components to tsx"
```

## Task 8: Add Python Project Tooling

**Files:**
- Create: `pyproject.toml`
- Modify: `README.md`

**Interfaces:**
- Produces: centralized pytest config.
- Keeps `requirements.txt` as the install source for now.

- [ ] **Step 1: Add pyproject**

Create `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]
```

- [ ] **Step 2: Update README commands**

In `README.md`, keep existing commands but add:

```bash
.venv/bin/python -m pytest
```

as the preferred test command after `pyproject.toml` exists.

- [ ] **Step 3: Verify**

Run:

```bash
.venv/bin/python -m pytest -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml README.md
git commit -m "chore: add python project config"
```

## Recommended Order

1. Task 1: SQLite migrations.
2. Task 2: FastAPI routers.
3. Task 3: storage module split.
4. Task 4: TypeScript tooling.
5. Task 5: typed frontend API boundary.
6. Task 6: app shell and helper conversion.
7. Task 7: full component TSX conversion.
8. Task 8: Python project tooling.

This order keeps the riskiest data-protection work first, then backend maintainability, then frontend typing.

## Final Verification

Run all checks:

```bash
.venv/bin/python -m pytest tests -v
cd frontend
npm run typecheck
npm run build
```

Then start the app:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8421
cd frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173/
```

Verify:

- Settings page loads.
- Game list loads.
- Existing saved game opens.
- Bot play page creates a local game.
- API docs load at `http://127.0.0.1:8421/docs`.

