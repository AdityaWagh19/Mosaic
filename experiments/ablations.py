"""
experiments/ablations.py
========================
Ablation Studies — 4 ablations vs baseline

Baseline : WS(N=200), θ=0.30, γ=1.0, σ=0.01     seeds 4000–4024
A1       : θ=100 (no bounded confidence)           seeds 4100–4124
A2       : γ=0.0 (no prestige)                     seeds 4200–4224
A3       : σ=0.0 (no noise)                        seeds 4300–4324
A4       : symmetric=True (symmetric update)       seeds 4400–4424

Figure   : ablation_boxplot.png
"""
from __future__ import annotations

import json
import logging

from dataclasses import replace
from pathlib import Path

import pandas as pd

from simulation.config import SimConfig
from simulation.runner import run_single
from viz.figures import plot_ablation_boxplot

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")
RUNS_DIR = Path("runs")

_ABLATIONS: list[tuple[str, dict, int]] = [
    ("Baseline",           {},                           4000),
    ("A1 – No homophily",  {"theta": 100.0},             4100),
    ("A2 – No prestige",   {"gamma": 0.0},               4200),
    ("A3 – No noise",      {"sigma": 0.0},               4300),
    ("A4 – Symmetric",     {"symmetric": True},          4400),
]


def _base_config() -> SimConfig:
    return SimConfig(
        topology="watts_strogatz", N=200, T=10_000,
        theta=0.30, gamma=1.0, sigma=0.01, log_every=100, n_runs=25,
    )


def _configs() -> list[tuple[str, SimConfig]]:
    base = _base_config()
    result = []
    for label, overrides, seed_base in _ABLATIONS:
        for i in range(25):
            cfg = replace(base, seed=seed_base + i, **overrides)  # type: ignore[arg-type]
            result.append((label, cfg))
    return result


def _load_or_run(config: SimConfig) -> dict:
    metrics_file = RUNS_DIR / config.run_id / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file) as f:
            r = json.load(f)
        return {
            "convergence_time": r["convergence_time"],
            "final_diversity": r["final_diversity"],
        }
    result = run_single(config)
    return {
        "convergence_time": result["convergence_time"],
        "final_diversity": result["final_diversity"],
    }


def run_experiment() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    label_configs = _configs()

    log.info("Ablations: running/loading %d runs...", len(label_configs))
    rows: list[dict] = []
    for i, (label, cfg) in enumerate(label_configs):
        r = _load_or_run(cfg)
        rows.append({"condition": label, **r})
        if (i + 1) % 25 == 0:
            log.info("  %d / %d done", i + 1, len(label_configs))

    ablation_df = pd.DataFrame(rows)

    plot_ablation_boxplot(
        ablation_df,
        out_path=str(FIGURES_DIR / "ablation_boxplot.png"),
    )

    log.info("Ablations complete. Summary:")
    grp = ablation_df.groupby("condition")[["convergence_time", "final_diversity"]]
    print(grp.mean().round(2).to_string())


if __name__ == "__main__":
    run_experiment()
