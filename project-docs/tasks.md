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

## Plan 1 — Foundation ✅ COMPLETE

### 1.1 Project Skeleton
- [x] Create all package directories: `simulation/`, `experiments/`, `viz/`, `analysis/`, `api/`, `tests/`, `notebooks/`
- [x] Create all `__init__.py` package markers
- [x] Create `runs/.gitkeep` and `results/figures/.gitkeep`

### 1.2 Configuration
- [x] Implement `simulation/config.py` — `SimConfig` dataclass (16 fields, validation, serialisation)
- [x] `to_dict()` / `from_dict()` / `to_json()` / `from_json()` / `save()` / `load()`
- [x] `run_id` property (`{topology}_{seed}`)
- [x] `__post_init__` validation (topology, N, T, theta, sigma, gamma, n_runs)

### 1.3 Project Config Files
- [x] `requirements.txt` — GPU (CUDA 12.1) pinned versions
- [x] `pyproject.toml` — project metadata + pytest config
- [x] `.gitignore`

### 1.4 Tests
- [x] `tests/test_config.py` — 26 tests (defaults, serialisation, forward-compat, validation)

### Plan 1 Exit Criteria
- [x] `from simulation.config import SimConfig` — imports cleanly
- [x] JSON round-trip assertion passes
- [x] All 6 `__init__.py` files exist
- [x] `pytest tests/test_config.py -v` — 26 passed, 0 failed
- [x] All packages importable (torch 2.4.1+cu121, torch-geometric 2.6.1, CUDA=True)

---

## Plan 2 — Simulation Engine ✅ COMPLETE

### 2.1 `simulation/metrics.py`
- [x] `shannon_diversity(accent_matrix, n_clusters=5)` — k-means + H entropy
- [x] `shannon_diversity_from_labels(labels)` — fast path for cached labels
- [x] `mean_pairwise_distance(accent_matrix)` — scipy pdist
- [x] `cross_community_distance(accent_matrix, community_ids)`
- [x] `influence_residual_scores(initial_accents, final_mean_accent)`
- [x] `adoption_fraction(accent_matrix, initial_dim0, threshold=0.2)`
- [x] `spearman_centrality_influence(centrality, influence_scores)`
- [x] `logistic_fit(t, adoption)` → (R², params)

### 2.2 `simulation/network.py`
- [x] `make_network(config)` dispatch to 4 topologies
- [x] ER — connectivity check with up to 5 retries (seed+1000)
- [x] WS — always connected, no retry needed
- [x] BA — always connected
- [x] SBM — sizes=[N//2, N-N//2], probs from p_in/p_out
- [x] Normalised degree centrality stored as node attribute
- [x] `community_id` assigned (SBM: 0/1 by block; others: 0)
- [x] Largest-component fallback with warning if all retries fail
- [x] `COMMUNITY_PROTOTYPES` dict exported for MosaicModel

### 2.3 `simulation/agent.py`
- [x] `AccentAgent(mesa.Agent)` with `unique_id, model, accent_vector, community_id, centrality`
- [x] `update(speaker)` — bounded confidence check, α_ij scaling, noise via model.rng, clip [0,1]
- [x] `initial_accent` snapshot at t=0 for influence residual scores (Experiment 2)

### 2.4 `simulation/model.py`
- [x] `MosaicModel(mesa.Model)` — edge list precomputed, `self.rng = np.random.default_rng(seed)`
- [x] `_init_accent(community_id)` — SBM: community prototypes; others: single Gaussian
- [x] `step()` — random edge sample, asymmetric update (i accommodates to j)
- [x] `_compute_h()` — k-means with 500-step refit cache
- [x] Convergence: `std(h_history[-200:]) < 0.001` with min 10 entries
- [x] `run(log)` → full metrics dict + timeline list

### 2.5 `simulation/logger.py`
- [x] Creates `runs/{run_id}/` directory, writes `config.json` at init
- [x] `log(t, agents)` — buffers agent snapshot rows in memory
- [x] `close(metrics, timeline)` — flushes CSV, writes `metrics.json` + `timeline.json`
- [x] CSV columns: `timestep, agent_id, community_id, centrality, d0..d5`

### 2.6 `simulation/runner.py`
- [x] `run_single(config)` — builds network, model, logger; runs; returns metrics
- [x] `run_monte_carlo(config)` — sequential loop, seed+i per replicate, writes `results/summary.csv`
- [x] `__main__` entry point with progress logging and summary statistics

### Plan 2 Exit Criteria
- [x] `python -m simulation.runner` — 25 runs complete without errors (**11.7s total, 0.5s/run**)
- [x] 25 `{topology}_{seed}/` directories in `runs/`, each with 4 files
- [x] `results/summary.csv` exists with all required columns
- [x] Single run N=200, T=10,000 in **0.5s** (<<60s requirement)
- [x] CSV schema: `timestep, agent_id, community_id, centrality, d0..d5` ✓
- [x] Reproducibility: same seed → bit-identical CSV ✓

---

## Plan 3 — Unit Test Suite ✅ COMPLETE

- [x] `tests/test_network.py` — 8 tests (parametrized topology connectivity, node count, centrality [0,1], community_id presence, SBM 2-community split, non-SBM single community, prototypes valid)
- [x] `tests/test_agent.py` — 7 tests (proportional movement, bounded-confidence suppression, gamma=0 no-move, sigma>0 stochastic, sigma=0 deterministic, clipping [0,1], seed reproducibility)
- [x] `tests/test_model.py` — 6 tests (required keys, timeline structure, run_id directory, hard cutoff, convergence detection, seed reproducibility)
- [x] `tests/test_metrics.py` — 7 tests (H=0 identical accents, D=0 identical accents, D_cross=0 converged, residual scores shape, logistic fit R², positive D diverse, labels consistent)

### Plan 3 Exit Criteria
- [x] `pytest tests/ -v` — **59 tests passed, 0 failed in 3.36s**

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

---

## Plan 5 — ML Analysis Layer

- [ ] `project-docs/ml-pipeline.md`
- [ ] `analysis/data_loader.py`
- [ ] `analysis/clustering.py`
- [ ] `analysis/gcn.py`
- [ ] `analysis/evaluate.py`
- [ ] `analysis/umap_viz.py`

---

## Plan 6 — FastAPI Backend

- [ ] `api/schemas.py`
- [ ] `api/main.py` — 4 endpoints
- [ ] `tests/test_api.py`

---

## Plan 7 — React Frontend

- [ ] Vite + React scaffold in `frontend/`
- [ ] All components per design.md

---

## Plan 8 — Integration and Polish

- [ ] `notebooks/demo.ipynb`
- [ ] `.github/workflows/tests.yml`
- [ ] Updated README.md

---

## Ongoing

- [x] Update `progress.md` after each phase completion
- [x] Update `tasks.md` after each phase completion
- [ ] Commit and push after each completed plan

---

*Last updated: 2026-07-10 — Plan 3 (Unit Test Suite) complete*
