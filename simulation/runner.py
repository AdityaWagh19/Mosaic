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
    return model.run(log)


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
