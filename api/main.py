"""
api/main.py
===========
FastAPI application for the Mosaic backend.
"""
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import analysis._umap_compat  # Shim to fix tensorflow issue
import umap

from api.schemas import (
    RunRequest,
    RunResponse,
    NetworkNode,
    NetworkEdge,
    NetworkData,
    AgentState,
    TimelineEntry,
    MetricsData,
)
from simulation.config import SimConfig
from simulation.network import make_network
from simulation.runner import run_single

log = logging.getLogger(__name__)

# Base directory for runs
RUNS_ROOT = Path("runs")
RESULTS_ROOT = Path("results")
FIGURES_ROOT = RESULTS_ROOT / "figures"
import os
os.makedirs(str(RUNS_ROOT), exist_ok=True)

app = FastAPI(title="Mosaic API", version="1.0.0")

EXPERIMENTS = {
    "topology": {
        "title": "Topology comparison",
        "summary": "Compare how random, small-world, scale-free, and community-structured networks shape diversity and convergence.",
        "figures": ["e1_diversity_timeseries.png", "e1_convergence_boxplot.png", "e1_final_diversity_bar.png"],
    },
    "prestige": {
        "title": "Prestige and centrality",
        "summary": "Test whether highly connected speakers exert more influence as prestige weighting increases.",
        "figures": ["e2_centrality_vs_influence.png", "e2_spearman_vs_gamma.png", "e2_network_snapshot.png"],
    },
    "contact": {
        "title": "Two-community contact",
        "summary": "Track how bridge density affects merger between initially distinct communities.",
        "figures": ["e3_network_4panel.png", "e3_cross_community_distance.png", "e3_merger_time_bar.png"],
    },
    "validation": {
        "title": "Model validation",
        "summary": "Inspect ablations, logistic adoption, and parameter landscapes used to check model behavior.",
        "figures": ["ablation_boxplot.png", "scurve.png", "heatmap_convergence_theta.png", "heatmap_diversity_gamma.png"],
    },
}

# Enable CORS for frontend.
# EC2 production: nginx serves React on the same origin, so /api/* proxy
# requests arrive without an Origin header — CORS middleware is not invoked.
# Local dev origins are listed explicitly.
# GitHub Pages showcase: read-only, no POST /run from that origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",          # vite preview
        "https://adityawagh19.github.io", # GitHub Pages showcase (read-only)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/topologies")
def get_topologies():
    """Return supported topologies, human-readable labels, and their specific parameters."""
    return {
        "er": {"label": "Erdős–Rényi", "desc": "Erdős–Rényi random graph", "params": ["p_er"]},
        "watts_strogatz": {"label": "Watts-Strogatz", "desc": "Watts-Strogatz small world", "params": ["k_ws", "p_rewire"]},
        "ba": {"label": "Barabási-Albert", "desc": "Barabási-Albert scale-free", "params": ["m_ba"]},
        "sbm": {"label": "Stochastic block model", "desc": "Two-community stochastic block model", "params": ["p_in", "p_out"]},
    }


@app.get("/config/schema")
def get_config_schema():
    """UI metadata for configuration controls; mirrors the public RunRequest contract."""
    return {
        "version": 1,
        "defaults": RunRequest().model_dump(),
        "fields": {
            "N": {"label": "Agents", "help": "Number of speakers in the network.", "min": 5, "max": 2000, "step": 10},
            "T": {"label": "Maximum steps", "help": "Stops early only when every agent accent is within the model's consensus tolerance.", "min": 100, "max": 100000, "step": 100},
            "gamma": {"label": "Prestige weight", "help": "Influence advantage of well-connected speakers.", "min": 0, "max": 2, "step": 0.1},
            "theta": {"label": "Confidence bound", "help": "Largest accent difference that still permits accommodation.", "min": 0.05, "max": 0.5, "step": 0.05},
            "sigma": {"label": "Phonetic drift", "help": "Random variation added during accommodation.", "min": 0, "max": 0.05, "step": 0.01},
            "initial_sigma": {"label": "Initial spread", "help": "Initial accent vector spread across the population.", "min": 0.05, "max": 0.5, "step": 0.05},
            "W": {"label": "Stationarity window", "help": "Window of logged timesteps to monitor for stationarity.", "min": 5, "max": 100, "step": 5},
            "epsilon_max": {"label": "Stationarity tolerance", "help": "Maximum permitted agent displacement over the window W to declare stationarity.", "min": 1e-6, "max": 1e-2, "step": 1e-5},
            "epsilon_distance": {"label": "Consensus tolerance", "help": "Maximum pairwise distance tolerance to declare absolute consensus.", "min": 1e-8, "max": 1e-2, "step": 1e-6},
            "p_er": {"label": "Connection probability", "help": "Chance of a tie between two speakers.", "min": 0.01, "max": 1, "step": 0.01},
            "k_ws": {"label": "Nearest neighbours", "help": "Initial local ties per speaker.", "min": 2, "max": 200, "step": 2},
            "p_rewire": {"label": "Rewiring probability", "help": "Chance a local tie becomes a shortcut.", "min": 0, "max": 1, "step": 0.05},
            "m_ba": {"label": "Links per new speaker", "help": "Controls hub formation.", "min": 1, "max": 100, "step": 1},
            "p_in": {"label": "Within-community ties", "help": "Chance of a tie within a community.", "min": 0.01, "max": 1, "step": 0.01},
            "p_out": {"label": "Between-community ties", "help": "Chance of a bridge between communities.", "min": 0, "max": 1, "step": 0.01},
            "seed": {"label": "Random seed", "help": "Reuse to reproduce a configuration.", "min": 0, "max": 2147483647, "step": 1},
        },
    }


@app.get("/runs")
def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    topology: str | None = None,
    cursor: str | None = None,
):
    """List locally persisted runs for the archive and comparison picker."""
    items = []
    for run_dir in RUNS_ROOT.iterdir() if RUNS_ROOT.exists() else []:
        if not run_dir.is_dir():
            continue
        try:
            with open(run_dir / "config.json") as fh:
                config = json.load(fh)
            with open(run_dir / "metrics.json") as fh:
                metrics = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if topology and config.get("topology") != topology:
            continue
        items.append({
            "run_id": run_dir.name,
            "topology": config.get("topology"),
            "seed": config.get("seed"),
            "N": config.get("N"),
            "T": config.get("T"),
            "gamma": config.get("gamma"),
            "theta": config.get("theta"),
            "sigma": config.get("sigma"),
            "converged": metrics.get("converged"),
            "convergence_time": metrics.get("convergence_time"),
            "final_diversity": metrics.get("final_diversity"),
            "final_pairwise_distance": metrics.get("final_pairwise_distance"),
        })
    items.sort(key=lambda item: item["run_id"], reverse=True)
    if cursor:
        items = [item for item in items if item["run_id"] < cursor]
    page = items[:limit]
    return {"items": page, "total": len(items), "next_cursor": page[-1]["run_id"] if len(items) > limit else None}


@app.get("/runs/{run_id}/export")
def export_run(run_id: str, format: str = Query(default="json", pattern="^(json|csv)$")):
    """Download a self-contained result summary or the logged agent-state CSV."""
    run_dir = RUNS_ROOT / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found.")
    if format == "csv":
        path = run_dir / "agent_states.csv"
        return FileResponse(path, media_type="text/csv", filename=f"{run_id}-agent-states.csv")
    
    return JSONResponse(content=_construct_run_response(run_id).model_dump())


@app.get("/runs/{run_id}/snapshots")
def get_snapshots(run_id: str, timesteps: str | None = None):
    """Return selected raw agent-state snapshots for playback or data inspection."""
    run_dir = RUNS_ROOT / run_id
    csv_path = run_dir / "agent_states.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Run or agent-state data not found.")
    df = pd.read_csv(csv_path)
    available = sorted(int(value) for value in df["timestep"].unique())
    requested = available
    if timesteps:
        try:
            requested = sorted({int(value) for value in timesteps.split(",")})
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="timesteps must be a comma-separated list of integers.") from exc
        requested = [value for value in requested if value in available]
    snapshots = []
    for timestep in requested:
        rows = df[df["timestep"] == timestep].sort_values("agent_id")
        snapshots.append({"timestep": timestep, "agents": rows.to_dict(orient="records")})
    return {"run_id": run_id, "available_timesteps": available, "snapshots": snapshots}


@app.get("/experiments")
def list_experiments():
    """Return the curated offline experiment archive and its available figures."""
    return {
        "items": [
            {"id": experiment_id, **experiment, "available": [name for name in experiment["figures"] if (FIGURES_ROOT / name).exists()]}
            for experiment_id, experiment in EXPERIMENTS.items()
        ]
    }


@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    experiment = EXPERIMENTS.get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    return {"id": experiment_id, **experiment, "available": [name for name in experiment["figures"] if (FIGURES_ROOT / name).exists()]}


@app.get("/figures/{filename}")
def get_figure(filename: str):
    """Serve only curated generated figures; never expose arbitrary filesystem paths."""
    allowed = {name for experiment in EXPERIMENTS.values() for name in experiment["figures"]}
    allowed.update({"gcn_vs_mlp_accuracy.png", "gcn_vs_mlp_loss.png", "cluster_map.png", "umap_4panel.png"})
    if filename not in allowed or not (FIGURES_ROOT / filename).is_file():
        raise HTTPException(status_code=404, detail="Figure not found.")
    return FileResponse(FIGURES_ROOT / filename, media_type="image/png", filename=filename)


@app.get("/analysis/summary")
def get_analysis_summary():
    """Expose validated offline ML metrics and the figure manifest for the ML page."""
    path = RESULTS_ROOT / "ml_results.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="ML analysis has not been generated.")
    with open(path) as fh:
        data = json.load(fh)
    data["figures"] = [name for name in ["gcn_vs_mlp_accuracy.png", "gcn_vs_mlp_loss.png", "cluster_map.png", "umap_4panel.png"] if (FIGURES_ROOT / name).exists()]
    return data


def _construct_run_response(run_id: str) -> RunResponse:
    """Helper to read saved files and construct the full RunResponse."""
    run_dir = RUNS_ROOT / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found.")

    canonical_path = run_dir / "canonical_run.json"
    if not canonical_path.exists():
        raise HTTPException(status_code=500, detail="Run is missing canonical artifact. Old runs may need to be deleted.")

    with open(canonical_path) as f:
        canonical = json.load(f)

    # 1. Config
    config_dict = canonical["config"]
    
    # 2. Metrics
    metrics_dict = canonical["metrics"]
    
    # 3. Timeline
    timeline_list = canonical["timeline"]
    
    # 4. Network
    network_data = NetworkData(
        nodes=[NetworkNode(**n) for n in canonical["network"]["nodes"]],
        edges=[NetworkEdge(**e) for e in canonical["network"]["edges"]]
    )
    
    # 5. Final Agent States (with cluster_id injected from KMeans for Phase 5)
    # We still need cluster_ids for the frontend. We can compute them here fast, or store them in canonical.
    # Let's compute it once and serve it.
    snapshots = canonical["snapshots"]
    final_snapshot = snapshots[-1]
    
    from sklearn.cluster import KMeans
    import numpy as np
    X_final = np.array([a["accent"] for a in sorted(final_snapshot["agents"], key=lambda x: x["agent_id"])])
    kmeans = KMeans(n_clusters=5, random_state=config_dict.get("seed", 42), n_init=10)
    cluster_ids = kmeans.fit_predict(X_final)
    
    agent_states = []
    for i, agent in enumerate(sorted(final_snapshot["agents"], key=lambda x: x["agent_id"])):
        agent_states.append(
            AgentState(
                agent_id=agent["agent_id"],
                accent=agent["accent"],
                community_id=agent["community_id"],
                centrality=agent["centrality"],
                cluster_id=int(cluster_ids[i])
            )
        )

    return RunResponse(
        run_id=run_id,
        config=config_dict,
        metrics=MetricsData(**metrics_dict),
        timeline=[TimelineEntry(**t) for t in timeline_list],
        final_agent_states=agent_states,
        network=network_data,
    )


@app.post("/run", response_model=RunResponse)
def run_simulation(req: RunRequest):
    """Run a simulation synchronously and return the full results."""
    # Convert request to SimConfig
    config = SimConfig.from_dict(req.model_dump())
    
    # Run the simulation (synchronous, <60s for N=200)
    log.info("Starting simulation run: %s", config.run_id)
    metrics = run_single(config)
    run_id = metrics["run_id"]
    log.info("Simulation completed: %s", run_id)
    
    # Construct response from saved artifacts
    return _construct_run_response(run_id)


@app.post("/run/stream")
def run_simulation_stream(req: RunRequest):
    """Run a simulation and stream progress chunks via NDJSON."""
    from fastapi.responses import StreamingResponse
    config = SimConfig.from_dict(req.model_dump())
    
    log.info("Starting simulation stream: %s", config.run_id)
    
    def generate():
        from simulation.runner import run_single_stream
        for chunk_str in run_single_stream(config):
            if '"event": "complete"' in chunk_str:
                import json
                chunk = json.loads(chunk_str)
                run_id = chunk["data"]["run_id"]
                full_res = _construct_run_response(run_id).model_dump()
                yield json.dumps({"event": "complete", "data": full_res}) + "\n"
            else:
                yield chunk_str
            
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={"X-Accel-Buffering": "no"}
    )

@app.get("/results/{run_id}", response_model=RunResponse)
def get_results(run_id: str):
    """Retrieve the results of a previously completed run."""
    return _construct_run_response(run_id)


@app.get("/umap/{run_id}")
def get_umap(run_id: str):
    """
    Get UMAP coordinates for 4 timesteps: [0, T/3, 2T/3, t_final].
    Reads directly from canonical artifact where it's pre-computed.
    """
    run_dir = RUNS_ROOT / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found.")
        
    canonical_path = run_dir / "canonical_run.json"
    if not canonical_path.exists():
        raise HTTPException(status_code=500, detail="Missing canonical artifact. Old runs may need to be deleted.")
        
    with open(canonical_path) as f:
        canonical = json.load(f)
        
    return canonical.get("umap", {})
