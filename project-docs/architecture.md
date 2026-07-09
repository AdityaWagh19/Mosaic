# Mosaic — System Architecture

This document defines all modules, their responsibilities, interfaces, and the
data flow between them. All decisions here are traceable to `model.md` (for
simulation design) or `prd.md` (for requirements).

---

## 1. System Overview

Mosaic has three separable layers that can be developed and tested independently:

```
┌─────────────────────────────────────────────────────────┐
│  SIMULATION LAYER  (Python)                             │
│  NetworkGenerator → MosaicModel → DataLogger            │
│                         ↑                               │
│                    AccentAgent                          │
│                    MonteCarloRunner                     │
│                    config.py (SimConfig dataclass)      │
└──────────────────────────┬──────────────────────────────┘
                           │  JSON over REST
┌──────────────────────────▼──────────────────────────────┐
│  API LAYER  (FastAPI)                                    │
│  POST /run  ·  GET /results/{id}  ·  GET /umap/{id}     │
└──────────────────────────┬──────────────────────────────┘
                           │  HTTP
┌──────────────────────────▼──────────────────────────────┐
│  FRONTEND LAYER  (React + Vite)                         │
│  ControlPanel → D3NetworkViz                            │
│              → RechartsTimeSeries                       │
│              → UMAPScatter                              │
└─────────────────────────────────────────────────────────┘
```

**Phase ownership:**
- Phase 1 — Simulation layer only (no API, no frontend)
- Phase 2 — ML module added to simulation layer
- Phase 3 — API layer + Frontend layer built

---

## 2. Project Directory Structure

```
mosaic/
├── simulation/
│   ├── __init__.py
│   ├── config.py          # SimConfig dataclass
│   ├── network.py         # NetworkGenerator
│   ├── agent.py           # AccentAgent
│   ├── model.py           # MosaicModel
│   ├── logger.py          # DataLogger
│   └── runner.py          # MonteCarloRunner
│
├── analysis/              # Phase 2 — ML & visualisation
│   ├── clustering.py      # k-means + DBSCAN dialect zone discovery
│   ├── gcn.py             # GCN trajectory predictor (PyTorch Geometric)
│   ├── umap_viz.py        # UMAP coordinates computation
│   └── shap_analysis.py   # SHAP feature importance (optional)
│
├── api/                   # Phase 3 — FastAPI backend
│   ├── main.py
│   └── schemas.py         # Pydantic request/response models
│
├── frontend/              # Phase 3 — React app
│   ├── src/
│   │   ├── components/
│   │   │   ├── ControlPanel.jsx
│   │   │   ├── NetworkGraph.jsx    # D3.js force-directed graph
│   │   │   ├── TimeSeries.jsx      # Recharts diversity/distance curves
│   │   │   └── UMAPScatter.jsx     # UMAP scatter with timestep slider
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── runs/                  # Auto-created; one sub-dir per simulation run
│   └── {run_id}/
│       ├── config.json
│       ├── agent_states.csv
│       └── metrics.json
│
├── results/               # Aggregated outputs from MonteCarloRunner
│   ├── summary.csv
│   └── figures/           # PNG exports (300 DPI)
│
├── tests/
│   ├── test_agent.py
│   ├── test_model.py
│   ├── test_network.py
│   └── test_metrics.py
│
├── notebooks/
│   └── demo.ipynb         # Narrative walkthrough of one full run
│
├── requirements.txt
└── README.md
```

---

## 3. Simulation Layer — Module Specifications

### 3.1 `config.py` — SimConfig

A Python dataclass that is the single source of truth for all simulation
parameters. Every run begins by instantiating a `SimConfig`.

```python
from dataclasses import dataclass

@dataclass
class SimConfig:
    # Population
    N: int = 200                      # Number of agents
    # Network
    topology: str = "watts_strogatz"  # "er" | "watts_strogatz" | "ba" | "sbm"
    p_er: float = 0.05                # ER edge probability
    k_ws: int = 6                     # WS nearest neighbours
    p_rewire: float = 0.1             # WS rewiring probability
    m_ba: int = 3                     # BA edges per new node
    p_in: float = 0.15                # SBM intra-community edge probability
    p_out: float = 0.02               # SBM inter-community edge probability
    n_communities: int = 2            # SBM community count (default 2)
    # Simulation
    T: int = 10000                    # Max timesteps
    log_every: int = 100              # Log agent states every N steps
    # Model parameters (from model.md §6)
    gamma: float = 1.0                # Prestige weight
    theta: float = 0.30               # Bounded confidence threshold
    sigma: float = 0.01               # Phonetic drift noise std
    # Reproducibility
    seed: int = 42
    # Monte Carlo
    n_runs: int = 25
```

Serialised to `config.json` at the start of every run. Deserialised by the
API layer when returning run metadata to the frontend.

---

### 3.2 `network.py` — NetworkGenerator

**Responsibility:** Generate a `nx.Graph` with all node attributes set.

**Interface:**
```python
def make_network(config: SimConfig) -> nx.Graph:
    """
    Returns a NetworkX Graph with node attributes:
      - 'community_id': int
      - 'centrality': float in [0,1] (normalised degree centrality)
    """
```

**Internal dispatch:**
```python
match config.topology:
    case "er":             G = nx.erdos_renyi_graph(N, p_er, seed=seed)
    case "watts_strogatz": G = nx.watts_strogatz_graph(N, k_ws, p_rewire, seed=seed)
    case "ba":             G = nx.barabasi_albert_graph(N, m_ba, seed=seed)
    case "sbm":            G = nx.stochastic_block_model(sizes, probs, seed=seed)
```

After generation:
1. Compute `nx.degree_centrality(G)` → normalise → store as `G.nodes[i]['centrality']`
2. Assign `community_id`: for SBM, from block membership; for others, all 0

**Guarantee:** The returned graph is always connected (re-sample if not, for ER).

---

### 3.3 `agent.py` — AccentAgent

**Responsibility:** Hold one agent's state and perform one accommodation step.

```python
class AccentAgent(mesa.Agent):
    def __init__(self, unique_id, model, accent_vector, community_id, centrality):
        super().__init__(unique_id, model)
        self.accent = np.array(accent_vector, dtype=float)  # shape (6,)
        self.community_id = community_id
        self.centrality = centrality

    def update(self, speaker: "AccentAgent"):
        """
        Listener (self) accommodates toward speaker.
        Implements model.md §6 update rule.
        """
        diff = speaker.accent - self.accent
        distance = np.linalg.norm(diff)

        if distance >= self.model.config.theta:
            return  # bounded confidence: no interaction

        alpha_ij = self.model.config.gamma * speaker.centrality
        noise = np.random.normal(0, self.model.config.sigma, size=6)
        self.accent = np.clip(self.accent + alpha_ij * diff + noise, 0.0, 1.0)
```

**No `step()` method on the agent.** The model controls scheduling (edge-based),
so agents never self-activate. The `update()` method is called by `MosaicModel`.

---

### 3.4 `model.py` — MosaicModel

**Responsibility:** Own the network, all agents, the scheduler, and the
simulation loop. Implement edge-based interaction scheduling.

```python
class MosaicModel(mesa.Model):
    def __init__(self, config: SimConfig, G: nx.Graph):
        super().__init__()
        self.config = config
        self.G = G
        self.edge_list = list(G.edges())
        self.rng = np.random.default_rng(config.seed)

        # Instantiate agents
        self.agents_map: dict[int, AccentAgent] = {}
        for node_id in G.nodes():
            accent = self._init_accent(G.nodes[node_id]['community_id'])
            agent = AccentAgent(
                node_id, self,
                accent_vector=accent,
                community_id=G.nodes[node_id]['community_id'],
                centrality=G.nodes[node_id]['centrality']
            )
            self.agents_map[node_id] = agent

    def step(self):
        """One timestep: sample a random edge, listener accommodates."""
        idx = self.rng.integers(len(self.edge_list))
        i, j = self.edge_list[idx]
        self.agents_map[i].update(self.agents_map[j])

    def run(self, logger: "DataLogger") -> dict:
        """Run for T steps or until convergence. Returns metrics dict."""
        ...
```

**Initialisation helper `_init_accent`:**
- For SBM: draws from N(μ_c, 0.05²·I) using community prototype from model.md §3
- For other topologies: draws from N([0.5]*6, 0.15²·I)
- Clips result to [0, 1] element-wise

---

### 3.5 `logger.py` — DataLogger

**Responsibility:** Write per-step agent state snapshots to CSV and final
metrics to JSON. Logging happens every `log_every` steps.

**Output files in `runs/{run_id}/`:**
- `agent_states.csv` — columns: `timestep, agent_id, community_id, centrality, d0, d1, d2, d3, d4, d5`
- `config.json` — serialised SimConfig
- `metrics.json` — convergence_time, converged, final_diversity, final_pairwise_distance

`run_id` is generated as `{topology}_{seed}_{timestamp}` for uniqueness
without requiring a database.

---

### 3.6 `runner.py` — MonteCarloRunner

**Responsibility:** Execute `n_runs` independent simulation runs over the same
`SimConfig`, varying only the random seed. Aggregate results into `results/summary.csv`.

```python
def run_monte_carlo(config: SimConfig) -> pd.DataFrame:
    results = []
    for i in range(config.n_runs):
        run_config = replace(config, seed=config.seed + i)
        G = make_network(run_config)
        model = MosaicModel(run_config, G)
        logger = DataLogger(run_config)
        metrics = model.run(logger)
        results.append(metrics)
    return pd.DataFrame(results)
```

Summary CSV columns: `run_id, topology, gamma, theta, sigma,
convergence_time, converged, final_diversity, final_pairwise_distance`.

---

## 4. Analysis Layer — Module Specifications (Phase 2)

### 4.1 `clustering.py`

Loads final agent accent vectors from a completed run. Applies:
- **k-means** (k ∈ {2,3,4,5}) — select optimal k via silhouette score
- **DBSCAN** — validation of k-means structure; no k parameter needed
- Computes: silhouette score, Davies-Bouldin index, ARI vs community_id (SBM runs)

### 4.2 `gcn.py`

Trains a 2-layer GCN on completed simulation run outputs.

**Training data construction:**
- Each run → one `torch_geometric.data.Data` object:
  - `x`: node feature matrix, shape `(N, 9)` — 6 accent dims + degree + clustering_coeff + community_id
  - `edge_index`: graph connectivity, shape `(2, E)`
  - `y`: final k-means cluster label per node, shape `(N,)` — integer class label
- 100 runs total → 80 train / 20 test split at the **run level** (not agent level)

**Architecture:**
```python
class AccentGCN(nn.Module):
    def __init__(self, in_channels=9, hidden=32, num_classes=5):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, num_classes)
        self.dropout = nn.Dropout(0.3)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = self.dropout(x)
        return self.conv2(x, edge_index)
```

**Baseline (MLP):** Same architecture but ignores `edge_index` — takes node
features only. GCN accuracy > MLP accuracy demonstrates that network structure
carries predictive signal beyond raw agent features. This directly answers RQ3.

**Optional upgrade:** Replace `GCNConv` with `GATConv` in one line.
Use `return_attention_weights=True` to extract and visualise learned prestige weights.

### 4.3 `umap_viz.py`

At 4 timesteps (0, T//3, 2T//3, t_conv), loads accent matrices from
`agent_states.csv` and computes 2D UMAP coordinates:

```python
reducer = umap.UMAP(n_components=2, random_state=seed)
coords = reducer.fit_transform(accent_matrix)  # shape (N, 2)
```

Saves per-timestep coordinates to `runs/{run_id}/umap_coords.json`:
```json
{
  "0":    [[x0, y0], [x1, y1], ...],
  "3333": [[x0, y0], ...],
  "6666": [...],
  "conv": [...]
}
```

Frontend renders this as an animated scatter plot with a timestep slider.

---

## 5. API Layer — FastAPI (Phase 3)

### 5.1 Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/run` | Accept SimConfig JSON → run simulation → return result |
| `GET` | `/results/{run_id}` | Return stored run result (metrics + timeline + network) |
| `GET` | `/umap/{run_id}` | Return UMAP coordinates JSON for a completed run |
| `GET` | `/topologies` | Return list of supported topologies with parameter descriptions |

### 5.2 POST /run — Request & Response

**Request body** (SimConfig JSON, all fields optional — defaults from SimConfig):
```json
{ "N": 200, "topology": "watts_strogatz", "T": 5000, "gamma": 1.0, "theta": 0.3 }
```

**Response:**
```json
{
  "run_id": "watts_strogatz_42_20260709",
  "config": { "...all SimConfig fields..." },
  "metrics": {
    "convergence_time": 4320,
    "converged": true,
    "final_diversity": 0.38,
    "final_pairwise_distance": 0.14
  },
  "timeline": [
    { "timestep": 0,   "diversity": 1.21, "pairwise_distance": 0.54 },
    { "timestep": 100, "diversity": 1.18, "pairwise_distance": 0.51 }
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

The `network` field contains serialised graph data so D3.js can render the
force-directed graph without any NetworkX dependency in the frontend.

### 5.3 Implementation Notes

- Simulation runs synchronously for N ≤ 500, T ≤ 10,000 (completes in <30s on CPU)
- `run_id` is returned immediately; no polling mechanism needed
- CORS enabled for `localhost:5173` (Vite dev server default port)
- No authentication or session management required

---

## 6. Frontend Layer — React + Vite (Phase 3)

### 6.1 Component Map

```
App
├── ControlPanel       — Parameter inputs + "Run Simulation" button
├── NetworkGraph       — D3.js force-directed graph (nodes = agents)
│     node colour:       mapped to cluster_id (categorical colour scale)
│     node size:         3 + centrality * 12 (hubs visually larger)
│     on hover:          tooltip: agent_id, community_id, centrality, accent dims
├── TimeSeries         — Recharts line chart: diversity + pairwise_distance vs timestep
└── UMAPScatter        — Scatter plot; timestep slider animates accent space collapse
```

### 6.2 D3.js Network Graph

- Force simulation: `d3.forceSimulation()` with `forceManyBody` + `forceLink`
- Node colour: `d3.scaleOrdinal(d3.schemeTableau10)` mapped to `cluster_id`
- Re-renders when a new simulation result arrives from the API
- Zoom and pan enabled via `d3.zoom()`

### 6.3 State Management

Plain React `useState` + `useEffect`. Three pieces of state:
- `config` — current form values (mirrors SimConfig fields)
- `loading` — boolean, true while API request is in flight
- `result` — full API response JSON, null until first run completes

### 6.4 API Communication

```javascript
const runSimulation = async (config) => {
  setLoading(true);
  const res = await fetch('http://localhost:8000/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  const data = await res.json();
  setResult(data);
  setLoading(false);
};
```

---

## 7. Technology Stack

| Layer | Technology | Version (target) |
|---|---|---|
| ABM | Mesa | ≥ 2.1 |
| Graph computation | NetworkX | ≥ 3.2 |
| Numerics | NumPy | ≥ 1.26 |
| Data handling | pandas | ≥ 2.1 |
| ML (GCN) | PyTorch + PyTorch Geometric | ≥ 2.1 / ≥ 2.4 |
| Dimensionality reduction | umap-learn | ≥ 0.5 |
| Scientific visualisation | matplotlib, seaborn | ≥ 3.8 / ≥ 0.13 |
| API backend | FastAPI + uvicorn | ≥ 0.104 |
| Frontend | React + Vite | ≥ 18 / ≥ 5 |
| Graph visualisation | D3.js | ≥ 7 |
| Charts | Recharts | ≥ 2.10 |
| Testing | pytest | ≥ 7 |

---

## 8. Testing Strategy

Unit tests in `tests/` cover the four most critical functional areas:

| Test file | What is tested |
|---|---|
| `test_agent.py` | Update rule: accent moves toward speaker by correct amount; bounded confidence suppresses update when distance ≥ θ; clipping keeps all values in [0,1] |
| `test_model.py` | Convergence detection fires at correct entropy threshold; hard cutoff at T; sanity check: θ=∞, γ=0, σ=0, complete graph → full consensus |
| `test_network.py` | All four topologies return connected graphs; node attributes `community_id` and `centrality` are set; SBM produces correct community sizes |
| `test_metrics.py` | Shannon diversity = 0 for identical agents; pairwise distance = 0 for identical agents; cross-community distance = 0 when communities converge |

Run all tests: `pytest tests/ -v`

---

*Last updated: 2026-07-09*
