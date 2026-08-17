# ChessCoach UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the ChessCoach frontend so the app matches the approved mockup direction: a focused desktop coaching workspace with clearer navigation, games list, analysis page, and training profile.

**Architecture:** Keep the existing Vite/React component structure and hash-based routing. Improve the current components in place, add small presentational helpers only where they reduce clutter, and centralize visual direction in `frontend/src/index.css`.

**Tech Stack:** React 19, Vite 8, `react-chessboard`, `recharts`, existing FastAPI backend APIs.

## Global Constraints

- Keep the app as a usable desktop/productivity tool, not a marketing landing page.
- Use dense, scannable layouts with restrained stone neutrals and chess green as the main accent.
- Preserve all existing backend API contracts.
- Do not add new dependencies unless a required UI element cannot reasonably be built with existing code.
- Verify each meaningful slice with `npm run build` and `npm run lint` from `frontend/`.
- Commit after each meaningful slice.

---

### Task 1: App Shell and Design Tokens

**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/ThemePicker.jsx`
- Modify: `frontend/src/theme.js`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: existing `view` objects from `App.jsx`.
- Produces: app shell classes `app-shell`, `sidebar`, `sidebar-nav`, `shell-main`, and a simplified `classic` theme value.

- [ ] **Step 1: Define the shell markup**

Replace the top horizontal navigation with a left sidebar that contains app identity, primary nav buttons, and theme/settings controls.

- [ ] **Step 2: Simplify theme selection**

Keep theme state compatible with `cc-theme`, but use a single light professional theme as the default visual baseline.

- [ ] **Step 3: Refresh global CSS tokens**

Replace decorative radial backgrounds with a quieter stone canvas, normalize buttons/inputs/cards, and add responsive shell behavior.

- [ ] **Step 4: Verify**

Run:

```bash
cd frontend
npm run build
npm run lint
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.jsx frontend/src/components/ThemePicker.jsx frontend/src/theme.js frontend/src/index.css
git commit -m "feat: refresh app shell"
```

### Task 2: Games Workspace

**Files:**
- Modify: `frontend/src/components/GameList.jsx`
- Modify: `frontend/src/components/Onboarding.jsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: existing `api.games()`, `api.settings()`, `api.importGames()`, and onboarding response shape.
- Produces: improved games workspace with search/filter controls, stronger stat cards, onboarding checklist, and clearer table labels.

- [ ] **Step 1: Add local list controls**

Add search text, result filter, and analysis filter state in `GameList.jsx`. Filter the existing `games` array client-side.

- [ ] **Step 2: Improve first-run workspace**

Adjust onboarding copy and layout so it reads as a task checklist integrated with the games workspace.

- [ ] **Step 3: Update table presentation**

Keep the existing columns but add concise status labels, row affordances, and empty-state copy.

- [ ] **Step 4: Verify**

Run:

```bash
cd frontend
npm run build
npm run lint
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/GameList.jsx frontend/src/components/Onboarding.jsx frontend/src/index.css
git commit -m "feat: improve games workspace"
```

### Task 3: Analysis Workspace

**Files:**
- Modify: `frontend/src/components/GameView.jsx`
- Modify: `frontend/src/components/MoveList.jsx`
- Modify: `frontend/src/components/EvalGraph.jsx`
- Modify: `frontend/src/components/PositionAnalysis.jsx`
- Modify: `frontend/src/components/CoachPanel.jsx`
- Modify: `frontend/src/components/GameChat.jsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: existing game/move/coach objects and callbacks.
- Produces: clearer analysis layout with board-first interaction, compact game header, current-position card, best moves, move list, coach report, and chat.

- [ ] **Step 1: Reorder analysis panels**

Keep the board sticky on large screens. In the right column, order panels by workflow: game summary/actions, current position, moves, coach report, chat.

- [ ] **Step 2: Improve action and variation states**

Make engine/coaching actions visually distinct and make best-line/variation banners easier to scan.

- [ ] **Step 3: Improve move and eval readability**

Style move rows, quality badges, eval graph, and best-move candidates using compact, tabular presentation.

- [ ] **Step 4: Verify**

Run:

```bash
cd frontend
npm run build
npm run lint
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/GameView.jsx frontend/src/components/MoveList.jsx frontend/src/components/EvalGraph.jsx frontend/src/components/PositionAnalysis.jsx frontend/src/components/CoachPanel.jsx frontend/src/components/GameChat.jsx frontend/src/index.css
git commit -m "feat: refine analysis workspace"
```

### Task 4: Training Profile Dashboard

**Files:**
- Modify: `frontend/src/components/Profile.jsx`
- Modify: `frontend/src/index.css`

**Interfaces:**
- Consumes: existing `api.profile()` response.
- Produces: profile dashboard with priority metrics, recurring-pattern chart, openings to review, strengths/focus areas, and recent analyzed games.

- [ ] **Step 1: Add derived profile sections**

Use existing summary fields, themes, openings, and recent games to derive strengths and focus areas without backend changes.

- [ ] **Step 2: Improve chart and tables**

Keep `recharts`, but make labels, colors, and table density match the redesigned dashboard.

- [ ] **Step 3: Verify**

Run:

```bash
cd frontend
npm run build
npm run lint
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/Profile.jsx frontend/src/index.css
git commit -m "feat: upgrade training profile"
```

### Task 5: Final Verification

**Files:**
- Read: all modified frontend files.

- [ ] **Step 1: Run full frontend verification**

Run:

```bash
cd frontend
npm run build
npm run lint
```

- [ ] **Step 2: Inspect git history and status**

Run:

```bash
git log --oneline -5
git status --short
```

- [ ] **Step 3: Report outcome**

Summarize the commits made, verification commands, and any residual risks.
