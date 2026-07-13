# Mosaic — Progress Log

A living record of decisions, findings, and blockers throughout development.
Updated continuously. Each entry is date-stamped.

---

## 2026-07-09 — Day 1: Planning & Documentation

### Project Established
Mosaic is a modular Python simulation of accent and dialect evolution in social
networks, combining Agent-Based Modelling, network science, and ML analytics,
with a custom React/FastAPI web interface.

### Key Design Decisions Made Today

**Accent representation:**
Chose a 6-dimensional named phonetic vector over abstract feature labels.
Dimensions: F1/F2 of /æ/, F1/F2 of /ɑ/, VOT of /p/, speaking rate proxy.
All normalized to [0,1]. Values initialized per community from plausible
phonetic ranges (no real audio processing).
Rationale: makes the model an accent model, not a generic opinion dynamics model.

**Update rule:**
Adopted prestige-weighted asymmetric accommodation:
  a_i += α_ij * (a_j - a_i) + ε
  where α_ij = γ · centrality(j) · 𝟙[‖a_j − a_i‖ < θ]
Rationale: grounded in Communication Accommodation Theory (Giles et al. 1991).
Asymmetric (only listener updates). Centrality drives prestige influence.

**Network topologies:**
ER, WS, BA, SBM (four). SBM added specifically for the two-community
dialect contact experiment. All available natively in NetworkX.

**Interaction scheduling:**
Random edge sampling in model.step() rather than random agent activation.
Rationale: language change is a property of dyadic encounters, not individual
agent decisions. Mesa's RandomActivation picks agents; we pick edges instead.

**ML components:**
- k-means + DBSCAN: unsupervised dialect zone discovery on final states
- GCN (PyTorch Geometric): supervised trajectory prediction from initial state
- UMAP: accent space evolution visualization at 4 timesteps
- SHAP: feature importance on MLP baseline (optional)
Start with GCNConv; upgrade to GATConv for interpretable attention weights.

**Data pipeline:**
CSV per run (not HDF5). Log every 100 steps. Save config.json per run.
Rationale: CSV + pandas is sufficient for N≤500, T≤10,000. Simple and debuggable.

**Frontend:**
React + Vite (frontend), FastAPI (backend), D3.js (network viz), Recharts (charts).
FastAPI serves simulation results as JSON. Frontend is a separate Phase 3 deliverable.

**Technology stack finalized:**
Mesa, NetworkX, PyTorch, PyTorch Geometric, umap-learn, FastAPI, React, D3.js,
Recharts, pytest, matplotlib, seaborn.

### Research Questions
RQ1: How does network topology affect rate and pattern of accent convergence?
RQ2: Does agent centrality correlate with speed of accent influence on community?
RQ3: Does a GCN outperform a flat MLP in predicting final accent from initial state?

### Documentation Structure (9 files)
Created project-docs/ with 9 empty files. Creation order:
progress.md → context.md → model.md → architecture.md → prd.md →
mvp.md → tasks.md → experiments.md → ml-pipeline.md

### Open Questions / Decisions Deferred
- Exact phonetic range values for community initialization (to decide in model.md)
- Number of communities for SBM default (2 or 3?)
- Whether to start GCN with GCNConv or go straight to GATConv
- Frontend: whether to show simulation running live (WebSocket) or only show
  completed run results (REST polling) — deferred to architecture.md

---

## 2026-07-10 — Plan 1 (Foundation): Complete

### What Was Built

**Project skeleton:** All 6 Python packages created (`simulation/`, `experiments/`,
`viz/`, `analysis/`, `api/`, `tests/`) with `__init__.py` markers. Directory
placeholders created for `runs/`, `results/figures/`, `notebooks/`.

**`simulation/config.py` — `SimConfig` dataclass:**
The single source of truth for all simulation parameters. All 16 fields from
`architecture.md §3.1` implemented with defaults. Key design choices:
- `to_dict()` / `from_dict()` via `dataclasses.asdict` — lossless JSON round-trip.
- `from_dict()` silently ignores unknown keys for forward compatibility.
- `__post_init__` validates topology (raises `ValueError`), N, T, theta, sigma, gamma, n_runs.
- `run_id` property added here (`{topology}_{seed}`) — deterministic, single source
  of truth used by logger (Plan 2) and data_loader (Plan 5).
- `save()` / `load()` file helpers added for logger convenience.

**`tests/test_config.py` — 26 tests, all passing:**
- 10 default value tests (one per field group)
- 6 serialisation tests (dict round-trip, JSON round-trip, file save/load, run_id format)
- 2 forward-compatibility tests (extra keys ignored, partial dict fills defaults)
- 8 validation tests (each invalid parameter raises `ValueError`)

**Project config files:**
- `requirements.txt` — pinned versions with GPU (CUDA 12.1) install instructions
- `pyproject.toml` — project metadata + pytest discovery config + coverage config
- `.gitignore` — tracks `runs/.gitkeep`, ignores all generated run directories and outputs

### Test Results
```
pytest tests/test_config.py -v
26 passed in 2.13s
```

### Key Decision: PyTorch Version Correction

The implementation plan originally pinned `torch==2.1.2+cu121`, but this version
does not exist — the PyTorch CUDA 12.1 wheel server starts at 2.2.0.

**Resolution:** Updated to `torch==2.4.1+cu121` (stable, latest 2.4.x) with
matching `torch-geometric==2.6.1` (compatible with PyTorch 2.4.x). Both the plan
and `requirements.txt` updated. Version bump only — no architectural change.

GPU confirmed: NVIDIA GeForce (4GB VRAM), driver 529.04, CUDA 12.0.
Driver 529.04 ≥ 527.41 minimum for cu121 — confirmed compatible.

---

## 2026-07-10 — Plan 2: Simulation Engine

### Modules Implemented
Six modules written and verified:

| Module | Lines | Key decisions |
|---|---|---|
| `simulation/metrics.py` | ~200 | 7 pure functions; `shannon_diversity_from_labels` for cached path |
| `simulation/network.py` | ~130 | 4 topology builders; ≤5 retries for ER/SBM; LCC fallback |
| `simulation/agent.py` | ~80 | No `step()` on agent; noise via `model.rng` (reproducible) |
| `simulation/model.py` | ~270 | k-means cache (refit every 500 steps); std(h_history) < 0.001 |
| `simulation/logger.py` | ~120 | In-memory row buffer; single CSV flush at close(); timeline.json |
| `simulation/runner.py` | ~110 | Sequential loop; seed+i per replicate; summary.csv |

### Performance Results (N=200, T=10,000)
- **0.5 seconds per run** on NVIDIA GTX 1650
- **25 runs in 11.7s total** — 5× faster than the 60s exit criterion
- 20,200 CSV rows per run (200 agents × 101 timesteps) written in one flush

### Verification Results
- 25 run directories: `runs/watts_strogatz_42/` through `…_66/`
- Each run: 4 files (`agent_states.csv, config.json, metrics.json, timeline.json`)
- CSV columns: `timestep, agent_id, community_id, centrality, d0..d5` ✓
- `results/summary.csv`: 25 rows, 11 columns ✓
- Reproducibility: same seed → bit-identical CSV (0 differences) ✓

---

## 2026-07-10 — Plan 3: Unit Test Suite

### What Was Built

Four new test files covering every Plan-2 module:

| File | Tests | Focus |
|---|---|---|
| `tests/test_network.py` | 8 | Connectivity, node count (WS/BA), centrality [0,1], community_id, SBM 2-community, non-SBM single community, prototypes |
| `tests/test_agent.py` | 7 | Proportional movement, bounded-confidence gate, gamma=0, sigma>0 stochasticity, sigma=0 determinism, clipping [0,1], seed reproducibility |
| `tests/test_model.py` | 6 | Required output keys, timeline structure, run_id directory naming, hard cutoff guarantee, convergence detection, seed reproducibility |
| `tests/test_metrics.py` | 7 | H=0 for identical accents, D=0 for identical accents, D_cross=0 when communities converge, residual score shape, logistic R² in [0,1], positive D for diverse data, label-consistency |

**Total: 59 tests across 5 files (26 Phase-1 config + 33 Phase-3 new)**

### Test Results
```
pytest tests/ -v
59 passed in 3.36s
```

---

## 2026-07-10 — Plan 4: Experiments + Visualisations ✅ COMPLETE

### Total Runtime
481 seconds (8.0 min) end-to-end on CPU.

### All 14 Outputs Present in `results/figures/`

| File | Size | Experiment |
|---|---|---|
| `e1_diversity_timeseries.png` | 510 KB | Exp 1 — Topology |
| `e1_convergence_boxplot.png` | 161 KB | Exp 1 — Topology |
| `e1_final_diversity_bar.png` | 132 KB | Exp 1 — Topology |
| `e2_centrality_vs_influence.png` | 414 KB | Exp 2 — Prestige |
| `e2_spearman_vs_gamma.png` | 153 KB | Exp 2 — Prestige |
| `e2_network_snapshot.png` | 1399 KB | Exp 2 — Prestige |
| `e3_network_4panel.png` | 4356 KB | Exp 3 — Contact |
| `e3_cross_community_distance.png` | 222 KB | Exp 3 — Contact |
| `e3_merger_time_bar.png` | 107 KB | Exp 3 — Contact |
| `ablation_boxplot.png` | 215 KB | Ablations |
| `scurve.png` | 170 KB | S-Curve |
| `heatmap_convergence_theta.png` | 208 KB | Heatmaps |
| `heatmap_diversity_gamma.png` | 168 KB | Heatmaps |
| `diffusion.gif` | 513 KB | GIF (60 frames @ 20 fps) |

### Key Findings

**Exp 1 — Topology (100 runs x 4 topologies):**
- BA converges fastest: mean t_conv=8,908 vs WS 9,636, ER/SBM hit T=10,000
- BA and WS reach final_diversity ~1.59 despite structural differences

**Exp 2 — Prestige/Centrality (100 BA runs x 4 gamma values):**
- Spearman rho near 0 for all gamma values (gamma=0: -0.003, gamma=2: 0.006)
- Centrality affects alpha but network topology mediates actual influence

**Exp 3 — Dialect Contact (SBM, 4 p_out values):**
- All merger_time_mean values hit T=10,000 — no community merger in 10,000 steps

**Ablations (5 conditions x 25 runs):**
- A2 (no prestige) fastest convergence: t=7,088
- A4 (symmetric update) lowest diversity: 1.35 vs Baseline 1.59

**S-Curve (10 WS runs):**
- R²=0.9349 >= 0.85 — logistic fit confirmed

---

## 2026-07-10 — Phase 5: ML Analysis Layer ✅ COMPLETE

### What was built
- `analysis/_umap_compat.py` — UMAP/TensorFlow compatibility shim
- `analysis/data_loader.py` — run discovery, graph reconstruction, PyG dataset builder
- `analysis/clustering.py` — DBSCAN, silhouette scoring, UMAP cluster overview figure
- `analysis/gcn.py` — 2-layer GCN + 2-layer MLP model definitions + helpers
- `analysis/evaluate.py` — full ML orchestration pipeline (100-epoch training)
- `analysis/umap_viz.py` — 4-panel UMAP accent-trajectory visualization
- `project-docs/ml-pipeline.md` — task definition, architecture spec, full results

### Results

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Random chance | 20.0% | — |
| MLP (baseline) | **89.2%** | **89.5%** |
| GCN | 51.1% | 50.3% |

**GCN vs MLP delta: −38.1 pp**

### Key Research Finding
The MLP's 89.2% accuracy reveals that the **initial accent position** is
highly predictive of final cluster membership. The GCN's lower performance
(51.1%) is attributable to **over-smoothing**: 2-layer graph convolution
averages over neighbours, diluting the precise initial accent signal.
Network topology governs convergence speed and isogloss boundaries,
not which cluster an individual agent ultimately joins.

### Clustering
- k-means silhouette: 0.089 (weak separation — final space is a continuum)
- DBSCAN: 1 cluster found — no discrete dialect zones; continuous distribution

---

## 2026-07-11 — Phase 6: FastAPI Backend ✅ COMPLETE

### What was built

**`api/schemas.py`** — Pydantic v2 models for all request/response contracts:
- `RunRequest` — mirrors `SimConfig`, all fields optional with backend defaults
- `RunResponse` — full result payload including config, metrics, timeline, agent states, network
- `MetricsData`, `TimelineEntry`, `AgentState`, `NetworkNode`, `NetworkEdge`, `NetworkData`

**`api/main.py`** — FastAPI application with 10 endpoints:

| Method | Path | Description |
|---|---|---|
| `POST` | `/run` | Run simulation synchronously; returns full `RunResponse` |
| `GET` | `/results/{run_id}` | Retrieve result of a previously completed run |
| `GET` | `/umap/{run_id}` | Compute or retrieve cached UMAP coordinates (4 timesteps) |
| `GET` | `/runs` | Paginated list of all locally persisted runs; filterable by topology |
| `GET` | `/runs/{run_id}/export` | Download JSON summary or agent-state CSV |
| `GET` | `/runs/{run_id}/snapshots` | Raw agent-state snapshots at selected timesteps |
| `GET` | `/topologies` | Topology metadata for frontend config form |
| `GET` | `/config/schema` | UI metadata (labels, ranges, help text) for all config fields |
| `GET` | `/experiments` | Offline experiment archive with figure availability |
| `GET` | `/figures/{filename}` | Serve curated research figures (allowlist-protected) |
| `GET` | `/analysis/summary` | ML benchmark results + figure manifest |

**Key implementation decisions:**
- Simulation runs synchronously (< 30s for N=200, T=10,000) — no async queue needed
- UMAP coordinates computed on-demand and cached to `runs/{run_id}/umap_coords.json`
- k-means (k=5) run inline in `_construct_run_response` to supply `cluster_id` per agent
- Figure serving uses an explicit allowlist to prevent arbitrary filesystem exposure
- CORS enabled for `localhost:5173` (Vite) and `127.0.0.1:5173`
- `run_id` format: `{topology}_{seed}_{counter}` (unique across re-runs of same config)

**`tests/test_api.py`** — Integration test suite covering all endpoints.

---

## 2026-07-11 — Phase 7: React Frontend ✅ COMPLETE

### What was built

**Framework:** React 18 + Vite 6 + TypeScript, running at `http://localhost:5173`.

**Routing:** `react-router-dom` v7, five main routes:

| Route | Component | Description |
|---|---|---|
| `/` | `LandingPage` | Hero, feature cards, use-case grid, CTA |
| `/simulate` | `Dashboard` | Full simulation studio with ControlPanel + result tabs |
| `/runs/:runId` | `Dashboard` | Deep-link to a specific persisted run |
| `/experiments` | `ExperimentsPage` | Curated research archive with filter + download |
| `/compare` | `ComparePage` | Side-by-side run comparison picker |
| `/analysis` | `AnalysisPage` | ML benchmark report + clustering diagnostics |
| `/guide` | `Guide` | Method explanation inline page |

**Global state:** `SimulationProvider` context (`SimulationContext.tsx`) owns:
- `config` — current form values mirroring `RunRequest`
- `result` — full `RunResponse` from last run
- `umap` — UMAP snapshot data
- `isRunning` — loading flag
- `error` — error string

**Components built:**

| File | Description |
|---|---|
| `components/simulation/ControlPanel.tsx` | Form with all SimConfig fields; mobile `<dialog>` modal on ≤800px |
| `components/simulation/ConfigForm.tsx` | Shared form body used by both desktop panel and mobile dialog |
| `components/visualizations/NetworkGraph.tsx` | D3.js force-directed graph; nodes sized by centrality, coloured by cluster |
| `components/visualizations/TimeSeriesChart.tsx` | Recharts line chart: diversity + pairwise distance vs timestep |
| `components/visualizations/UmapScatter.tsx` | D3 scatter with timestep slider over 4 UMAP snapshots |
| `components/visualizations/SnapshotPlayback.tsx` | Agent-state snapshot scrubber using `/runs/{id}/snapshots` |

**Pages built:**

| File | Key features |
|---|---|
| `LandingPage.tsx` | Hero headline, feature grid (3-col), use-case grid (3-col) |
| `Dashboard.tsx` | 4-tab result view: Overview (chart), Network (D3), Accent space (UMAP), Data (export) |
| `ExperimentsPage.tsx` | Experiment filter pills, per-figure findings captions, "how to read" disclosures, PNG download buttons |
| `AnalysisPage.tsx` | MLP/GCN benchmark table, silhouette/DBSCAN diagnostic cards, interpretation section |
| `ComparePage.tsx` | Two run-picker dropdowns; side-by-side metric comparison |

**Styles:**
- `styles/tokens.css` — CSS custom properties: colors, spacing, radius, shadows, typography
- `styles/accessibility.css` — Focus rings and reduced-motion support
- `index.css` — All layout classes, component classes, mobile breakpoints, `<dialog>` styles

**API client:** `api/client.ts` — typed fetch wrappers for all 10 backend endpoints.

**TypeScript types:** `types/models.ts` — full interface definitions matching backend Pydantic schemas.

### Mobile UX
- Desktop (> 800px): sticky 300px sidebar panel
- Mobile (≤ 800px): sidebar hidden, "⚙ Configure run" button opens native `<dialog>` with slide-up animation and backdrop blur

---

## 2026-07-11 — Repository Cleanup

Removed 17 tracked files that were obsolete or orphaned:
- Root-level planning docs: `IMPLEMENTATION_PLAN.md`, `phase5.5_validation_plan.md`, `phase5.5_validation_walkthrough.md`
- Orphaned CSS: `components.css`, `landing.css`, `layout.css`, `navbar.css`
- Orphaned components: `NavBar`, `FeatureCard`, `UseCaseCard`, `Badge`, `Dropdown`, `Slider`, `Button`, `Card`
- Orphaned layouts: `MainLayout.tsx`, `Sidebar.tsx`
- Local `runs/` directory cleared (1,467 experiment output directories, gitignored)
- Python `__pycache__` directories purged locally

---

## 2026-07-13 — Plan 8 (Integration + Polish): Complete

### What Was Built

**Backend Convergence Refactoring:**
Fixed the critical phantom diversity bug by eliminating KMeans entropy checks for convergence. Implemented strict separation between:
- **Consensus:** Triggered when `sigma == 0` (noiseless), requiring absolute pairwise distance across all agents to fall below `epsilon_distance` (1e-6).
- **Stationarity:** Triggered when `sigma > 0` (noisy), requiring maximum agent displacement over a sliding window `W` (20) to remain below `epsilon_max` (1e-4).
- Added explicit `termination_reason` metrics to the API response.

**Frontend UX Polish:**
- Eliminated disruptive dark mode alerts.
- Fixed broken mobile hero illustrations in CSS.
- Added structured hover states and transition timings across all interactive elements (buttons, cards, links).
- Implemented robust PDF reporting via `html2canvas` and `jspdf` (`frontend/src/utils/capture.ts`).

**Property Testing:**
- Rigorous tests added (`tests/test_interactions.py`) to verify update rules, bounds clipping, and suppressed noise during rejected interactions.

**Repository Sanitization:**
- Scrubbed all leftover UI recordings, scratch scripts, cache directories, and obsolete planning markdown files.
- Renamed `research/` to `docs/` for better academic organization.

---

*Last updated: 2026-07-13 — Phase 8 (Integration + Polish) complete. Phase 9 (Future Work) next.*
