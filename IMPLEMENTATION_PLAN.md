# Mosaic — Definitive Implementation Plan

**Role:** System Architect + AI/ML Engineer + Software Engineer  
**Approach:** Clean separation of concerns, no over-engineering, all plans independently testable, no stubs when complete.

---

## Part 1 — Architecture Analysis

### Three Structural Gaps in Current project-docs

The existing `architecture.md` is well-specified but has three structural omissions
that would cause coupling problems during implementation:

**Gap 1: No `metrics.py` module.**
`architecture.md` embeds metric computation inside `model.py`. This means:
- Metrics (H(t), D(t), s_i, A(t), D_cross) cannot be unit-tested independently
- Experiment scripts must import the model just to compute post-hoc metrics
- The model file becomes a god-object mixing orchestration + math

**Resolution:** Extract all metric functions into `simulation/metrics.py` as pure
functions that take `np.ndarray` inputs and return scalars. The model calls them
internally; experiment scripts call them on loaded CSV data.

---

**Gap 2: No `analysis/data_loader.py`.**
The ML layer (Plan 5) reads from `runs/` CSV files. Without an explicit loader,
`gcn.py` and `clustering.py` each re-implement CSV parsing, path resolution, and
data transformation. This creates fragile duplication.

**Resolution:** A dedicated `analysis/data_loader.py` is the bridge between
Phase 1 outputs and Phase 2 inputs. It loads run directories into structured
Python objects and constructs PyTorch Geometric `Data` objects for GCN training.

---

**Gap 3: No `viz/` package — visualization logic is implied to live in experiment scripts.**
Mixing figure generation code into experiment scripts violates single responsibility.
Experiment scripts should only orchestrate runs and call visualization functions,
not embed matplotlib code.

**Resolution:** A `viz/` package with `figures.py` (static matplotlib/seaborn)
and `gif.py` (animated GIF). Experiment scripts call functions from `viz/`; `viz/`
has no knowledge of simulations.

---

### Resolved Decisions (answering open questions from prior analysis)

| Decision | Resolution |
|---|---|
| CI/CD | Include basic GitHub Actions workflow (pytest on push) in Plan 8 |
| SHAP | Out of scope — not in any plan |
| Frontend CSS | Single `index.css` file with all custom properties |
| GIF size | N=100 agents, 3 seconds, 20fps — estimated ~2–4MB |
| `tasks.md §1.9` stale metric | `experiments.md` is canonical — use Influence Residual Score s_i |
| Heatmap "5 topologies" typo | 4 topologies: ER, WS, BA, SBM |
| `GET /topologies` endpoint | Include it — zero cost, improves frontend UX |
| `ml-pipeline.md` empty | Written as first deliverable of Plan 5 |
| Run ID format | `{topology}_{seed}` — deterministic, predictable, reproducible |

---

## Part 2 — Canonical Directory Structure

This is the definitive file tree. Every file listed will exist when all 8 plans
are complete. No other files are expected in production scope.

```
Mosaic/
│
├── simulation/                    # Phase 1: ABM simulation engine
│   ├── __init__.py
│   ├── config.py                  # SimConfig dataclass — single parameter truth
│   ├── network.py                 # make_network() → nx.Graph with node attrs
│   ├── agent.py                   # AccentAgent — state + update rule
│   ├── model.py                   # MosaicModel — orchestrator + convergence
│   ├── metrics.py                 # Pure metric functions (NEW)
│   ├── logger.py                  # DataLogger — file I/O for run outputs
│   └── runner.py                  # MonteCarloRunner — batch execution
│
├── experiments/                   # Phase 1: Experiment orchestration
│   ├── __init__.py
│   ├── run_all.py                 # Entry point: python -m experiments.run_all
│   ├── exp1_topology.py
│   ├── exp2_prestige.py
│   ├── exp3_contact.py
│   ├── ablations.py
│   ├── scurve.py
│   └── heatmaps.py
│
├── viz/                           # Phase 1: Visualization layer (NEW package)
│   ├── __init__.py
│   ├── figures.py                 # All static matplotlib/seaborn figure functions
│   └── gif.py                     # Animated GIF generation
│
├── analysis/                      # Phase 2: ML analysis layer
│   ├── __init__.py
│   ├── data_loader.py             # Run outputs → ML-ready data (NEW)
│   ├── clustering.py              # k-means + DBSCAN + metrics
│   ├── gcn.py                     # AccentGCN + AccentMLP + training loop
│   ├── evaluate.py                # Evaluation metrics + reporting (NEW)
│   └── umap_viz.py                # UMAP coordinate computation
│
├── api/                           # Phase 3: FastAPI backend
│   ├── __init__.py
│   ├── main.py
│   └── schemas.py
│
├── frontend/                      # Phase 3: React + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── ControlPanel.jsx
│   │   │   ├── NetworkGraph.jsx
│   │   │   ├── TimeSeries.jsx
│   │   │   └── UMAPScatter.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css              # All design tokens from design.md §18
│   ├── package.json
│   └── vite.config.js
│
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_network.py
│   ├── test_agent.py
│   ├── test_model.py
│   └── test_metrics.py            # Tests for metrics.py
│
├── notebooks/
│   └── demo.ipynb
│
├── .github/
│   └── workflows/
│       └── tests.yml              # Run pytest on push to main
│
├── runs/                          # Auto-generated — not git-tracked
│   └── .gitkeep
│
├── results/
│   └── figures/
│       └── .gitkeep
│
├── project-docs/                  # Existing documentation
├── research/                      # Existing research reports
├── .gitignore
├── pyproject.toml                 # Project metadata + pytest config
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Part 3 — Module Interface Specifications

### `simulation/metrics.py` — Pure Functions

```python
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from scipy.optimize import curve_fit
from scipy.stats import spearmanr

def shannon_diversity(accent_matrix: np.ndarray, n_clusters: int = 5) -> float:
    """
    Compute Shannon diversity H(t) via k-means clustering.
    accent_matrix: (N, 6) array of current agent accent vectors.
    Returns scalar entropy value.
    """

def mean_pairwise_distance(accent_matrix: np.ndarray) -> float:
    """
    Compute D(t) = mean Euclidean distance over all agent pairs.
    Uses vectorised computation. accent_matrix: (N, 6).
    """

def cross_community_distance(
    accent_matrix: np.ndarray,
    community_ids: np.ndarray
) -> float:
    """
    Compute D_cross(t) = ||mu_0(t) - mu_1(t)||.
    community_ids: (N,) integer array. Only valid for 2-community SBM runs.
    """

def influence_residual_scores(
    initial_accents: np.ndarray,
    final_mean_accent: np.ndarray
) -> np.ndarray:
    """
    Compute s_i = -||a_i(0) - mu_final|| for all agents.
    Returns (N,) array of influence scores.
    """

def adoption_fraction(
    accent_matrix: np.ndarray,
    initial_mean_dim0: float,
    threshold: float = 0.2
) -> float:
    """
    Compute A(t): fraction of agents where dim_0 > initial_mean_dim0 + threshold.
    Used by S-curve experiment.
    """

def spearman_centrality_influence(
    centrality: np.ndarray,
    influence_scores: np.ndarray
) -> tuple[float, float]:
    """
    Returns (r, p_value) Spearman correlation between centrality and s_i.
    """

def logistic_fit(
    t: np.ndarray,
    adoption: np.ndarray
) -> tuple[float, float, float]:
    """
    Fit A(t) = 1 / (1 + exp(-k*(t - t0))) to data.
    Returns (k, t0, r_squared).
    """
```

---

### `analysis/data_loader.py` — Phase 1→2 Bridge

```python
import pandas as pd
import numpy as np
from torch_geometric.data import Data
from simulation.config import SimConfig

def load_run(run_id: str, runs_dir: str = "runs") -> dict:
    """
    Load a completed run from disk.
    Returns:
      {
        "config": SimConfig,
        "agent_states": pd.DataFrame,  # all timesteps
        "metrics": dict                # from metrics.json
      }
    Raises FileNotFoundError if run_id does not exist in runs_dir.
    """

def get_accent_matrix(
    agent_states: pd.DataFrame,
    timestep: int
) -> np.ndarray:
    """
    Extract (N, 6) accent matrix at a specific timestep.
    Columns d0..d5 are extracted. Raises ValueError if timestep not found.
    """

def get_final_accent_matrix(agent_states: pd.DataFrame) -> np.ndarray:
    """Extract accent matrix at the last logged timestep."""

def get_initial_accent_matrix(agent_states: pd.DataFrame) -> np.ndarray:
    """Extract accent matrix at timestep 0."""

def build_pyg_dataset(
    run_ids: list[str],
    runs_dir: str = "runs",
    n_clusters: int = 5
) -> list[Data]:
    """
    Build PyTorch Geometric Data objects for GCN training.
    
    For each run:
    - x: (N, 9) node features — 6 accent dims + degree + clustering_coeff + community_id
    - edge_index: (2, E) graph connectivity
    - y: (N,) integer final k-means cluster labels
    
    Returns list of Data objects, one per run.
    """

def list_run_ids(runs_dir: str = "runs") -> list[str]:
    """Return all run_ids present in runs_dir as a sorted list."""
```

---

### `analysis/evaluate.py` — ML Evaluation

```python
import numpy as np

def classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str
) -> dict:
    """
    Returns accuracy, macro F1, and confusion matrix.
    Prints formatted report to stdout.
    """

def compare_models(
    gcn_preds: np.ndarray,
    mlp_preds: np.ndarray,
    y_true: np.ndarray
) -> dict:
    """
    Side-by-side comparison of GCN vs MLP.
    Returns dict with keys: gcn_accuracy, mlp_accuracy, gcn_f1, mlp_f1.
    """

def save_evaluation_report(results: dict, path: str) -> None:
    """Save evaluation results to JSON."""
```

---

### Data Contracts

**`runs/{topology}_{seed}/agent_states.csv`**
```
timestep, agent_id, community_id, centrality, d0, d1, d2, d3, d4, d5
```

**`runs/{topology}_{seed}/config.json`**
```json
{
  "N": 200, "topology": "watts_strogatz",
  "p_er": 0.05, "k_ws": 6, "p_rewire": 0.1,
  "m_ba": 3, "p_in": 0.15, "p_out": 0.02, "n_communities": 2,
  "T": 10000, "log_every": 100,
  "gamma": 1.0, "theta": 0.30, "sigma": 0.01,
  "seed": 42, "n_runs": 25
}
```

**`runs/{topology}_{seed}/metrics.json`**
```json
{
  "run_id": "watts_strogatz_42",
  "convergence_time": 4320,
  "converged": true,
  "final_diversity": 0.38,
  "final_pairwise_distance": 0.14
}
```

**`results/summary.csv`**
```
run_id, topology, gamma, theta, sigma, seed,
convergence_time, converged, final_diversity, final_pairwise_distance
```

**`runs/{topology}_{seed}/umap_coords.json`** (Phase 2 only)
```json
{
  "0":    [[x0, y0], [x1, y1], ...],
  "3333": [[x0, y0], ...],
  "6666": [...],
  "conv": [...]
}
```

---

## Part 4 — Implementation Plans

---

### Plan 1 — Foundation

**Purpose:**
Establish the complete project skeleton: all directories, packaging config,
dependency specification, `.gitignore`, and the `SimConfig` dataclass that
every other module depends on.

**Scope (includes):**
- Project directory tree creation (all packages with `__init__.py`)
- `requirements.txt` with all pinned versions
- `pyproject.toml` with project metadata and pytest config
- `.gitignore` for Python, venv, run outputs, notebook checkpoints
- `simulation/config.py` — complete `SimConfig` dataclass
- `runs/.gitkeep` and `results/figures/.gitkeep`

**Scope (excludes):**
- Any simulation logic (that is Plan 2)
- Any test files other than a smoke test (Plan 3)

**Exact Deliverables:**

| File | Description |
|---|---|
| `simulation/__init__.py` | Empty |
| `experiments/__init__.py` | Empty |
| `viz/__init__.py` | Empty |
| `analysis/__init__.py` | Empty |
| `api/__init__.py` | Empty |
| `tests/__init__.py` | Empty |
| `simulation/config.py` | `SimConfig` dataclass, `to_dict()`, `from_dict()`, `__post_init__` validation |
| `requirements.txt` | All pinned versions |
| `pyproject.toml` | `[tool.pytest.ini_options]` testpaths, markers |
| `.gitignore` | `.venv/`, `__pycache__/`, `*.pyc`, `runs/*/`, `results/summary.csv`, `.ipynb_checkpoints/` — NOT `runs/.gitkeep` |
| `runs/.gitkeep` | Placeholder |
| `results/figures/.gitkeep` | Placeholder |

**`SimConfig` fields (complete):**
```python
@dataclass
class SimConfig:
    # Population
    N: int = 200
    # Network
    topology: str = "watts_strogatz"   # "er"|"watts_strogatz"|"ba"|"sbm"
    p_er: float = 0.05
    k_ws: int = 6
    p_rewire: float = 0.1
    m_ba: int = 3
    p_in: float = 0.15
    p_out: float = 0.02
    n_communities: int = 2
    # Simulation
    T: int = 10000
    log_every: int = 100
    # Model parameters
    gamma: float = 1.0
    theta: float = 0.30
    sigma: float = 0.01
    # Reproducibility
    seed: int = 42
    # Monte Carlo
    n_runs: int = 25

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d: dict) -> "SimConfig": ...
```

**`requirements.txt` (pinned):**
```
mesa==2.1.5
networkx==3.2.1
numpy==1.26.4
pandas==2.1.4
scipy==1.11.4
scikit-learn==1.3.2
matplotlib==3.8.2
seaborn==0.13.2
pillow==10.2.0
torch==2.4.1+cu121      # GPU; see requirements.txt header for install command
torch-geometric==2.6.1  # compatible with torch 2.4.x
umap-learn==0.5.5
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.2
pytest==7.4.4
jupyter==1.0.0
```

**Entry criteria:** None (first plan).

**Exit criteria:**
- `python -c "from simulation.config import SimConfig; c = SimConfig(); assert c.to_dict() == SimConfig.from_dict(c.to_dict()).to_dict()"` passes
- `pip install -r requirements.txt` succeeds cleanly
- All `__init__.py` files exist (verify with `find . -name __init__.py`)

**Dependencies:** None.

**Risks:**
- PyTorch GPU (cu121): `torch==2.4.1+cu121` from `https://download.pytorch.org/whl/cu121`. Requires driver ≥ 527.41 (user has 529.04 — OK). Note: cu121 wheel server starts at 2.2.0, so 2.1.2+cu121 does not exist.
- Mesa 2.x removed `BatchActivation` and changed `Model.__init__` signature. Verify compatibility before Plan 2.

**Tests:** One smoke test in `tests/test_config.py`: default values match `architecture.md §3.1`; JSON round-trip is lossless; invalid topology string raises `ValueError` from `__post_init__`.

---

### Plan 2 — Simulation Engine

**Purpose:**
Implement the six modules that constitute the ABM: network generation, agent
state and behaviour, model orchestration, metric computation, data logging, and
Monte Carlo batch execution. This is the project's computational core.

**Scope (includes):**
- All 6 `simulation/` modules except `config.py` (Plan 1)
- First exercise of the `runs/` and `results/` directories

**Scope (excludes):**
- Experiment scripts (Plan 4)
- Visualization (Plan 4)
- ML analysis (Plan 5)

**Exact Deliverables:**

| File | Key responsibilities |
|---|---|
| `simulation/network.py` | `make_network(config) → nx.Graph`; dispatches to 4 topology generators; computes and normalises degree centrality; assigns `community_id`; guarantees connectivity |
| `simulation/agent.py` | `AccentAgent(mesa.Agent)`; `update(speaker)` implementing `model.md §6`; bounded confidence check; noise + clipping |
| `simulation/model.py` | `MosaicModel(mesa.Model)`; edge list precomputed at init; `step()`; convergence tracking; `run(logger) → dict` |
| `simulation/metrics.py` | 7 pure metric functions as specified in Part 3 |
| `simulation/logger.py` | `DataLogger`; creates `runs/{run_id}/`; writes CSV every `log_every` steps; writes `config.json` at start; writes `metrics.json` at end |
| `simulation/runner.py` | `run_monte_carlo(config) → pd.DataFrame`; seed-incremented loop; writes `results/summary.csv` |

**Key implementation details:**

`model.py` — Convergence detection:
```python
# Track last 200 logged H values; convergence = std(last_200) < delta
# delta = 0.001 per model.md §7
# Only check convergence at log intervals (every log_every steps)
# Shannon diversity is computed via metrics.shannon_diversity() — NOT inline
```

`model.py` — k-means caching:
```python
# Refit k-means every 500 steps, not every 100
# Cache centroids between refits; assign labels from cached centroids on off-steps
# n_clusters=5 for convergence tracking (matches model.md §8.1)
```

`network.py` — ER connectivity:
```python
# If not nx.is_connected(G): retry with seed+1000 (up to 5 retries)
# Log warning if fallback used
```

`runner.py` — Parallelisation:
```python
# DEFAULT: sequential loop (simple, debuggable)
# HEATMAP MODE: ProcessPoolExecutor (used only by experiments/heatmaps.py)
# Do NOT parallelise the default MonteCarloRunner — keep it simple
```

**Entry criteria:** Plan 1 complete.

**Exit criteria:**
- `python -m simulation.runner` completes 25 runs without errors
- `runs/` populated with 25 `{topology}_{seed}/` directories, each containing 3 files
- `results/summary.csv` exists with all required columns
- Single run N=200, T=10,000 completes in < 60 seconds

**Dependencies:** Plan 1.

**Risks:**

| Risk | Mitigation |
|---|---|
| Mean pairwise distance O(N²) is expensive for large N | Use `scipy.spatial.distance.pdist` — vectorised and ~10x faster than loops |
| SBM disconnected at low p_out | Add connectivity check in `make_network()` for all topologies |
| k-means non-determinism affects convergence tracking | Pass `random_state=config.seed` to every KMeans call |
| Mesa 2.x scheduler API | Mosaic does NOT use Mesa's scheduler — agents have no `step()`. Only model calls `update()` directly. This sidesteps all Mesa scheduler complexity |

**Tests:** `test_network.py`, `test_agent.py`, `test_model.py`, `test_metrics.py` (Plan 3).

---

### Plan 3 — Unit Test Suite

**Purpose:**
Implement the full test suite against Plan 2 modules. Achieve ≥ 20 passing tests
covering all critical paths: update rule correctness, convergence detection,
graph generation, and metric mathematical properties.

**Scope (includes):** All tests for Plans 1–2 modules.

**Scope (excludes):** Integration tests, experiment tests, API tests (those are Plan 6).

**Exact Deliverables and Test Count:**

| File | Tests | What is tested |
|---|---|---|
| `tests/test_config.py` | 4 | Default values; JSON round-trip; `from_dict` with extra keys ignored; invalid topology raises |
| `tests/test_network.py` | 6 | All 4 topologies are connected; node attributes `centrality` and `community_id` set on all nodes; SBM produces 2 communities of correct size; centrality in [0,1]; ER re-samples if disconnected |
| `tests/test_agent.py` | 7 | Accent moves toward speaker by `gamma * centrality_j * diff`; update suppressed when `dist >= theta`; `gamma=0` produces zero-influence update; noise term applied when sigma>0; noise=0 when sigma=0; clipping: result always in [0,1]; deterministic: same seed produces same update |
| `tests/test_model.py` | 6 | Convergence detected when H stabilises; hard cutoff at T returns `converged=False`; sanity check: `theta=inf, gamma=0, sigma=0, complete_graph → all agents same accent`; run returns dict with required keys; run_id in `metrics.json` matches expected format; seed reproducibility |
| `tests/test_metrics.py` | 5 | `shannon_diversity` = 0 for identical accents; `mean_pairwise_distance` = 0 for identical accents; `cross_community_distance` = 0 when communities converge; `influence_residual_scores` shape is (N,); `logistic_fit` returns R² in [0,1] for valid data |

**Total: ≥ 28 tests** (exceeds the ≥ 20 requirement from `prd.md F1.9`).

**Entry criteria:** Plan 2 complete.

**Exit criteria:** `pytest tests/ -v` → all 28+ tests pass, 0 fail, 0 error.

**Dependencies:** Plans 1–2.

**Risks:** None significant.

---

### Plan 4 — Experiments and Visualisations

**Purpose:**
Run all 6 pre-specified experiments from `experiments.md`, generate all 13
static figures, and produce the animated diffusion GIF. This is Phase 1's
scientific deliverable and makes the project demonstrable before any frontend.

**Scope (includes):**
- `experiments/` package (6 scripts + `run_all.py`)
- `viz/` package (`figures.py` + `gif.py`)
- All 13 figures + 1 animated GIF
- `results/summary.csv` populated with all experiment runs

**Scope (excludes):**
- ML analysis (Plan 5)
- API or frontend (Plans 6–7)
- `demo.ipynb` (Plan 8)

**Exact Deliverables:**

`viz/figures.py` — exported functions:
```python
def plot_diversity_timeseries(summary_df, topology_col, diversity_col, out_path) -> None
def plot_convergence_boxplot(summary_df, topology_col, conv_time_col, out_path) -> None
def plot_final_diversity_bar(summary_df, topology_col, diversity_col, out_path) -> None
def plot_network_snapshot(G, agent_states_df, timestep, colour_by, size_by, out_path) -> None
def plot_spearman_vs_gamma(spearman_df, out_path) -> None
def plot_centrality_vs_influence(centrality, scores, gamma, out_path) -> None
def plot_cross_community_distance(dcross_df, p_out_values, out_path) -> None
def plot_merger_time_bar(merger_df, p_out_values, out_path) -> None
def plot_ablation_boxplot(ablation_df, out_path) -> None
def plot_scurve(t, adoption_matrix, fit_params, out_path) -> None
def plot_heatmap(pivot_df, xlabel, ylabel, title, out_path) -> None
```

`viz/gif.py`:
```python
def make_diffusion_gif(
    run_id: str,
    runs_dir: str = "runs",
    n_display: int = 100,     # subsample agents for clarity
    fps: int = 20,
    n_frames: int = 60,       # 60 frames × 20fps = 3 seconds
    out_path: str = "results/figures/diffusion.gif"
) -> None
```

Experiment scripts all follow the same pattern:
1. Build configs
2. Run `MonteCarloRunner` (or load from `runs/` if already run)
3. Compute metrics from loaded CSVs using `simulation/metrics.py`
4. Call `viz/figures.py` functions to generate and save figures

**Figures produced:**

| Figure ID | File | Experiment |
|---|---|---|
| E1-A | `e1_diversity_timeseries.png` | Exp 1 — topology comparison |
| E1-B | `e1_convergence_boxplot.png` | Exp 1 |
| E1-C | `e1_final_diversity_bar.png` | Exp 1 |
| E2-A | `e2_centrality_vs_influence.png` | Exp 2 — prestige effect |
| E2-B | `e2_spearman_vs_gamma.png` | Exp 2 |
| E2-C | `e2_network_snapshot.png` | Exp 2 |
| E3-A | `e3_network_4panel.png` | Exp 3 — dialect contact |
| E3-B | `e3_cross_community_distance.png` | Exp 3 |
| E3-C | `e3_merger_time_bar.png` | Exp 3 |
| A-all | `ablation_boxplot.png` | Ablations |
| V1 | `scurve.png` | S-curve validation |
| H1 | `heatmap_convergence_theta.png` | Heatmap 1 |
| H2 | `heatmap_diversity_gamma.png` | Heatmap 2 |
| GIF | `diffusion.gif` | Animated |

**Heatmap parallelisation:**
```python
# experiments/heatmaps.py uses ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor

def run_single(config):
    G = make_network(config)
    model = MosaicModel(config, G)
    logger = DataLogger(config)
    return model.run(logger)

with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
    results = list(executor.map(run_single, all_configs))
```

**Entry criteria:** Plan 3 complete (all tests green).

**Exit criteria:**
- All 13 PNG figures exist in `results/figures/` at 300 DPI
- `diffusion.gif` exists and file size < 5MB
- S-curve R² > 0.85 (logged in experiment output)
- BA topology mean convergence time < ER topology (AC4)
- All `mvp.md` AC2–AC9 pass

**Dependencies:** Plans 1–3.

**Risks:**

| Risk | Mitigation |
|---|---|
| Heatmap 1,000 runs slow | `ProcessPoolExecutor` from the start; estimate 15–30min on 8 cores |
| GIF > 5MB | N=100 agents, 60 frames, 20fps; use `optimize=True` + `quantize` in Pillow |
| S-curve R² < 0.85 | Adjust θ upward (0.35) before running; document in `progress.md` |
| scipy curve_fit fails on non-logistic data | Catch `OptimizeWarning`; log R²=-1 as sentinel; flag run |

---

### Plan 5 — ML Analysis Layer

**Purpose:**
Build the Phase 2 analysis pipeline: unsupervised dialect zone discovery,
GCN-based accent trajectory prediction, and UMAP accent space visualisation.
Write `ml-pipeline.md` from the actual implementation.

**Scope (includes):**
- `analysis/data_loader.py`, `analysis/clustering.py`, `analysis/gcn.py`, `analysis/evaluate.py`, `analysis/umap_viz.py`
- Training on 80 runs from Experiment 1 (4 topologies × 25 runs = 100 total; 80/20 split at run level)
- All 3 ML figures
- `project-docs/ml-pipeline.md`

**Scope (excludes):**
- SHAP (completely out of scope)
- API integration (Plan 6)
- Real speech data

**Exact Deliverables:**

`analysis/clustering.py`:
```python
def cluster_final_accents(
    run_id: str,
    runs_dir: str = "runs",
    k_range: range = range(2, 6)
) -> dict:
    """
    Apply k-means for each k in k_range, select best k by silhouette score.
    Also applies DBSCAN as validation.
    Returns: {"best_k": int, "labels": np.ndarray, "silhouette": float,
              "davies_bouldin": float, "ari": float}
    """
```

`analysis/gcn.py`:
```python
class AccentGCN(nn.Module):
    """2-layer GCN. in_channels=9, hidden=32, num_classes=5."""

class AccentMLP(nn.Module):
    """Same architecture as GCN but ignores edge_index."""

def train_model(
    model: nn.Module,
    train_data: list[Data],
    epochs: int = 100,
    lr: float = 0.01
) -> list[float]:
    """Returns list of per-epoch loss values."""

def predict(model: nn.Module, data: Data) -> np.ndarray:
    """Returns (N,) integer predicted cluster labels."""

def run_experiment(
    train_ids: list[str],
    test_ids: list[str],
    runs_dir: str = "runs"
) -> dict:
    """
    Full GCN vs MLP training + evaluation pipeline.
    Returns: {"gcn": {...metrics}, "mlp": {...metrics},
              "gcn_loss_curve": list, "mlp_loss_curve": list}
    """
```

`analysis/umap_viz.py`:
```python
def compute_umap_coords(
    run_id: str,
    runs_dir: str = "runs",
    n_timesteps: int = 4
) -> dict:
    """
    Compute 2D UMAP at 4 timesteps: t=0, T//3, 2T//3, t_conv.
    Saves to runs/{run_id}/umap_coords.json.
    Returns coords dict.
    """
```

**ML figures:**
- `results/figures/gcn_loss_curve.png` — GCN + MLP loss curves side by side
- `results/figures/gcn_confusion_matrix.png` — GCN confusion matrix heatmap
- `results/figures/umap_4panel.png` — UMAP scatter at 4 timesteps, coloured by cluster

**Training data setup:**
- Use all 100 runs from Experiment 1 (Exp 1 already generated them in Plan 4)
- `data_loader.build_pyg_dataset()` loads them into PyG `Data` objects
- Deterministic 80/20 split: runs 0–79 train, runs 80–99 test (sorted by run_id)

**Entry criteria:**
- Plans 1–4 complete
- ≥ 100 run directories present in `runs/` from Exp 1
- PyTorch Geometric importable: `python -c "import torch_geometric; print('OK')"`

**Exit criteria:**
- GCN accuracy and MLP accuracy both reported (null result is acceptable and documented)
- UMAP JSON files exist in at least one run directory
- `results/figures/umap_4panel.png` shows visible accent space change over time
- `project-docs/ml-pipeline.md` written and committed

**Dependencies:** Plans 1–4.

**Risks:**

| Risk | Mitigation |
|---|---|
| GCN does not outperform MLP | Document null result — still answers RQ3 empirically |
| PyG Data batching across varied N | Use `DataLoader(dataset, batch_size=1)` to avoid padding issues — each graph is one run |
| UMAP non-determinism | Always pass `random_state=config.seed` |
| k-means label permutation across runs | Use ARI instead of raw accuracy for cross-run comparison; standardise label assignment by majority vote |

---

### Plan 6 — FastAPI Backend

**Purpose:**
Expose the simulation over HTTP so the React frontend can trigger runs and
retrieve results. No database — all state in the `runs/` filesystem.

**Scope (includes):**
- `api/main.py` with 4 endpoints
- `api/schemas.py` with full Pydantic models
- CORS configuration
- Manual endpoint verification

**Scope (excludes):**
- Authentication (out of scope per `prd.md §5`)
- Async simulation (synchronous is sufficient for T≤10,000)
- Production deployment

**Exact Deliverables:**

`api/schemas.py`:
```python
class RunRequest(BaseModel):
    N: int = 200
    topology: str = "watts_strogatz"
    T: int = 10000
    gamma: float = 1.0
    theta: float = 0.30
    sigma: float = 0.01
    seed: int = 42

class AgentState(BaseModel):
    agent_id: int
    accent: list[float]       # length 6
    community_id: int
    centrality: float
    cluster_id: int

class TimelinePoint(BaseModel):
    timestep: int
    diversity: float
    pairwise_distance: float

class NetworkNode(BaseModel):
    id: int
    community_id: int
    centrality: float

class NetworkEdge(BaseModel):
    source: int
    target: int

class RunResult(BaseModel):
    run_id: str
    config: dict
    metrics: dict
    timeline: list[TimelinePoint]
    final_agent_states: list[AgentState]
    network: dict              # {"nodes": [...], "edges": [...]}
```

`api/main.py` — endpoints:
```
POST  /run              → RunResult
GET   /results/{run_id} → RunResult (from disk) | 404
GET   /umap/{run_id}    → dict (umap_coords.json) | 404
GET   /topologies       → list[dict]  # topology metadata
```

**`POST /run` implementation:**
```python
@app.post("/run")
def run_simulation(request: RunRequest) -> RunResult:
    config = SimConfig(**request.dict())
    G = make_network(config)
    model = MosaicModel(config, G)
    logger = DataLogger(config)
    metrics = model.run(logger)
    return _build_result(config, G, model, logger, metrics)
```

**`_build_result` constructs:**
- `timeline`: read `agent_states.csv` grouped by timestep → compute D(t) and H(t) per timestep
- `final_agent_states`: load last timestep, add `cluster_id` from k-means on final accents
- `network`: serialise `G.nodes` and `G.edges` with attributes

**CORS:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Entry criteria:** Plans 1–2 complete (simulation importable).

**Exit criteria:**
- `uvicorn api.main:app --reload` starts without errors
- `curl -X POST localhost:8000/run -H "Content-Type: application/json" -d '{}'` returns valid JSON in < 60s
- `curl localhost:8000/topologies` returns list of 4 topology dicts
- `curl -H "Origin: http://localhost:5173" localhost:8000/run ...` response includes CORS headers

**Dependencies:** Plans 1–2. Plan 5 optional (UMAP endpoint returns 404 if not computed).

**Risks:**

| Risk | Mitigation |
|---|---|
| Synchronous run blocks event loop | Acceptable for ≤60s runs; document in API README |
| Large response payload (N=200, all timesteps) | Timeline is logged every 100 steps → max 100 timeline points. Fine. |
| Run ID collision | `{topology}_{seed}` is deterministic — same inputs produce same run_id, logger overwrites directory |

**Tests:** `tests/test_api.py` using `httpx.TestClient`:
- POST /run with defaults → 200, all fields present
- POST /run with invalid topology → 422
- GET /results/{valid_id} → 200
- GET /results/{invalid_id} → 404
- GET /topologies → 200, list of 4

> Note: `test_api.py` added to test suite in this plan, pushing total tests to ≥ 33.

---

### Plan 7 — React Frontend

**Purpose:**
Build the interactive web interface per `architecture.md §6` and `design.md`.
Pure visualisation and control layer — no simulation logic in the frontend.

**Scope (includes):**
- Full Vite + React scaffold
- 4 components fully implemented
- Complete design token application from `design.md`
- All user flows: run simulation → see results
- Loading + error states

**Scope (excludes):**
- Mobile responsiveness (desktop-only per `design.md §15`)
- Dark mode (explicitly excluded per `design.md §19`)
- Unit tests (manual E2E is sufficient for this scale)

**Exact Deliverables:**

`frontend/src/index.css`:
- All CSS custom properties from `design.md §18`
- Base body typography: `font-family: var(--font-diatype)`, `background: var(--surface-canvas)`, `color: var(--color-ink)`

`frontend/src/App.jsx`:
```jsx
// State:
// config: {topology, N, T, gamma, theta, sigma}  (default values from SimConfig)
// loading: boolean
// result: null | RunResult
// error: null | string

// Layout: single-column on load, 2-panel after first result
// (ControlPanel left, [NetworkGraph + TimeSeries + UMAPScatter] right)
```

`frontend/src/components/ControlPanel.jsx`:
- Input fields: topology (select), N (number, 50–500), T (number, 1000–20000),
  gamma (range 0–2, step 0.1), theta (range 0.05–0.5, step 0.05), sigma (range 0–0.05, step 0.005)
- Run button: primary dark button, disabled + shows "RUNNING…" while loading
- All labels: 11px Diatype Mono uppercase per `design.md §12`

`frontend/src/components/NetworkGraph.jsx`:
- D3.js force simulation; nodes = agents; edges = network connections
- Node size: `3 + agent.centrality * 12`
- Node fill: categorical colour scale mapped to `cluster_id` (5 clusters → 5 colours)
- Hover tooltip: `agent_id`, `centrality`, `community_id`, accent dims
- D3 owns SVG via `useRef` + `useEffect`; React never touches SVG DOM directly
- Zoom + pan via `d3.zoom()`

`frontend/src/components/TimeSeries.jsx`:
- Recharts `LineChart`; two lines: diversity (solid) and pairwise_distance (dashed)
- X-axis: timestep; Y-axis: value
- Legend: 11px Diatype Mono uppercase per design.md
- Grid lines: `--color-paper-warm`

`frontend/src/components/UMAPScatter.jsx`:
- Rendered with D3 (not Recharts — scatter with custom node sizing)
- Timestep slider: 4 discrete positions (t=0, T//3, 2T//3, t_conv)
- Points coloured by cluster_id (same colour scale as NetworkGraph)
- Shows "UMAP not available" if `/umap/{run_id}` returns 404

**API calls:**
```javascript
// All in App.jsx
const API = "http://localhost:8000"

const runSimulation = async (config) => {
    setLoading(true);
    setError(null);
    try {
        const res = await fetch(`${API}/run`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(config)
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        setResult(data);
        // Fetch UMAP separately (may 404)
        const umapRes = await fetch(`${API}/umap/${data.run_id}`);
        if (umapRes.ok) setUmapData(await umapRes.json());
    } catch (e) {
        setError(e.message);
    } finally {
        setLoading(false);
    }
};
```

**Entry criteria:** Plan 6 complete and API returns valid responses.

**Exit criteria:**
- `http://localhost:5173` renders full UI without console errors
- Run from frontend → all 3 visualisations populate within 60s
- NetworkGraph nodes vary in size by centrality
- UMAPScatter slider switches between 4 accent space snapshots (or shows "not available")
- Design matches `design.md` (Ink fills, 9px radius, Diatype Mono labels)
- No hardcoded hex values in any `.jsx` or `.css` file — all via CSS custom properties

**Dependencies:** Plan 6 (API must be running).

**Risks:**

| Risk | Mitigation |
|---|---|
| D3 + React DOM conflict | Strict: D3 only inside `useEffect`, only touches ref'd SVG. React never sets SVG children directly. |
| Node cluster colours not consistent | Define colour scale once in a shared `utils/colours.js` constant; import in both NetworkGraph and UMAPScatter |
| Response payload timing (60s wait) | Show progress text "Simulation running… (~60s)" during loading |
| CORS error on first run | Verify Plan 6 CORS config before starting frontend |

---

### Plan 8 — Integration, Polish, and Demo Notebook

**Purpose:**
Verify the complete system end-to-end, write the demo notebook, polish the
README, add the GIF embed, add GitHub Actions CI, and close all acceptance
criteria from `mvp.md §4`.

**Scope (includes):**
- `notebooks/demo.ipynb`
- Updated `README.md` with GIF + figures
- `.github/workflows/tests.yml` (pytest CI)
- Final `progress.md` update
- All AC1–AC10 verification

**Exact Deliverables:**

`notebooks/demo.ipynb` — cells:
1. Title + description (Markdown)
2. Imports + SimConfig definition
3. Build WS network, run single simulation
4. Plot diversity time series
5. Plot network snapshot coloured by cluster
6. Run 3-topology comparison (ER/WS/BA, 5 runs each — small for demo speed)
7. Plot comparative convergence boxplot
8. Conclusion + next steps

`tests.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: "3.11"}
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

**Entry criteria:** Plans 1–7 complete.

**Exit criteria:**

| Acceptance Criterion | How verified |
|---|---|
| AC1: ≥ 20 tests pass | `pytest tests/ -v` — all ≥ 33 green |
| AC2: Single run < 60s | `time python -m simulation.runner` |
| AC3: Diversity decreases | Check `results/summary.csv` |
| AC4: BA faster than ER | Check Exp 1 summary |
| AC5: S-curve R² > 0.85 | Check experiment output |
| AC6: GIF generated | Visual review |
| AC7: Heatmap trend | Visual review |
| AC8: demo.ipynb runs | `jupyter nbconvert --to notebook --execute notebooks/demo.ipynb` |
| AC9: Seed reproducible | `diff` two runs with same seed |
| AC10: README complete | Review on GitHub |

**Dependencies:** Plans 1–7.

---

## Part 5 — Execution Order and Parallelism

```
Plan 1: Foundation                     (no deps)
    │
Plan 2: Simulation Engine              (after Plan 1)
    │
Plan 3: Unit Tests                     (after Plan 2)
    │
    ├─── Plan 4: Experiments + Viz     (after Plan 3)
    │        │
    │    Plan 5: ML Layer              (after Plan 4)
    │
    └─── Plan 6: API Backend           (after Plan 2, can run parallel to Plan 4)
             │
         Plan 7: Frontend              (after Plan 6)
             │
         Plan 8: Integration           (after Plans 4, 5, 7)
```

**Parallelism note:** Plans 4 and 6 can proceed simultaneously after Plan 3.
Plan 5 requires Plan 4's run outputs. Plan 7 requires Plan 6's API.
Do not start Plan 8 until Plans 4, 5, and 7 are all complete.

---

## Part 6 — Architecture Decisions Summary

| Decision | Choice | Rationale |
|---|---|---|
| `metrics.py` as separate module | Yes | Pure functions; independently testable; shared by model + experiment scripts |
| `analysis/data_loader.py` | Yes | Clean Phase 1→2 boundary; encapsulates all CSV parsing for ML layer |
| `viz/` as separate package | Yes | Visualization ≠ experiment orchestration; reusable across experiments |
| `analysis/evaluate.py` | Yes | Evaluation logic separate from model architecture |
| SHAP analysis | Excluded | Out of scope; adds complexity without serving an RQ |
| CSS strategy | Single `index.css` | Simpler than CSS Modules for a 4-component app |
| Run ID format | `{topology}_{seed}` | Deterministic, reproducible, readable |
| GIF parameters | N=100, 60 frames, 20fps | ~2–4MB, renders on GitHub |
| Simulation async | No — synchronous | ≤60s is acceptable; async adds complexity for no user benefit |
| CI/CD | GitHub Actions pytest | Simple, standard, no additional services |
| Mesa scheduler | Not used | Edge-based scheduling is implemented directly in `MosaicModel.step()` |
| k-means in model | Refit every 500 steps | Balance between accuracy and performance |
