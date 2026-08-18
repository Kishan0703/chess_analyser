# Local Ollama Performance Plan

## Goal

Make offline coaching run at usable laptop speed without weakening online analysis quality.

The honest direction is not "just switch models." The current slow path is mostly architectural:
`coach_game()` asks Ollama to do up to 11 serial jobs for one game: candidate gathering, up to 10
key-moment explanations, and one summary. Each local LLM call receives repeated instructions and
position context. That makes prompt processing expensive even after `num_ctx` and `think` are tuned.

Hosted providers can keep the richer analysis path. Offline Ollama should use Stockfish and
deterministic board facts as the main analyst, then use the local LLM only where language generation
adds value.

Core rule: **Stockfish is the authority.** The local LLM must not decide whether a chess move is
good, bad, tactical, positional, winning, or losing. It receives verified facts from Stockfish and
`features.py`, then rewrites them into clear coaching prose.

## Current Local Path

- `backend/coach.py` calls Ollama through `/api/chat`.
- Ollama options now include `think: false` and `num_ctx: 8192`.
- Each key moment gets a separate LLM call.
- Each moment prompt includes long static coaching rules, piece placement, position facts, engine
  candidates, played move consequences, best move consequences, and the best line.
- The final summary call receives the key-moment outputs plus full movetext.
- Stockfish already stores useful facts in SQLite: `best_san`, `best_line`, `eval_cp`, `eval_mate`,
  `classification`, and `win_pct_loss`.

## Evidence

### Ollama Can Prove Where Time Goes

Ollama responses include `prompt_eval_count`, `prompt_eval_duration`, `eval_count`, and
`eval_duration`. Use these to separate prompt-processing cost from output-generation cost.

Source: https://docs.ollama.com/api/usage

Why it matters here: if compact prompts reduce `prompt_eval_count` and `prompt_eval_duration`, the
optimization is real. If only `eval_duration` is high, reduce output length or thinking behavior.

### `think: false` Is A Valid Speed Optimization

Ollama documents a `think` API field. When thinking is disabled, supported models return content
directly instead of generating separate thinking output.

Source: https://ollama.com/blog/thinking

Qwen3 also documents non-thinking mode as useful for efficiency and recommends separate sampling
settings for non-thinking mode.

Source: https://huggingface.co/Qwen/Qwen3-4B-FP8

Current code already does the right thing here. Keep it.

### Parallel Ollama Calls Are Not Free On A Laptop

Ollama documents that parallel request processing increases required RAM by parallelism times context
length. Example: four 2K-context requests require an 8K allocation.

Source: https://docs.ollama.com/faq

Recommendation: do not blindly parallelize moment calls for offline mode. On a laptop this can cause
memory pressure, model offload, and worse latency. Prefer caching and smaller prompts first.

### Prompt Reuse Is A Real Inference Optimization

Prompt/prefix caching reuses KV attention states for repeated prompt prefixes. Google Research reports
large latency reductions in a Prompt Cache prototype, especially for repeated long prompt modules.

Source: https://research.google/pubs/prompt-cache-modular-attention-reuse-for-low-latency-inference/

Practical caveat: app-level caching is safer than assuming Ollama will always reuse prefixes across
`/api/chat` calls on every backend. Cache generated chess artifacts in SQLite and make repeated
coaching idempotent.

### Context Length Has A Real Cost

Longer prompts cost more because attention and KV-cache work grow with sequence length. FlashAttention
exists because standard attention is slow and memory-heavy on long sequences.

Source: https://huggingface.co/papers/2205.14135

Grouped-query attention reduces KV-cache cost while preserving much of model quality, which is another
reason modern inference speed depends heavily on context and cache behavior.

Source: https://arxiv.org/abs/2305.13245

Recommendation: `num_ctx=8192` is a ceiling, not a target. The best offline prompt is the smallest one
that contains all necessary chess facts.

### Stockfish Should Carry More Of The Offline Work

Stockfish MultiPV can provide multiple candidate lines, but official docs note that MultiPV spends
search resources on extra moves and can weaken the best move search.

Source: https://official-stockfish.github.io/docs/stockfish-wiki/Terminology.html

Recommendation: use stored single-PV analysis for most offline explanations. Run MultiPV only for
selected critical moments, and cache those results.

Chess.com documentation is consistent with the same tradeoff: deeper analysis costs more time, and
faster review can differ from later deeper review.

Source: https://support.chess.com/en/articles/8584089-how-does-game-review-work

## Recommended Architecture

### Keep Online Quality Path

For `claude` and `gemini`, keep the current richer path:

- one focused call per key moment
- full strategic prompt
- richer summary synthesis
- existing JSON shape

Hosted models are faster and stronger enough to justify the extra context.

### Add Offline Ollama Fast Path

For `ollama`, make Stockfish and deterministic features the source of truth:

- Use saved move rows before asking Stockfish again.
- Generate a deterministic fact packet per key moment:
  - move number, side, SAN/UCI
  - classification and win-percent loss
  - eval before/after from user's perspective
  - stored best move and best line
  - piece placement
  - compact position facts from `features.extract()` or `features.describe()`
  - played move consequences
  - best move consequences when available
- Build a deterministic draft explanation from those facts.
- Ask Ollama to rewrite the draft into concise coach prose, not to infer tactics or search.

This changes the LLM role from "analyze the chess position" to "verbalize verified chess analysis."

For a 16 GB laptop, keep `qwen3:8b` as the first local rewrite model:

- Stockfish does the expensive chess judgment.
- Qwen3 8B only turns compact verified facts into readable coaching.
- `think: false`, `num_ctx` around 4096-8192, and a short output budget should be tested after the
  compact path exists.
- Do not benchmark model switching first; that would measure the current large-prompt architecture,
  not the intended offline architecture.

### Cache Reusable Results

Add caches with invalidation keys instead of recomputing:

- Engine candidate cache by FEN, Stockfish path/version if available, movetime, MultiPV, threads, and
  line length.
- Moment explanation cache by game id, ply, model, prompt version, Ollama options, and candidate hash.
- Summary cache by game id, prompt version, model, and moment-output hash.

Expected benefit: re-coaching the same game should become almost instant unless settings or engine
results changed.

### Reduce Offline Calls

Default offline report should not need 10 local LLM calls.

Recommended offline default:

- Top 3 negative moments.
- Top 1 positive moment.
- Deterministic summary from counts and cached moment themes.
- Optional "deepen this moment" action that runs one richer LLM call for a selected position.

This preserves usefulness: users see the biggest mistakes first, then request detail where they care.

Do not over-template the final local coaching output. Templates should assemble facts and protect
accuracy, but Qwen3 8B should still write the final explanation so the offline version feels like a
coach rather than a report generator.

### Shrink Offline Prompts

For local Ollama only:

- Keep static system prompt short.
- Avoid repeating long grounding rules in every prompt; rely on deterministic fact packets.
- Avoid full PGN/movetext in local summary unless the user asks for whole-game narrative.
- Lower local output budgets for moment prose, for example 500-900 tokens instead of 1500.
- Keep `format: "json"` or a JSON schema so parsing stays reliable.

Ollama supports structured JSON output and JSON schemas.

Source: https://docs.ollama.com/capabilities/structured-outputs

## Benchmark Plan

Measure before changing defaults.

Use three representative games:

- short clean game
- normal middlegame game
- tactical or long game with many mistakes

Record:

- total `coach_game()` wall time
- number of Ollama calls
- total input tokens
- total output tokens
- total prompt eval duration
- total eval duration
- JSON parse success rate
- cache hit rate

Compare:

- current Ollama path
- compact offline prompt path
- compact path plus moment cache
- compact path plus candidate cache
- deterministic-only fallback
- optional model comparison only after the compact path works

Success target:

- first offline coaching run is materially faster than current behavior
- repeated re-coach avoids repeated LLM and Stockfish work
- explanations remain grounded in legal board facts and Stockfish lines
- hosted provider output remains unchanged

## Implementation Plan

1. Add a local performance benchmark helper that wraps `_call_ollama()` and logs Ollama timing fields.
2. Add SQLite tables or JSON columns for cached candidate and moment artifacts.
3. Add provider routing: hosted providers use current path; Ollama uses offline fast path.
4. Add deterministic moment fact-packet builder.
5. Add deterministic draft explanation templates based on classification, eval swing, best line, and
   move consequences.
6. Add compact Ollama rewrite prompt for local mode.
7. Add cache lookup before Stockfish candidate gathering and before each Ollama moment call.
8. Add deterministic fallback when Ollama fails or returns invalid JSON.
9. Keep tests proving hosted behavior is unchanged.
10. Benchmark `qwen3:8b` on the compact path before trying different local models.

## Risks

- Over-compressing prompts can make prose generic. Mitigation: keep the deterministic draft specific
  and include exact best line plus consequences.
- MultiPV can reduce best-move quality if overused. Mitigation: use stored PV by default and reserve
  MultiPV for selected critical moments.
- Cache invalidation can become stale. Mitigation: include prompt version, model, engine settings, and
  candidate hash in cache keys.
- Fully deterministic summaries may be less elegant. Mitigation: offline summary can be template-first
  and optionally rewritten by one small LLM call.

## Honest Recommendation

Do not change online quality. For offline speed, the best engineering win is:

1. Cache repeated Stockfish and LLM artifacts.
2. Send smaller verified fact packets to Ollama.
3. Let Stockfish decide chess facts and let Ollama polish language.
4. Generate fewer local moments by default, with on-demand deepening.
5. Keep `qwen3:8b` as the first 16 GB laptop target, then benchmark alternatives only if the compact
   path is still too slow.

Only benchmark model changes after those are in place. Otherwise a smaller model hides the real issue:
the app is repeatedly sending large prompts and asking the local LLM to do work Stockfish already did.
