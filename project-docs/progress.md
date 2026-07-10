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
