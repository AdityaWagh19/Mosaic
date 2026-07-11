# Mosaic

People change how they speak depending on who they talk to. Over time, those small
shifts accumulate into dialects — whole communities that sound like each other and
different from everyone else. Mosaic simulates that process.

Give it a population of speakers, a social network, and a set of rules about who
influences whom. Watch accents drift, cluster, and either converge or hold their
ground — depending entirely on how the network is shaped.

Built with Python (Mesa, NetworkX, PyTorch), analyzed with a Graph Convolutional
Network, and explored through a full-stack React web interface.

---

## How It Works

Each agent holds a 6-dimensional accent vector representing real phonetic features
(vowel formants, voice onset time, speaking rate). At every timestep, two connected
agents have a conversation. The listener shifts their accent slightly toward the
speaker — but only if they are socially similar enough, and weighted by how
influential the speaker is.

Run this for thousands of interactions across hundreds of agents, and dialect zones
emerge on their own. No rules about which accent "wins" — just local interactions
producing global structure.

---

## Research Questions

**RQ1 — Topology:**
How does the shape of the social network affect how quickly and completely accents converge?

**RQ2 — Prestige:**
Do well-connected speakers — the social hubs — actually drive more accent change than peripheral ones?

**RQ3 — Predictability:**
Can a Graph Convolutional Network predict where an agent's accent will end up, just from their starting position in the network?

---

## Key Results

| Finding | Value |
|---|---|
| Fastest convergence topology | Barabási-Albert (mean t=8,908 steps) |
| Slowest / no convergence | Erdős-Rényi and SBM (hit T=10,000) |
| Prestige-centrality correlation (Spearman ρ) | ~0 — topology mediates influence, not raw centrality |
| MLP accent-cluster prediction accuracy | **89.2%** (initial position predicts final cluster) |
| GCN accent-cluster prediction accuracy | 51.1% (over-smoothing dilutes fine-grained signal) |
| k-means silhouette on final accent space | 0.089 — continuous distribution, no discrete zones |
| S-curve logistic adoption R² | 0.9349 |

---

## System Architecture

Four independent layers:

```
┌─────────────────────────────────────┐
│  Simulation Layer  (Python)         │
│  SimConfig → Network → Model → Log  │
└──────────────────┬──────────────────┘
                   │ CSV + JSON (runs/)
┌──────────────────▼──────────────────┐
│  Analysis Layer  (Python)           │
│  clustering → GCN/MLP → UMAP        │
└──────────────────┬──────────────────┘
                   │ REST API
┌──────────────────▼──────────────────┐
│  API Layer  (FastAPI, port 8000)    │
│  10 endpoints — run, results, umap, │
│  experiments, figures, analysis     │
└──────────────────┬──────────────────┘
                   │ HTTP + CORS
┌──────────────────▼──────────────────┐
│  Frontend  (React + Vite, port 5173)│
│  Landing · Simulator · Experiments  │
│  Compare · ML Analysis              │
└─────────────────────────────────────┘
```

---

## Network Topologies

| Topology | Structure | What it produces |
|---|---|---|
| Erdős-Rényi | Random edges | Moderate convergence, high run-to-run variance |
| Watts-Strogatz | High clustering, short paths | Preserves local dialect diversity; slow global spread |
| Barabási-Albert | Power-law degree, few dominant hubs | Fast convergence driven by influential speakers |
| Stochastic Block Model | Two explicit communities | Two-phase convergence: fast within, slow between communities |

---

## Technology Stack

| Layer | Technology |
|---|---|
| Agent-based model | Mesa, NetworkX, NumPy |
| Data pipeline | pandas |
| Machine learning | PyTorch 2.4.1, PyTorch Geometric 2.6.1 |
| Dimensionality reduction | umap-learn |
| Visualisation | matplotlib, seaborn |
| API backend | FastAPI, uvicorn |
| Frontend | React 18, Vite 6, TypeScript 5 |
| Routing | react-router-dom v7 |
| Graph viz | D3.js |
| Charts | Recharts |
| Testing | pytest |

---

## Project Structure

```
Mosaic/
├── simulation/        # Core ABM — config, network, agent, model, logger, runner, metrics
├── analysis/          # ML pipeline — clustering, GCN, MLP, UMAP
├── experiments/       # Four experiments + ablations + heatmaps + run_all.py
├── viz/               # matplotlib figure functions + diffusion GIF generator
├── api/               # FastAPI backend (main.py + schemas.py)
├── frontend/          # React + Vite app (src/ with pages, components, hooks, contexts)
├── tests/             # pytest unit + integration tests (59 tests)
├── results/
│   ├── figures/       # 19 PNG/GIF research outputs (tracked in git)
│   └── ml_results.json
├── runs/              # Auto-generated simulation outputs (gitignored)
├── research/          # Background literature notes
├── notebooks/         # demo.ipynb (Phase 8)
└── project-docs/      # All specification and design documents
```

---

## Installation

**Prerequisites:** Python 3.11+, Node.js 18+, Git

```bash
git clone https://github.com/AdityaWagh19/Mosaic.git
cd Mosaic

# Python environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

---

## Running the Web Interface

```bash
# Terminal 1 — start the API
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — start the frontend
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

The frontend connects to the API automatically. Configure the simulation,
run it, and explore the results across four tabs: time series, network graph,
UMAP accent space, and raw data export.

---

## Running Experiments

```bash
# Run all four experiments + ablations + heatmaps (≈ 8 minutes on CPU)
python -m experiments.run_all

# Run a single simulation
python -m simulation.runner

# Run a specific experiment
python -m experiments.exp1_topology
```

All figures are saved to `results/figures/` at 300 DPI.

---

## Running Tests

```bash
pytest tests/ -v
# 59 tests, 0 failures
```

---

## Programmatic Use

```python
from simulation.config import SimConfig
from simulation.network import make_network
from simulation.model import MosaicModel
from simulation.logger import DataLogger

config = SimConfig(topology="watts_strogatz", N=200, T=10000, gamma=1.0, theta=0.30)
G = make_network(config)
logger = DataLogger(config)
model = MosaicModel(config, G)
metrics = model.run(logger)

print(f"Converged: {metrics['converged']} at step {metrics['convergence_time']}")
print(f"Final diversity: {metrics['final_diversity']:.3f}")
```

---

## API Reference

The backend exposes 10 endpoints at `http://localhost:8000`. Interactive docs available at `http://localhost:8000/docs`.

| Method | Path | Description |
|---|---|---|
| `POST` | `/run` | Run simulation; returns full result payload |
| `GET` | `/results/{run_id}` | Retrieve a previously completed run |
| `GET` | `/umap/{run_id}` | UMAP coordinates for 4 timesteps |
| `GET` | `/runs` | Paginated list of persisted runs |
| `GET` | `/runs/{id}/export` | Download JSON summary or agent-state CSV |
| `GET` | `/runs/{id}/snapshots` | Agent-state snapshots for playback |
| `GET` | `/experiments` | Curated offline experiment archive |
| `GET` | `/figures/{filename}` | Serve a research figure |
| `GET` | `/analysis/summary` | ML benchmark results |
| `GET` | `/config/schema` | UI field metadata |

---

## Documentation

All design decisions and specifications in `project-docs/`:

| Document | Contents |
|---|---|
| `context.md` | Project identity, research questions, non-goals |
| `model.md` | Full mathematical specification of the ABM |
| `architecture.md` | Module specs, API contract, frontend component map |
| `prd.md` | Functional requirements per phase (with completion status) |
| `design.md` | Frontend design system and UI specification |
| `experiments.md` | Pre-specified experimental design and metrics |
| `ml-pipeline.md` | ML architecture, training procedure, full results |
| `progress.md` | Running log of decisions and findings by phase |
| `tasks.md` | Living task tracker for all phases |
| `frontend-implementation-plan.md` | Detailed Phase 7 frontend implementation plan |

---

## Roadmap

| Phase | Status | Description |
|---|---|---|
| Phase 0 — Documentation | ✅ Complete | Project docs, design system |
| Phase 1 — Simulation Core | ✅ Complete | ABM, experiments, 14 figures |
| Phase 2 — ML Analysis | ✅ Complete | GCN, MLP, UMAP, clustering |
| Phase 3 — FastAPI Backend | ✅ Complete | 10 endpoints, Pydantic schemas |
| Phase 4 — React Frontend | ✅ Complete | 5 pages, D3, Recharts, mobile modal |
| Phase 5 — Repository Cleanup | ✅ Complete | Removed orphaned files |
| Phase 8 — Integration + Polish | 🔄 In progress | CI, demo notebook, error handling |

---

## License

MIT License
