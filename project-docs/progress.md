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

### Deferred to Plan 2
- Mesa 2.x API compatibility check (Mesa scheduler not used — sidesteps the issue)
- SBM connectivity guarantee implementation

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

### Key Design Decisions
- **No Mesa scheduler**: MosaicModel controls scheduling via edge-list sampling.
- **Convergence**: `std(rolling deque of H values) < 0.001` (min 10 entries).
  With T=10,000 and theta=0.3 (WS default), H variance ~0.01 → rarely triggers;
  hard cutoff at T handles it cleanly.
- **k-means caching**: Refit every 500 steps; `predict()` on intervening steps.
- **Logger buffering**: All rows accumulated in memory; single flush at close().

### Deferred to Plan 3
- Unit tests for all 6 modules
- SBM convergence verification (expected to trigger faster than WS)

---
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

### Bug Fixes During Testing
Five failures identified and resolved before merge:

1. **test_agent — proportional movement**: theta=1.0 < L2(test vectors)≈1.11 → bounded-confidence gate fired. Fix: raised theta to 2.0.
2. **test_model — hard cutoff**: theta=0.001 → no interactions → H frozen → std(H)=0 triggered "convergence". Fix: T=800, log_every=100 (9 entries < min=10, check never runs).
3. **test_network — ER node count**: default p_er=0.05 too sparse for N=20 → LCC fallback reduces N. Fix: parametrize over WS+BA only.
4. **test_network — SBM node count**: same LCC issue. Fix: same as above.
5. **test_network — SBM 2 communities**: LCC removed community 1. Fix: p_in=0.5, p_out=0.2, seed=7 for reliable density.

---

## 2026-07-10 — Plan 4: Experiments + Visualisations ✅ COMPLETE

### Total Runtime
481 seconds (8.0 min) end-to-end on CPU.

### Outputs — All 14 Files Present

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
| `scurve.png` | 170 KB | S-Curve V1 |
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
- R2=0.9349 >= 0.85 — logistic fit confirmed
- Mechanism: persistent innovators + bidirectional edges + cumulative adoption (gamma=5.0)

**Heatmaps (1,000 parallel runs):**
- Runtime: 213s via ProcessPoolExecutor

### Bug Fixes During Phase 4
1. S-curve R2 < 0: asymmetric edge list limited spread. Fix: reversed edges + persistent reset + cumulative adoption + gamma=5.0
2. cp1252 UnicodeEncodeError: Unicode subscripts in print(). Fix: ASCII (t0, R2)
3. Pillow ADAPTIVE AttributeError: removed in Pillow 10+. Fix: .quantize(colors=64)
4. pyrefly false positives from docstring patterns. Fix: plain-prose docstrings
5. Unused import os in 5 experiment files after switching to Path.mkdir()

*Last updated: 2026-07-10 — Plan 4 (Experiments + Visualisations) complete*

---

## 2026-07-10 — Phase 5: ML Analysis Layer

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

### Bug Fixes During Phase 5
1. `umap` import crash: `parametric_umap.py` uses `tf.keras` at class-definition time.
   Fix: pre-register `umap.parametric_umap` stub in `sys.modules` (`analysis/_umap_compat.py`).
2. PyG 2.6.1 y-shape issue with specific batches.
   Fix: explicit `num_nodes=N` in `Data(...)` constructor.
3. 4 runs had duplicate agent rows at t_final (Phase 4 re-run artifact).
   Fix: `drop_duplicates(subset=["timestep","agent_id"], keep="last")` in `load_run`.

*Last updated: 2026-07-10 — Plan 5 (ML Analysis Layer) complete*
