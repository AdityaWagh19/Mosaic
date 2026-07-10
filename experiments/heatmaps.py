"""
experiments/heatmaps.py
=======================
Parameter Heatmaps — 1,000 runs (parallelised)

Heatmap 1 — Convergence Time vs (Topology × θ)
  4 topologies × 5 θ values × 25 runs = 500 runs
  θ ∈ {0.10, 0.20, 0.30, 0.40, 0.50}
  Seeds: base 6000 + topology_idx*125 + theta_idx*25 + run_idx

Heatmap 2 — Final Diversity vs (Topology × γ)
  4 topologies × 5 γ values × 25 runs = 500 runs
  γ ∈ {0.0, 0.5, 1.0, 1.5, 2.0}
  Seeds: base 7500 + topology_idx*125 + gamma_idx*25 + run_idx

Parallelism: concurrent.futures.ProcessPoolExecutor (all CPU cores).
Figures: heatmap_convergence_theta.png, heatmap_diversity_gamma.png
"""
from __future__ import annotations

import json
import logging
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from simulation.config import SimConfig
from simulation.runner import run_single
from viz.figures import plot_heatmap

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")
RUNS_DIR = Path("runs")

TOPOLOGIES = ["er", "watts_strogatz", "ba", "sbm"]
THETA_VALUES = [0.10, 0.20, 0.30, 0.40, 0.50]
GAMMA_VALUES = [0.0, 0.5, 1.0, 1.5, 2.0]
N_RUNS = 25


def _load_or_run(config: SimConfig) -> dict:
    """Run or load a single simulation; returns scalar metrics."""
    metrics_file = RUNS_DIR / config.run_id / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            r = json.load(f)
        return {
            "topology": config.topology,
            "theta": config.theta,
            "gamma": config.gamma,
            "convergence_time": r["convergence_time"],
            "final_diversity": r["final_diversity"],
        }
    result = run_single(config)
    return {
        "topology": config.topology,
        "theta": config.theta,
        "gamma": config.gamma,
        "convergence_time": result["convergence_time"],
        "final_diversity": result["final_diversity"],
    }


# ---- Heatmap 1 configs ----

def _heatmap1_configs() -> list[SimConfig]:
    """Convergence time: vary topology × θ."""
    configs = []
    for t_idx, topology in enumerate(TOPOLOGIES):
        for th_idx, theta in enumerate(THETA_VALUES):
            seed_base = 6000 + t_idx * 125 + th_idx * N_RUNS
            base = SimConfig(
                topology=topology, N=200, T=10_000,
                theta=theta, gamma=1.0, sigma=0.01, log_every=100,
            )
            for i in range(N_RUNS):
                configs.append(replace(base, seed=seed_base + i))
    return configs


# ---- Heatmap 2 configs ----

def _heatmap2_configs() -> list[SimConfig]:
    """Final diversity: vary topology × γ."""
    configs = []
    for t_idx, topology in enumerate(TOPOLOGIES):
        for g_idx, gamma in enumerate(GAMMA_VALUES):
            seed_base = 7500 + t_idx * 125 + g_idx * N_RUNS
            base = SimConfig(
                topology=topology, N=200, T=10_000,
                theta=0.30, gamma=gamma, sigma=0.01, log_every=100,
            )
            for i in range(N_RUNS):
                configs.append(replace(base, seed=seed_base + i))
    return configs


def _run_parallel(configs: list[SimConfig], desc: str) -> list[dict]:
    """Run all configs in parallel using ProcessPoolExecutor."""
    n_workers = max(1, os.cpu_count() or 1)
    log.info("%s: running %d configs on %d workers...", desc, len(configs), n_workers)

    results: list[dict] = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        future_to_idx = {executor.submit(_load_or_run, cfg): i for i, cfg in enumerate(configs)}
        done = 0
        for future in as_completed(future_to_idx):
            result = future.result()
            results.append(result)
            done += 1
            if done % 50 == 0 or done == len(configs):
                log.info("  %d / %d done", done, len(configs))

    return results


def _build_pivot(results: list[dict], row_col: str, col_col: str, value_col: str) -> pd.DataFrame:
    df = pd.DataFrame(results)
    pivot = df.groupby([row_col, col_col])[value_col].mean().unstack(col_col)
    return pivot


def run_experiment() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Heatmap 1: Convergence Time ----
    log.info("=== Heatmap 1: Convergence Time (Topology × θ) ===")
    h1_configs = _heatmap1_configs()
    h1_results = _run_parallel(h1_configs, "Heatmap 1")
    pivot_h1 = _build_pivot(h1_results, row_col="topology", col_col="theta", value_col="convergence_time")
    plot_heatmap(
        pivot_h1,
        xlabel="Confidence Threshold θ",
        ylabel="Network Topology",
        title="Mean Convergence Time",
        out_path=str(FIGURES_DIR / "heatmap_convergence_theta.png"),
    )
    log.info("Heatmap 1 saved.")

    # ---- Heatmap 2: Final Diversity ----
    log.info("=== Heatmap 2: Final Diversity (Topology × γ) ===")
    h2_configs = _heatmap2_configs()
    h2_results = _run_parallel(h2_configs, "Heatmap 2")
    pivot_h2 = _build_pivot(h2_results, row_col="topology", col_col="gamma", value_col="final_diversity")
    plot_heatmap(
        pivot_h2,
        xlabel="Prestige Weight γ",
        ylabel="Network Topology",
        title="Mean Final Shannon Diversity",
        out_path=str(FIGURES_DIR / "heatmap_diversity_gamma.png"),
    )
    log.info("Heatmap 2 saved.")
    log.info("Heatmaps complete.")


if __name__ == "__main__":
    run_experiment()
