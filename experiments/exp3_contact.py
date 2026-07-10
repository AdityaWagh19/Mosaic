"""
experiments/exp3_contact.py
============================
Experiment 3 — Two-Community Dialect Contact (RQ1 extended)

Design   : SBM(N=200, 2 communities), p_out ∈ {0.005, 0.01, 0.02, 0.05}, 25 runs each
Fixed    : p_in=0.15, γ=1.0, θ=0.30, σ=0.01, log_every=100
Seeds    : p_out=0.005 → 3000–3024, 0.01 → 3100–, 0.02 → 3200–, 0.05 → 3300–

Figures  : E3-A (4-panel network grid), E3-B (D_cross timeseries), E3-C (merger time bar)
"""
from __future__ import annotations

import json
import logging

from dataclasses import replace
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from simulation.config import SimConfig
from simulation import metrics as m
from simulation.network import make_network
from simulation.runner import run_single
from viz.figures import (
    plot_cross_community_distance,
    plot_merger_time_bar,
    plot_network_snapshot,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")
RUNS_DIR = Path("runs")

POUT_VALUES = [0.005, 0.01, 0.02, 0.05]
SEED_BASES = {0.005: 3000, 0.01: 3100, 0.02: 3200, 0.05: 3300}
MERGER_THRESHOLD = 0.1  # D_cross < 0.1 → merger declared


def _configs() -> list[SimConfig]:
    base = SimConfig(
        topology="sbm", N=200, p_in=0.15, T=10_000,
        gamma=1.0, theta=0.30, sigma=0.01, log_every=100, n_runs=25,
    )
    configs = []
    for pout in POUT_VALUES:
        seed_base = SEED_BASES[pout]
        for i in range(25):
            configs.append(replace(base, p_out=pout, seed=seed_base + i))
    return configs


def _load_or_run(config: SimConfig) -> dict:
    metrics_file = RUNS_DIR / config.run_id / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            r = json.load(f)
        return {
            "run_id": config.run_id,
            "p_out": config.p_out,
            "convergence_time": r["convergence_time"],
            "converged": r["converged"],
            "final_diversity": r["final_diversity"],
        }
    return {**run_single(config), "p_out": config.p_out}


def _compute_dcross_timeline(run_id: str, p_out: float) -> list[dict]:
    """Compute D_cross at each logged timestep by loading agent_states.csv."""
    csv_path = RUNS_DIR / run_id / "agent_states.csv"
    if not csv_path.exists():
        return []

    df = pd.read_csv(csv_path)
    accent_cols = [f"d{i}" for i in range(6)]
    rows = []
    for t_step, grp in df.groupby("timestep"):
        accent_mat = grp[accent_cols].values.astype(float)
        comm_ids = grp["community_id"].values.astype(int)
        d_cross = m.cross_community_distance(accent_mat, comm_ids)
        rows.append({"p_out": p_out, "timestep": int(t_step), "d_cross": d_cross})  # type: ignore[arg-type]
    return rows


def run_experiment() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    configs = _configs()

    log.info("Exp 3: running/loading %d runs...", len(configs))
    results: list[dict] = []
    for i, cfg in enumerate(configs):
        r = _load_or_run(cfg)
        results.append(r)
        if (i + 1) % 25 == 0:
            log.info("  %d / %d done", i + 1, len(configs))

    # ---- Compute D_cross timeseries per run ----
    log.info("Computing cross-community distance timelines...")
    all_dcross_rows: list[dict] = []
    for cfg in configs:
        all_dcross_rows.extend(_compute_dcross_timeline(cfg.run_id, cfg.p_out))

    dcross_raw = pd.DataFrame(all_dcross_rows)

    # Aggregate: mean + std per (p_out, timestep)
    if not dcross_raw.empty:
        dcross_df = (
            dcross_raw.groupby(["p_out", "timestep"])["d_cross"]
            .agg(["mean", "std"])
            .rename(columns={"mean": "d_cross_mean", "std": "d_cross_std"})
            .reset_index()
        )
        dcross_df["d_cross_std"] = dcross_df["d_cross_std"].fillna(0)
    else:
        dcross_df = pd.DataFrame(columns=["p_out", "timestep", "d_cross_mean", "d_cross_std"])

    # ---- Merger times ----
    merger_rows = []
    for pout in POUT_VALUES:
        sub = dcross_raw[dcross_raw["p_out"] == pout]
        merger_times = []
        for run_id in [cfg.run_id for cfg in configs if cfg.p_out == pout]:
            run_sub = sub  # we grouped by p_out not run_id in dcross_raw
            # Simple proxy: use the aggregated data
            pass
        # Per run merger time: load per-run dcross
        for cfg in [c for c in configs if c.p_out == pout]:
            run_rows = _compute_dcross_timeline(cfg.run_id, cfg.p_out)
            if not run_rows:
                continue
            for row in sorted(run_rows, key=lambda r: r["timestep"]):
                if row["d_cross"] < MERGER_THRESHOLD:
                    merger_times.append(row["timestep"])
                    break
            else:
                merger_times.append(10_000)  # no merger within T

        merger_rows.append({
            "p_out": pout,
            "merger_time_mean": float(np.mean(merger_times)) if merger_times else 10_000,
            "merger_time_std":  float(np.std(merger_times))  if merger_times else 0,
        })

    merger_df = pd.DataFrame(merger_rows)

    # ---- E3-A: 4-panel network grid (representative run, p_out=0.02) ----
    log.info("Generating E3-A: 4-panel network grid...")
    rep_pout = 0.02
    rep_cfg = replace(
        SimConfig(topology="sbm", N=200, p_in=0.15, p_out=rep_pout,
                  gamma=1.0, theta=0.30, sigma=0.01, log_every=100),
        seed=SEED_BASES[rep_pout],
    )
    G = make_network(rep_cfg)
    csv_path = RUNS_DIR / rep_cfg.run_id / "agent_states.csv"

    if csv_path.exists():
        df_snap = pd.read_csv(csv_path)
        all_timesteps = sorted(df_snap["timestep"].unique())
        t_max = all_timesteps[-1]

        # Four timesteps: t=0, closest to 2000, closest to 6000, final
        def closest(ts_list, target):
            return min(ts_list, key=lambda x: abs(x - target))

        snap_times = [0, closest(all_timesteps, 2000), closest(all_timesteps, 6000), t_max]
        snap_labels = ["t = 0 (initial)", "t ≈ 2,000", "t ≈ 6,000", f"t = {t_max:,} (final)"]

        fig, axes = plt.subplots(1, 4, figsize=(22, 6))
        pos = None
        for ax, t_step, label in zip(axes, snap_times, snap_labels):
            snap_df = df_snap[df_snap["timestep"] == t_step].copy()
            colour_col = "community_id" if t_step == 0 else "cluster_id"
            pos = plot_network_snapshot(
                G, snap_df, timestep=t_step,
                colour_by=colour_col, size_by="centrality",
                out_path="", ax=ax, pos=pos, title=label,
            )
        fig.suptitle("Dialect Contact: Accent Cluster Evolution (p_out=0.02)", fontsize=13)
        plt.tight_layout()
        out_e3a = str(FIGURES_DIR / "e3_network_4panel.png")
        plt.savefig(out_e3a, dpi=300, bbox_inches="tight")
        plt.close()
        log.info("  Saved %s", out_e3a)
    else:
        log.warning("agent_states.csv not found for E3-A; skipping network panel.")

    # ---- E3-B: D_cross timeseries ----
    plot_cross_community_distance(
        dcross_df, p_out_values=POUT_VALUES,
        out_path=str(FIGURES_DIR / "e3_cross_community_distance.png"),
    )

    # ---- E3-C: Merger time bar ----
    plot_merger_time_bar(
        merger_df, p_out_values=POUT_VALUES,
        out_path=str(FIGURES_DIR / "e3_merger_time_bar.png"),
    )

    log.info("Exp 3 complete. Merger time summary:")
    print(merger_df.to_string(index=False))


if __name__ == "__main__":
    run_experiment()
