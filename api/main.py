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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
import os
os.makedirs(str(RUNS_ROOT), exist_ok=True)

app = FastAPI(title="Mosaic API", version="1.0.0")

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
        "sbm": {"desc": "Stochastic Block Model", "params": ["n_communities", "p_in", "p_out"]},
    }


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
    run_single(config)
    log.info("Simulation completed: %s", config.run_id)
    
    # Construct response from saved artifacts
    return _construct_run_response(config.run_id)


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
            return json.load(f)
            
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
    
    coords_dict = {}
    for t in target_ts:
        X_t = df[df["timestep"] == t][accent_cols].values
        coords_t = reducer.transform(X_t)
        # Convert to standard python lists
        coords_dict[str(t)] = coords_t.tolist()
        
    with open(umap_path, "w") as f:
        json.dump(coords_dict, f)
        
    return coords_dict
