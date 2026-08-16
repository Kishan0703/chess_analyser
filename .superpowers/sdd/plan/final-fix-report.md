# Final Fix Report

## Findings Addressed

1. Secrets are no longer persisted to `settings.json`. Runtime secrets are read only
   from process environment or `.env`; saving removes legacy JSON secret fields.
2. Profile move-quality, themes, openings, average loss, and recent games now use only
   engine-analyzed games. The profile presents an explicit unanalyzed state when imports
   exist but no analysis has completed.
3. Stockfish readiness now requires an existing regular file and, outside Windows, an
   executable bit. Settings displays readiness or the returned validation error beside
   the path input after loading and saving.
4. Profile opening and recent-game tables have unstyled horizontal overflow wrappers.
5. Aggregation maps `1-0`, `0-1`, and draws explicitly, separately counts unknown
   results, excludes `NULL` losses consistently, and covers empty, limit, and opponent
   filtering behavior.
6. Coach-prompt tests now assert exact `NO enemy pieces`, a known attacked piece, and
   `_moment_block` placement and consequence grounding.

## Files Changed

- `backend/db.py`
- `backend/engine.py`
- `backend/settings.py`
- `frontend/src/components/Profile.jsx`
- `frontend/src/components/Settings.jsx`
- `frontend/src/index.css`
- `tests/test_coach_prompt.py`
- `tests/test_profile.py`
- `tests/test_settings.py`
- `tests/test_stockfish_settings.py`
- `.superpowers/sdd/plan/final-fix-report.md`

## Verification

- `.venv/bin/python -m pytest tests -v`: exit 0; 31 passed, 1 warning in 0.32s.
  Warning: `StarletteDeprecationWarning` from `fastapi.testclient` advising against the
  deprecated `httpx` TestClient integration.
- `npm run lint` from `frontend`: exit 0; ESLint completed with no warnings.
- `npm run build` from `frontend`: exit 0; Vite built successfully in 190ms.
  Warning: the generated JavaScript chunk is 707.44 kB and exceeds Vite's 500 kB
  advisory limit.
- `git diff --check`: exit 0; no whitespace errors.

## Commit

Commit hash: `HEAD` (the final commit created for this report).

## Residual Concerns

- The pre-existing FastAPI TestClient deprecation warning remains.
- The frontend production bundle retains Vite's chunk-size advisory; this pass does not
  broaden scope into code splitting.
