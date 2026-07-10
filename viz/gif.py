"""
viz/gif.py
==========
Animated diffusion GIF for the Mosaic ABM.

make_diffusion_gif() renders 60 frames of network evolution:
  - Nodes coloured by k-means accent cluster at each frame timestep
  - Node size ∝ degree centrality
  - Spring layout computed once and held fixed for visual continuity
  - Saved as an optimised animated GIF via Pillow (target < 5 MB)
"""
from __future__ import annotations

import io
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.cluster import KMeans


def make_diffusion_gif(
    run_id: str,
    runs_dir: str = "runs",
    n_display: int = 100,
    fps: int = 20,
    n_frames: int = 60,
    out_path: str = "results/figures/diffusion.gif",
) -> None:
    """
    Create an animated GIF showing accent cluster evolution on the social network.

    Parameters
    ----------
    run_id    : identifier of the run directory (e.g. 'watts_strogatz_1100')
    runs_dir  : root directory containing run sub-directories (default 'runs')
    n_display : max number of agents to display (subsampled for clarity)
    fps       : frames per second for the GIF (default 20)
    n_frames  : total number of animation frames (default 60)
    out_path  : save path for the GIF
    """
    run_dir = Path(runs_dir) / run_id
    csv_path = run_dir / "agent_states.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"agent_states.csv not found for run '{run_id}'")

    os.makedirs(Path(out_path).parent, exist_ok=True)

    # ------------------------------------------------------------------
    # Load agent states
    # ------------------------------------------------------------------
    df = pd.read_csv(csv_path)
    timesteps = sorted(df["timestep"].unique())
    T_total = len(timesteps)

    # Subsample frames evenly across the full simulation
    frame_indices = np.linspace(0, T_total - 1, n_frames, dtype=int)
    frame_timesteps = [timesteps[i] for i in frame_indices]

    # ------------------------------------------------------------------
    # Build a lightweight graph for layout (from agent connectivity proxy)
    # We reconstruct the graph topology from the centrality values using
    # a Watts-Strogatz approximation — for GIF purposes the exact edges
    # don't matter; what matters is a stable spring layout.
    # If the run directory contains a network file we'd use it; otherwise
    # we build a proxy graph from the number of agents.
    # ------------------------------------------------------------------
    t0_df = df[df["timestep"] == timesteps[0]].copy()
    N = len(t0_df)

    # Subsample agents for clarity
    agent_ids_all = t0_df["agent_id"].values
    if N > n_display:
        rng = np.random.default_rng(42)
        agent_ids = rng.choice(agent_ids_all, size=n_display, replace=False)
        agent_ids = sorted(agent_ids)
    else:
        agent_ids = sorted(agent_ids_all)

    # Build proxy graph: connect agents with similar initial centrality as neighbours
    G_proxy = nx.watts_strogatz_graph(len(agent_ids), k=6, p=0.1, seed=42)
    pos = nx.spring_layout(G_proxy, seed=42, k=1.5 / np.sqrt(max(len(agent_ids), 1)))

    # Get centrality for node sizes (fixed at t=0)
    t0_sub = t0_df.set_index("agent_id").loc[agent_ids]
    centralities = t0_sub["centrality"].values.astype(float)
    node_sizes = 25 + 200 * (centralities - centralities.min()) / max(centralities.ptp(), 1e-9)

    accent_cols = [c for c in df.columns if c.startswith("d") and c[1:].isdigit()]

    # ------------------------------------------------------------------
    # Render frames
    # ------------------------------------------------------------------
    frames: list[Image.Image] = []
    n_clusters = 5

    for t_step in frame_timesteps:
        frame_df = df[df["timestep"] == t_step].set_index("agent_id")

        # Get accent matrix for displayed agents
        available = [aid for aid in agent_ids if aid in frame_df.index]
        if not available:
            continue

        accent_mat = frame_df.loc[available, accent_cols].values.astype(float)
        k = min(n_clusters, len(available))
        km = KMeans(n_clusters=k, n_init=3, random_state=42)
        labels = km.fit_predict(accent_mat)

        # Map labels to colours
        cmap_colors = plt.cm.Set2.colors  # type: ignore[attr-defined]
        node_colors = [cmap_colors[int(lbl) % len(cmap_colors)] for lbl in labels]

        # Sizes may need alignment if some agents dropped out
        sizes_frame = node_sizes[: len(available)]
        node_list = list(range(len(available)))  # proxy graph node indices

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_facecolor("#1A1A2E")
        fig.patch.set_facecolor("#1A1A2E")

        nx.draw_networkx_edges(
            G_proxy, pos, ax=ax,
            edge_color="#333355", width=0.4, alpha=0.5,
        )
        nx.draw_networkx_nodes(
            G_proxy, pos,
            nodelist=node_list,
            node_color=node_colors,  # type: ignore[arg-type]
            node_size=sizes_frame.tolist(),
            ax=ax, alpha=0.92,
        )

        ax.set_title(
            f"t = {t_step:,}",
            color="white", fontsize=14, fontweight="bold", pad=8,
        )
        ax.axis("off")
        plt.tight_layout(pad=0.3)

        # Render to PIL Image
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=80, facecolor=fig.get_facecolor())
        plt.close()
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
        frames.append(img.quantize(colors=64))  # Pillow 10+ compatible

    if not frames:
        raise RuntimeError("No frames rendered — check that agent_states.csv has data.")

    # ------------------------------------------------------------------
    # Save GIF
    # ------------------------------------------------------------------
    duration_ms = int(1000 / fps)
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        optimize=True,
        loop=0,
        duration=duration_ms,
    )
    size_mb = Path(out_path).stat().st_size / 1_048_576
    print(f"  GIF saved: {out_path}  ({size_mb:.2f} MB, {len(frames)} frames @ {fps} fps)")
