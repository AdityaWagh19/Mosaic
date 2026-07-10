"""
analysis/umap_viz.py
--------------------
UMAP 4-panel accent-space trajectory visualization.

Shows how the population's accent distribution evolves across 4 timestep
snapshots, projected into 2-D via UMAP (fitted on the final timestep).

Usage
-----
    python -m analysis.umap_viz
"""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

RUNS_ROOT    = Path("runs")
FIGURES_DIR  = Path("results/figures")
ACCENT_COLS  = [f"d{i}" for i in range(6)]
REFERENCE_RUN = "watts_strogatz_1100"   # N=200, T=10,000 (Exp-1 run)
PANEL_TIMES   = [0, 2500, 5000, 10000]  # must be multiples of log_every=100


from analysis._umap_compat import UMAP  # type: ignore[import-untyped]  # noqa: E402

# ---------------------------------------------------------------------------
# Core visualisation
# ---------------------------------------------------------------------------

def plot_umap_4panel(
    run_dir: Path,
    out_path: Path,
    panel_times: list[int] | None = None,
) -> None:
    """
    Produce a 4-panel UMAP figure from one simulation run.

    The UMAP reducer is fitted on the final timestep, then used to transform
    earlier snapshots — giving a stable embedding across all four panels.

    Parameters
    ----------
    run_dir     : Path to the run directory (must contain agent_states.csv)
    out_path    : Output PNG path
    panel_times : Timesteps to display; defaults to [0, 2500, 5000, 10000]
    """
    if panel_times is None:
        panel_times = PANEL_TIMES

    run_dir = Path(run_dir)
    df = pd.read_csv(run_dir / "agent_states.csv")

    available_ts = sorted(df["timestep"].unique())

    # Snap each requested timestep to the nearest available logged timestep
    snapped: list[int] = []
    for t in panel_times:
        closest = int(min(available_ts, key=lambda x: abs(x - t)))
        if closest != t:
            log.info("t=%d not found — snapped to t=%d", t, closest)
        snapped.append(closest)

    # Fit UMAP on the final timestep (anchored embedding)
    t_final = int(available_ts[-1])
    df_final = (
        df[df["timestep"] == t_final]
        .sort_values("agent_id")
        .reset_index(drop=True)
    )
    X_final = df_final[ACCENT_COLS].values.astype(np.float32)
    community_ids_final = df_final["community_id"].values

    log.info("Fitting UMAP on t=%d accent state (N=%d) ...", t_final, len(X_final))
    reducer = UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.15)
    reducer.fit(X_final)

    # Build stable community colour map
    unique_communities = sorted(set(community_ids_final.tolist()))
    n_comm = max(len(unique_communities), 2)
    cmap   = plt.cm.get_cmap("Set1", n_comm)  # type: ignore[attr-defined]
    comm_colors = {c: cmap(i) for i, c in enumerate(unique_communities)}

    # ── Render 4 panels ──────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 4, figsize=(22, 5))
    run_name  = run_dir.name.replace("_", " ").title()
    fig.suptitle(
        f"Accent Space Trajectories — {run_name}  (UMAP)",
        fontsize=14,
        fontweight="bold",
    )

    for ax, t_snap in zip(axes, snapped):
        df_t = (
            df[df["timestep"] == t_snap]
            .sort_values("agent_id")
            .reset_index(drop=True)
        )
        X_t    = df_t[ACCENT_COLS].values.astype(np.float32)
        comm_t = df_t["community_id"].values

        embed = reducer.transform(X_t)  # type: ignore[union-attr]

        for comm in unique_communities:
            mask = comm_t == comm
            ax.scatter(
                embed[mask, 0],
                embed[mask, 1],
                c=[comm_colors[comm]],
                s=20,
                alpha=0.78,
                label=f"Community {comm}",
                edgecolors="none",
            )

        ax.set_title(f"t = {t_snap:,}", fontsize=12, fontweight="bold")
        ax.set_xlabel("UMAP 1", fontsize=9)
        ax.set_ylabel("UMAP 2", fontsize=9)
        ax.tick_params(labelsize=8)

    # Shared legend below all panels
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels,
        loc="lower center",
        ncol=len(unique_communities),
        fontsize=11,
        framealpha=0.9,
    )
    plt.tight_layout(rect=(0, 0, 1, 0.95))

    import os
    os.makedirs(str(out_path.parent), exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    log.info("UMAP 4-panel saved: %s", out_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-5s  %(message)s",
        datefmt="%H:%M:%S",
    )
    ref_dir  = RUNS_ROOT / REFERENCE_RUN
    out_path = FIGURES_DIR / "umap_4panel.png"

    if not ref_dir.exists():
        raise FileNotFoundError(
            f"Reference run not found: {ref_dir}\n"
            "Run 'python -m experiments.run_all' first."
        )

    plot_umap_4panel(ref_dir, out_path)
    print(f"UMAP 4-panel saved: {out_path}")


if __name__ == "__main__":
    main()
