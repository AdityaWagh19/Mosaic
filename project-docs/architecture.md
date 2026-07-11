# Mosaic — System Architecture

This document defines all modules, their responsibilities, interfaces, and the
data flow between them. It reflects the implemented state as of Phase 7.

---

## 1. System Overview

Mosaic has four separable layers that can be developed and tested independently:

```
┌─────────────────────────────────────────────────────────┐
│  SIMULATION LAYER  (Python)                             │
│  SimConfig → NetworkGenerator → MosaicModel → DataLogger│
│                      ↑                                  │
│                 AccentAgent  MonteCarloRunner            │
│                 metrics.py                               │
└──────────────────────────┬──────────────────────────────┘
                           │  file I/O (runs/, results/)
┌──────────────────────────▼──────────────────────────────┐
│  ANALYSIS LAYER  (Python)                               │
│  data_loader → clustering → gcn/mlp → umap_viz          │
└──────────────────────────┬──────────────────────────────┘
                           │  JSON over REST
┌──────────────────────────▼──────────────────────────────┐
│  API LAYER  (FastAPI, port 8000)                        │
│  POST /run  ·  GET /results/{id}  ·  GET /umap/{id}     │
│  GET /runs  ·  GET /experiments   ·  GET /figures/{f}   │
│  GET /config/schema  ·  GET /analysis/summary           │
│  GET /runs/{id}/export  ·  GET /runs/{id}/snapshots     │
└──────────────────────────┬──────────────────────────────┘
                           │  HTTP (CORS: localhost:5173)
┌──────────────────────────▼──────────────────────────────┐
│  FRONTEND LAYER  (React + Vite, port 5173)              │
│  LandingPage → /simulate (Dashboard)                    │
│             → /experiments (ExperimentsPage)            │
│             → /compare    (ComparePage)                 │
│             → /analysis   (AnalysisPage)                │
│             → /guide      (Guide)                       │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Project Directory Structure

```
Mosaic/
├── simulation/
│   ├── __init__.py
│   ├── config.py          # SimConfig dataclass — single source of truth
│   ├── network.py         # make_network() — 4 topologies
│   ├── agent.py           # AccentAgent — phonetic state + update rule
│   ├── model.py           # MosaicModel — edge-based scheduling + convergence
│   ├── logger.py          # DataLogger — CSV + JSON output per run
│   ├── metrics.py         # Pure metric functions (H, D, cross-distance, etc.)
│   └── runner.py          # run_single() + run_monte_carlo()
│
├── analysis/
│   ├── _umap_compat.py    # UMAP/TensorFlow import shim
│   ├── data_loader.py     # CSV loading, graph reconstruction, PyG dataset builder
│   ├── clustering.py      # k-means + DBSCAN dialect zone discovery
│   ├── gcn.py             # AccentGCN + AccentMLP model definitions + helpers
│   ├── evaluate.py        # Training orchestration pipeline (100 epochs)
│   ├── umap_viz.py        # 4-panel UMAP accent-trajectory figure
│   └── validation.py      # Phase 5.5 validation suite
│
├── experiments/
│   ├── __init__.py
│   ├── exp1_topology.py   # Topology comparison (100 runs × 4 topologies)
│   ├── exp2_prestige.py   # Prestige/centrality effect (100 BA runs × 4 gamma)
│   ├── exp3_contact.py    # Dialect contact (SBM, 4 p_out values)
│   ├── ablations.py       # 5 ablation conditions × 25 runs each
│   ├── scurve.py          # Logistic adoption S-curve validation
│   ├── heatmaps.py        # Parameter heatmaps (1,000 parallelised runs)
│   └── run_all.py         # Single entry point for all experiments
│
├── viz/
│   ├── __init__.py
│   ├── figures.py         # 11 matplotlib/seaborn figure functions (300 DPI)
│   └── gif.py             # make_diffusion_gif() — 60 frames @ 20 fps
│
├── api/
│   ├── main.py            # FastAPI application — 10 endpoints
│   └── schemas.py         # Pydantic v2 request/response models
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                        # BrowserRouter + route definitions
│   │   ├── index.css                      # All CSS (tokens + layout + components)
│   │   ├── api/
│   │   │   └── client.ts                  # Typed fetch wrappers for all endpoints
│   │   ├── contexts/
│   │   │   └── SimulationContext.tsx      # Global state: config, result, umap, loading
│   │   ├── hooks/
│   │   │   ├── useD3Network.ts            # D3 force simulation hook
│   │   │   ├── useD3Scatter.ts            # D3 scatter plot hook
│   │   │   └── useResizeObserver.ts       # ResizeObserver hook
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx            # / — hero + feature + use-case grid
│   │   │   ├── Dashboard.tsx              # /simulate + /runs/:runId — studio
│   │   │   ├── ExperimentsPage.tsx        # /experiments — research archive
│   │   │   ├── ComparePage.tsx            # /compare — side-by-side runs
│   │   │   └── AnalysisPage.tsx           # /analysis — ML benchmark report
│   │   ├── components/
│   │   │   ├── simulation/
│   │   │   │   ├── ControlPanel.tsx       # Sidebar form + mobile <dialog>
│   │   │   │   └── ConfigForm.tsx         # Shared form body
│   │   │   └── visualizations/
│   │   │       ├── NetworkGraph.tsx       # D3.js force-directed graph
│   │   │       ├── TimeSeriesChart.tsx    # Recharts diversity + distance
│   │   │       ├── UmapScatter.tsx        # D3 scatter + timestep slider
│   │   │       └── SnapshotPlayback.tsx   # Agent-state scrubber
│   │   ├── styles/
│   │   │   ├── tokens.css                 # CSS custom properties
│   │   │   └── accessibility.css          # Focus rings, reduced-motion
│   │   └── types/
│   │       └── models.ts                  # TypeScript interfaces (mirrors schemas.py)
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.app.json
│
├── tests/
│   ├── test_config.py     # 26 tests — SimConfig defaults, serialisation, validation
│   ├── test_agent.py      # 7 tests — update rule, clipping, reproducibility
│   ├── test_model.py      # 6 tests — convergence, cutoff, run_id, reproducibility
│   ├── test_network.py    # 8 tests — topology connectivity, attributes, SBM
│   ├── test_metrics.py    # 7 tests — H, D, cross-D, logistic fit
│   └── test_api.py        # API integration tests
│
├── results/
│   ├── summary.csv        # Aggregated Monte Carlo outputs (gitignored)
│   ├── ml_results.json    # GCN vs MLP benchmark metrics
│   └── figures/           # 19 PNG/GIF files — all tracked in git
│
├── runs/                  # Auto-created; gitignored; one dir per run
│   └── .gitkeep
│
├── research/              # Background research reports (3 markdown files)
├── notebooks/             # Placeholder; demo.ipynb planned for Phase 8
├── project-docs/          # All design and specification documents
├── .github/               # GitHub Actions workflows (Phase 8)
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 3. Simulation Layer

### 3.1 `config.py` — SimConfig

Single source of truth for all simulation parameters. Every run begins with a `SimConfig`.

```python
@dataclass
class SimConfig:
    N: int = 200                      # Number of agents
    topology: str = "watts_strogatz"  # "er" | "watts_strogatz" | "ba" | "sbm"
    p_er: float = 0.05
    k_ws: int = 6
    p_rewire: float = 0.1
    m_ba: int = 3
    p_in: float = 0.15
    p_out: float = 0.02
    n_communities: int = 2
    T: int = 10000
    log_every: int = 100
    gamma: float = 1.0
    theta: float = 0.30
    sigma: float = 0.01
    seed: int = 42
    n_runs: int = 25
```

`run_id` property: `{topology}_{seed}_{n}` where `n` is an auto-incrementing counter
ensuring uniqueness across repeated runs of the same config.

### 3.2 `network.py` — make_network()

Returns a `nx.Graph` with `community_id` (int) and `centrality` (float in [0,1])
set on every node. Connectivity is guaranteed: ER/SBM retry up to 5 times, then
fall back to the largest connected component with a warning.

### 3.3 `agent.py` — AccentAgent

No `step()` method. The model schedules interactions by edge sampling.
`update(speaker)` applies the bounded-confidence prestige-weighted update:

```
if ‖a_speaker − a_self‖ < θ:
    a_self += γ · centrality(speaker) · (a_speaker − a_self) + N(0, σ²)
    a_self = clip(a_self, 0, 1)
```

### 3.4 `model.py` — MosaicModel

- Edge list pre-computed at init; `self.rng = np.random.default_rng(seed)` controls all randomness
- k-means cluster labels cached and refit every 500 steps (5-cluster default)
- Convergence: `std(h_history[-200:]) < 0.001` with minimum 10 measurements
- Hard cutoff: stops at T regardless

### 3.5 `logger.py` — DataLogger

Buffers all agent-state rows in memory. Single CSV flush at `close()`.
Output per run:
- `agent_states.csv` — `timestep, agent_id, community_id, centrality, d0..d5`
- `config.json` — serialised SimConfig
- `metrics.json` — `convergence_time, converged, final_diversity, final_pairwise_distance`
- `timeline.json` — array of `{timestep, diversity, pairwise_distance}` entries

### 3.6 `runner.py`

- `run_single(config)` — builds network + model + logger, runs, returns metrics dict
- `run_monte_carlo(config)` — sequential loop, seed+i per replicate, writes `results/summary.csv`

---

## 4. Analysis Layer

### 4.1 `clustering.py`
k-means (k=2..5, best k by silhouette) + DBSCAN. Outputs silhouette score and cluster map figure.

### 4.2 `gcn.py`
2-layer GCN (`AccentGCN`) and 2-layer MLP (`AccentMLP`) sharing identical hidden dimensions.
Node features: 6 accent dims + degree + clustering coefficient + community_id = 9 total.
Train/test split at **run level** (80 runs train, 20 test) to prevent data leakage.

**Results:** MLP 89.2% / GCN 51.1% — initial accent position, not graph structure,
predicts final cluster membership.

### 4.3 `umap_viz.py`
Fits UMAP on the final agent-state accent matrix, transforms 3 earlier timesteps into
the same 2D embedding space. Produces a 4-panel figure showing accent space collapse.

---

## 5. API Layer

### 5.1 Complete Endpoint Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/run` | — | Run simulation → `RunResponse` |
| `GET` | `/results/{run_id}` | — | Retrieve persisted run |
| `GET` | `/umap/{run_id}` | — | UMAP coords (computed on demand, cached) |
| `GET` | `/runs` | — | Paginated run list; `?topology=` filter; cursor pagination |
| `GET` | `/runs/{run_id}/export` | — | `?format=json` or `?format=csv` download |
| `GET` | `/runs/{run_id}/snapshots` | — | `?timesteps=0,100,200` agent-state data |
| `GET` | `/topologies` | — | Topology metadata for form |
| `GET` | `/config/schema` | — | Field labels, ranges, help text |
| `GET` | `/experiments` | — | Offline experiment archive |
| `GET` | `/figures/{filename}` | — | Serve figures (allowlisted filenames only) |
| `GET` | `/analysis/summary` | — | ML results JSON + figure availability |

### 5.2 POST /run Request & Response

**Request:**
```json
{ "N": 200, "topology": "watts_strogatz", "T": 5000, "gamma": 1.0, "theta": 0.3 }
```

**Response (`RunResponse`):**
```json
{
  "run_id": "watts_strogatz_42_3",
  "config": { "...all SimConfig fields..." },
  "metrics": {
    "convergence_time": 4320,
    "converged": true,
    "final_diversity": 0.38,
    "final_pairwise_distance": 0.14
  },
  "timeline": [
    { "timestep": 0, "diversity": 1.21, "pairwise_distance": 0.54 }
  ],
  "final_agent_states": [
    { "agent_id": 0, "accent": [0.71, 0.43, 0.55, 0.38, 0.29, 0.61],
      "community_id": 0, "centrality": 0.12, "cluster_id": 2 }
  ],
  "network": {
    "nodes": [{ "id": 0, "community_id": 0, "centrality": 0.12 }],
    "edges": [{ "source": 0, "target": 5 }]
  }
}
```

### 5.3 Implementation Notes

- Simulation runs synchronously (< 30s for N=200, T=10,000) — no async queue
- UMAP coordinates are computed on first request and cached to `runs/{id}/umap_coords.json`
- k-means (k=5) is run inline at result-construction time to assign `cluster_id` per agent
- Figure serving uses an explicit allowlist — no arbitrary filesystem paths exposed
- CORS: `http://localhost:5173`, `http://127.0.0.1:5173`

---

## 6. Frontend Layer

### 6.1 Routes

| Path | Component | Purpose |
|---|---|---|
| `/` | `LandingPage` | Hero, feature cards, use-case grid |
| `/simulate` | `Dashboard` | Simulation studio (config + results) |
| `/runs/:runId` | `Dashboard` | Deep-link to a specific persisted run |
| `/experiments` | `ExperimentsPage` | Curated research archive |
| `/compare` | `ComparePage` | Side-by-side run comparison |
| `/analysis` | `AnalysisPage` | ML benchmark report |
| `/guide` | `Guide` | Method explanation |
| `*` | `NotFound` | 404 fallback |

### 6.2 State Architecture

`SimulationProvider` (React context) owns all cross-page state:

| State | Type | Owner | Description |
|---|---|---|---|
| `config` | `RunRequest` | Provider | Current form values |
| `result` | `RunResponse \| null` | Provider | Last completed run |
| `umap` | `UmapResponse \| null` | Provider | UMAP data for last run |
| `isRunning` | `boolean` | Provider | Request in flight |
| `error` | `string \| null` | Provider | Last error message |

### 6.3 Component Map

```
App (BrowserRouter + SimulationProvider)
├── Nav (inline — links + CTA)
├── LandingPage
│   ├── Hero section
│   ├── Feature grid (3-col cards)
│   └── Use-case grid (3-col cards)
├── Dashboard
│   ├── ControlPanel
│   │   └── ConfigForm (shared with mobile dialog)
│   └── Results section (aria-live)
│       ├── Loading spinner
│       ├── Empty state
│       └── Result view (4 tabs)
│           ├── Overview tab → TimeSeriesChart
│           ├── Network tab → NetworkGraph (D3)
│           ├── Accent space tab → UmapScatter (D3)
│           └── Data tab → export links + SnapshotPlayback
├── ExperimentsPage
│   ├── Filter pills
│   └── Experiment sections
│       └── Figure cards (findings + how-to-read + download)
├── ComparePage
│   ├── Run picker A
│   ├── Run picker B
│   └── Side-by-side metric comparison
└── AnalysisPage
    ├── ML benchmark table (MLP vs GCN vs chance)
    ├── Clustering diagnostic cards
    └── Interpretation section
```

### 6.4 Design System

All styles live in `index.css` (utilities) and `styles/tokens.css` (variables).
No external CSS framework. Design follows `design.md`:
- Color: Signal Blue `#0077ff` (primary), Paper `#ffffff`, Ink `#000000`, Hairline `#e5e7eb`
- Font: Inter Variable, 12px base for controls, 16px body
- Radius: `--radius-full` (pill nav), `--radius-cards` (16px), `--radius-buttons` (8px)
- Shadow: `--shadow-subtle` on nav and primary buttons only

---

## 7. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| ABM | Mesa | ≥ 2.1 |
| Graph computation | NetworkX | ≥ 3.2 |
| Numerics | NumPy | ≥ 1.26 |
| Data handling | pandas | ≥ 2.1 |
| ML (GCN) | PyTorch + PyTorch Geometric | 2.4.1 / 2.6.1 |
| Dimensionality reduction | umap-learn | ≥ 0.5 |
| Scientific visualisation | matplotlib, seaborn | ≥ 3.8 / ≥ 0.13 |
| API backend | FastAPI + uvicorn | ≥ 0.104 |
| Frontend framework | React + Vite | 18 / 6 |
| Frontend language | TypeScript | 5 |
| Routing | react-router-dom | 7 |
| Graph visualisation | D3.js | ≥ 7 |
| Charts | Recharts | ≥ 2.10 |
| Testing | pytest | ≥ 7 |

---

## 8. Testing Strategy

| Test file | Coverage |
|---|---|
| `test_config.py` | SimConfig defaults, serialisation, forward-compat, validation (26 tests) |
| `test_agent.py` | Update rule, bounded confidence, clipping, reproducibility (7 tests) |
| `test_model.py` | Convergence, hard cutoff, run_id format, reproducibility (6 tests) |
| `test_network.py` | Topology connectivity, node attributes, SBM community split (8 tests) |
| `test_metrics.py` | Shannon H, pairwise D, cross-D, logistic fit (7 tests) |
| `test_api.py` | FastAPI endpoint integration tests |

Run all tests: `pytest tests/ -v`

---

*Last updated: 2026-07-11 — Phase 7 (React Frontend) complete*
