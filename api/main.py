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

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/topologies")
def get_topologies():
    """Return supported topologies and their specific parameters."""
    return {
        "er": {"desc": "Erdös-Rényi random graph", "params": ["p_er"]},
        "watts_strogatz": {"desc": "Watts-Strogatz small world", "params": ["k_ws", "p_rewire"]},
        "ba": {"desc": "Barabási-Albert scale-free", "params": ["m_ba"]},
        "sbm": {"desc": "Two-community stochastic block model", "params": ["p_in", "p_out"]},
    }


@app.get("/config/schema")
def get_config_schema():
    """UI metadata for configuration controls; mirrors the public RunRequest contract."""
    return {
        "version": 1,
        "defaults": RunRequest().model_dump(),
        "fields": {
            "N": {"label": "Agents", "help": "Number of speakers in the network.", "min": 5, "max": 2000, "step": 10},
            "T": {"label": "Maximum steps", "help": "Stops early if the diversity criterion stabilizes.", "min": 100, "max": 100000, "step": 100},
            "gamma": {"label": "Prestige weight", "help": "Influence advantage of well-connected speakers.", "min": 0, "max": 2, "step": 0.1},
            "theta": {"label": "Confidence bound", "help": "Largest accent difference that still permits accommodation.", "min": 0.05, "max": 0.5, "step": 0.05},
            "sigma": {"label": "Phonetic drift", "help": "Random variation added during accommodation.", "min": 0, "max": 0.05, "step": 0.01},
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

    with open(run_dir / "config.json") as f:
        config_dict = json.load(f)
    with open(run_dir / "metrics.json") as f:
        metrics_dict = json.load(f)
    with open(run_dir / "timeline.json") as f:
        timeline_list = json.load(f)

    # Reconstruct the config to build the network
    # We ignore unknown keys in case the config format changed
    config = SimConfig.from_dict(config_dict)
    
    # Read the final timestep from agent_states.csv
    csv_path = run_dir / "agent_states.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=500, detail="Missing agent_states.csv")
        
    df = pd.read_csv(csv_path)
    # Get only the last timestep
    final_t = df["timestep"].max()
    final_df = df[df["timestep"] == final_t]

    # Run kmeans to get cluster_ids (since Phase 5 expects them)
    # Or just use the dimensions to return to the frontend.
    # The MVP and Phase 3 spec says frontend needs `cluster_id`.
    # Let's perform k-means here if needed, or check if it's already in the CSV.
    # Wait, the simulation does NOT write cluster_id to agent_states.csv!
    # Phase 2 clustering adds it. Let's do a quick k-means to supply `cluster_id`.
    from sklearn.cluster import KMeans
    accent_cols = [f"d{i}" for i in range(6)]
    accents = final_df[accent_cols].values
    kmeans = KMeans(n_clusters=5, random_state=config.seed, n_init=10)
    cluster_ids = kmeans.fit_predict(accents)
    final_df = final_df.copy()
    final_df["cluster_id"] = cluster_ids

    agent_states = []
    for _, row in final_df.iterrows():
        agent_states.append(
            AgentState(
                agent_id=int(row["agent_id"]),
                accent=[float(row[c]) for c in accent_cols],
                community_id=int(row["community_id"]),
                centrality=float(row["centrality"]),
                cluster_id=int(row["cluster_id"]),
            )
        )

    # Reconstruct the network using the same seed
    G = make_network(config)
    
    nodes = []
    for n in G.nodes():
        nodes.append(
            NetworkNode(
                id=n,
                community_id=G.nodes[n]["community_id"],
                centrality=G.nodes[n]["centrality"],
            )
        )
        
    edges = []
    for u, v in G.edges():
        edges.append(NetworkEdge(source=u, target=v))
        
    network_data = NetworkData(nodes=nodes, edges=edges)

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


@app.get("/results/{run_id}", response_model=RunResponse)
def get_results(run_id: str):
    """Retrieve the results of a previously completed run."""
    return _construct_run_response(run_id)


@app.get("/umap/{run_id}")
def get_umap(run_id: str):
    """
    Get UMAP coordinates for 4 timesteps: [0, T/3, 2T/3, t_final].
    Computes them on-the-fly if missing and caches the result.
    """
    run_dir = RUNS_ROOT / run_id
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found.")
        
    umap_path = run_dir / "umap_coords.json"
    if umap_path.exists():
        with open(umap_path) as f:
            cached = json.load(f)
        if isinstance(cached, dict) and "snapshots" in cached:
            return cached
            
    # Need to compute UMAP
    csv_path = run_dir / "agent_states.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=500, detail="Missing agent_states.csv")
        
    df = pd.read_csv(csv_path)
    timesteps = sorted(df["timestep"].unique())
    if not timesteps:
        return {}
        
    final_t = timesteps[-1]
    
    # Pick 4 representative timesteps
    target_ts = [
        0,
        timesteps[max(1, len(timesteps)//3)],
        timesteps[max(1, 2*len(timesteps)//3)],
        final_t
    ]
    # Deduplicate and sort
    target_ts = sorted(list(set(target_ts)))
    
    # To keep UMAP consistent across timesteps, we fit on the union of these timesteps
    # or just fit on the final state and transform the others.
    # UMAP standard is to fit on the final state to establish cluster boundaries,
    # then transform the earlier states into that space.
    
    accent_cols = [f"d{i}" for i in range(6)]
    final_df = df[df["timestep"] == final_t]
    X_final = final_df[accent_cols].values
    
    # Use same config seed for reproducibility
    with open(run_dir / "config.json") as f:
        config = json.load(f)
    seed = config.get("seed", 42)
    
    reducer = umap.UMAP(n_components=2, random_state=seed, n_neighbors=15, min_dist=0.1)
    reducer.fit(X_final)
    
    snapshots = []
    for t in target_ts:
        timestep_df = df[df["timestep"] == t].sort_values("agent_id")
        X_t = timestep_df[accent_cols].values
        coords_t = reducer.transform(X_t)
        points = [
            {
                "agent_id": int(row.agent_id),
                "x": float(coords_t[index][0]),
                "y": float(coords_t[index][1]),
                "community_id": int(row.community_id),
            }
            for index, row in enumerate(timestep_df.itertuples(index=False))
        ]
        snapshots.append({"timestep": int(t), "points": points})

    response = {
        "run_id": run_id,
        "metadata": {
            "method": "UMAP",
            "n_neighbors": 15,
            "min_dist": 0.1,
            "fit_timestep": int(final_t),
        },
        "snapshots": snapshots,
    }

    with open(umap_path, "w") as f:
        json.dump(response, f)
        
    return response
