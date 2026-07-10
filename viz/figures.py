"""
viz/figures.py
==============
All static figure-generation functions for the Mosaic ABM.

Every function:
  - Takes DataFrames / NumPy arrays — no simulation state
  - Saves a PNG at 300 DPI to ``out_path``
  - Calls plt.close() after saving to prevent memory leaks in batch runs

Colour palette (ColorBrewer qualitative Set2, colour-blind-friendly):
  topology order: er, watts_strogatz, ba, sbm
"""
from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")          # headless — no GUI window
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans

# ---------------------------------------------------------------------------
# Global style
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid", context="paper", font_scale=1.3)

_TOPOLOGY_PALETTE = {
    "er":             "#E74C3C",
    "watts_strogatz": "#3498DB",
    "ba":             "#2ECC71",
    "sbm":            "#9B59B6",
}
_TOPOLOGY_LABELS = {
    "er": "Erdős-Rényi",
    "watts_strogatz": "Watts-Strogatz",
    "ba": "Barabási-Albert",
    "sbm": "Stochastic Block",
}
_ABLATION_PALETTE = {
    "Baseline": "#3498DB",
    "A1 – No homophily":  "#E74C3C",
    "A2 – No prestige":   "#2ECC71",
    "A3 – No noise":      "#9B59B6",
    "A4 – Symmetric":     "#F39C12",
}
_POUT_PALETTE = {
    0.005: "#1B4F72",
    0.01:  "#2E86C1",
    0.02:  "#85C1E9",
    0.05:  "#D6EAF8",
}


def _ensure_dir(path: str | Path) -> None:
    os.makedirs(Path(path).parent, exist_ok=True)


# ---------------------------------------------------------------------------
# 1.  Diversity timeseries  (E1-A)
# ---------------------------------------------------------------------------

def plot_diversity_timeseries(
    timeline_df: pd.DataFrame,
    topology_col: str,
    diversity_col: str,
    out_path: str,
) -> None:
    """
    Line plot of H(t) vs timestep for each topology.
    Mean ± 1 SD shaded band across replicates.

    Parameters
    ----------
    timeline_df : columns [topology, timestep, diversity] — long format, one row per (run, timestep)
    topology_col : column name for topology
    diversity_col : column name for diversity (H)
    out_path : save path
    """
    _ensure_dir(out_path)
    fig, ax = plt.subplots(figsize=(10, 6))

    topologies = timeline_df[topology_col].unique()
    for topo in sorted(topologies, key=lambda t: list(_TOPOLOGY_PALETTE).index(t) if t in _TOPOLOGY_PALETTE else 99):
        color = _TOPOLOGY_PALETTE.get(topo, "grey")
        label = _TOPOLOGY_LABELS.get(topo, topo)
        grp = timeline_df[timeline_df[topology_col] == topo].groupby("timestep")[diversity_col]
        mean = grp.mean()
        std = grp.std().fillna(0)
        ax.plot(mean.index, mean.values, color=color, linewidth=2, label=label)
        ax.fill_between(mean.index, mean - std, mean + std, color=color, alpha=0.15)

    ax.set_xlabel("Timestep")
    ax.set_ylabel("Shannon Diversity H(t)")
    ax.set_title("Accent Diversity Over Time by Network Topology")
    ax.legend(frameon=True, loc="upper right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 2.  Convergence time boxplot  (E1-B)
# ---------------------------------------------------------------------------

def plot_convergence_boxplot(
    summary_df: pd.DataFrame,
    topology_col: str,
    conv_time_col: str,
    out_path: str,
) -> None:
    """
    Boxplot of convergence time per topology.

    Parameters
    ----------
    summary_df : columns [topology, convergence_time] — one row per run
    """
    _ensure_dir(out_path)
    topo_order = [t for t in _TOPOLOGY_PALETTE if t in summary_df[topology_col].values]
    palette = {t: _TOPOLOGY_PALETTE[t] for t in topo_order}
    labels = [_TOPOLOGY_LABELS.get(t, t) for t in topo_order]

    fig, ax = plt.subplots(figsize=(9, 6))
    data = [summary_df[summary_df[topology_col] == t][conv_time_col].values for t in topo_order]
    bp = ax.boxplot(
        data,
        patch_artist=True,
        widths=0.5,
        medianprops=dict(color="white", linewidth=2),
    )
    for patch, t in zip(bp["boxes"], topo_order):
        patch.set_facecolor(_TOPOLOGY_PALETTE.get(t, "grey"))
        patch.set_alpha(0.85)

    ax.set_xticks(range(1, len(topo_order) + 1))
    ax.set_xticklabels(labels, rotation=15, ha="right")
    ax.set_ylabel("Convergence Time (steps)")
    ax.set_title("Convergence Time Distribution by Network Topology")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 3.  Final diversity bar chart  (E1-C)
# ---------------------------------------------------------------------------

def plot_final_diversity_bar(
    summary_df: pd.DataFrame,
    topology_col: str,
    diversity_col: str,
    out_path: str,
) -> None:
    """Bar chart of mean final Shannon diversity per topology (± 1 SD)."""
    _ensure_dir(out_path)
    topo_order = [t for t in _TOPOLOGY_PALETTE if t in summary_df[topology_col].values]
    labels = [_TOPOLOGY_LABELS.get(t, t) for t in topo_order]
    means = [summary_df[summary_df[topology_col] == t][diversity_col].mean() for t in topo_order]
    stds  = [summary_df[summary_df[topology_col] == t][diversity_col].std() for t in topo_order]
    colors = [_TOPOLOGY_PALETTE.get(t, "grey") for t in topo_order]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(labels, means, yerr=stds, color=colors, alpha=0.85,
                  edgecolor="white", capsize=5, width=0.6)
    ax.set_ylabel("Final Shannon Diversity H")
    ax.set_title("Final Accent Diversity by Network Topology")
    ax.set_ylim(0, max(means) * 1.35 if means else 2)
    for bar, mean, std in zip(bars, means, stds):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            mean + std + 0.02,
            f"{mean:.3f}",
            ha="center", va="bottom", fontsize=10,
        )
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 4.  Network snapshot  (E2-C, E3-A panels)
# ---------------------------------------------------------------------------

def plot_network_snapshot(
    G,
    agent_states_df: pd.DataFrame,
    timestep: int,
    colour_by: str,
    size_by: str,
    out_path: str,
    pos: dict | None = None,
    ax=None,
    title: str = "",
) -> dict:
    """
    Draw a single NetworkX snapshot.

    Parameters
    ----------
    G             : nx.Graph
    agent_states_df : DataFrame filtered to one timestep, columns include
                    agent_id, community_id, centrality, d0..d5, and optionally cluster_id
    timestep      : displayed in title
    colour_by     : 'community_id' or 'cluster_id'
    size_by       : 'centrality'
    out_path      : if not empty string, save figure here (else don't save)
    pos           : pre-computed layout dict (computed internally if None)
    ax            : existing Axes (creates new figure if None)
    title         : subplot title

    Returns
    -------
    pos : layout dict (reuse across panels for consistent layout)
    """
    _ensure_dir(out_path) if out_path else None

    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 7))

    # Layout
    if pos is None:
        pos = nx.spring_layout(G, seed=42, k=1.5 / np.sqrt(max(len(G), 1)))

    # Build per-node arrays aligned to G.nodes()
    df = agent_states_df.set_index("agent_id")
    node_list = list(G.nodes())

    # Colour
    if colour_by in df.columns:
        raw_vals = df.loc[node_list, colour_by].values
    else:
        # Compute cluster_id from accent dims
        accent_cols = [c for c in df.columns if c.startswith("d")]
        accent_mat = df.loc[node_list, accent_cols].values.astype(float)
        k = min(5, len(node_list))
        km = KMeans(n_clusters=k, n_init=5, random_state=42)
        raw_vals = km.fit_predict(accent_mat)

    # Discrete colour map
    unique_vals = sorted(set(raw_vals))
    cmap_colors = plt.cm.Set2.colors  # type: ignore[attr-defined]
    color_map = {v: cmap_colors[i % len(cmap_colors)] for i, v in enumerate(unique_vals)}
    node_colors = [color_map[v] for v in raw_vals]

    # Size
    if size_by in df.columns:
        centralities = df.loc[node_list, size_by].values.astype(float)
    else:
        centralities = np.ones(len(node_list))
    node_sizes = 50 + 400 * (centralities - centralities.min()) / max(centralities.ptp(), 1e-9)

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#CCCCCC", width=0.4, alpha=0.6)
    nx.draw_networkx_nodes(
        G, pos, nodelist=node_list,
        node_color=node_colors,  # type: ignore[arg-type]
        node_size=node_sizes.tolist(),
        ax=ax, alpha=0.9,
    )
    ax.set_title(title or f"t = {timestep}", fontsize=12, fontweight="bold")
    ax.axis("off")

    if standalone and out_path:
        plt.tight_layout()
        plt.savefig(out_path, dpi=300)
        plt.close()

    return pos


# ---------------------------------------------------------------------------
# 5.  Spearman r vs gamma  (E2-B)
# ---------------------------------------------------------------------------

def plot_spearman_vs_gamma(
    spearman_df: pd.DataFrame,
    out_path: str,
) -> None:
    """
    Line + error-bar plot of mean Spearman r vs gamma.

    Parameters
    ----------
    spearman_df : columns [gamma, spearman_r_mean, spearman_r_std]
    """
    _ensure_dir(out_path)
    fig, ax = plt.subplots(figsize=(8, 5))
    df = spearman_df.sort_values("gamma")
    ax.errorbar(
        df["gamma"], df["spearman_r_mean"], yerr=df["spearman_r_std"],
        color="#E74C3C", linewidth=2, marker="o", markersize=7,
        capsize=5, capthick=1.5, label="Spearman r",
    )
    ax.axhline(0, color="grey", linewidth=1, linestyle="--", alpha=0.5)
    ax.set_xlabel("Prestige weight γ")
    ax.set_ylabel("Mean Spearman r (centrality vs influence)")
    ax.set_title("Effect of Prestige Weight on Centrality–Influence Correlation")
    ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 6.  Centrality vs influence scatter  (E2-A)
# ---------------------------------------------------------------------------

def plot_centrality_vs_influence(
    centrality: np.ndarray,
    scores: np.ndarray,
    gamma: float,
    out_path: str,
) -> None:
    """Scatter of centrality vs influence residual score with regression line."""
    _ensure_dir(out_path)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(centrality, scores, color="#9B59B6", alpha=0.55, s=25, edgecolors="none")

    # Regression line
    m_reg, b = np.polyfit(centrality, scores, 1)
    x_line = np.linspace(centrality.min(), centrality.max(), 100)
    ax.plot(x_line, m_reg * x_line + b, color="#E74C3C", linewidth=2, label="OLS fit")

    ax.set_xlabel("Degree Centrality")
    ax.set_ylabel("Influence Residual Score  sᵢ")
    ax.set_title(f"Centrality vs Influence  (γ = {gamma:.1f})")
    ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 7.  Cross-community distance  (E3-B)
# ---------------------------------------------------------------------------

def plot_cross_community_distance(
    dcross_df: pd.DataFrame,
    p_out_values: list,
    out_path: str,
) -> None:
    """
    Line plot of D_cross(t) vs timestep for each p_out value.

    Parameters
    ----------
    dcross_df : columns [p_out, timestep, d_cross_mean, d_cross_std]
    """
    _ensure_dir(out_path)
    colors = list(plt.cm.Blues(np.linspace(0.4, 1.0, len(p_out_values))))  # type: ignore[attr-defined]
    fig, ax = plt.subplots(figsize=(10, 6))

    for i, pout in enumerate(sorted(p_out_values)):
        sub = dcross_df[dcross_df["p_out"] == pout].sort_values("timestep")
        color = colors[i]
        ax.plot(sub["timestep"], sub["d_cross_mean"], color=color, linewidth=2,
                label=f"p_out = {pout}")
        ax.fill_between(
            sub["timestep"],
            sub["d_cross_mean"] - sub["d_cross_std"],
            sub["d_cross_mean"] + sub["d_cross_std"],
            color=color, alpha=0.15,
        )

    ax.axhline(0.1, color="grey", linewidth=1, linestyle="--", alpha=0.6, label="Merger threshold")
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Cross-Community Distance  D_cross(t)")
    ax.set_title("Dialect Merger Dynamics by Bridge Density (SBM)")
    ax.legend(frameon=True, loc="upper right")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 8.  Merger time bar chart  (E3-C)
# ---------------------------------------------------------------------------

def plot_merger_time_bar(
    merger_df: pd.DataFrame,
    p_out_values: list,
    out_path: str,
) -> None:
    """
    Bar chart of mean time-to-merger vs p_out.

    Parameters
    ----------
    merger_df : columns [p_out, merger_time_mean, merger_time_std]
    """
    _ensure_dir(out_path)
    colors = list(plt.cm.Blues(np.linspace(0.4, 1.0, len(p_out_values))))  # type: ignore[attr-defined]
    df = merger_df.sort_values("p_out")
    labels = [str(p) for p in df["p_out"]]
    means = df["merger_time_mean"].values
    stds = df["merger_time_std"].values

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, means, yerr=stds, color=colors, alpha=0.85,
                  edgecolor="white", capsize=5, width=0.6)
    ax.set_xlabel("Bridge Density  p_out")
    ax.set_ylabel("Mean Time to Merger (steps)")
    ax.set_title("Dialect Merger Speed vs Inter-Community Bridge Density")
    for bar, mean, std in zip(bars, means, stds):
        txt = f"{int(mean):,}" if mean < 1e9 else "No merger"
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            min(mean + std + 100, ax.get_ylim()[1] * 0.95),
            txt, ha="center", va="bottom", fontsize=9,
        )
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 9.  Ablation boxplot  (A-all)
# ---------------------------------------------------------------------------

def plot_ablation_boxplot(
    ablation_df: pd.DataFrame,
    out_path: str,
) -> None:
    """
    Two-panel boxplot: convergence time and final diversity across all ablations.

    Parameters
    ----------
    ablation_df : columns [condition, convergence_time, final_diversity]
    """
    _ensure_dir(out_path)
    condition_order = [
        "Baseline",
        "A1 – No homophily",
        "A2 – No prestige",
        "A3 – No noise",
        "A4 – Symmetric",
    ]
    # Keep only conditions that actually exist in data
    condition_order = [c for c in condition_order if c in ablation_df["condition"].values]
    palette = [_ABLATION_PALETTE.get(c, "grey") for c in condition_order]

    fig, axes = plt.subplots(1, 2, figsize=(13, 6))

    for ax, metric, ylabel, title in [
        (axes[0], "convergence_time",  "Convergence Time (steps)", "Convergence Time"),
        (axes[1], "final_diversity",   "Final Shannon Diversity H", "Final Diversity"),
    ]:
        data_by_cond = [
            ablation_df[ablation_df["condition"] == c][metric].values
            for c in condition_order
        ]
        bp = ax.boxplot(
            data_by_cond,
            patch_artist=True,
            widths=0.5,
            medianprops=dict(color="white", linewidth=2),
        )
        for patch, color in zip(bp["boxes"], palette):
            patch.set_facecolor(color)
            patch.set_alpha(0.85)
        ax.set_xticks(range(1, len(condition_order) + 1))
        ax.set_xticklabels(condition_order, rotation=20, ha="right", fontsize=9)
        ax.set_ylabel(ylabel)
        ax.set_title(title)

    fig.suptitle("Ablation Study: Component Contributions to Emergent Dynamics", fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()


# ---------------------------------------------------------------------------
# 10.  S-curve  (V1)
# ---------------------------------------------------------------------------

def plot_scurve(
    t: np.ndarray,
    adoption_matrix: np.ndarray,
    fit_params: dict,
    out_path: str,
) -> None:
    """
    Line plot of adoption fraction A(t) vs timestep.

    Parameters
    ----------
    t              : 1-D array of logged timesteps
    adoption_matrix : shape (n_runs, len(t)) — A(t) per run
    fit_params      : dict with keys 'L', 'k', 't0', 'r2'
    out_path        : save path
    """
    _ensure_dir(out_path)
    fig, ax = plt.subplots(figsize=(9, 6))

    # Individual runs in light grey
    for row in adoption_matrix:
        n = min(len(t), len(row))
        ax.plot(t[:n], row[:n], color="#AAAAAA", linewidth=0.8, alpha=0.5)

    # Mean in blue
    mean_adoption = adoption_matrix.mean(axis=0)
    ax.plot(t[:len(mean_adoption)], mean_adoption, color="#3498DB", linewidth=2.5,
            label=f"Mean A(t) across {len(adoption_matrix)} runs")

    # Logistic fit in red dashed
    if fit_params:
        L, k, t0, r2 = fit_params["L"], fit_params["k"], fit_params["t0"], fit_params["r2"]
        t_fit = np.linspace(t[0], t[-1], 500)
        fit_curve = L / (1.0 + np.exp(-k * (t_fit - t0)))
        ax.plot(t_fit, fit_curve, color="#E74C3C", linewidth=2, linestyle="--",
                label=f"Logistic fit  (R² = {r2:.3f})")

    ax.set_xlabel("Timestep")
    ax.set_ylabel("Adoption Fraction A(t)")
    ax.set_title("S-Curve Validation: Logistic Phonetic Innovation Spread")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# 11.  Heatmap  (H1, H2)
# ---------------------------------------------------------------------------

def plot_heatmap(
    pivot_df: pd.DataFrame,
    xlabel: str,
    ylabel: str,
    title: str,
    out_path: str,
) -> None:
    """
    Seaborn heatmap from a pivot DataFrame (rows = topologies, cols = param values).

    Parameters
    ----------
    pivot_df : pivot table indexed by topology label, columns by param values
    """
    _ensure_dir(out_path)
    fig, ax = plt.subplots(figsize=(10, 5))

    # Rename index to pretty labels
    pretty_index = [_TOPOLOGY_LABELS.get(str(idx), str(idx)) for idx in pivot_df.index]
    pivot_df = pivot_df.copy()
    pivot_df.index = pretty_index

    sns.heatmap(
        pivot_df,
        annot=True,
        fmt=".1f",
        cmap="YlOrRd",
        linewidths=0.5,
        linecolor="white",
        ax=ax,
        cbar_kws={"label": title},
    )
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
