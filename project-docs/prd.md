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

## 2. Phase 1 — Simulation Core ✅ COMPLETE

**Goal:** A working, reproducible ABM that runs experiments and produces
publication-quality figures answering RQ1 and RQ2.

### Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| F1.1 | System shall simulate N agents (default 200) on a social network for T timesteps (default 10,000) | ✅ |
| F1.2 | Each agent shall hold a 6-dimensional phonetically-named accent vector, initialised per `model.md §3` | ✅ |
| F1.3 | Each timestep shall select one random edge and apply the asymmetric prestige-weighted update rule | ✅ |
| F1.4 | System shall support four network topologies: ER, WS, BA, SBM | ✅ |
| F1.5 | System shall detect convergence using the entropy criterion | ✅ |
| F1.6 | System shall log agent states every 100 steps to CSV and save `config.json` and `metrics.json` per run | ✅ |
| F1.7 | System shall run N Monte Carlo replicates (default 25) with varying seeds and produce a summary CSV | ✅ |
| F1.8 | System shall produce: diversity time series, convergence boxplot, network snapshot, parameter heatmaps, animated GIF | ✅ |
| F1.9 | System shall have ≥ 20 pytest unit tests covering update rule, convergence, network generation, and metrics | ✅ (59 tests) |
| F1.10 | All runs shall be fully reproducible given the same seed | ✅ |

### Non-Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| NF1.1 | Single run N=200, T=10,000 must complete in < 60 seconds | ✅ (0.5s/run) |
| NF1.2 | Code must be modular: simulation, analysis, API, frontend are independent packages | ✅ |
| NF1.3 | All parameters must flow through `SimConfig` | ✅ |
| NF1.4 | Each run directory must be self-contained | ✅ |

---

## 3. Phase 2 — ML Analysis Layer ✅ COMPLETE

**Goal:** Train and evaluate a GCN on simulation outputs. Generate UMAP
visualisations. Answer RQ3 with a clear quantitative comparison.

### Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| F2.1 | System shall cluster final agent accent vectors using k-means (k=2..5) and DBSCAN | ✅ |
| F2.2 | System shall compute silhouette score, Davies-Bouldin index, and ARI | ✅ |
| F2.3 | System shall train a 2-layer GCN on 80 simulation runs and evaluate on 20 held-out runs | ✅ |
| F2.4 | System shall train an MLP baseline for comparison | ✅ |
| F2.5 | System shall report GCN vs MLP: accuracy, macro F1 | ✅ (MLP 89.2%, GCN 51.1%) |
| F2.6 | System shall compute UMAP 2D coordinates at 4 timesteps and save as JSON | ✅ |
| F2.7 | System shall produce a UMAP scatter figure (4 panels) | ✅ |

---

## 4. Phase 3 — Web Interface ✅ COMPLETE

**Goal:** A deployable local web application that allows interactive exploration
of the simulation — adjusting parameters, running simulations, and visualising
results through a custom React UI.

### Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| F3.1 | FastAPI backend shall expose all endpoints per `architecture.md §5` | ✅ (10 endpoints) |
| F3.2 | POST /run shall accept SimConfig-compatible JSON and return a full result payload | ✅ |
| F3.3 | React frontend shall render a ControlPanel with inputs for all key SimConfig parameters | ✅ |
| F3.4 | Frontend shall render a D3.js force-directed network graph with nodes sized by centrality and coloured by accent cluster | ✅ |
| F3.5 | Frontend shall render a Recharts time series of diversity and pairwise distance | ✅ |
| F3.6 | Frontend shall render a UMAP scatter plot with a timestep slider | ✅ |
| F3.7 | Frontend shall handle loading state (spinner while simulation runs) | ✅ |
| F3.8 | Frontend shall include a Landing Page, Experiments archive, Comparison view, and ML Analysis page | ✅ |
| F3.9 | Mobile configuration (≤800px) shall use a modal/sheet rather than a sidebar | ✅ |
| F3.10 | Experiments page shall show per-figure findings, "how to read" guidance, and download controls | ✅ |
| F3.11 | ML Analysis page shall show benchmark table (MLP vs GCN) and clustering diagnostics | ✅ |

### Non-Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| NF3.1 | API and frontend must run independently (CORS configured) | ✅ |
| NF3.2 | Frontend must not embed simulation logic | ✅ |
| NF3.3 | No authentication, no database, no cloud deployment required | ✅ |

---

## 5. Phase 4 — Integration + Polish (Phase 8)

**Goal:** Production-ready quality — CI, demo notebook, error resilience, and final README.

### Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| F4.1 | `notebooks/demo.ipynb` shall walk through one complete simulation run | [ ] |
| F4.2 | `.github/workflows/tests.yml` shall run `pytest tests/ -v` and `npm run build` on every push | [ ] |
| F4.3 | Frontend error boundaries shall catch and display API failures gracefully | [ ] |
| F4.4 | All data-fetching components shall show loading skeleton states | [ ] |
| F4.5 | Keyboard navigation and ARIA labels shall pass a basic accessibility audit | [ ] |
| F4.6 | README shall include animated GIF, screenshots, and quick-start instructions | [ ] |

---

## 6. Out of Scope (All Phases)

The following are explicitly not requirements and will not be built:

- Real-time speech or audio input/output
- LLM or GPT-based agent decision making
- Multi-user sessions or authentication
- Persistent database (SQLite, Postgres, etc.)
- Deployment to a public cloud server
- Inter-generational transmission dynamics
- Dynamic network rewiring during simulation
- Formal publication submission or manuscript writing

---

## 7. MVP Definition

The **Minimum Viable Product** — Phase 1 + Phase 2 complete. Specifically:

- All F1.1–F1.10 met ✅
- All F2.1–F2.7 met ✅
- Animated GIF of accent diffusion ✅
- Parameter heatmaps showing interpretable trends ✅
- All unit tests passing on `pytest tests/ -v` ✅

Phase 3 (web interface) and Phase 4 (integration polish) are enhancements
that build on the MVP. The project is demonstrably complete at MVP level.

---

*Last updated: 2026-07-11 — Phase 7 complete. Phase 8 (Integration + Polish) in progress.*
