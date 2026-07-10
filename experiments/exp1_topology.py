"""
experiments/exp1_topology.py
============================
Experiment 1 — Topology Comparison (RQ1)

Design   : 4 topologies × 25 runs = 100 total runs
Fixed    : N=200, T=10,000, θ=0.30, γ=1.0, σ=0.01, log_every=100
Seeds    : ER 1000–1024, WS 1100–1124, BA 1200–1224, SBM 1300–1324

Figures  : E1-A (diversity timeseries), E1-B (convergence boxplot), E1-C (final diversity bar)
"""
from __future__ import annotations

import json
import logging

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from simulation.config import SimConfig
from simulation.runner import run_single
from viz.figures import (
    plot_convergence_boxplot,
    plot_diversity_timeseries,
    plot_final_diversity_bar,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")
RUNS_DIR = Path("runs")

# Seed offsets per topology
_SEED_BASES = {
    "er": 1000,
    "watts_strogatz": 1100,
    "ba": 1200,
    "sbm": 1300,
}


def _configs() -> list[SimConfig]:
    configs = []
    base = SimConfig(N=200, T=10_000, theta=0.30, gamma=1.0, sigma=0.01, log_every=100, n_runs=25)
    for topology, seed_base in _SEED_BASES.items():
        for i in range(25):
            configs.append(replace(base, topology=topology, seed=seed_base + i))
    return configs


def _load_or_run(config: SimConfig) -> dict:
    metrics_file = RUNS_DIR / config.run_id / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            m = json.load(f)
        # Reconstruct minimal metrics dict
        return {
            "run_id": config.run_id,
            "topology": config.topology,
            "convergence_time": m["convergence_time"],
            "converged": m["converged"],
            "final_diversity": m["final_diversity"],
            "final_pairwise_distance": m["final_pairwise_distance"],
        }
    return run_single(config)


def _load_timeline(run_id: str) -> list[dict]:
    path = RUNS_DIR / run_id / "timeline.json"
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def run_experiment() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    configs = _configs()

    log.info("Exp 1: running/loading %d runs...", len(configs))
    results: list[dict] = []
    for i, cfg in enumerate(configs):
        r = _load_or_run(cfg)
        results.append(r)
        if (i + 1) % 25 == 0:
            log.info("  %d / %d done", i + 1, len(configs))

    # ---- Summary DataFrame ----
    summary = pd.DataFrame(results)

    # ---- Timeline DataFrame (long format) ----
    timeline_rows = []
    for cfg in configs:
        tl = _load_timeline(cfg.run_id)
        for entry in tl:
            timeline_rows.append({
                "topology": cfg.topology,
                "run_id": cfg.run_id,
                "timestep": entry["timestep"],
                "diversity": entry["diversity"],
                "pairwise_distance": entry["pairwise_distance"],
            })
    timeline_df = pd.DataFrame(timeline_rows)

    # ---- Figures ----
    log.info("Generating E1 figures...")

    plot_diversity_timeseries(
        timeline_df, topology_col="topology", diversity_col="diversity",
        out_path=str(FIGURES_DIR / "e1_diversity_timeseries.png"),
    )
    plot_convergence_boxplot(
        summary, topology_col="topology", conv_time_col="convergence_time",
        out_path=str(FIGURES_DIR / "e1_convergence_boxplot.png"),
    )
    plot_final_diversity_bar(
        summary, topology_col="topology", diversity_col="final_diversity",
        out_path=str(FIGURES_DIR / "e1_final_diversity_bar.png"),
    )

    # ---- Quick report ----
    log.info("Exp 1 complete. Summary:")
    grp = summary.groupby("topology")[["convergence_time", "final_diversity"]]
    print(grp.mean().round(2).to_string())


if __name__ == "__main__":
    run_experiment()
