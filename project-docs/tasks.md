# Mosaic — Task Tracker

Living task list for all phases.
Status: `[ ]` not started · `[/]` in progress · `[x]` done

---

## Phase 0 — Documentation ✅ COMPLETE

- [x] Create project-docs/ folder with 9 files
- [x] Write progress.md, context.md, model.md, architecture.md
- [x] Write prd.md, mvp.md, tasks.md, experiments.md
- [x] Write design.md (frontend design system)
- [x] Write ml-pipeline.md (written from actual implementation)
- [x] Write frontend-implementation-plan.md

---

## Plan 1 — Foundation ✅ COMPLETE

- [x] All package directories and `__init__.py` markers
- [x] `runs/.gitkeep`, `results/figures/.gitkeep`
- [x] `simulation/config.py` — `SimConfig` dataclass (16 fields, validation, serialisation)
- [x] `requirements.txt`, `pyproject.toml`, `.gitignore`
- [x] `tests/test_config.py` — 26 tests passing

---

## Plan 2 — Simulation Engine ✅ COMPLETE

- [x] `simulation/metrics.py` — 7 pure metric functions
- [x] `simulation/network.py` — 4 topology builders, connectivity guarantee
- [x] `simulation/agent.py` — `AccentAgent` with bounded-confidence update rule
- [x] `simulation/model.py` — edge-based scheduling, k-means cache, convergence detection
- [x] `simulation/logger.py` — in-memory buffer, single CSV flush, timeline.json
- [x] `simulation/runner.py` — Monte Carlo loop, `results/summary.csv`
- [x] 25 runs in 11.7s (0.5s/run) ✓; reproducibility confirmed ✓

---

## Plan 3 — Unit Test Suite ✅ COMPLETE

- [x] `tests/test_network.py` — 8 tests
- [x] `tests/test_agent.py` — 7 tests
- [x] `tests/test_model.py` — 6 tests
- [x] `tests/test_metrics.py` — 7 tests
- [x] `pytest tests/ -v` — **59 tests, 0 failed** ✓

---

## Plan 4 — Experiments + Visualisations ✅ COMPLETE

- [x] `viz/figures.py` — 11 figure functions
- [x] `viz/gif.py` — `make_diffusion_gif()`
- [x] `experiments/exp1_topology.py` — topology comparison
- [x] `experiments/exp2_prestige.py` — prestige/centrality effect
- [x] `experiments/exp3_contact.py` — SBM dialect contact
- [x] `experiments/ablations.py` — 5 ablation conditions
- [x] `experiments/scurve.py` — S-curve validation (R²=0.9349) ✓
- [x] `experiments/heatmaps.py` — parameter heatmaps (1,000 parallelised runs)
- [x] `experiments/run_all.py` — single entry point
- [x] All 14 figures/GIF saved to `results/figures/` ✓

---

## Plan 5 — ML Analysis Layer ✅ COMPLETE

- [x] `analysis/_umap_compat.py` — UMAP import shim
- [x] `analysis/data_loader.py` — load CSVs, reconstruct graphs, PyG datasets
- [x] `analysis/clustering.py` — DBSCAN + silhouette
- [x] `analysis/gcn.py` — GCN + MLP model definitions
- [x] `analysis/evaluate.py` — training + evaluation pipeline
- [x] `analysis/umap_viz.py` — 4-panel UMAP figure
- [x] MLP: 89.2% accuracy; GCN: 51.1% ✓
- [x] `results/ml_results.json` ✓; all ML figures in `results/figures/` ✓

---

## Plan 6 — FastAPI Backend ✅ COMPLETE

- [x] `api/schemas.py` — Pydantic v2 request/response models
- [x] `api/main.py` — 10 endpoints (see architecture.md §5 for full list)
  - [x] `POST /run` — synchronous simulation execution
  - [x] `GET /results/{run_id}` — retrieve persisted run
  - [x] `GET /umap/{run_id}` — on-demand UMAP with caching
  - [x] `GET /runs` — paginated run archive
  - [x] `GET /runs/{run_id}/export` — JSON or CSV download
  - [x] `GET /runs/{run_id}/snapshots` — agent-state playback data
  - [x] `GET /topologies` — topology metadata
  - [x] `GET /config/schema` — UI field metadata
  - [x] `GET /experiments` — offline experiment archive
  - [x] `GET /figures/{filename}` — allowlist-protected figure serving
  - [x] `GET /analysis/summary` — ML results + figure manifest
- [x] CORS configured for `localhost:5173`
- [x] `tests/test_api.py` — integration tests

---

## Plan 7 — React Frontend ✅ COMPLETE

- [x] Vite 6 + React 18 + TypeScript scaffold in `frontend/`
- [x] `react-router-dom` v7 routing (7 routes)
- [x] `SimulationProvider` context — global state ownership
- [x] `api/client.ts` — typed fetch wrappers for all endpoints
- [x] `types/models.ts` — TypeScript interfaces matching backend schemas
- [x] `styles/tokens.css` — full CSS design token system
- [x] `styles/accessibility.css` — focus rings, reduced-motion
- [x] `index.css` — all utility/layout classes + mobile breakpoints
- [x] `LandingPage.tsx` — hero, feature cards, use-case grid
- [x] `Dashboard.tsx` — simulation studio with 4-tab result view
- [x] `ExperimentsPage.tsx` — research archive with filters, findings, download
- [x] `AnalysisPage.tsx` — ML benchmark table + clustering diagnostics
- [x] `ComparePage.tsx` — side-by-side run comparison
- [x] `ControlPanel.tsx` — config form; mobile `<dialog>` modal on ≤800px
- [x] `NetworkGraph.tsx` — D3.js force-directed graph
- [x] `TimeSeriesChart.tsx` — Recharts diversity + pairwise distance curves
- [x] `UmapScatter.tsx` — D3 scatter with timestep slider
- [x] `SnapshotPlayback.tsx` — agent-state snapshot scrubber

---

## Plan 8 — Integration + Polish ✅ COMPLETE

- [x] Backend Convergence Fixes: Distinct Stationarity vs. Consensus tracking
- [x] Exact API termination `reason` and timeline interaction fraction tracking
- [x] Property testing for interaction and clipping bounds (`tests/test_interactions.py`)
- [x] Frontend UX Audit: Remove dark mode warning, fix mobile layouts, add structured hover states
- [x] Add PDF Report Export capability for run summaries (`frontend/src/utils/capture.ts`)
- [x] `notebooks/demo.ipynb` — narrative walkthrough of one full run
- [x] End-to-end smoke test: POST /run → frontend render
- [x] Accessibility audit (keyboard nav, ARIA labels, color contrast)
- [x] Final README update with convergence conditions

---

## Plan 9 — Future Work [ ] IN PROGRESS
- [ ] Implement CI pipeline (`.github/workflows/tests.yml`)
- [ ] Error boundary + graceful degradation for API failures
- [ ] Loading skeleton states for all data-fetching components
- [ ] Performance: lazy-load D3/Recharts only when tab is active
- [ ] SEO: meta descriptions, og:image, canonical URLs for each page
- [ ] Version tag: `git tag v1.0.0`

---

## Ongoing

- [x] Update `progress.md` after each phase completion
- [x] Update `tasks.md` after each phase completion
- [x] Commit and push after each completed plan

---

*Last updated: 2026-07-11 — Phase 7 complete. Phase 8 starting next.*
