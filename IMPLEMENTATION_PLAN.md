# Mosaic — Frontend Gap Analysis & Final Polish Plan

> **Scope:** Elevate Mosaic from a functional research application into a premium, portfolio-quality interactive platform. No changes to research scope, simulation model, API contracts, or core route set.
> **Execution:** All 4 phases implemented in full. CSS refactor in Phase 1. Testing after each phase. No deferrals.

---

## 1. Executive Summary

Mosaic's frontend is architecturally sound. Routing, lazy loading, Radix primitives, Motion for React, D3 visualizations, and a comprehensive design token system are all in place. The gap is not in what exists — it is in the **degree of finish** across every surface.

The five highest-leverage improvements are:

1. **Logo & brand identity** — The new Mosaic logo (starburst mark) must replace the current `<span class="brand-mark">` SVG hack immediately.
2. **Landing page density** — The hero and glance panel have strong copy but feel underweight; they need illustrations and richer data preview.
3. **Simulation empty state** — The preset chooser is functional but unpolished; it should become the front door of the product.
4. **Simulation not running / API errors** — Simulations silently fail due to a missing API base URL configuration for production. This is a blocking bug.
5. **Visual surface differentiation** — Cards blend into the page background; the color hierarchy in `design.md` is partially implemented but not enforced.

---

## 2. Current UX Assessment

### What works well
- Route architecture is clean and lazy-loaded correctly.
- Radix Tabs, Toast, and Tooltip are installed and wired.
- Motion for React is installed; `useReducedMotion` is respected throughout.
- The Research popover grouping is implemented.
- Network graph has a speaker inspector, legend, accessible table, and label toggle.
- UMAP has named stage selectors with correct semantics.
- Comparison page detects controlled vs. mixed configurations.
- Loading skeletons exist.

### What is broken or critically missing
- **Simulation API failure**: `VITE_API_BASE_URL=/api` is set in CI/CD. Locally, without the variable, `import.meta.env.VITE_API_BASE_URL` is `undefined` and the client makes requests to `undefined/simulate`. No visible error is shown to the user.
- **Logo implementation**: The brand mark is rendered via `background-position` CSS trickery on a cropped SVG. Fragile, inaccessible, and visually wrong at current offsets.
- **`index.css` is a monolith**: Lines 4–13 each contain thousands of characters of minified CSS — unreadable and unmaintainable.
- **Inline styles everywhere**: `ExperimentsPage.tsx`, `AnalysisPage.tsx`, and `ComparePage.tsx` rely heavily on `style={{}}` props rather than design tokens.
- **No footer**: No research citation, GitHub link, attribution, or model version anywhere.
- **No illustrations**: The landing hero, empty states, and NotFound page have no visuals.
- **Simulation report / PDF export**: Not implemented.
- **`Guide` page is minified**: Single 1,000-character JSX expression in `App.tsx`. Unmaintainable.
- **`ComparePage.tsx` is 1 line**: A 6kb single-line JSX expression. Cannot be safely reviewed or edited.
- **`btn-secondary` has no border**: Transparent background with no border is invisible on white.
- **Metric card `font-size: 28px` hardcoded inline** in `AnalysisPage.tsx` — breaks responsive behavior.
- **No skip-to-content link**: Missing critical accessibility landmark.

---

## 3. Validated Issues (from FRONTEND_POLISH_UX_PLAN.md)

All 14 issues from the prior plan are confirmed present. Key additions from this audit:

| # | Issue | Source | Severity |
|---|---|---|---|
| V1 | Research popover `<details>/<summary>` loses keyboard focus on close | `App.tsx:19` | High |
| V2 | Result statement has `background:#fafafa` inline — not a design token | `index.css:4` | Medium |
| V3 | Preset cards have no expected-outcome visual (only `<small>` text) | `ControlPanel.tsx:101` | High |
| V4 | `SimulationLoading` stage list is static — all stages show active dot simultaneously | `Dashboard.tsx:31` | High |
| V5 | Tabs use both `data-state` and `aria-selected` inconsistently | `index.css:11` | Medium |
| V6 | Overview previews use Unicode `●—●—●` as network thumbnail | `Dashboard.tsx:26` | High |
| V7 | `Run complete` used as `h1` — should be a result-oriented statement | `Dashboard.tsx:23` | High |
| V8 | Empty state `h2` "Start with a question." has no visual anchor | `Dashboard.tsx:30` | Medium |
| V9 | Filter buttons in Experiments use inline `background` override | `ExperimentsPage.tsx:120` | Medium |
| V10 | `comparison-status` uses `#fafafa` not a token | `index.css:6` | Low |

---

## 4. Newly Identified Issues

### 4.1 Simulation API / Network Diagnosis

**Root cause hypothesis**: The Vite dev build uses `VITE_API_BASE_URL=/api` proxied by nginx. Locally, without the env var, `api/client.ts` constructs requests to `undefined/...`. This is a configuration and error-handling gap, not a rendering bug.

**Required fixes**:
- Add `const BASE = import.meta.env.VITE_API_BASE_URL ?? ''` with empty-string fallback.
- Add a startup health check `GET /api/health` on app mount; show a banner if it fails.
- Verify FastAPI CORS configuration includes the production domain.

### 4.2 Logo Implementation

The current logo uses:
```css
.brand-mark img { position: absolute; top: -100px; left: -80px; width: 230px; }
```
This crops an SVG at a pixel offset. The new logo (`Mosaic_20260712_123124_0000.png`) is a solid Signal Blue radiating starburst — clean, bold, and geometrically complete.

**Required**:
- Copy PNG → `frontend/public/brand/mosaic-logo.png`.
- Render as `<img>` at 22×22px in the nav pill.
- Add "Mosaic" as a separate `<span>` in Inter Variable 12px, weight 700.
- Use the mark at 48×48px on the landing hero above the eyebrow.
- Generate a 32×32 favicon from the PNG.

### 4.3 Typography Violations

- `font-size: 28px` in `AnalysisPage.tsx` MetricCard — hardcoded inline.
- `font-size: 24px` for experiment `h2` — hardcoded inline.
- `letter-spacing: -0.04em` appears in multiple inline styles vs. token `-0.025em`.
- Eyebrow labels use 10px, 11px, and 12px inconsistently across files.

### 4.4 Surface / Color Violations

- `background: #fafafa` appears 3+ times inline — needs a `--surface-subtle` token.
- `rgba(0,0,0,0.02)` as `<tr>` background in AnalysisPage — not a token.
- Interpretation panel uses `border-left: 3px solid var(--color-hairline)` — for a primary finding, should be Signal Blue.
- Active filter buttons use `color: #fff` hardcoded instead of `var(--color-paper)`.

### 4.5 Empty State & Illustration Gaps

- Landing page hero has ~200px of empty white below the CTA before the glance panel.
- Dashboard overview previews use Unicode braille/bullet characters as icons.
- NotFound page: plain text only, no visual.
- Experiments: empty-figures state shows a raw terminal command — inappropriate for a portfolio surface.

### 4.6 CSS Architecture Problems

- `index.css` lines 4–13 are each 1,000–5,000 character minified blocks.
- Layout rules for Dashboard, landing, compare, analysis all live in a single file.
- No `--surface-subtle: #fafafa` token despite 4+ uses.

### 4.7 Responsiveness Gaps

- Landing 3-column grid collapses to 1-column at 800px — too early (should be 600px → 2col, 1024px → 3col).
- Compare `table-wrap` has no horizontal scroll indicator.
- NetworkGraph inspector sidebar (220px fixed) overflows at < 600px.
- UMAP stage selector `overflow-x: auto` has no fade-gradient scroll affordance.

### 4.8 Accessibility Gaps

- `<details>/<summary>` for Research popover does not trap focus, does not close on outside click reliably, and does not manage `aria-expanded`.
- `role="tablist"` on UMAP stage selector, but child buttons lack `role="tab"` — mismatched ARIA.
- Spinner in `AppRoutes` fallback has no `aria-label`.
- Arrow-key tab navigation not implemented on result tabs.
- No focus restoration when Research popover closes.
- No `aria-live` on Experiments or Analysis error states.

### 4.9 PDF Simulation Report

Not implemented. See Section 12 for full specification.

### 4.10 Missing Footer

No footer exists on any page. Research-grade platforms require: attribution, GitHub link, research paper links, model version, research disclaimer.

---

## 5. Page-by-Page Improvement Plan

### 5.1 Landing Page (`/`)

**Gaps**: No illustration, abstract glance metrics, feature cards have no icons, credibility section has no separator.

**Improvements**:
1. **Logo in hero**: Render the new logo at 48×48px above the eyebrow text — immediate brand anchor.
2. **Hero illustration**: Static SVG social network illustration to the right of hero text at ≥ 1024px; below CTA on mobile. ~20 nodes, Signal Blue edges, Ink nodes, two cluster colors. `aria-hidden="true"`.
3. **Glance panel**: Add Lucide icons per metric — `TrendingDown` (convergence), `Network` (topology), `Hash` (seed).
4. **Feature card icons**: `GitBranch` (topology), `Star` (hubs), `Users` (communities) in illustration-palette colors.
5. **Credibility section**: Add hairline divider above it, plus compact citation pills (Axelrod 1997, Deffuant 2000, Watts & Strogatz 1998).
6. **Footer**: Site footer on all pages (Section 9).

### 5.2 Simulator / Dashboard (`/simulate`, `/runs/:runId`)

**Gaps**: `h1` reads "Run complete", loading stages are static, overview previews use Unicode, no export-graph action, `btn-secondary` invisible, no sidebar scroll affordance.

**Improvements**:
1. **Result `h1`**: Use outcome interpretation sentence as primary heading; demote run ID to `<code>` span.
2. **Staged loading**: Steps activate at 0ms, 800ms, 1600ms via `setTimeout` — perceived progress.
3. **Overview preview icons**: Replace Unicode with Lucide `Network` and `ScatterChart`.
4. **`btn-secondary`**: Add `border: 1px solid var(--color-hairline)`, hover: `border-color: var(--color-ink)`.
5. **Sidebar**: Add `border-right: 1px solid var(--color-hairline)` and `overflow-y: auto` for short viewports.
6. **Focus on completion**: `useEffect` + `ref.current?.focus()` on result `h1` when `result` becomes non-null.
7. **Export graph as PNG**: "Save as PNG" button in network toolbar using SVG serialization.
8. **Mobile config trigger**: Replace `⚙` with Lucide `SlidersHorizontal`.

### 5.3 Experiments Page (`/experiments`)

**Gaps**: Filter buttons use inline styles, empty-figures state shows terminal command, figure alt text is raw filename, figures have no loading skeleton.

**Improvements**:
1. **Filter pills**: `.filter-pill` + `.filter-pill.is-active` CSS classes — remove all inline styles.
2. **Empty figures state**: "Figures haven't been generated yet. See the Method guide for instructions." Link to `/guide`.
3. **Figure alt text**: Use `meta.finding.slice(0, 120)` as alt text.
4. **Figure loading skeleton**: Show `<LoadingSkeleton chart />` until `onLoad` fires.
5. **Anchor nav**: "Topology · Prestige · Contact · Validation" links at page top.

### 5.4 Compare Page (`/compare`)

**Gaps**: Entire page is a 6kb single-line JSX, chart has no Y-axis label, empty state has no visual.

**Improvements**:
1. **Refactor**: Break into named subcomponents — `RunArchive`, `ConfigTable`, `TrajectoryChart`, `ComparisonStatus`, `CompareEmptyState`.
2. **Y-axis label**: `label={{ value: 'Diversity (H)', angle: -90, position: 'insideLeft' }}`.
3. **Conclusion panel**: Plain-language summary below chart for both controlled and mixed modes.
4. **Empty state**: Lucide `GitCompare` icon + "Select two to four runs to compare their configurations and outcomes."

### 5.5 ML Analysis Page (`/analysis`)

**Gaps**: All section headings inline-styled, MetricCard value `fontSize: 28` inline, interpretation border is Hairline not Signal Blue, no limitations accordion.

**Improvements**:
1. **Remove all inline styles** — use token-aligned CSS classes.
2. **Interpretation panel**: `border-left: 3px solid var(--color-signal-blue)`.
3. **Limitations accordion**: "What this benchmark does not show" — covers synthetic data caveat, k-means partition, small dataset, no real-world generalizability.
4. **Source papers link**: "Read the foundational papers →" linking to the guide's citations section.

### 5.6 Guide / Method Page (`/guide`)

**Gaps**: Entire `Guide` component is inline in `App.tsx` as a 1,000-character single-line expression. No illustrations. Missing citations section.

**Improvements**:
1. **Extract**: Move to `frontend/src/pages/GuidePage.tsx` with proper formatting.
2. **Citations section**: Sixth accordion — "Foundational research" — listing all 10 papers with authors, year, and DOI link.
3. **Preset links**: All 5 sections should link to a relevant simulator preset.
4. **Inline diagrams**: Small SVG conceptual illustrations per accordion (see Section 10).

---

## 6. Navigation & Routing Improvements

### Current gaps
- `<details>/<summary>` for Research popover lacks focus management and `aria-expanded`.
- "Menu" text trigger on mobile should be a Lucide `Menu` icon.
- Logo is a CSS crop hack.

### Changes
- Replace Research `<details>` with a `useRef` + click-outside + `aria-haspopup="listbox"` + `aria-expanded` implementation — or use `@radix-ui/react-popover`.
- Mobile menu: same approach as Research popover for consistency.
- Logo:
```tsx
<Link className="brand" to="/" aria-label="Mosaic home">
  <img src="/brand/mosaic-logo.png" alt="" width={22} height={22} className="brand-mark" />
  <span className="brand-wordmark">Mosaic</span>
</Link>
```
- Skip link: `<a href="#main-content" className="skip-link">Skip to main content</a>` in `index.html` before `#root`.

---

## 7. Component Plan

### Already installed — expand usage

| Component | Current use | Action |
|---|---|---|
| `@radix-ui/react-tabs` | Dashboard | Add arrow-key support; ensure `aria-selected` consistency |
| `@radix-ui/react-toast` | ToastProvider | Add success/error icons per toast type |
| `@radix-ui/react-tooltip` | InfoTooltip | Wire to metric cards and chart labels |
| `lucide-react` | Not yet used | Apply systematically (see icon assignments below) |
| `motion/react` | Route transitions, AnimatedNumber | Expand per Section 8 |

### Lucide icon assignments

| Location | Icon |
|---|---|
| Nav CTA | `Play` |
| Mobile nav | `Menu` |
| Mobile config trigger | `SlidersHorizontal` |
| Overview network preview | `Network` |
| Overview UMAP preview | `ScatterChart` |
| Copy run link | `Link2` |
| Download JSON/CSV | `Download` |
| Landing: Topology card | `GitBranch` |
| Landing: Hubs card | `Star` |
| Landing: Communities card | `Users` |
| Glance: convergence | `TrendingDown` |
| Glance: topology | `Network` |
| Glance: seed | `Hash` |
| Compare empty | `GitCompare` |
| Guide: speaker | `User` |
| Guide: influence | `MessageSquare` |
| Guide: network | `GitBranch` |
| Guide: metrics | `BarChart2` |
| Guide: limits | `AlertCircle` |

### New components to build

| Component | File | Description |
|---|---|---|
| `SiteFooter` | `components/ui/SiteFooter.tsx` | 3-column footer with attribution and disclaimer |
| `ApiStatus` | `components/ui/ApiStatus.tsx` | Health check banner |
| `FilterPills` | `components/ui/FilterPills.tsx` | Reusable pill filter bar |
| `CitationPill` | `components/ui/CitationPill.tsx` | Compact paper reference |
| `IllustrationNetwork` | `components/ui/IllustrationNetwork.tsx` | Static SVG hero illustration |
| `SimulationReport` | `components/simulation/SimulationReport.tsx` | PDF report trigger and viewer |

---

## 8. Motion & Animation Plan

All existing motion is correct and should remain. Additions:

| Interaction | Implementation | Duration | Purpose |
|---|---|---|---|
| Logo hover | `rotate(15deg)` CSS transform | 300ms ease | Brand delight |
| Preset selection | Border + `scale(1.01)` | 120ms | Confirm intent |
| Loading stage steps | Staggered activation at 0/800/1600ms | — | Perceived progress |
| Metric card entrance | `motion.div` stagger 0, 60, 120, 180ms | 200ms | Reading order |
| Overview preview hover | `translateY(-2px)` + border color | 150ms | Interactive affordance |
| Filter pill active state | Background/color cross-fade | 100ms | Instant feedback |
| API error banner | Slide down from top | 200ms | Alert clarity |
| PDF report dialog | Scale + fade | 220ms | Spatial context |
| Footer entrance | `IntersectionObserver` + opacity | 400ms | Reduce noise |

All motion must check `useReducedMotion()` or `@media (prefers-reduced-motion: reduce)`.

---

## 9. Site Footer Specification

Add `<SiteFooter />` to all pages at the bottom of `.shell`.

**Layout** — three columns at ≥ 768px, single column below:

| Column 1: Brand | Column 2: Research | Column 3: Project |
|---|---|---|
| Mosaic logo mark (16px) | Experiments | GitHub repository |
| "Agent-based sociolinguistics simulation." | Compare runs | View research papers |
| Disclaimer: "Mosaic is a synthetic model. It does not make claims about real speech communities." | ML Analysis | Model v1.0 |
| | Method guide | Built with FastAPI + React |

**Styling**: `border-top: 1px solid var(--color-hairline)`. `padding: 48px 0`. 12px Graphite body, Ink section headings.

---

## 10. Illustration & Visual Storytelling Plan

### Landing hero illustration
- ~20-node SVG social network with Signal Blue edges and Ink nodes.
- Two node clusters in Ember vs. Signal Blue to imply accent divergence.
- Pure static SVG (no D3) in `IllustrationNetwork.tsx`.
- Two-column layout at ≥ 1024px; below CTA on mobile.
- `aria-hidden="true"` — decorative.

### Guide page diagrams (per accordion)
1. **Speaker** → Single circle with 6 colored dimension bars
2. **Influence** → Two circles with bidirectional arrow and confidence zone
3. **Network** → Three mini topology silhouettes (ring, hub, two-cluster)
4. **Metrics** → Two converging line curves (diversity, pairwise distance)
5. **Limits** → Circle with slash through it

### Empty state illustrations
- Dashboard empty: Dotted-outline network with `?` nodes — "waiting to be filled"
- Compare empty: Two overlapping ghosted comparison cards

### Do NOT add illustration to
- Result panels (data is the illustration)
- Analysis figures grid (real charts are the content)
- Experiment figures (same)

---

## 11. Simulation Experience Redesign

### Why simulations appear to fail

Three likely causes:

1. **Missing `VITE_API_BASE_URL`**: Undefined in local dev → requests go to `undefined/simulate`.
2. **CORS**: nginx proxies `/api/` to uvicorn but FastAPI may be missing CORS headers.
3. **`proxy_read_timeout` (currently 180s)**: May be insufficient for large simulations.

**Fixes**:
- `const BASE = import.meta.env.VITE_API_BASE_URL ?? ''` in `api/client.ts`.
- App-mount health check `GET /api/health`; show `<ApiStatus />` banner on failure.
- Confirm FastAPI has `CORSMiddleware` including the production domain.

### Result statement enrichment

Current: `"The population reached a stable state after X steps. Final diversity was Y."`

Proposed: `"Using a {topology_label} network of {N} speakers, the population {converged after X steps / reached the {T}-step limit}. Final diversity (H = {Y}) indicates {high/moderate/low} accent cluster spread."`

### Loading stage progression

```tsx
// Cosmetic staggered activation — not wired to real backend events
useEffect(() => {
  if (!isRunning) return;
  const t1 = setTimeout(() => setStage(2), 800);
  const t2 = setTimeout(() => setStage(3), 1600);
  return () => { clearTimeout(t1); clearTimeout(t2); };
}, [isRunning]);
```

---

## 12. Simulation Report (PDF) Specification

### Technology
`@react-pdf/renderer` — client-side, no server required.

### Report pages

**Page 1 — Cover**
- Logo mark + "Mosaic" wordmark
- "SIMULATION REPORT"
- Run ID, ISO timestamp

**Page 2 — Result Summary**
- Result interpretation sentence
- 2×2 metric grid: status, convergence time, final diversity, pairwise distance
- Configuration parameters table

**Page 3 — Evidence**
- Time-series chart (PNG via canvas serialization)
- Network topology name + key parameters
- UMAP final state (PNG)

**Page 4 — Reproducibility**
- Run ID, seed, configuration fingerprint
- Full parameter table
- Shareable URL

**Page 5 — Limitations & Attribution**
- Standard limitations paragraph
- Research references (Axelrod, Deffuant, Harrington, Gubian)
- Mosaic version number
- "Generated with Mosaic — [URL]"

### Styling
- A4, 40px margins.
- Black and Signal Blue only.
- Header on pages 2–5: "Mosaic · Run [run_id] · Page N of 5".

### Trigger
- "Download PDF report" button in Data tab next to JSON/CSV exports.
- `saveAs(blob, 'mosaic-run-{run_id}.pdf')`.

---

## 13. Typography Improvements

### Violations to fix

| Location | Current | Correct |
|---|---|---|
| `AnalysisPage` MetricCard value | `style={{fontSize: 28}}` | `.metric-value` class, 24px or 28px named token |
| Experiment section `h2` | `style={{fontSize: 24}}` | `.panel-title` class or `section-title` token |
| Eyebrow labels | 10px / 11px / 12px mixed | Always `--text-caption` (12px), `font-weight: 600`, `letter-spacing: 0.06em`, `text-transform: uppercase` |
| `run-header h1` | `font-size: 32px` fixed | `clamp(24px, 4vw, 32px)` |
| `panel-title` | `font-size: 20px`, no line-height | Add `line-height: 1.2; letter-spacing: -0.03em` |

### New tokens to add to `tokens.css`

```css
--surface-subtle: #fafafa;
--text-section-title: 20px;
--text-run-header: 32px;
--leading-panel-title: 1.2;
```

### Line length
- Body prose max-width: `65ch`.
- Panel descriptions: `max-width: 66ch`.
- Utility: `.prose { max-width: 65ch }`.

---

## 14. CSS Architecture Refactor

### Proposed structure

```
frontend/src/styles/
  tokens.css           ← exists
  accessibility.css    ← exists
  base.css             ← reset, body, globals (NEW)
  layout.css           ← shell, nav, studio, grid (NEW)
  components/
    buttons.css
    cards.css
    metrics.css
    tabs.css
    forms.css
    tooltips.css
    toasts.css
    skeletons.css
    badges.css
    footer.css
  pages/
    landing.css
    simulator.css
    experiments.css
    compare.css
    analysis.css
    guide.css
  motion.css           ← all @keyframes and transitions
index.css              ← @import chain only, zero rules
```

Priority: Medium (does not affect visual output; critical for maintainability).

---

## 15. Accessibility & Responsive Improvements

### Accessibility — Critical

1. **Skip link**: `<a href="#main-content" class="skip-link">Skip to main content</a>` before `<div id="root">` in `index.html`.
2. **Research popover**: Replace `<details>` with `useRef` + click-outside + `aria-expanded` + `aria-haspopup="listbox"`.
3. **UMAP ARIA**: Remove mismatched `role="tablist"`/button roles or fix to proper `role="tab"` on each button.
4. **Focus on run complete**: `useEffect(() => { if (result) resultHeadingRef.current?.focus(); }, [result])`.
5. **Spinner aria-label**: Add `aria-label="Loading"` to `<span className="spinner">` in fallback.
6. **Tabs arrow keys**: Radix Tabs supports this natively via keyboard — ensure `defaultValue` is set so keyboard handling is active.
7. **Live regions**: Add `aria-live="polite"` to Experiments and Analysis error containers.

### Color contrast audit

| Token | Hex | On Paper | Ratio | WCAG |
|---|---|---|---|---|
| Ink | #000000 | White | 21:1 | AAA |
| Graphite | #525252 | White | 7.0:1 | AAA |
| Ash | #737373 | White | 4.6:1 | AA (normal) |
| Mercury | #a3a3a3 | White | 2.8:1 | **Fails** |
| Signal Blue | #0077ff | White | 4.5:1 | AA (large text) |

> [!CAUTION]
> Mercury (#a3a3a3) fails WCAG AA. **Never use Mercury for text.** It is restricted to decorative strokes and disabled icon states only.

### Responsive fixes

| Width | Gap | Fix |
|---|---|---|
| < 600px | NetworkGraph inspector overflows | Stack inspector below graph inside a `<details>` |
| < 600px | UMAP stage selector no scroll affordance | `mask-image` right fade gradient |
| < 600px | Compare table overflows | `overflow-x: auto` + fade gradient |
| 600–800px | Landing grid collapses to 1-col too early | 2-col at 600px, 3-col at 1024px |
| Any | No `prefers-contrast: more` | Graphite → Ink, Ash → Graphite overrides |

---

## 16. 21st.dev Components & Shadcn Motion Effects

### Design constraint
Mosaic is light-only, white-canvas, monochrome chrome. **No dark gradients, glow effects, colored shadows, or full-bleed animated backgrounds** from these libraries. All effects must be adapted to Mosaic's token system — white surfaces, Ink text, Signal Blue only for primary actions.

### Selected 21st.dev / Motion Primitives components

| Component | Source | Location | Adaptation |
|---|---|---|---|
| **Text Reveal on Scroll** | Motion Primitives `BlurIn` / `FadeIn` | Landing hero headline, section titles | Ink text only; reduced-motion safe; 0→1 opacity + 4px y-settle |
| **Animated Counter** | Motion Primitives `NumberTicker` | Metric cards on result (replaces custom AnimatedNumber) | Keep existing AnimatedNumber — it already does this |
| **Stagger Children** | Motion Primitives `StaggeredFade` | Landing feature cards, metric cards entrance | 60ms stagger, opacity + translateY(4px), Ink/Paper only |
| **Scroll Progress Indicator** | Motion `useScroll` + `scaleX` | Top-of-page thin Signal Blue progress bar | 2px height, Signal Blue, appears on all content pages |
| **Magnetic Button** | 21st.dev magnetic | Nav CTA "Run a simulation" only | Max 8px pull; disabled on mobile; reduced-motion disables entirely |
| **Spotlight Card** | 21st.dev / Aceternity | Feature cards on landing page | White spotlight on Paper surface — no color fill, just a subtle radial brighten on hover |
| **Text Parallax** | 21st.dev `TextParallaxContent` | Credibility section on landing | Subtle 0.3× parallax factor; Ink text; `prefers-reduced-motion` disables |
| **Scroll Fade Edges** | shadcn `scroll-fade` utility | UMAP stage selector, run archive, compare table | CSS mask-image right/left fade gradient; shows scroll affordance |
| **Blur Reveal (entrance)** | Motion Primitives | Section titles on Experiments, Analysis, Compare, Guide | `filter: blur(4px) → blur(0)` on viewport enter; 300ms; reduced-motion: instant |
| **Line Reveal** | Custom `motion.div` scaleX | Hairline dividers between major sections | Dividers animate from 0→100% width on scroll enter; 400ms |
| **Presence Transition** | `AnimatePresence` (existing) | Already on route transitions | Keep; verify all pages are wrapped |
| **Floating Pill Ambient** | CSS `@keyframes float` | Nav pill | Very subtle 0→2px→0 y-transform, 4s ease-in-out infinite; `prefers-reduced-motion: none` |

### What NOT to use
- Particle backgrounds, aurora backgrounds, animated gradients — break the white-canvas design
- Full-width horizontal scroll sections — not appropriate for a research tool
- 3D card tilt on data cards — distracting during scientific reading
- Typewriter effects on body copy — accessibility issue (screen readers read partial text)
- Looping video backgrounds — off-brand
- Dark-mode spotlight radials (the Aceternity dark version) — import the light variant or adapt manually

### Implementation approach

All effects are implemented as **self-contained wrapper components** in `components/ui/motion/`. They accept `children` and apply the motion. This keeps page components clean.

```
components/ui/motion/
  BlurReveal.tsx       ← blur-in on viewport enter
  StaggerFade.tsx      ← stagger children entrance
  ScrollProgress.tsx   ← top progress bar
  MagneticButton.tsx   ← magnetic pull on nav CTA
  SpotlightCard.tsx    ← white spotlight on hover
  ScrollFade.tsx       ← mask-image fade edges
  FloatPill.tsx        ← ambient nav pill float
```

### Install additions needed
```bash
npm install motion  # already installed
# All effects are built using motion/react primitives — no new heavy dependencies
# SpotlightCard uses onMouseMove + CSS radial-gradient — no library needed
# MagneticButton uses onMouseMove + motion.div — no library needed
```

> [!IMPORTANT]
> Do NOT install Aceternity UI or Magic UI as full packages — they import Tailwind v3 and will conflict with the existing CSS token system. Use them only as **copy-paste reference implementations** adapted to Mosaic's vanilla CSS tokens.

---

## 17. Priority Matrix

### 🔴 Critical

| # | Task | Effort |
|---|---|---|
| C1 | Fix API base URL fallback + health check banner | S |
| C2 | Replace logo CSS hack with `<img>` + copy PNG to `public/brand/` | S |
| C3 | Fix `btn-secondary` — add Hairline border | S |
| C4 | Fix UMAP ARIA role mismatch | S |
| C5 | Extract `Guide` from `App.tsx` → `GuidePage.tsx` | S |
| C6 | Refactor `ComparePage.tsx` single-line JSX | M |
| C7 | Replace Research popover `<details>` with accessible popover | M |
| C8 | Add skip-to-content link in `index.html` | S |
| C9 | Move focus to result heading when run completes | S |

### 🟠 High

| # | Task | Effort |
|---|---|---|
| H1 | Landing hero SVG illustration | M |
| H2 | Logo mark on landing hero (48×48) + favicon | S |
| H3 | Animate loading stage progression (staggered) | S |
| H4 | Replace Unicode overview preview icons with Lucide | S |
| H5 | Change result `h1` from "Run complete" to outcome statement | S |
| H6 | Add `SiteFooter` to all pages | M |
| H7 | Remove all inline `style={{}}` from Experiments and Analysis | M |
| H8 | Add Y-axis label to Compare chart | S |
| H9 | Build `FilterPills` component for Experiments | S |
| H10 | Fix NetworkGraph mobile inspector overflow | M |
| H11 | Add API error state across all data-loading pages | M |

### 🟡 Medium

| # | Task | Effort |
|---|---|---|
| M1 | CSS architecture refactor — split `index.css` | L |
| M2 | Add `--surface-subtle` token; eliminate `#fafafa` hardcodes | S |
| M3 | Add Lucide icons to landing feature cards | S |
| M4 | Add Lucide icons to glance metrics | S |
| M5 | Add Citations section to Guide | S |
| M6 | Add Limitations accordion to Analysis | S |
| M7 | Fix all typography inline styles → token classes | M |
| M8 | Add `prefers-contrast: more` overrides | S |
| M9 | Add UMAP stage scroll fade gradient | S |
| M10 | Preset card selection checkmark badge | S |
| M11 | Add conclusion panel to Compare page | S |
| M12 | Fix Experiments empty-figures error copy | S |
| M13 | Extend Guide preset links to all 5 sections | S |
| M14 | Export network graph as PNG | M |
| M15 | Verify Radix Tabs arrow-key behavior | S |

### 🟢 Low (Delight layer)

| # | Task | Effort |
|---|---|---|
| L1 | Logo mark rotation on hover | S |
| L2 | Guide accordion SVG illustrations | L |
| L3 | Simulation PDF report (`@react-pdf/renderer`) | XL |
| L4 | Metric card entrance stagger (`StaggerFade`) | S |
| L5 | Research citation pills on landing | S |
| L6 | Landing hero network illustration (advanced SVG) | L |
| L7 | Compare empty-state illustration | M |
| L8 | `prefers-color-scheme` detection banner | S |
| L9 | Scroll progress bar (`ScrollProgress`) | S |
| L10 | Magnetic button on Nav CTA (`MagneticButton`) | S |
| L11 | Spotlight hover on landing feature cards (`SpotlightCard`) | S |
| L12 | Text parallax on credibility section | M |
| L13 | Blur-reveal on section titles (`BlurReveal`) | S |
| L14 | Line-reveal on hairline dividers | S |
| L15 | Nav pill ambient float animation | S |

*S < 1h · M 1–4h · L 4–8h · XL > 8h*

---

## 18. Implementation Roadmap

### Phase 1 — Critical fixes + CSS refactor (1–2 sessions)
All 🔴 Critical items + M1 CSS architecture refactor (done first to unlock clean foundation). Outcome: correct logo, API error handling, accessible navigation, readable maintainable code, split CSS.

### Phase 2 — High-impact polish (2–3 sessions)
All 🟠 items. Outcome: compelling first impression, satisfying result experience, professional footer.

### Phase 3 — Token system and content (1–2 sessions)
All 🟡 items. Outcome: consistent typography, all inline styles removed, WCAG 2.1 AA verified.

### Phase 4 — Delight layer + 21st.dev effects (3–4 sessions)
All 🟢 items including L9–L15 (scroll progress, magnetic button, spotlight cards, parallax, blur reveals, line reveals, ambient float). Outcome: PDF report, illustrations, full motion design, premium 21st.dev-quality interactions, flagship product.

---

## 19. Definition of Done

- [ ] Logo mark renders correctly at all sizes and contexts
- [ ] Simulations run and produce results without errors in production
- [ ] A new user reaches a meaningful first run within 60 seconds
- [ ] A completed run produces a self-explanatory result statement
- [ ] Every page handles API errors gracefully with a recovery path
- [ ] Every visualization has an accessible text or table alternative
- [ ] CSS is split into organized files using design tokens throughout
- [ ] All text passes WCAG 2.1 AA contrast (no Mercury for text)
- [ ] Site renders correctly at 375px, 768px, 1024px, and 1440px
- [ ] `prefers-reduced-motion` respected throughout
- [ ] Site footer with attribution, links, and disclaimer on all pages
- [ ] Simulation PDF report downloadable from any completed run
- [ ] 21st.dev-inspired motion effects (scroll progress, magnetic button, spotlight cards, blur reveals) are live and reduced-motion safe
