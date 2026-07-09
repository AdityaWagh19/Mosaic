# Mosaic — Task Tracker

Living task list for all three phases. Update status markers as work progresses.

Status: `[ ]` not started · `[/]` in progress · `[x]` done

---

## Phase 0 — Documentation (Current)

- [x] Create project-docs/ folder with 9 empty files
- [x] Write progress.md
- [x] Write context.md
- [x] Write model.md
- [x] Write architecture.md
- [x] Write prd.md
- [x] Write mvp.md
- [x] Write tasks.md
- [ ] Write experiments.md
- [ ] Write ml-pipeline.md (Phase 2 start)

---

## Phase 1 — Simulation Core

### 1.1 Project Setup
- [ ] Create `mosaic/` source directory and subdirectories per architecture.md §2
- [ ] Create `requirements.txt` with pinned versions
- [ ] Set up virtual environment (venv or conda)
- [ ] Verify all imports work: mesa, networkx, numpy, pandas, matplotlib, seaborn, scipy, pytest

### 1.2 `config.py` — SimConfig
- [ ] Implement SimConfig dataclass with all fields from architecture.md §3.1
- [ ] Add `to_dict()` method for JSON serialisation
- [ ] Add `from_dict()` classmethod for deserialisation
- [ ] Write unit tests: default values correct; serialise/deserialise round-trip

### 1.3 `network.py` — NetworkGenerator
- [ ] Implement `make_network(config)` dispatch function
- [ ] Implement ER topology (`nx.erdos_renyi_graph`)
- [ ] Implement WS topology (`nx.watts_strogatz_graph`)
- [ ] Implement BA topology (`nx.barabasi_albert_graph`)
- [ ] Implement SBM topology (`nx.stochastic_block_model`) with 2 communities
- [ ] Compute and normalise degree centrality; store as node attribute
- [ ] Assign `community_id` node attribute (0 for all in non-SBM topologies)
- [ ] Add connectivity guarantee for ER (re-sample if not connected)
- [ ] Write unit tests: all topologies return connected graphs; node attributes set;
      SBM community sizes correct

### 1.4 `agent.py` — AccentAgent
- [ ] Implement AccentAgent extending mesa.Agent
- [ ] Implement 6-dim accent vector initialisation (Gaussian per community prototype)
- [ ] Implement `update(speaker)` with prestige-weighted asymmetric rule (model.md §6)
- [ ] Implement bounded confidence check (suppress update if distance ≥ θ)
- [ ] Implement noise term (N(0, σ²·I)) and post-update clipping to [0,1]
- [ ] Write unit tests:
      - accent moves toward speaker by correct α_ij amount
      - update suppressed when ‖a_j − a_i‖ ≥ θ
      - γ=0 produces uniform (centrality-independent) update
      - result always in [0,1] after clipping

### 1.5 `model.py` — MosaicModel
- [ ] Implement MosaicModel extending mesa.Model
- [ ] Implement agent instantiation with per-community accent initialisation
- [ ] Implement edge list precomputation at init
- [ ] Implement `step()`: random edge sample → `agents_map[i].update(agents_map[j])`
- [ ] Implement Shannon diversity metric (H(t)) — k-means refit every 500 steps
- [ ] Implement convergence detection (δ=0.001 for 200 consecutive steps)
- [ ] Implement `run(logger)` loop returning metrics dict
- [ ] Write unit tests:
      - θ=∞, γ=0, σ=0, complete graph → all agents converge to same accent
      - convergence detection fires at correct step
      - hard cutoff at T returns `converged=False`

### 1.6 `logger.py` — DataLogger
- [ ] Implement run directory creation (`runs/{run_id}/`)
- [ ] Implement agent state CSV write (every `log_every` steps)
- [ ] Implement `config.json` write at run start
- [ ] Implement `metrics.json` write at run end
- [ ] Verify round-trip: metrics saved == metrics returned by `model.run()`

### 1.7 `runner.py` — MonteCarloRunner
- [ ] Implement `run_monte_carlo(config)` loop over n_runs with seed variation
- [ ] Aggregate results into `results/summary.csv`
- [ ] Compute mean ± SD for convergence_time and final_diversity
- [ ] Test: 3 runs of same config with different seeds produce different convergence times

### 1.8 Unit Test Suite
- [ ] `tests/test_agent.py` — ≥ 6 tests
- [ ] `tests/test_model.py` — ≥ 6 tests
- [ ] `tests/test_network.py` — ≥ 5 tests
- [ ] `tests/test_metrics.py` — ≥ 4 tests
- [ ] All tests pass: `pytest tests/ -v`

### 1.9 Experiments
- [ ] **Experiment 1:** Topology comparison
      - Run 25 × 4 topologies at θ=0.3, γ=1.0
      - Produce diversity time series + convergence boxplot
- [ ] **Experiment 2:** Prestige sweep
      - Run 25 × 4 γ values (0, 0.5, 1.0, 2.0) on BA network
      - Compute Spearman correlation: centrality vs time-of-adoption
      - Produce correlation plot with error bars
- [ ] **Experiment 3:** Two-community contact (SBM)
      - Run 25 × 4 p_out values (0.005, 0.01, 0.02, 0.05)
      - Produce 4-snapshot network grid + cross-community distance decay curve
- [ ] **Ablation 1:** No homophily (θ = ∞)
- [ ] **Ablation 2:** No prestige (γ = 0)
- [ ] **Ablation 3:** No noise (σ = 0)
- [ ] **Ablation 4:** Symmetric interaction (both i and j update)
- [ ] **S-curve validation:** seed innovation in 5% of agents; fit logistic curve; verify R² > 0.85
- [ ] **Parameter heatmaps:** (topology × θ) and (topology × γ) — 2 heatmaps

### 1.10 Visualisations
- [ ] Diversity time series plot (with ± SD band)
- [ ] Convergence time boxplots (one box per topology)
- [ ] Network snapshot coloured by accent cluster (spring layout, matplotlib)
- [ ] **Animated diffusion GIF** (matplotlib FuncAnimation, export with Pillow)
- [ ] Heatmap: convergence time over topology × θ
- [ ] Heatmap: final diversity over topology × γ
- [ ] Cross-community distance decay curve
- [ ] S-curve adoption plot with logistic fit
- [ ] All figures saved to `results/figures/` at 300 DPI

### 1.11 Polish
- [ ] `notebooks/demo.ipynb` — runnable end-to-end walkthrough
- [ ] `README.md` — description, setup, GIF embed, key figures, research questions
- [ ] `requirements.txt` — pinned versions
- [ ] Verify all acceptance criteria in `mvp.md §4`

---

## Phase 2 — ML Analysis Layer

*(Begin after all Phase 1 acceptance criteria are met)*

### 2.1 Clustering
- [ ] Implement `analysis/clustering.py`
- [ ] k-means for k ∈ {2,3,4,5} — select best k by silhouette score
- [ ] DBSCAN with ε tuned to data range
- [ ] Compute: silhouette, Davies-Bouldin, ARI vs community_id (SBM runs)
- [ ] Produce: cluster count vs topology figure

### 2.2 GCN Predictor
- [ ] Generate 100 simulation runs (varied configs) → save PyG Data objects
- [ ] Implement `analysis/gcn.py` — AccentGCN (2-layer GCNConv)
- [ ] Implement MLP baseline (identical structure, no edge_index)
- [ ] Train on 80 runs, evaluate on 20 held-out runs
- [ ] Report: accuracy, macro F1, confusion matrix for GCN vs MLP
- [ ] Produce: loss curve plot, confusion matrix heatmap
- [ ] Optional: upgrade GCNConv → GATConv; visualise attention weights

### 2.3 UMAP Visualisation
- [ ] Implement `analysis/umap_viz.py`
- [ ] Compute UMAP coords at timesteps {0, T//3, 2T//3, t_conv}
- [ ] Save to `runs/{run_id}/umap_coords.json`
- [ ] Produce: 4-panel UMAP scatter figure (coloured by community + by cluster)

### 2.4 Write ml-pipeline.md
- [ ] Document GCN architecture, training protocol, and evaluation in `project-docs/ml-pipeline.md`

---

## Phase 3 — Web Interface

*(Begin after Phase 2 complete)*

### 3.1 FastAPI Backend
- [ ] Set up `api/` package
- [ ] Implement `POST /run` endpoint
- [ ] Implement `GET /results/{run_id}` endpoint
- [ ] Implement `GET /umap/{run_id}` endpoint
- [ ] Configure CORS for localhost:5173
- [ ] Test all endpoints with curl / Postman

### 3.2 React Frontend
- [ ] Scaffold with `npm create vite@latest frontend -- --template react`
- [ ] Install D3.js, Recharts
- [ ] Implement `ControlPanel` component (parameter inputs)
- [ ] Implement `NetworkGraph` component (D3.js force-directed)
- [ ] Implement `TimeSeries` component (Recharts)
- [ ] Implement `UMAPScatter` component with timestep slider
- [ ] Wire API calls in `App.jsx`
- [ ] Handle loading and error states
- [ ] Style and polish UI/UX

### 3.3 Integration
- [ ] End-to-end test: adjust params → run → see results update in all components
- [ ] Update README with frontend setup instructions and demo screenshot

---

## Ongoing

- [ ] Update `progress.md` after each significant decision or experiment result
- [ ] Commit and push after each completed task group

---

*Last updated: 2026-07-09*
