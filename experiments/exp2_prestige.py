"""
experiments/exp2_prestige.py
============================
Experiment 2 — Prestige and Centrality Effect (RQ2)

Design   : BA(N=300, m=3), γ ∈ {0.0, 0.5, 1.0, 2.0}, 25 runs each = 100 total
Fixed    : θ=0.30, σ=0.01, log_every=100
Seeds    : γ=0.0 → 2000–2024, γ=0.5 → 2100–2124, γ=1.0 → 2200–2224, γ=2.0 → 2300–2324

Figures  : E2-A (scatter centrality vs influence, 4 panels), E2-B (Spearman vs γ), E2-C (network snapshot)
"""
from __future__ import annotations

import json
import logging

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from simulation.config import SimConfig
from simulation.network import make_network
from simulation import metrics as m
from simulation.runner import run_single
from viz.figures import (
    plot_centrality_vs_influence,
    plot_network_snapshot,
    plot_spearman_vs_gamma,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")
RUNS_DIR = Path("runs")

GAMMA_VALUES = [0.0, 0.5, 1.0, 2.0]
SEED_BASES = {0.0: 2000, 0.5: 2100, 1.0: 2200, 2.0: 2300}


def _configs() -> list[SimConfig]:
    base = SimConfig(topology="ba", N=300, m_ba=3, T=10_000,
                     theta=0.30, sigma=0.01, log_every=100, n_runs=25)
    configs = []
    for gamma in GAMMA_VALUES:
        seed_base = SEED_BASES[gamma]
        for i in range(25):
            configs.append(replace(base, gamma=gamma, seed=seed_base + i))
    return configs


def _load_or_run(config: SimConfig) -> dict:
    metrics_file = RUNS_DIR / config.run_id / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            r = json.load(f)
        return {
            "run_id": config.run_id,
            "topology": config.topology,
            "gamma": config.gamma,
            "convergence_time": r["convergence_time"],
            "converged": r["converged"],
            "final_diversity": r["final_diversity"],
            "final_pairwise_distance": r["final_pairwise_distance"],
        }
    return run_single(config)


def _compute_influence_scores(config: SimConfig) -> tuple[np.ndarray, np.ndarray]:
    """
    Load agent_states.csv for one run; return (centrality, influence_residual_scores).
    """
    csv_path = RUNS_DIR / config.run_id / "agent_states.csv"
    if not csv_path.exists():
        return np.array([]), np.array([])

    df = pd.read_csv(csv_path)
    accent_cols = [f"d{i}" for i in range(6)]

    # Initial accents at t=0
    t0 = df[df["timestep"] == 0].set_index("agent_id")
    if t0.empty:
        return np.array([]), np.array([])

    # Final accents
    t_final = df[df["timestep"] == df["timestep"].max()].set_index("agent_id")

    common_ids = t0.index.intersection(t_final.index)
    if len(common_ids) < 2:
        return np.array([]), np.array([])

    initial_accents = t0.loc[common_ids, accent_cols].values.astype(float)
    final_accents = t_final.loc[common_ids, accent_cols].values.astype(float)
    centrality = t0.loc[common_ids, "centrality"].values.astype(float)
    final_mean = final_accents.mean(axis=0)

    scores = m.influence_residual_scores(initial_accents, final_mean)
    return centrality, scores


def run_experiment() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    configs = _configs()

    log.info("Exp 2: running/loading %d runs...", len(configs))
    results: list[dict] = []
    for i, cfg in enumerate(configs):
        r = _load_or_run(cfg)
        results.append(r)
        if (i + 1) % 25 == 0:
            log.info("  %d / %d done", i + 1, len(configs))

    # ---- Compute Spearman r per run ----
    spearman_rows = []
    for cfg in configs:
        c, s = _compute_influence_scores(cfg)
        if len(c) >= 5:
            r_val, _ = stats.spearmanr(c, s)
            spearman_rows.append({"gamma": cfg.gamma, "spearman_r": float(r_val)})

    spearman_df = pd.DataFrame(spearman_rows)
    spearman_summary = (
        spearman_df.groupby("gamma")["spearman_r"]
        .agg(["mean", "std"])
        .rename(columns={"mean": "spearman_r_mean", "std": "spearman_r_std"})
        .reset_index()
    )

    # ---- E2-A: Centrality vs influence scatter (one panel per γ) ----
    log.info("Generating E2-A: centrality vs influence scatter...")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 4, figsize=(18, 5), sharey=True)
    for ax, gamma in zip(axes, GAMMA_VALUES):
        # Use the first run for each gamma
        seed_base = SEED_BASES[gamma]
        rep_config = replace(
            SimConfig(topology="ba", N=300, m_ba=3, T=10_000,
                      theta=0.30, sigma=0.01, log_every=100),
            gamma=gamma, seed=seed_base,
        )
        c, s = _compute_influence_scores(rep_config)
        if len(c) < 5:
            ax.set_title(f"γ={gamma}")
            continue
        ax.scatter(c, s, alpha=0.4, s=15, color="#9B59B6", edgecolors="none")
        m_reg, b = np.polyfit(c, s, 1)
        x_line = np.linspace(c.min(), c.max(), 100)
        ax.plot(x_line, m_reg * x_line + b, color="#E74C3C", linewidth=1.8)
        rval, _ = stats.spearmanr(c, s)
        ax.set_title(f"γ = {gamma}  (r = {rval:.2f})", fontsize=11)
        ax.set_xlabel("Degree Centrality")
        if ax is axes[0]:
            ax.set_ylabel("Influence Score  sᵢ")

    fig.suptitle("Centrality vs Influence Residual Score by Prestige Weight", fontsize=13)
    plt.tight_layout()
    out_e2a = str(FIGURES_DIR / "e2_centrality_vs_influence.png")
    plt.savefig(out_e2a, dpi=300, bbox_inches="tight")
    plt.close()
    log.info("  Saved %s", out_e2a)

    # ---- E2-B: Spearman vs gamma ----
    plot_spearman_vs_gamma(spearman_summary, out_path=str(FIGURES_DIR / "e2_spearman_vs_gamma.png"))

    # ---- E2-C: Network snapshot ----
    log.info("Generating E2-C: network snapshot...")
    rep_gamma = 2.0
    rep_seed = SEED_BASES[rep_gamma]
    snap_config = replace(
        SimConfig(topology="ba", N=300, m_ba=3, T=10_000,
                  theta=0.30, sigma=0.01, log_every=100),
        gamma=rep_gamma, seed=rep_seed,
    )
    G = make_network(snap_config)
    csv_path = RUNS_DIR / snap_config.run_id / "agent_states.csv"
    if csv_path.exists():
        df_snap = pd.read_csv(csv_path)
        t_final = df_snap["timestep"].max()
        snap_df = df_snap[df_snap["timestep"] == t_final].copy()
        plot_network_snapshot(
            G, snap_df, timestep=int(t_final),
            colour_by="cluster_id",
            size_by="centrality",
            out_path=str(FIGURES_DIR / "e2_network_snapshot.png"),
            title=f"BA Network at Convergence (γ={rep_gamma})",
        )
    else:
        log.warning("agent_states.csv not found for E2-C snapshot; skipping.")

    log.info("Exp 2 complete. Spearman summary:")
    print(spearman_summary.to_string(index=False))


if __name__ == "__main__":
    run_experiment()
