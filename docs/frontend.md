# ChessCoach — Frontend Design System

This document is the visual/UX spec for restyling ChessCoach into a more professional, modern, "cool" product — supporting both **light** and **dark** mode. It covers design tokens, typography, and component patterns. It does **not** prescribe a tech stack — keep building on the app's current stack and component structure; this doc only changes tokens, styles, and a handful of interaction patterns layered on top of it.

Reference: current app is dark-mode-only, purple-accented, with a chess board + move list, a stats dashboard, a games table, and a "Coach's Report" narrative panel.

---

## 1. Design Principles

1. **Instrument-panel precision.** This is an analysis tool, not a casual game UI. Favor tabular alignment, monospace notation, and restrained color over playful decoration.
2. **Color means something.** Green/amber/red are reserved for move quality and outcomes (win/loss, blunder/brilliant). Never use accent color decoratively where it could be mistaken for a signal.
3. **Editorial coaching, technical data.** The Coach's Report is the product's voice — give it a slightly warmer, more readable typographic treatment than the surrounding dashboard chrome.
4. **One brand color, used sparingly.** A single confident green carries the brand (buttons, links, active states, "best move" markers) rather than scattering color everywhere.
5. **Light and dark are equally first-class.** Dark mode isn't an inverted afterthought — both themes are tuned independently for contrast and mood.

---

## 2. Color Tokens

### 2.1 Brand scale — Chess Green

| Token | Hex | Use |
|---|---|---|
| `--green-50` | `#EEF7ED` | light-mode soft backgrounds |
| `--green-100` | `#D7EEDA` | hover fills |
| `--green-200` | `#B3DFB9` | borders on soft fills |
| `--green-300` | `#8BCB95` | — |
| `--green-400` | `#65B873` | dark-mode primary accent |
| `--green-500` | `#4C9F58` | mid brand green (icons, charts) |
| `--green-600` | `#3A8045` | light-mode primary accent (buttons/links) |
| `--green-700` | `#2C6435` | light-mode hover/active |
| `--green-800` | `#214B28` | — |
| `--green-900` | `#16331B` | dark-mode soft-fill text |

> ⚠️ Accessibility note: bright greens (`400`/`500`) read well as **text on dark backgrounds** or as **button fills with white/near-black text**, but fail AA as text-on-light. Never use `green-400`/`500` as a text color on a light surface.

### 2.2 Neutral scale — "Stone" (cool, slightly green-tinted gray)

| Token | Hex |
|---|---|
| `--stone-0` | `#FFFFFF` |
| `--stone-50` | `#F6F8F6` |
| `--stone-100` | `#EBEFEA` |
| `--stone-200` | `#D7DED5` |
| `--stone-300` | `#B7C2B4` |
| `--stone-400` | `#8C9988` |
| `--stone-500` | `#6B7A67` |
| `--stone-600` | `#4F5C4C` |
| `--stone-700` | `#384238` |
| `--stone-800` | `#1C241B` |
| `--stone-850` | `#161D15` |
| `--stone-900` | `#0E1410` |
| `--stone-950` | `#0A0F0C` |

### 2.3 Semantic tokens (theme-aware)

```css
:root {
  /* surfaces */
  --color-bg-canvas: var(--stone-50);
  --color-bg-surface: var(--stone-0);
  --color-bg-surface-raised: var(--stone-0);
  --color-bg-sunken: var(--stone-100);

  /* borders */
  --color-border-subtle: var(--stone-200);
  --color-border-strong: var(--stone-300);

  /* text */
  --color-text-primary: #141A16;
  --color-text-secondary: #4B5750;
  --color-text-muted: #7C8880;
  --color-text-on-accent: #FFFFFF;

  /* brand */
  --color-accent: var(--green-600);
  --color-accent-hover: var(--green-700);
  --color-accent-soft-bg: var(--green-50);
  --color-accent-soft-text: var(--green-700);

  /* semantic states */
  --color-success: var(--green-600);
  --color-danger: #C13B3B;
  --color-danger-soft-bg: #FBEAEA;
  --color-danger-soft-text: #A02E2E;
  --color-warning: #B5740A;
  --color-warning-soft-bg: #FBF1DF;
  --color-warning-soft-text: #8F5C08;
  --color-info: #3568B0;
  --color-info-soft-bg: #E9F1FB;
  --color-info-soft-text: #2A538C;

  /* board (kept consistent across themes for recognizability) */
  --board-light-square: #EEEED2;
  --board-dark-square: #6FA34C;
  --board-highlight: rgba(76, 159, 88, 0.30);
  --board-best-marker: var(--green-600);

  /* shadows */
  --shadow-sm: 0 1px 2px rgba(20, 26, 22, 0.06);
  --shadow-md: 0 4px 12px rgba(20, 26, 22, 0.08);
  --shadow-lg: 0 12px 32px rgba(20, 26, 22, 0.12);
}

[data-theme="dark"] {
  --color-bg-canvas: var(--stone-950);
  --color-bg-surface: var(--stone-900);
  --color-bg-surface-raised: #1A231C;
  --color-bg-sunken: var(--stone-850);

  --color-border-subtle: #232F25;
  --color-border-strong: #34423A;

  --color-text-primary: #EAF2EA;
  --color-text-secondary: #A7B6A4;
  --color-text-muted: #6E7C6C;
  --color-text-on-accent: #0B100D;

  --color-accent: var(--green-400);
  --color-accent-hover: #84D08C;
  --color-accent-soft-bg: #16291A;
  --color-accent-soft-text: #8FDC97;

  --color-success: var(--green-400);
  --color-danger: #F2666B;
  --color-danger-soft-bg: #2B1517;
  --color-danger-soft-text: #FF9DA1;
  --color-warning: #F2A93B;
  --color-warning-soft-bg: #2B2113;
  --color-warning-soft-text: #FFC774;
  --color-info: #5B9BD8;
  --color-info-soft-bg: #112334;
  --color-info-soft-text: #9CC7EE;

  --board-light-square: #D8D9C2;
  --board-dark-square: #5C8A45;
  --board-highlight: rgba(107, 192, 116, 0.28);
  --board-best-marker: var(--green-400);

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 14px rgba(0, 0, 0, 0.45);
  --shadow-lg: 0 16px 36px rgba(0, 0, 0, 0.55);
}
```

> Important: in dark mode the primary button uses **dark text on a bright green fill** (`--color-text-on-accent` flips to near-black), because `green-400` is too light for white text to sit on top of with good contrast. In light mode it's the reverse — white text on `green-600`.

---

## 3. Typography

| Role | Font | Notes |
|---|---|---|
| UI / dashboard | **Inter** | All chrome: nav, buttons, tables, labels, stat numbers |
| Coach's Report narrative | **Source Serif 4** (fallback: Georgia) | Used only for the prose paragraphs in the coaching panel — gives the "written analysis" a distinct, premium, editorial feel vs. the surrounding data UI |
| Notation / numeric data | **IBM Plex Mono** (fallback: JetBrains Mono) | Move list SAN, eval numbers, coordinates, ratings — monospace keeps columns aligned and reads as "engine-precise" |

```css
--font-ui: 'Inter', system-ui, sans-serif;
--font-serif: 'Source Serif 4', Georgia, serif;
--font-mono: 'IBM Plex Mono', 'JetBrains Mono', monospace;
```

Type scale:

| Token | Size / Line-height | Weight | Use |
|---|---|---|---|
| `--text-display` | 28px / 1.2 | 700 | Stat card numbers |
| `--text-h1` | 22px / 1.3 | 600 | Page/section titles |
| `--text-h2` | 17px / 1.4 | 600 | Card headings (e.g. "Knight Sacrifice and Positional Concessions") |
| `--text-body-lg` | 16px / 1.7 | 400 (serif for coach text) | Coach's Report paragraphs |
| `--text-body` | 14px / 1.5 | 400/500 | Default UI text, table cells |
| `--text-caption` | 12px / 1.4 | 500, uppercase, +0.04em tracking | Stat labels, column headers |
| `--text-mono` | 13.5px / 1.6 | 400/500 | Move list, eval values |

Numeric figures (ratings, stat counts, eval scores) should use `font-variant-numeric: tabular-nums`.

---

## 4. Spacing, Radius, Shadow, Motion

```css
--space-1: 4px;  --space-2: 8px;  --space-3: 12px; --space-4: 16px;
--space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px; --space-16: 64px;

--radius-sm: 6px;   /* badges, small chips */
--radius-md: 10px;  /* buttons, inputs, board wrapper */
--radius-lg: 16px;  /* cards, panels */
--radius-pill: 999px;

--duration-fast: 120ms;
--duration-base: 200ms;
--ease-standard: cubic-bezier(0.2, 0, 0, 1);
```

Use `--shadow-sm` for resting cards, `--shadow-md` on hover/elevated cards, `--shadow-lg` only for popovers/tooltips. In dark mode, lean more on a 1px `--color-border-subtle` than shadow, since shadows barely read on dark backgrounds.

---

## 5. Iconography

Use **Lucide** icons throughout (already available in this environment) — consistent 1.75–2px stroke, 16/18/20px sizing depending on context.

Key icon mappings: `Sun`/`Moon` (theme toggle), `Settings`, `ChevronLeft`/`ChevronRight`/`SkipBack`/`SkipForward` (move navigation, replacing the current ▶◀ glyph buttons), `ArrowLeftRight` (replacing the "↔ step through" text), `Star` (best/brilliant move marker), `TrendingUp`/`TrendingDown` (eval direction), `Target` / `BookOpen` (coaching tips list).

---

## 6. Component Patterns

### 6.1 App Header
- Sticky, `--color-bg-surface`, 1px bottom border (`--color-border-subtle`), height 64px.
- Left: small pawn/knight glyph mark + "ChessCoach" (`--font-ui`, 600) + muted caption tagline "positional coaching".
- Right: theme toggle icon-button (sun/moon, animated 200ms rotate+fade swap), then a `Settings` ghost button. Replace the current unlabeled colored dots with a proper **segmented control** (see 6.4) if they represent switchable views/tabs.

### 6.2 Buttons
- **Primary** — filled `--color-accent`, text `--color-text-on-accent`, `--radius-md`, `--shadow-sm`; hover → `--color-accent-hover` + `--shadow-md`.
- **Secondary** — transparent bg, 1px `--color-border-strong`, text `--color-text-primary`; hover bg `--color-bg-sunken`.
- **Ghost** — no border, text `--color-text-secondary`; hover bg `--color-bg-sunken`, text `--color-text-primary`.
- Sizes: sm 32px / md 40px / lg 48px height. Icon-to-label gap `--space-2`.

### 6.3 Stat Cards (Games / W-L-D / Analyzed / Coached)
- `--color-bg-surface` card, `--radius-lg`, `--shadow-sm`, padding `--space-5`–`--space-6`; hover: `--shadow-md` + `translateY(-2px)`, `--duration-base`.
- Big number in `--text-display`, tabular-nums.
- Caption label below in `--text-caption`, `--color-text-muted`.
- For the W-L-D card specifically: add a thin **stacked horizontal bar** beneath the numbers (green segment = wins, danger segment = losses, stone segment = draws) sized proportionally — turns a plain number triplet into a quick visual read.

### 6.4 Segmented Control / Tabs
- Track: `--color-bg-sunken`, `--radius-pill`.
- Active segment: `--color-bg-surface` + `--shadow-sm`, text `--color-text-primary`.
- Inactive: transparent, text `--color-text-muted`.

### 6.5 Games Table
- Container: `--color-bg-surface`, `--radius-lg`, 1px `--color-border-subtle`, clipped overflow.
- Header row: `--text-caption`, `--color-text-muted`, bottom border `--color-border-strong`, sticky on scroll.
- Rows: 52px height, bottom hairline `--color-border-subtle` only (no vertical gridlines), hover bg `--color-bg-sunken`.
- Keep the existing pattern of bolding whichever name is the tracked user.
- **Result column** → pill badge, `--radius-pill`, `--text-body` medium: Win = `--color-accent-soft-bg` / `--color-accent-soft-text`; Loss = `--color-danger-soft-bg` / `--color-danger-soft-text`; Draw = `--color-bg-sunken` / `--color-text-muted`.
- **Opening column** → `--color-text-secondary`, truncate with ellipsis + title tooltip for long names.
- **Analysis column** → `--color-accent-soft-bg` pill reading "Coached" / "Analyzed" when present; plain muted dash when not (keep minimal, as today).

### 6.6 Chess Board
- Squares use the dedicated `--board-light-square` / `--board-dark-square` tokens (chess-classic cream + green), constant across both themes for recognizability — dark mode uses slightly desaturated variants to reduce glare against the dark chrome.
- Wrap the board in a card: `--radius-md`, `--shadow-sm`, padding `--space-3`, so it no longer sits flush against the page edge.
- Coordinates (a–h, 1–8) in `--font-mono` `--text-caption`, `--color-text-muted`.
- Last-move highlight: `--board-highlight` overlay on from/to squares.
- "Best move available here" marker (currently a green star/dot): keep the dot motif, recolor to `--board-best-marker`, add a soft pulse animation (respect `prefers-reduced-motion`).
- Pieces: keep current flat two-tone vector style; add a subtle 2px/20%-opacity drop shadow per piece for slight tactile depth.

### 6.7 Move List
- Two-column (White | Black), `--font-mono` for SAN so columns align.
- Move number in `--color-text-muted`.
- Row hover: `--color-bg-sunken`, clickable (jumps board to that position).
- Selected/active move: `--color-accent-soft-bg` background + 2–3px left accent bar.
- Quality glyphs (`!`, `?!`, `?`, `??`, `★`) rendered as small 16px circular chips (not bare colored text) for scannability:
  - `★` best/brilliant → `--color-accent-soft-bg`/`--color-accent-soft-text`
  - `!` good → `--color-info-soft-bg`/`--color-info-soft-text`
  - `?!` inaccuracy → `--color-warning-soft-bg`/`--color-warning-soft-text`
  - `?` mistake → `--color-warning` solid, white text
  - `??` blunder → `--color-danger-soft-bg`/`--color-danger-soft-text`, bold

### 6.8 Coach's Report
- Section callout cards: `--color-bg-surface-raised`, `--radius-md`, left border 3–4px `--color-accent`, padding `--space-5`.
- Heading: `--font-ui` `--text-h2`. Body: `--font-serif` `--text-body-lg`, `--color-text-secondary`, line-height 1.7 — this is the one place serif type appears, deliberately distinguishing narrative coaching from dashboard data.
- "Best: …" line: `--font-mono`, `--color-text-muted`, small-caps label "BEST LINE" above it; the "click to step through" affordance becomes a real ghost button with an `ArrowLeftRight` icon, not unicode text.
- Insight tags (`no-plan-drift`, `tactical-oversight`, etc.): outline pill, `--radius-pill`, border + text colored by severity (danger border for tactical errors, warning border for planning/development issues), transparent fill, soft-fill on hover.
- "What to work on": replace the plain bullet list with a checklist-style block — each item in a `--color-bg-sunken` row, `--radius-md`, a small `Target`/`BookOpen` icon in `--color-accent`, text `--color-text-secondary`.

### 6.9 Eval Graph
- Replace the flat monochrome area fill with a duotone fill split at the zero line; only shift the fill toward `--color-danger`/`--color-accent` tinting once the evaluation crosses a "decisive" threshold (e.g. ±3) — keep small fluctuations neutral (`--stone-300`/`--stone-600`) so color stays meaningful rather than decorative.
- Add a dashed zero-line in `--color-border-strong`.
- Endpoint marker: filled dot colored by final eval sign; the floating "−4.8 after 19...Qxd4" label becomes a small pill tooltip (`--color-bg-surface-raised`, `--shadow-sm`, `--radius-pill`) anchored above the dot.
- On hover/scrub: vertical guideline + tooltip showing eval and move number at cursor position.

### 6.10 Empty / Loading States
- Skeleton shimmer blocks (`--color-bg-sunken`, pulsing opacity) matching the shape of stat cards/table rows while data loads, instead of a bare spinner.

---

## 7. Accessibility Checklist

- All text/background pairs meet WCAG AA (4.5:1 body text, 3:1 large text) in **both** themes — re-check after any token tweak, especially the brand green against light backgrounds.
- Move-quality glyphs and tags always pair color with a symbol/label — never color-only signaling.
- Visible focus ring on every interactive element: 2px `--color-accent` outline, 2px offset, never suppressed.
- Minimum 40×40px hit target for icon-only buttons.
- Respect `prefers-reduced-motion`: disable the best-move pulse and eval-graph scrub animation.
- Default theme follows `prefers-color-scheme` on first load; explicit user toggle is remembered after that.

---

## 8. Implementation Notes

- Continue with the app's current stack and component structure — this spec changes tokens, styling, and a few interaction details (tooltips, skeletons, segmented control, icon-based controls), not the underlying architecture.
- Introduce the tokens above as CSS custom properties at the root, with a `[data-theme="dark"]` (or equivalent class) override block matching whatever theming convention the current codebase already uses.
- Migrate hard-coded colors to tokens incrementally, in this order: header → stat cards → games table → board → move list → coach's report → eval graph.
- Ship light mode as the default visual baseline in this doc's examples, but detect `prefers-color-scheme` on first load as described above.