# ChessCoach Architecture

ChessCoach is a local-first chess analysis app. It combines a public game source, a local database, an external chess engine process, deterministic board feature extraction, and local or hosted LLM coaching.

```mermaid
flowchart LR
    ChessCom[Chess.com Public API] --> Importer[backend/chesscom.py]
    Importer --> SQLite[(SQLite chesscoach.db)]
    SQLite --> Engine[backend/engine.py]
    Engine --> Stockfish[Stockfish UCI binary]
    Engine --> Moves[(Move evals and grades)]
    Moves --> Features[backend/features.py]
    Features --> Coach[backend/coach.py]
    Coach --> Ollama[Ollama local LLM]
    Coach --> Gemini[Gemini fallback]
    Coach --> Claude[Claude fallback]
    Coach --> Analyses[(Coach reports and themes)]
    Moves --> API[FastAPI]
    Analyses --> API
    SQLite --> Profile[Training Profile aggregation]
    Profile --> API
    API --> React[React desktop/web UI]
```

## Why This Is Resume-Relevant

- Stockfish is controlled as a local UCI process, not consumed as a hosted API.
- Ollama support proves local LLM orchestration with long prompts and JSON output.
- Deterministic board facts ground LLM coaching so explanations are auditable.
- SQLite keeps analysis local and enables cross-game player profiling.
- The React UI turns engine data into an interactive study workflow.
