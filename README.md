# ChessCoach

ChessCoach is a local chess analysis app for your Chess.com games. It imports your
recent games, runs Stockfish, grades moves, and generates positional coaching with an
LLM.

The main goal is practical study: not only whether a move was bad, but why the
position called for a different plan.

## What It Does

- Imports public Chess.com games by username.
- Stores games locally in SQLite.
- Runs a Stockfish analysis pass for every move.
- Shows move grades, evaluations, and best-line suggestions.
- Generates a coaching report for key moments.
- Explains plans, pawn structures, piece quality, weak squares, files, and recurring
  themes.
- Supports local and hosted LLM backends.

## Coaching Backends

ChessCoach can use one of these providers:

- `ollama`: local model through Ollama.
- `claude`: Anthropic Claude API.
- `gemini`: Google Gemini API.

The selected provider is controlled by app settings or by `.env`.

## Requirements

- Python 3.11+
- Node 20+
- Stockfish binary
- One coaching backend:
  - Ollama and a local model, or
  - Anthropic API key, or
  - Gemini API key

On Windows, the desktop shell uses WebView2 through `pywebview`. On macOS/Linux, you can
run the backend and frontend directly in the browser.

## Setup

Create the Python environment:

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

Add Stockfish:

- Download Stockfish from `https://stockfishchess.org/download/`.
- Put the binary in `engines/`.
- Make sure the path used by `backend/engine.py` matches your platform.

## Environment Variables

Create a root `.env` file. A template is included in `.env.example`.

For Gemini:

```env
COACH_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.5-flash-lite
GEMINI_FALLBACK_MODELS=gemini-3.5-flash,gemini-3.1-flash-lite,gemini-2.5-flash
```

For Claude:

```env
COACH_PROVIDER=claude
ANTHROPIC_API_KEY=your-anthropic-api-key
```

For Ollama:

```env
COACH_PROVIDER=ollama
```

Then pull a local model:

```bash
ollama pull qwen2.5:14b
```

Runtime `.env` values override `settings.json`. Secrets are not written back into
`settings.json`.

## Run

Build the frontend bundle for the desktop app:

```bash
cd frontend
npm run build
cd ..
```

Start the desktop app:

```bash
.venv/bin/python desktop.py
```

On Windows:

```powershell
.venv\Scripts\python.exe desktop.py
```

You can also run the backend and frontend separately:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8421
```

```bash
cd frontend
npm run dev
```

## Workflow

1. Enter a Chess.com username.
2. Import recent games.
3. Open a game.
4. Run engine analysis.
5. Get coaching.

The game list is scoped to the configured Chess.com username. If the local database has
games from multiple usernames, the UI only shows games where the configured user played
White or Black.

## Data Storage

Local data is stored in `chesscoach.db`.

Settings are stored in `settings.json`, except secrets provided by `.env`.

The database stores:

- games
- moves
- engine evaluations
- coaching reports
- strategic themes

## Project Structure

- `backend/app.py`: FastAPI routes.
- `backend/chesscom.py`: Chess.com import logic.
- `backend/db.py`: SQLite schema and queries.
- `backend/engine.py`: Stockfish analysis and move classification.
- `backend/features.py`: deterministic board facts used to ground coaching.
- `backend/coach.py`: LLM provider calls and coaching orchestration.
- `frontend/`: React UI.
- `desktop.py`: pywebview desktop wrapper.
- `tests/`: backend tests.

## Development

Run tests:

```bash
.venv/bin/python -m pytest tests
```

Run backend only:

```bash
.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port 8421
```

Run frontend only:

```bash
cd frontend
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

## Notes

- Chess.com game data comes from the public Chess.com API.
- Stockfish is not bundled with this project.
- Hosted LLM providers may rate-limit, fail during high demand, or charge per request.
- Gemini calls retry transient failures and can fall back through configured models.

## License

ChessCoach code is MIT licensed. Stockfish is GPLv3 and is invoked as a separate
external binary that you provide yourself.
