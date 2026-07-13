"""
simulation/runner.py
====================
MonteCarloRunner — executes n_runs independent simulation replicates.

Public API:
    run_monte_carlo(config: SimConfig) -> pd.DataFrame

Each replicate uses the same SimConfig but increments the seed by the
run index (seed + i for i in 0..n_runs-1), ensuring statistically
independent replicates while remaining fully reproducible.

Summary CSV (architecture.md §3.6):
    results/summary.csv
    Columns: run_id, topology, gamma, theta, sigma, seed, N,
             convergence_time, converged, final_diversity, final_pairwise_distance

__main__ entry point:
    python -m simulation.runner
    Runs 25 replicates of the default SimConfig and prints a summary.

Design notes (implementation plan §Plan 2):
    - DEFAULT: sequential loop — simple, debuggable, no subprocess overhead.
    - HEATMAP MODE: parallelised via ProcessPoolExecutor — used ONLY in
      experiments/heatmaps.py.  Do NOT parallelise here.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import replace
from pathlib import Path

import pandas as pd

from simulation.config import SimConfig
from simulation.logger import DataLogger
from simulation.model import MosaicModel
from simulation.network import make_network

logger = logging.getLogger(__name__)

_RESULTS_ROOT = Path("results")

# Columns written to summary.csv (architecture.md §3.6)
_SUMMARY_COLUMNS = [
    "run_id", "topology", "gamma", "theta", "sigma", "seed", "N",
    "convergence_time", "converged",
    "final_diversity", "final_pairwise_distance",
]


# ---------------------------------------------------------------------------
# Single-run helper (used by run_monte_carlo and by heatmaps.py)
# ---------------------------------------------------------------------------

def run_single(config: SimConfig) -> dict:
    """
    Execute one simulation run and return its metrics dict.

    Parameters
    ----------
    config : SimConfig — fully specified (seed already set for this replicate).

    Returns
    -------
    metrics : dict — all scalar run outputs plus timeline (excluded from CSV).
    """
    G = make_network(config)
    model = MosaicModel(config, G)
    log = DataLogger(config)
    
    metrics = model.run(log)
    
    import json
    import analysis._umap_compat
    import umap
    import numpy as np

    # 1. Build Network structure
    nodes = []
    for n in G.nodes():
        nodes.append({
            "id": n,
            "community_id": int(G.nodes[n]["community_id"]),
            "centrality": float(G.nodes[n]["centrality"]),
        })
    edges = [{"source": u, "target": v} for u, v in G.edges()]
    network_data = {"nodes": nodes, "edges": edges}

    # 2. Compute UMAP for canonical artifact
    canonical_path = log.run_dir / "canonical_run.json"
    with open(canonical_path) as f:
        canonical_data = json.load(f)
        
    snapshots = canonical_data["snapshots"]
    if not snapshots:
        canonical_data["network"] = network_data
        with open(canonical_path, "w", encoding="utf-8") as f:
            json.dump(canonical_data, f, separators=(",", ":"))
        return metrics

    # Determine 4 target timesteps: [0, T/3, 2T/3, final]
    timesteps = [s["timestep"] for s in snapshots]
    final_t = timesteps[-1]
    
    if len(timesteps) < 2:
        target_ts = [final_t]
    else:
        target_ts = [
            0,
            timesteps[max(1, len(timesteps)//3)],
            timesteps[min(len(timesteps)-1, max(1, 2*len(timesteps)//3))],
            final_t
        ]
    target_ts = sorted(list(set(target_ts)))

    # Fit UMAP on final timestep
    final_snapshot = next(s for s in snapshots if s["timestep"] == final_t)
    X_final = np.array([a["accent"] for a in sorted(final_snapshot["agents"], key=lambda x: x["agent_id"])])
    
    reducer = umap.UMAP(n_components=2, random_state=config.seed, n_neighbors=15, min_dist=0.1)
    reducer.fit(X_final)
    
    umap_snapshots = []
    for t in target_ts:
        snap_t = next(s for s in snapshots if s["timestep"] == t)
        X_t = np.array([a["accent"] for a in sorted(snap_t["agents"], key=lambda x: x["agent_id"])])
        coords_t = reducer.transform(X_t)
        
        points = []
        for i, agent in enumerate(sorted(snap_t["agents"], key=lambda x: x["agent_id"])):
            points.append({
                "agent_id": agent["agent_id"],
                "x": float(coords_t[i][0]),
                "y": float(coords_t[i][1]),
                "community_id": agent["community_id"]
            })
        umap_snapshots.append({"timestep": t, "points": points})
        
    canonical_data["network"] = network_data
    canonical_data["umap"] = {
        "metadata": {
            "method": "UMAP",
            "n_neighbors": 15,
            "min_dist": 0.1,
            "fit_timestep": int(final_t),
        },
        "snapshots": umap_snapshots
    }
    
    # Save back to disk
    with open(canonical_path, "w", encoding="utf-8") as f:
        json.dump(canonical_data, f, separators=(",", ":"))
        
    return metrics


# ---------------------------------------------------------------------------
# Monte Carlo runner
# ---------------------------------------------------------------------------

def run_monte_carlo(config: SimConfig) -> pd.DataFrame:
    """
    Execute config.n_runs replicates, collect results, write summary.csv.

    Each replicate increments the seed by 1 relative to the base seed
    (seed, seed+1, …, seed+n_runs-1).  The topology and all other
    parameters remain identical across replicates.

    Parameters
    ----------
    config : SimConfig — base configuration (n_runs and seed are read here).

    Returns
    -------
    df : pd.DataFrame with _SUMMARY_COLUMNS, one row per replicate.
    """
    n = config.n_runs
    logger.info(
        "Starting Monte Carlo: %d runs, topology=%s, seed=%d..%d",
        n, config.topology, config.seed, config.seed + n - 1,
    )

    rows: list[dict] = []
    t_start = time.monotonic()

    for i in range(n):
        run_config = replace(config, seed=config.seed + i)
        t0 = time.monotonic()
        metrics = run_single(run_config)
        elapsed = time.monotonic() - t0

        # Keep only summary columns (drop timeline from CSV)
        row = {k: metrics[k] for k in _SUMMARY_COLUMNS}
        rows.append(row)

        logger.info(
            "  [%2d/%2d] %-22s  conv=%s  t_conv=%5d  H=%.4f  D=%.4f  (%.1fs)",
            i + 1, n,
            run_config.run_id,
            str(metrics["converged"])[0],   # T / F
            metrics["convergence_time"],
            metrics["final_diversity"],
            metrics["final_pairwise_distance"],
            elapsed,
        )

    df = pd.DataFrame(rows, columns=_SUMMARY_COLUMNS)

    # Write summary CSV
    os.makedirs(str(_RESULTS_ROOT), exist_ok=True)
    summary_path = _RESULTS_ROOT / "summary.csv"
    df.to_csv(summary_path, index=False)
    logger.info(
        "Summary written → %s  (total: %.1fs)",
        summary_path,
        time.monotonic() - t_start,
    )

    return df


# ---------------------------------------------------------------------------
# __main__ entry point  (exit criterion: python -m simulation.runner)
# ---------------------------------------------------------------------------

def _setup_logging() -> None:
    """Configure console logging for the runner."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )


if __name__ == "__main__":
    _setup_logging()

    print("=" * 65)
    print("Mosaic — Monte Carlo Simulation Runner")
    print("=" * 65)

    config = SimConfig()
    print(f"Config: topology={config.topology}, N={config.N}, T={config.T}")
    print(f"        gamma={config.gamma}, theta={config.theta}, sigma={config.sigma}")
    print(f"        seed={config.seed}, n_runs={config.n_runs}")
    print()

    wall_t0 = time.monotonic()
    df = run_monte_carlo(config)
    wall_elapsed = time.monotonic() - wall_t0

    print()
    print("=" * 65)
    print(f"Completed {len(df)} runs in {wall_elapsed:.1f}s "
          f"({wall_elapsed / len(df):.1f}s per run)")
    print()
    print(
        df[["run_id", "convergence_time", "converged",
            "final_diversity", "final_pairwise_distance"]]
        .to_string(index=False)
    )
    print()
    print("Summary statistics:")
    print(df[["convergence_time", "final_diversity", "final_pairwise_distance"]]
          .describe().round(4).to_string())
    print()
    print(f"Run directories: runs/")
    print(f"Summary CSV:     results/summary.csv")
    print("=" * 65)
