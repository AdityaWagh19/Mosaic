# Mosaic — Frontend Implementation Plan

**Status:** COMPLETED. The frontend has been successfully implemented according to this plan.
**Authority:** Repository source, `project-docs/`, and `project-docs/design.md`.  
**Last reviewed:** 2026-07-13

## 1. Product and technical baseline

Mosaic is a research demonstration for computational sociolinguistics. A user configures a social network and an accent-accommodation model, runs a reproducible agent-based simulation, and interprets how topology, prestige, bounded confidence, and phonetic drift affect accent convergence. It also contains completed offline experiments and an ML analysis pipeline for predicting final accent-cluster membership.

### Current system flow

```text
Configuration → FastAPI POST /run → NetworkX graph → Mesa simulation
→ CSV/JSON artifacts in runs/{topology}_{seed}/ → API response → React views
                                          ↘ GET /umap/{run_id} (computed/cached)

Offline experiment scripts → runs/ + results/figures/ + results/summary.csv
Offline ML evaluation      → results/ml_results.json + static figures
```

`SimConfig` is the configuration authority. A run builds one of four connected NetworkX graphs, assigns centrality and community IDs, initializes each agent’s six-dimensional accent vector, then samples one graph edge per timestep. The listener accommodates toward the speaker only when accent distance is below `theta`; `gamma` weights the speaker’s centrality and `sigma` adds bounded noise. The engine records agent snapshots every `log_every` steps and stops on entropy stability or at `T`.

### What is presently deliverable through the API

| Capability | Available now | Notes |
|---|---|---|
| Configure and run one simulation | Yes | `POST /run` is synchronous; request waits for completion. |
| Render final network and final cluster assignment | Yes | Response includes graph and final agent states. |
| Plot diversity and mean pairwise distance | Yes | Response includes a logged timeline. |
| Render four UMAP snapshots | Yes | `GET /umap/{run_id}` computes/caches coordinates after completion. |
| Load a known run | Yes | `GET /results/{run_id}`. |
| Discover topology names and active parameters | Yes | `GET /topologies` returns descriptions and parameter keys. |
| Browse experiment findings | Yes | Offline experiments available in `/experiments` route. |
| Show ML metrics/results in the app | Yes | ML analysis available via `/analysis` route. |
| Compare runs | Yes | Implemented in `/compare` route. |
| Animate actual network evolution | No | API returns final network state only; no per-timestep cluster/accent states. |

### MVP boundary

The immediate web MVP is a **single-run simulation studio**: configure, run, inspect final network, interpret two time-series metrics, and explore UMAP snapshots. It must not claim live streaming, experiment comparison, model inference, or per-timestep network playback until the supporting APIs exist. Research-library and ML-analysis pages are valuable follow-on work, not blockers for the MVP studio.

---

## 2. Information architecture

### Recommended route map

| Route | Page | Purpose | MVP |
|---|---|---|---|
| `/` | Landing | Explain Mosaic, set expectations, route to the simulator or research findings. | Yes |
| `/simulate` | Simulation Studio | Configure and execute one run; display results in-place. | Yes |
| `/runs/:runId` | Run Results | Deep-linkable, read-only view of a completed run. | Yes, once run lookup is polished |
| `/experiments` | Experiment Explorer | Browse the finished topology, prestige, contact, ablation, S-curve, and heatmap findings. | Later; requires read API |
| `/compare` | Run Comparison | Compare two to four saved runs and their metrics. | Later; requires API |
| `/analysis` | ML Analysis | Present validated model benchmarks, cluster diagnostics, and methodological caveats. | Later; requires API |
| `/guide` | Method Guide | Beginner-friendly explanation of the simulation, metrics, and reproducibility. | Later; static content can ship sooner |
| `*` | Not Found | Return users to the simulator or home page. | Yes |

### Navigation and user journey

The centered floating pill navigation uses `Mosaic` as the wordmark, links for **Simulator**, **Experiments**, **Method**, and one Signal Blue **Run a simulation** CTA. On small screens, collapse text links into a labeled menu; preserve the CTA.

```text
Landing
  ├─ “Run a simulation” → Simulation Studio → completed run → Run Results permalink
  ├─ “Explore findings” → Experiment Explorer → linked metric explanation / comparison
  └─ “How it works” → Method Guide → Simulator preset

Simulation Studio
  ├─ choose a preset or adjust parameters → Run
  ├─ result tabs: Overview / Network / Accent space / Data
  ├─ “Duplicate configuration” → editable Studio form
  └─ “Copy run link” → /runs/:runId
```

Future pages are deliberately separate from the run workspace. This keeps the main journey simple and leaves room for an experiment catalogue, exports, and a reproducibility archive without turning the simulator into an overloaded dashboard.

---

## 3. Page specifications

### 3.1 Landing

**Objective:** Establish what Mosaic models, what it does not model, and direct a new user to a meaningful first run.

**Layout:** White canvas, floating navigation, 1200px centered content, single 62px display heading, then a two-column explanation and a restrained three-card capability grid. Use 128px section gaps.

**Sections and copy:**

- Hero heading: **“See how social structure shapes accent change.”**
- Hero body: “Mosaic simulates how speakers influence one another across a network. Adjust the social structure, run the model, and inspect how accent patterns converge or persist.”
- Primary CTA: **Run a simulation →**; secondary Graphite link: **Explore the method**.
- “What you can test” cards: **Network topology**, **Social prestige**, **Community contact**.
- “From assumptions to evidence” strip: Configure → Simulate → Inspect → Reproduce.
- Research note: “Mosaic models synthetic accent vectors, not recorded speech or real communities.”

**States:** No data dependency. If research findings are not API-backed, do not show fabricated statistics or institutional logos.

**Responsive:** Stack every two/three-column block at `<768px`; reduce display heading smoothly; keep the nav CTA visible.

### 3.2 Simulation Studio

**Objective:** Let a user run a valid, reproducible single simulation and understand the output without knowing the underlying mathematics.

**Desktop layout:** A sticky, 320px left configuration rail; a right content area with a page header, a compact run-status area, then results. On tablet, the rail becomes a modal/sheet. On mobile, it becomes a top “Configure run” disclosure before results.

**Configuration rail:**

- Header: **Simulation setup**; secondary action: **Reset**.
- Preset selector: **Small-world baseline**, **Hub influence**, **Two-community contact**, **Quiet convergence**. Presets are frontend constants until a preset endpoint exists.
- Network section: topology radio/select and a short topology description returned by the API.
- Model section: agent count, maximum timesteps, prestige weight, confidence bound, noise, seed.
- Conditional topology section: ER edge probability; WS neighbours and rewiring; BA edges per new node; SBM within/between-community connection probability.
- Reproducibility section: seed, a plain-language deterministic-run note, and a “Copy configuration” action after completion.
- Primary button: **Run simulation →**. Disabled only while a request is in flight.

**Results area:**

- Before run: title **Start with a question**, body “Choose a topology and parameters, then run the model. Your results will appear here.” Include one preset card.
- During run: progress panel: **“Running {topology label} network…”** with “The model is computing interactions locally. This may take up to a minute for the default run.” Since the backend has no progress endpoint, use an indeterminate spinner—never a fake percentage.
- Error: **“This run could not be completed.”** Show the backend message, preserved configuration, **Try again**, and **Reset to baseline**. For invalid inputs, show the field error beside the relevant control.
- Completed: header **Run complete**, run ID, **Copy link**, **Duplicate configuration**, and a non-color-only status badge: “Converged” / “Reached maximum steps.”

**Result tabs:**

1. **Overview** — metric cards, interpretation callout, summary chart.
2. **Network** — interactive final-state graph and selected-agent panel.
3. **Accent space** — UMAP scatter and snapshot slider.
4. **Data** — configuration, metric definitions, and available JSON/CSV export actions once backend support exists.

**Metric cards:**

| Card | Value | Support copy |
|---|---|---|
| Run status | Converged / Maximum reached | “Convergence is based on stable cluster diversity, not a claim that every agent is identical.” |
| Convergence time | `{t}` steps or “Not reached” | “First logged point at which diversity stayed stable under the model criterion.” |
| Final diversity | `H = {value}` | “Higher values indicate a more varied distribution of accent clusters.” |
| Final pairwise distance | `D = {value}` | “Average distance between agents’ six-dimensional accent vectors.” |

**Responsive:** Charts retain a minimum useful height; the graph uses full width. Tabs become a horizontally scrollable tablist or a select menu. Do not place tiny controls over a dense graph.

### 3.3 Run Results

**Objective:** Provide a stable, shareable, read-only result view at `/runs/:runId`.

**Layout and contents:** Same visualization shell as the Studio, but starts with run metadata and a **Duplicate configuration** action that navigates to `/simulate` with serialized form state. Load `GET /results/:runId`, then UMAP separately. Show a 404-specific empty state: **“We couldn’t find this run.”** Explain that local run storage may have been cleared and link to Simulator.

**Loading/error:** Skeleton cards and charts while result data loads. UMAP has an independent panel skeleton and non-blocking error: **“Accent-space projection is unavailable for this run. The rest of the result is still available.”**

### 3.4 Experiment Explorer (post-MVP)

**Objective:** Turn the existing offline experimental work into an understandable research exhibit.

**Layout:** Overview cards for three experiments, filters by experiment and metric, then article-like result sections. Each section must distinguish a static published result from a user-created run.

- **Topology comparison:** Diversity trajectories, convergence distribution, final diversity.
- **Prestige and centrality:** centrality-vs-influence scatter, Spearman trend, final network snapshot.
- **Dialect contact:** four network snapshots, cross-community distance, merger time.
- **Validation:** ablation distribution, logistic adoption curve, parameter heatmaps.

Each figure needs a caption, a short finding, a “How to read this” disclosure, and a download link only after static-asset/export support is available.

### 3.5 Run Comparison (post-MVP)

**Objective:** Compare controlled conditions, not simply juxtapose screenshots.

Allow two to four saved runs. Show configuration differences first, then aligned metric cards and time-series overlays. The primary compare interaction is “lock all fields, vary one parameter.” Empty state: **“Choose at least two completed runs to compare.”** Reject incompatible time bases gracefully by normalizing the x-axis to `% of maximum steps` and labeling it.

### 3.6 ML Analysis (post-MVP)

**Objective:** Present ML results honestly as offline benchmark findings, not real-time predictions for a new run.

Show benchmark cards and a compact table: MLP 89.18% accuracy / 89.55% macro-F1; GCN 51.08% / 50.35%; random chance 20%; 80 training and 20 test runs; five target clusters. Include the caveat: **“In this benchmark, initial node features were more predictive than the graph model. This is evidence about this synthetic dataset, not a general claim about real-world accent change.”** Include clustering diagnostics: k-means silhouette 0.0895; DBSCAN found one cluster. Do not state that well-separated dialect zones were discovered.

### 3.7 Method Guide (post-MVP)

Use short accordion sections for “Agents and accent vectors,” “Networks,” “Accommodation rule,” “Convergence,” and “Metrics.” Each section links into a ready-made Studio preset. This is the primary educational layer, not a substitute for project documentation.

---

## 4. Reusable component architecture

### Foundation components

| Component | Key props / state | Responsibility |
|---|---|---|
| `AppShell` | `children`, active route | Global page canvas, navigation, route outlet. |
| `FloatingNav` | `links`, `primaryAction` | Pill navigation; keyboard menu at compact widths. |
| `PageHeader` | `eyebrow`, `title`, `description`, `actions` | Consistent page introduction. |
| `Card` | `variant: content|feature`, `children` | 16px Paper container; feature variant uses rare XL shadow. |
| `Button` | `variant`, `loading`, `disabled`, `icon` | Accessible primary and text-secondary actions. |
| `StatusBadge` | `status`, `label` | Text + icon status, never color alone. |
| `EmptyState` | `title`, `body`, `action` | First-run and absent-data experiences. |
| `InlineError` | `title`, `message`, `onRetry` | Actionable request failure. |
| `MetricCard` | `label`, `value`, `help`, `status` | Compact result summary. |
| `Tooltip` | `content`, `children` | Keyboard-available metric and control explanations. |

### Simulation feature tree

```text
SimulationStudioPage
├─ SimulationConfigPanel
│  ├─ PresetSelector
│  ├─ TopologyField
│  ├─ ParameterSection
│  │  └─ NumberField / RangeField (all controlled)
│  └─ RunActions
└─ RunWorkspace
   ├─ RunStatePanel (empty | running | error | completed)
   └─ ResultTabs
      ├─ OverviewTab → MetricGrid, MetricTrendChart, ResultNarrative
      ├─ NetworkTab → NetworkGraph, AgentInspector
      ├─ AccentSpaceTab → UmapScatter, SnapshotSlider
      └─ DataTab → ConfigSummary, ExportMenu
```

### Visualization components

| Component | Input | Local state | Responsibility |
|---|---|---|---|
| `NetworkGraph` | graph, final agent states, selection callback | D3 zoom transform, hovered/selected agent | Force-directed final graph; accessible list alternative. |
| `AgentInspector` | selected agent, connected graph | none | Agent ID, community, centrality, cluster, six named accent dimensions. |
| `MetricTrendChart` | timeline, selected series | active metric / tooltip | Diversity and pairwise distance over time. |
| `UmapScatter` | coordinates keyed by timestep, selected timestep | hover/selection | Accent-space snapshot; maintains stable agent ordering. |
| `SnapshotSlider` | available timesteps, value, change callback | keyboard focus only | Selects one returned UMAP snapshot. |
| `ComparisonChart` | normalized run series | visible runs | Post-MVP overlay chart. |

**Styling convention:** CSS Modules or feature-scoped CSS files consume only the canonical variables from `styles/tokens.css`. Migrate the existing frontend’s obsolete warm-neutral, serif, and mono references before functional work. Inline styles should not be used for design-system layout. Use semantic component classes; no hard-coded colors, radii, shadows, or breakpoint values in feature code.

---

## 5. Backend integration and API contract

### Existing endpoint mapping

| UI consumer | Endpoint | Request | Response used | Loading/error strategy |
|---|---|---|---|---|
| Studio topology field | `GET /topologies` | none | topology key, `desc`, active `params` | Fetch at panel mount; use a local fallback list and an inline retry if unavailable. |
| Studio run action | `POST /run` | `RunRequest` JSON | complete `RunResponse` | One awaited request with abort support. Indeterminate loading; preserve config on error. No polling/WebSocket needed. |
| Deep-linked result | `GET /results/{run_id}` | path ID | complete `RunResponse` | Page skeleton; 404-specific state; retry 5xx/network failures. |
| Accent-space tab | `GET /umap/{run_id}` | path ID | `{ "timestep": [[x,y], ...] }` | Start only after result success; independent panel loading/error. |

### Current `POST /run` request fields

`topology`, `N`, `T`, `gamma`, `theta`, `sigma`, `seed`, `p_er`, `k_ws`, `p_rewire`, `m_ba`, `n_communities`, `p_in`, `p_out`.

The UI should validate before submission using the engine’s real constraints: `N >= 2`, `T >= 1`, `gamma >= 0`, `theta > 0`, `sigma >= 0`, and `n_communities >= 2`. Use domain-recommended UI ranges—not misleading hard limits—as follows: `gamma 0–2`, `theta 0.05–0.5`, `sigma 0–0.05`. A user-entered number field should be available for valid values outside a slider’s recommendation.

### `RunResponse` fields and frontend transformations

| Field | UI use |
|---|---|
| `run_id` | Permalink, reproducibility identifier, API retrieval. |
| `config` | Result metadata and duplicate-run configuration. |
| `metrics` | Status and metric-card values. |
| `timeline[]` | Recharts line series, ordered by `timestep`. |
| `final_agent_states[]` | Network node fill by `cluster_id`, selected-agent detail, final accent table. |
| `network.nodes[]`, `network.edges[]` | D3 links and layout node attributes. |

### API/model mismatches to resolve before UI implementation

1. **Run IDs overwrite data.** Runtime `run_id` is `{topology}_{seed}`. Re-running a different configuration with the same topology and seed overwrites the directory; this violates the intended reproducibility/archive UX. Add a unique `run_id` plus a configuration fingerprint.
2. **SBM community count is misleading.** The API exposes `n_communities`, but network creation and annotation currently create two blocks only. Either implement arbitrary community counts or remove the field from `RunRequest`, endpoint metadata, and UI.
3. **Configuration defaults conflict.** `SimConfig` uses `p_in=0.15` and `p_out=0.02`; `RunRequest` uses `p_in=0.3` and `p_out=0.05`. Return an authoritative schema/defaults endpoint or align the models before creating presets.
4. **The public request omits `log_every`, `n_runs`, and `symmetric`.** This is acceptable for the single-run MVP if clearly intentional, but makes the symmetric ablation and output granularity inaccessible.
5. **No structured field validation response is documented.** Convert configuration `ValueError`s to a stable 422 response with `{field, code, message}` rather than a generic 500.
6. **UMAP output has no agent IDs, timestep metadata, labels, or projection parameters.** It relies on CSV ordering. Return snapshots as `{timestep, points: [{agent_id,x,y,community_id,cluster_id}]}` plus UMAP metadata to eliminate positional coupling.
7. **Clusters are recomputed only for the final state.** The API uses a fixed five-cluster k-means at response construction. Expose the cluster method, `k`, seed, and silhouette, and return historical labels if a cluster-evolution view is desired.

### Required APIs for the planned post-MVP pages

| Endpoint | Why it is needed |
|---|---|
| `GET /runs?limit=&cursor=&topology=` | Run history, picker, and comparison candidate list. |
| `GET /runs/{id}/snapshots?timesteps=` | Agent state / cluster evolution and real network playback. |
| `GET /runs/{id}/export?format=json|csv` | Reproducibility downloads. |
| `GET /experiments` and `GET /experiments/{id}` | Structured experiment metadata, result series, captions, and figure links. |
| `GET /analysis/summary` | Serve validated ML metrics and methodological metadata from `ml_results.json`. |
| `GET /analysis/figures/{name}` or static asset manifest | Safely render/download existing generated figures. |
| `GET /config/schema` | Authoritative field labels, defaults, recommended ranges, topology rules, and version. |
| `POST /runs` + `GET /runs/{id}/status` (or SSE) | Needed only if runs become asynchronous or exceed request-timeout limits. |

Do not add polling or WebSockets to the MVP: the current synchronous `POST /run` returns final data and documented runs are short. Adopt job polling/SSE only when the backend changes to an asynchronous queue.

---

## 6. State management, data layer, and architecture

Use TypeScript, React Router, and a small feature-oriented application structure. React context is appropriate for ephemeral Studio form and active-run UI state; use a query cache (recommended: TanStack Query) for endpoint data, request cancellation, retry behavior, and deep-linked result caching. This is a justified new dependency: it avoids duplicating fetch state and keeps result/UMAP queries independent.

```text
frontend/src/
├─ app/                 # router, providers, application shell
├─ api/                 # fetch client, endpoint functions, API DTOs
├─ features/
│  ├─ simulation/       # config form, presets, validation, run mutation
│  ├─ results/          # result tabs, metric transforms, agent inspector
│  ├─ experiments/      # post-MVP explorer
│  ├─ comparison/       # post-MVP comparison
│  └─ analysis/         # post-MVP ML report
├─ components/
│  ├─ core/             # Button, Card, Tooltip, EmptyState, StatusBadge
│  └─ visualizations/   # D3/Recharts visualization primitives
├─ pages/               # route-level composition only
├─ hooks/               # useResizeObserver, useMediaQuery, useRunShare
├─ lib/                 # formatters, scales, validation, chart helpers
├─ constants/           # presets, feature names, metric text, routes
├─ types/               # domain types and DTO-to-domain mappers
├─ styles/              # tokens.css, globals.css, component primitives
└─ assets/              # owned SVG marks only; no research result duplication
```

### State ownership

| State | Owner | Persistence |
|---|---|---|
| Draft simulation config | `SimulationConfigProvider` or page reducer | URL query for shareable drafts; optionally local storage. |
| Run mutation state | Query/mutation layer | In memory. |
| Completed result | Query cache keyed by `runId` | Refetchable from API. |
| UMAP result | Query cache keyed by `runId` | Independent from run result. |
| Graph zoom/selected node | `NetworkGraph` plus selected agent lifted to tab | In memory. |
| Active result tab / UMAP timestep | URL search params | Deep-linkable. |
| Experiment/ML collections | Query cache | Post-MVP API backed. |

Define strict API DTOs and map them to UI domain objects. Do not rely on the current `.d.ts` optional fields; `community_id` exists on API agent states and should be required. Centralize API base URL in `VITE_API_BASE_URL`, not a hard-coded localhost string.

---

## 7. Visualization plan

| Question | Visualization | Library | Interaction and accessibility |
|---|---|---|---|
| What does the final social network look like? | Force-directed node-link graph | D3 | Zoom/pan, hover/focus, select node; node size maps to centrality; final cluster uses bounded categorical accents only in data view. Provide agent table/list alternative. |
| Is the population stabilizing? | Dual line chart: diversity and pairwise distance | Recharts | Shared tooltip, metric toggle, direct values, table fallback. Avoid a shared y-axis unless normalized. |
| How does accent space change? | UMAP 2D scatter for four returned snapshots | D3 | Slider selects discrete snapshot; stable scales across snapshots; community shape/outline plus cluster color where data supports it. |
| Do communities merge? | Cross-community distance line | Recharts | Post-MVP experiment data; only for SBM. |
| Does prestige matter? | Scatter with regression + Spearman summary line | Recharts/D3 | Post-MVP experiment data. Include uncertainty/caption. |
| Which topology converges differently? | Mean line with SD band; convergence boxplot; final-diversity bar | Recharts for interactive series; D3 for boxplots | Post-MVP experiment API. |
| Where are parameter regimes? | Labeled heatmap | D3 | Post-MVP; keyboard-focusable cells plus data table. |
| How do model benchmarks compare? | Grouped bar/table and loss line | Recharts | Post-MVP static data API; show sample size, chance baseline, and caveat. |

### Visualization semantics

- Network node radius: `3 + centrality × 12`, clamped for legibility.
- For data visualizations only, assign clusters a stable categorical palette derived from Signal Blue, Deep Signal, Ember, Amber, and Crimson. Pair every category with a label, symbol/outline, and inspectable value; do not use this palette as UI chrome.
- Show community ID separately from cluster ID. Community is the initial structural group; cluster is an accent-state grouping. The UI must never imply they are equivalent.
- UMAP is a visualization of six-dimensional accent vectors, not a geographic map and not proof of naturally occurring dialect boundaries.

---

## 8. Content and copy guide

### Parameter descriptions

| Control | Label and help text |
|---|---|
| `N` | **Agents** — “How many speakers take part. Larger networks give richer structure but take longer to run.” |
| `T` | **Maximum steps** — “The run stops early if diversity stabilizes; otherwise it ends at this limit.” |
| `gamma` | **Prestige weight** — “How strongly a well-connected speaker influences a neighbour. At 0, centrality does not change influence.” |
| `theta` | **Confidence bound** — “The largest accent difference that still allows accommodation. Smaller values preserve separate groups more easily.” |
| `sigma` | **Phonetic drift** — “Small random variation added during accommodation. Set to 0 for a deterministic run.” |
| `seed` | **Random seed** — “Use the same seed and configuration to reproduce the same run.” |
| ER `p_er` | **Connection probability** — “Chance that any pair of speakers has a connection.” |
| WS `k_ws` | **Nearest neighbours** — “Initial number of local connections per speaker. Use an even number.” |
| WS `p_rewire` | **Rewiring probability** — “Chance that a local connection becomes a long-range shortcut.” |
| BA `m_ba` | **Links per new speaker** — “Controls how strongly hubs form as the network grows.” |
| SBM `p_in` | **Within-community connection** — “Chance of a tie between speakers in the same community.” |
| SBM `p_out` | **Between-community connection** — “Chance of a bridge between the two communities.” |

### Presets

| Name | Intent | Configuration |
|---|---|---|
| Small-world baseline | A balanced first run. | WS, N 200, T 10,000, k 6, rewiring .1, gamma 1, theta .3, sigma .01, seed 42. |
| Hub influence | Make centrality visible. | BA, N 200, T 10,000, m 3, gamma 1.5, theta .3, sigma .01, seed 42. |
| Two-community contact | Explore merger across sparse bridges. | SBM, N 200, T 10,000, p_in .15, p_out .02, gamma 1, theta .3, sigma .01, seed 42. |
| Quiet convergence | Remove random drift. | WS baseline with sigma 0. |

### Useful microcopy

- Network empty state: **“Run a simulation to see the final social network.”**
- UMAP empty state: **“Accent-space snapshots will appear after a completed run.”**
- Network tooltip title: **“Agent {id}”**; labels: Community, Accent cluster, Centrality, Accent dimensions.
- UMAP tooltip: **“Agent {id} · snapshot t={timestep}”**.
- Copy success: **“Run link copied.”**
- Export unavailable: **“Export will be available when run artifacts are exposed by the API.”**
- Non-convergence explanation: **“The model reached the maximum number of steps before the diversity criterion stabilized. This is a result, not an error.”**
- Algorithm explainers: **“Bounded confidence means agents only accommodate to neighbours whose accents are already close enough.”** / **“UMAP compresses six accent dimensions into two display dimensions so patterns can be inspected.”**

---

## 9. Design, responsive, and accessibility compliance

### Design checklist

- [ ] Paper `#ffffff` is the canvas and standard surface; Ink is primary text; Hairline separates structure.
- [ ] Signal Blue is reserved for the primary CTA, active navigation, and logo mark.
- [ ] Inter Variable is the only font; global tracking is `-0.025em`.
- [ ] Use 8px radii for controls, 16px for cards/images, and full radius only for capsules.
- [ ] Use 8px component gaps, 16px card padding, and 128px major section gaps.
- [ ] Use subtle 1px shadow only for pill navigation/CTA; reserve XL shadow for rare feature cards.
- [ ] No gradients, tinted surfaces, warm editorial tokens, Egyptienne/Diatype fonts, or blue text links.
- [ ] Decorative data colors are confined to visualization marks, never controls or layout chrome.

### Responsive strategy

- Build mobile-first from a single column. At 768px, introduce two-column content; at 1200px, use the full 1200px max-width layout.
- The config rail is not permanently visible below desktop. Use a modal sheet with focus trapping and a persistent “Configure run” trigger.
- Every visualization requires: responsive width, a minimum height, non-hover access to details, and a data-table/summary alternative when it cannot remain readable.
- Respect `prefers-reduced-motion`: no animated force reheating after initial layout, no autoplay UMAP transitions, and no indefinite decorative motion beyond the necessary loading indicator.

### Accessibility requirements

- Meet WCAG 2.1 AA contrast at the rendered size; do not use Ash for essential small text without verification.
- All form controls have visible labels, help text, keyboard behavior, and inline validation announced through an `aria-live` region.
- Primary focus treatment is a 2px Ink outline with 2px offset.
- Tabs, slider snapshots, graph node selection, and modal configuration must work by keyboard.
- D3 graph requires an accessible textual node inspector and summary. It must not be the only way to access a result.
- Charts need descriptive titles, visible legend labels, a screen-reader summary, and a downloadable/copyable data alternative once supported.
- Status uses text plus icon; no red/green-only meaning.

---

## 10. Phased implementation plan

| Phase | Scope and deliverables | Dependencies | Acceptance criteria | Complexity |
|---|---|---|---|---|
| 0. Contract alignment | Resolve run IDs, SBM `n_communities`, default mismatch, validation errors, UMAP metadata. Write frontend API fixtures. | Backend changes | API schema is documented/versioned; same config never silently overwrites another run. | High |
| 1. Frontend foundation | Replace retired styling; apply current tokens; add router, app shell, nav, core components, responsive CSS, error boundary. | `design.md` | Build/lint pass; landing and empty simulator match token rules at desktop/mobile. | Medium |
| 2. Configuration studio | Typed config reducer, presets, topology metadata, conditional controls, client validation, accessible fields. | `/topologies`, schema decision | Each supported topology submits valid payload; controls preserve draft through an error. | Medium |
| 3. Run lifecycle and overview | Run mutation, indeterminate loading, error handling, run metadata, metric cards, deep links, read-only results route. | `POST /run`, `GET /results` | A default run completes and can be loaded by URL; no fake progress; non-convergence explained. | Medium |
| 4. Core visualizations | Rebuild D3 final network, Recharts timeline, UMAP panel/slider, node inspector, resize and accessibility fallbacks. | Run/UMAP response; Phase 3 | Values match API payload; graph and tabs are keyboard usable; no obsolete design tokens. | High |
| 5. Reproducibility polish | Config copying, URL draft serialization, run link, responsive config sheet, loading skeletons, frontend tests. | Stable run IDs | User can rerun an exact configuration and share a completed-run URL. | Medium |
| 6. Research archive APIs | Add run list/export, experiment manifest/data, ML summary/static asset API. | Backend ownership decision | No frontend reads server filesystem directly; static analysis/experiments are documented API resources. | High |
| 7. Research demonstration | Experiment Explorer, comparison, ML Analysis, figure downloads, method guide, citations/caveats. | Phase 6 | Existing findings are browsable, accurately contextualized, and exportable. | High |

### Test plan

- Unit test configuration validation, preset selection, DTO mappers, metric formatting, and visualization transforms.
- Component test loading, error, empty, completed, and non-converged states for every result tab.
- Mock API integration test the full Studio flow plus deep-linked result retrieval and UMAP failure isolation.
- Playwright-style end-to-end test once the development server is available: baseline run → inspect node → change UMAP snapshot → copy link → reload result.
- Visual regression at 375px, 768px, 1200px, and 1440px against the final design tokens.

---

## 11. Research-demo opportunities and guardrails

Prioritized improvements after the MVP:

1. **Guided first run:** preset-driven walkthrough that highlights network, metric trend, and UMAP in three steps. It makes the project approachable without obscuring the science.
2. **Reproducibility card:** configuration fingerprint, engine/version metadata, seed, run timestamp, and export. This is the strongest resume-quality research engineering signal.
3. **Controlled comparison mode:** lock parameters, vary one factor, and overlay metrics. This transforms the app from a visualization shell into an experiment tool.
4. **Publication-quality export:** CSV/JSON plus SVG/PNG chart export with captions and parameter metadata.
5. **Experiment library:** serve the completed figures with methods, uncertainty, and concise findings. This connects the interactive UI to the already-finished research work.
6. **Honest ML report:** emphasize the observed MLP-over-GCN outcome and clustering weakness as a methodological result, not a polished but misleading “AI success” story.

Do not add authentication, a database, real-time collaboration, geographic dialect maps, or audio-processing controls. They are outside the project’s stated scope and would dilute the simulation-first demonstration.

---

## 12. Implementation decision summary

Build the **single-run Simulation Studio** first, with Landing and shareable Run Results as its supporting pages. Use D3 for the final network and UMAP scatter; use Recharts for metric trends. Keep React state focused on a draft configuration and local visualization interaction, while endpoint data belongs in a query cache. Make the current backend contracts reliable before exposing advanced interactions. Then add experiment, comparison, and ML pages only when the existing offline artifacts are represented by explicit read APIs.

This sequence satisfies the current MVP, respects the final design system, and leaves a clean path to a strong research demonstration without frontend architectural rework.
