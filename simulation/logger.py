"""
simulation/logger.py
====================
DataLogger — writes run outputs to the filesystem.

Creates ``runs/{run_id}/`` and writes three files:
  - ``config.json``       — serialised SimConfig (written at init)
  - ``agent_states.csv``  — snapshot every config.log_every steps
  - ``metrics.json``      — scalar run results (written at close)
  - ``timeline.json``     — [{timestep, diversity, pairwise_distance}] (written at close)

CSV column order (model.md §9):
    timestep, agent_id, community_id, centrality, d0, d1, d2, d3, d4, d5

Design notes
------------
- Agent state rows are buffered in memory and flushed to CSV in one write
  at close().  For N=200 and 100 log steps, this is 20,000 rows (~3 MB) —
  comfortably in memory and much faster than line-by-line disk I/O.
- The DataLogger is constructed before MosaicModel.run() and passed in so
  that the run directory exists before the simulation starts (config.json
  must be written first for crash recovery).
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from simulation.config import SimConfig

if TYPE_CHECKING:
    from simulation.agent import AccentAgent

# Module-level logger made accessible to MosaicModel for run-complete messages.
module_logger = logging.getLogger(__name__)

# Directory that contains all run sub-directories.
_RUNS_ROOT = Path("runs")
_RESULTS_ROOT = Path("results")

# CSV column headers (model.md §9)
_CSV_HEADERS = [
    "timestep", "agent_id", "community_id", "centrality",
    "d0", "d1", "d2", "d3", "d4", "d5",
]


class DataLogger:
    """
    Writes per-step agent snapshots and final metrics for one simulation run.

    Usage (called by MonteCarloRunner / MosaicModel):
    ::
        logger = DataLogger(config)          # creates runs/{run_id}/config.json
        metrics = model.run(logger)          # calls logger.log() at each log step
        # logger.close() is called internally by model.run()

    Attributes
    ----------
    run_dir : Path — absolute path to this run's output directory.
    run_id  : str  — the run identifier (``{topology}_{seed}``).
    """

    def __init__(self, config: SimConfig) -> None:
        self.config = config
        self.run_id: str = config.run_id
        self.module_logger = module_logger

        # Create run directory
        self.run_dir: Path = _RUNS_ROOT / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Write config.json immediately (before simulation starts)
        config_path = self.run_dir / "config.json"
        config.save(str(config_path))

        # Internal buffer for agent state rows (flushed in close())
        self._rows: list[list] = []

        module_logger.debug("DataLogger initialised for run '%s'.", self.run_id)

    # ------------------------------------------------------------------
    # Per-step logging
    # ------------------------------------------------------------------

    def log(self, t: int, agents: dict[int, "AccentAgent"]) -> None:
        """
        Buffer a snapshot of all agents at timestep t.

        Rows are accumulated in memory and written as a single CSV at close().
        This is significantly faster than appending to the file on every call.

        Parameters
        ----------
        t      : current simulation timestep
        agents : the model's agents_map (node_id → AccentAgent)
        """
        for agent_id in sorted(agents):
            agent = agents[agent_id]
            a = agent.accent
            self._rows.append([
                t,
                agent_id,
                agent.community_id,
                round(agent.centrality, 6),
                round(float(a[0]), 6),
                round(float(a[1]), 6),
                round(float(a[2]), 6),
                round(float(a[3]), 6),
                round(float(a[4]), 6),
                round(float(a[5]), 6),
            ])

    # ------------------------------------------------------------------
    # Finalisation
    # ------------------------------------------------------------------

    def close(self, metrics: dict, timeline: list[dict]) -> None:
        """
        Flush buffered rows to agent_states.csv and write metrics/timeline JSON.

        Called by MosaicModel.run() at the end of the simulation.

        Parameters
        ----------
        metrics  : dict — scalar run results (convergence_time, etc.)
        timeline : list of {timestep, diversity, pairwise_distance} dicts
        """
        # 1. Write agent_states.csv
        csv_path = self.run_dir / "agent_states.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(_CSV_HEADERS)
            writer.writerows(self._rows)

        # 2. Write metrics.json (only the 4 scalar outputs as per model.md §9)
        scalar_metrics = {
            "convergence_time":        metrics["convergence_time"],
            "converged":               metrics["converged"],
            "final_diversity":         metrics["final_diversity"],
            "final_pairwise_distance": metrics["final_pairwise_distance"],
        }
        metrics_path = self.run_dir / "metrics.json"
        with open(metrics_path, "w", encoding="utf-8") as fh:
            json.dump(scalar_metrics, fh, indent=2)

        # 3. Write timeline.json (used by the FastAPI backend in Plan 6)
        timeline_path = self.run_dir / "timeline.json"
        with open(timeline_path, "w", encoding="utf-8") as fh:
            json.dump(timeline, fh, indent=2)

        module_logger.debug(
            "Run '%s': wrote %d CSV rows, metrics.json, timeline.json.",
            self.run_id,
            len(self._rows),
        )

        # Free memory
        self._rows = []
