# ChessCoach

ChessCoach is a local-first chess coaching desktop app for Chess.com games. It imports your games, stores them in SQLite, analyzes every move with a local Stockfish UCI engine, and uses Ollama or hosted LLMs to explain the strategic reason behind key moments.

This is not a simple AI API wrapper. The app coordinates local executables, deterministic chess feature extraction, background jobs, model-provider fallbacks, and an interactive React analysis UI.

## What It Does

- Imports public Chess.com games by username.
- Stores games locally in SQLite.
- Runs a Stockfish analysis pass for every move.
- Shows move grades, evaluations, and best-line suggestions.
- Generates a coaching report for key moments.
- Explains plans, pawn structures, piece quality, weak squares, files, and recurring
  themes.
- Supports local and hosted LLM backends.

## Engineering Highlights

- Runs Stockfish as a local UCI process and stores per-move evals, best lines, and win-probability loss.
- Supports Ollama for local LLM coaching, with Claude and Gemini as optional hosted backends.
- Grounds LLM prompts with deterministic board facts, exact piece placement, and legal move consequences to reduce hallucinations.
- Builds a cross-game Training Profile from stored move grades and strategic themes.
- Ships as a local desktop app through `pywebview`, while still supporting browser-based development.

## Screenshots

Screenshots should be placed in `docs/screenshots/`:

- `game-view.png`: board, eval graph, moves, coach report.
- `profile.png`: Training Profile page with themes and openings.
- `variation.png`: red played-move arrow versus green Stockfish best-move arrow.
- `settings.png`: Stockfish and Ollama readiness.

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
ollama pull qwen3:8b
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
.venv/bin/python -m pytest
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
