# ChessCoach Architecture

ChessCoach is a local-first chess analysis app. It combines a public game source, a local database, an external chess engine process, deterministic board feature extraction, and local or hosted LLM coaching.

```mermaid
flowchart TD
    ChessCom[Chess.com Public API] --> Importer[backend/chesscom.py]
    Importer --> SQLite[(SQLite chesscoach.db)]

    SQLite --> Engine[backend/engine.py]
    Engine --> Stockfish[Stockfish UCI binary]
    Stockfish --> Moves[(moves table: evals, grades, best move, PV)]

    Moves --> Features[backend/features.py]
    Features --> Facts[Verified fact packets]
    Moves --> Facts

    Facts --> Coach[backend/coach.py]
    Coach --> Provider{Coach provider}

    Provider -->|online quality path| Gemini[Gemini]
    Provider -->|online quality path| Claude[Claude]
    Gemini --> HostedReport[Rich per-moment analysis]
    Claude --> HostedReport

    Provider -->|offline fast path| LocalCache[(candidate and moment cache)]
    LocalCache --> OfflineDraft[Stockfish-authoritative draft]
    OfflineDraft --> Qwen[Qwen3 8B via Ollama]
    Qwen --> LocalReport[Concise rewritten coaching]

    HostedReport --> Analyses[(analyses and themes)]
    LocalReport --> Analyses
    Analyses --> API[FastAPI]
    Moves --> API
    SQLite --> Profile[Training Profile aggregation]
    Profile --> API
    API --> React[React desktop/web UI]
```

## Coaching Authority Model

Stockfish is the authority for chess judgment. It decides the best move, principal variation,
evaluation swing, move classification, and winning-chance loss. `backend/features.py` adds
deterministic board facts such as piece placement, pawn structure, files, outposts, king safety, and
move consequences.

The LLM is not the chess engine. Its job is to turn verified Stockfish and feature data into useful
coaching prose without inventing unsupported claims.

## Provider Paths

Online providers use the quality path. Claude and Gemini can receive richer prompts and produce
deeper per-moment strategic analysis because they are fast enough and stronger at long-context
reasoning.

Offline Ollama uses the fast path. It should keep `qwen3:8b` as the first local target on a 16 GB
laptop, but only as a rewrite layer: Stockfish and `features.py` provide the facts, then Qwen writes a
short human explanation. This keeps local quality decent while avoiding repeated large prompts.

The offline path should prioritize:

- fewer default moments: top 3 negative and top 1 positive
- cached Stockfish candidate results
- cached per-moment Qwen rewrites
- compact fact packets instead of full repeated coaching prompts
- optional on-demand deepening for a single selected moment

## Why This Is Resume-Relevant

- Stockfish is controlled as a local UCI process, not consumed as a hosted API.
- Ollama support proves local LLM orchestration with long prompts and JSON output.
- Deterministic board facts ground LLM coaching so explanations are auditable.
- SQLite keeps analysis local and enables cross-game player profiling.
- The React UI turns engine data into an interactive study workflow.
