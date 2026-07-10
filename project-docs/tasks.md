# Mosaic — Task Tracker

Living task list aligned with `IMPLEMENTATION_PLAN.md` (8 plans).
Update status markers as work progresses.

Status: `[ ]` not started · `[/]` in progress · `[x]` done

---

## Phase 0 — Documentation

- [x] Create project-docs/ folder with 9 files
- [x] Write progress.md
- [x] Write context.md
- [x] Write model.md
- [x] Write architecture.md
- [x] Write prd.md
- [x] Write mvp.md
- [x] Write tasks.md
- [x] Write experiments.md
- [x] Write design.md (merged from 4 source files)
- [ ] Write ml-pipeline.md — deferred to Plan 5 (written from actual implementation)
- [x] Create IMPLEMENTATION_PLAN.md in project root

---

## Plan 1 — Foundation

### 1.1 Project Skeleton
- [x] Create all package directories: `simulation/`, `experiments/`, `viz/`, `analysis/`, `api/`, `tests/`, `notebooks/`
- [x] Create all `__init__.py` package markers
- [x] Create `runs/.gitkeep` and `results/figures/.gitkeep`

### 1.2 Configuration
- [x] Implement `simulation/config.py` — `SimConfig` dataclass
  - [x] All 16 fields with defaults matching `architecture.md §3.1`
  - [x] `to_dict()` / `from_dict()` — lossless JSON round-trip
  - [x] `to_json()` / `from_json()` / `save()` / `load()` helpers
  - [x] `run_id` property (`{topology}_{seed}`)
  - [x] `__post_init__` validation (topology, N, T, theta, sigma, gamma, n_runs)

### 1.3 Project Configuration Files
- [x] Create `requirements.txt` with pinned versions (GPU/CUDA 12.1 build)
- [x] Create `pyproject.toml` with project metadata and pytest config
- [x] Create `.gitignore` (tracks `runs/.gitkeep`, ignores `runs/*/` and generated outputs)

### 1.4 Tests
- [x] `tests/test_config.py` — 26 tests
  - [x] Default values match spec (10 tests)
  - [x] JSON / file round-trip (6 tests)
  - [x] Extra keys silently ignored (2 tests)
  - [x] Validation raises ValueError (8 tests)

### 1.5 Dependency Installation
- [x] Non-ML packages installable via `pip install -r requirements.txt`
- [/] PyTorch 2.4.1+cu121 — installing (large GPU wheel, ~2.5GB)
- [ ] torch-geometric==2.6.1 + sparse extensions
- [ ] Verify `torch.cuda.is_available()` returns `True`

### Plan 1 Exit Criteria
- [x] `from simulation.config import SimConfig` — imports cleanly
- [x] JSON round-trip assertion passes
- [x] All 6 `__init__.py` files exist
- [x] `pytest tests/test_config.py -v` — 26 passed, 0 failed
- [/] `pip install -r requirements.txt` — in progress

---

## Plan 2 — Simulation Engine

- [ ] `simulation/network.py` — `make_network(config)`
  - [ ] ER topology with connectivity guarantee (retry up to 5x)
  - [ ] WS small-world topology
  - [ ] BA scale-free topology
  - [ ] SBM 2-community topology
  - [ ] Degree centrality computed + normalised as node attribute
  - [ ] `community_id` assigned on all nodes
- [ ] `simulation/agent.py` — `AccentAgent`
  - [ ] 6-dim accent vector initialised (Gaussian per community prototype)
  - [ ] `update(speaker)` implementing `model.md §6` update rule
  - [ ] Bounded confidence check (suppress if dist ≥ θ)
  - [ ] Phonetic noise (N(0, σ²·I)) + clipping to [0,1]
- [ ] `simulation/metrics.py` — 7 pure metric functions
  - [ ] `shannon_diversity(accent_matrix, n_clusters=5)`
  - [ ] `mean_pairwise_distance(accent_matrix)`
  - [ ] `cross_community_distance(accent_matrix, community_ids)`
  - [ ] `influence_residual_scores(initial_accents, final_mean_accent)`
  - [ ] `adoption_fraction(accent_matrix, initial_mean_dim0, threshold=0.2)`
  - [ ] `spearman_centrality_influence(centrality, influence_scores)`
  - [ ] `logistic_fit(t, adoption)`
- [ ] `simulation/model.py` — `MosaicModel`
  - [ ] Edge list precomputed at init
  - [ ] `step()`: random edge sample → `agents[i].update(agents[j])`
  - [ ] k-means refit every 500 steps (cached between refits)
  - [ ] Convergence detection (std of last 200 H values < 0.001)
  - [ ] `run(logger)` loop returning metrics dict
- [ ] `simulation/logger.py` — `DataLogger`
  - [ ] Creates `runs/{run_id}/` directory
  - [ ] Writes `agent_states.csv` every `log_every` steps
  - [ ] Writes `config.json` at run start
  - [ ] Writes `metrics.json` at run end
- [ ] `simulation/runner.py` — `MonteCarloRunner`
  - [ ] `run_monte_carlo(config)` with seed-incremented loop
  - [ ] Writes `results/summary.csv`

### Plan 2 Exit Criteria
- [ ] `python -m simulation.runner` completes 25 runs without errors
- [ ] 25 `{topology}_{seed}/` directories in `runs/`, each with 3 files
- [ ] `results/summary.csv` exists with all required columns
- [ ] Single run N=200, T=10,000 < 60 seconds

---

## Plan 3 — Unit Test Suite

- [ ] `tests/test_network.py` — ≥ 6 tests
- [ ] `tests/test_agent.py` — ≥ 7 tests
- [ ] `tests/test_model.py` — ≥ 6 tests
- [ ] `tests/test_metrics.py` — ≥ 5 tests

### Plan 3 Exit Criteria
- [ ] `pytest tests/ -v` — all ≥ 28 tests pass, 0 failed

---

## Plan 4 — Experiments and Visualisations

- [ ] `viz/figures.py` — 11 figure functions
- [ ] `viz/gif.py` — `make_diffusion_gif()`
- [ ] `experiments/exp1_topology.py` — topology comparison
- [ ] `experiments/exp2_prestige.py` — prestige/centrality effect
- [ ] `experiments/exp3_contact.py` — SBM dialect contact
- [ ] `experiments/ablations.py` — 4 ablation studies
- [ ] `experiments/scurve.py` — S-curve logistic validation
- [ ] `experiments/heatmaps.py` — parameter heatmaps (parallelised)
- [ ] `experiments/run_all.py` — single entry point
- [ ] All 13 figures saved to `results/figures/` at 300 DPI
- [ ] `diffusion.gif` generated (< 5MB)

### Plan 4 Exit Criteria
- [ ] All 13 PNGs exist in `results/figures/`
- [ ] S-curve R² > 0.85
- [ ] All mvp.md AC2–AC9 pass

---

## Plan 5 — ML Analysis Layer

- [ ] `project-docs/ml-pipeline.md` — written from actual implementation
- [ ] `analysis/data_loader.py` — Phase 1→2 bridge
- [ ] `analysis/clustering.py` — k-means + DBSCAN
- [ ] `analysis/gcn.py` — `AccentGCN` + `AccentMLP` + training
- [ ] `analysis/evaluate.py` — evaluation metrics + reporting
- [ ] `analysis/umap_viz.py` — UMAP at 4 timesteps
- [ ] 3 ML figures generated

### Plan 5 Exit Criteria
- [ ] GCN vs MLP accuracy both reported
- [ ] UMAP 4-panel figure generated
- [ ] ml-pipeline.md written and committed

---

## Plan 6 — FastAPI Backend

- [ ] `api/schemas.py` — Pydantic models
- [ ] `api/main.py` — 4 endpoints (`POST /run`, `GET /results/{id}`, `GET /umap/{id}`, `GET /topologies`)
- [ ] CORS configured for localhost:5173
- [ ] `tests/test_api.py` — endpoint tests with httpx

### Plan 6 Exit Criteria
- [ ] `POST /run` returns valid JSON in < 60s
- [ ] All 4 endpoints return correct responses
- [ ] CORS headers verified

---

## Plan 7 — React Frontend

- [ ] Vite + React scaffold in `frontend/`
- [ ] `frontend/src/index.css` — all design tokens from design.md
- [ ] `frontend/src/App.jsx` — layout + state management
- [ ] `frontend/src/components/ControlPanel.jsx`
- [ ] `frontend/src/components/NetworkGraph.jsx` — D3.js
- [ ] `frontend/src/components/TimeSeries.jsx` — Recharts
- [ ] `frontend/src/components/UMAPScatter.jsx` — D3.js + slider

### Plan 7 Exit Criteria
- [ ] Full UI renders at localhost:5173 without console errors
- [ ] All 3 visualisations populate after Run
- [ ] Design matches design.md

---

## Plan 8 — Integration and Polish

- [ ] `notebooks/demo.ipynb` — executable end-to-end walkthrough
- [ ] `.github/workflows/tests.yml` — GitHub Actions CI
- [ ] Updated README.md with GIF embed
- [ ] All mvp.md AC1–AC10 verified

### Plan 8 Exit Criteria
- [ ] `pytest tests/ -v` — all green
- [ ] `nbconvert --execute demo.ipynb` passes
- [ ] README renders with embedded GIF on GitHub

---

## Ongoing

- [x] Update `progress.md` after each significant decision
- [x] Update `tasks.md` after each phase completion
- [ ] Commit and push after each completed plan

---

*Last updated: 2026-07-10 — Plan 1 (Foundation) complete*
