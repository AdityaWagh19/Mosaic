# Mosaic — Product Requirements Document

Defines what the system must do, phase by phase. All functional requirements
are traceable to `context.md` (research questions) and constrained by the
design decisions in `model.md` and `architecture.md`.

---

## 1. Research Goals (North Star)

Every feature in every phase must serve at least one of these:

- **RQ1:** Understand how network topology shapes accent convergence
- **RQ2:** Understand how agent prestige (centrality) shapes influence speed
- **RQ3:** Determine whether graph structure (GCN) predicts accent outcome better than features alone (MLP)

---

## 2. Phase 1 — Simulation Core

**Goal:** A working, reproducible ABM that runs experiments and produces
publication-quality figures answering RQ1 and RQ2.

### Functional Requirements

| ID | Requirement |
|---|---|
| F1.1 | System shall simulate N agents (default 200) on a social network for T timesteps (default 10,000) |
| F1.2 | Each agent shall hold a 6-dimensional phonetically-named accent vector, initialised per `model.md §3` |
| F1.3 | Each timestep shall select one random edge and apply the asymmetric prestige-weighted update rule from `model.md §6` |
| F1.4 | System shall support four network topologies: ER, WS, BA, SBM (`model.md §4`) |
| F1.5 | System shall detect convergence using the entropy criterion from `model.md §7` |
| F1.6 | System shall log agent states every 100 steps to CSV and save `config.json` and `metrics.json` per run |
| F1.7 | System shall run N Monte Carlo replicates (default 25) with varying seeds and produce a summary CSV |
| F1.8 | System shall produce: diversity time series plot, convergence boxplot, network snapshot coloured by accent cluster, parameter heatmaps, animated diffusion GIF |
| F1.9 | System shall have ≥ 20 pytest unit tests covering update rule, convergence, network generation, and metrics |
| F1.10 | All runs shall be fully reproducible given the same seed |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NF1.1 | Single run of N=200, T=10,000 must complete in < 60 seconds on a standard laptop CPU |
| NF1.2 | Code must be modular: simulation, analysis, API, and frontend are independent packages |
| NF1.3 | All parameters must flow through `SimConfig` — no magic numbers in simulation code |
| NF1.4 | Each run directory must be self-contained (config + data + metrics) — reproducible without re-running |

---

## 3. Phase 2 — ML Analysis Layer

**Goal:** Train and evaluate a GCN on simulation outputs. Generate UMAP
visualisations. Answer RQ3 with a clear quantitative comparison.

### Functional Requirements

| ID | Requirement |
|---|---|
| F2.1 | System shall cluster final agent accent vectors using k-means (k=2..5, best k by silhouette) and DBSCAN |
| F2.2 | System shall compute silhouette score, Davies-Bouldin index, and ARI vs community_id for each clustering |
| F2.3 | System shall train a 2-layer GCN (PyTorch Geometric) on 80 simulation runs and evaluate on 20 held-out runs |
| F2.4 | System shall train an MLP baseline (same architecture, no edge_index) for comparison against GCN |
| F2.5 | System shall report GCN vs MLP: accuracy, macro F1, confusion matrix |
| F2.6 | System shall compute UMAP 2D coordinates at timesteps {0, T//3, 2T//3, t_conv} and save as JSON |
| F2.7 | System shall produce a UMAP scatter figure (4 panels) showing accent space evolution |

---

## 4. Phase 3 — Web Interface

**Goal:** A deployable local web application that allows interactive exploration
of the simulation — adjusting parameters, running simulations, and visualising
results through a custom React UI.

### Functional Requirements

| ID | Requirement |
|---|---|
| F3.1 | FastAPI backend shall expose POST /run, GET /results/{id}, GET /umap/{id} per `architecture.md §5` |
| F3.2 | POST /run shall accept SimConfig-compatible JSON and return a full result payload (see `architecture.md §5.2`) |
| F3.3 | React frontend shall render a ControlPanel with inputs for all key SimConfig parameters |
| F3.4 | Frontend shall render a D3.js force-directed network graph with nodes sized by centrality and coloured by accent cluster |
| F3.5 | Frontend shall render a Recharts time series of diversity and pairwise distance over simulation time |
| F3.6 | Frontend shall render a UMAP scatter plot with a timestep slider |
| F3.7 | Frontend shall handle loading state (spinner/disabled controls while simulation runs) |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NF3.1 | API and frontend must run independently (separate processes, CORS configured) |
| NF3.2 | Frontend must not embed simulation logic — it is purely a visualisation and control layer |
| NF3.3 | No authentication, no database, no cloud deployment required |

---

## 5. Out of Scope (All Phases)

The following are explicitly not requirements and should not be built:

- Real-time speech or audio input/output
- LLM or GPT-based agent decision making
- Multi-user sessions or authentication
- Persistent database (SQLite, Postgres, etc.)
- Deployment to a public cloud server
- Inter-generational transmission dynamics
- Dynamic network rewiring during simulation
- Formal publication submission or manuscript writing

---

## 6. MVP Definition

The **Minimum Viable Product** is Phase 1 complete. Specifically:

- All F1.1 – F1.10 requirements met
- Animated GIF of accent diffusion embedded in README
- Parameter heatmap showing at least one interpretable trend
- All unit tests passing on `pytest tests/ -v`
- `demo.ipynb` notebook runnable end-to-end

Phase 2 and Phase 3 are enhancements that build on the MVP. The project is
demonstrably useful and complete at MVP level.

---

*Last updated: 2026-07-09*
