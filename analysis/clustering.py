"""
analysis/clustering.py
----------------------
Unsupervised dialect-zone discovery on simulation final accent states.

Functions
---------
run_dbscan(accent_matrix)                          -> (labels, n_clusters)
silhouette(accent_matrix, labels)                  -> float
plot_cluster_overview(x_final, labels, ...)        -> None  (saves figure)
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score

log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")

from analysis._umap_compat import UMAP  # type: ignore[import-untyped]  # noqa: E402


# ---------------------------------------------------------------------------
# DBSCAN
# ---------------------------------------------------------------------------

def run_dbscan(
    accent_matrix: np.ndarray,
    min_samples: int = 5,
) -> tuple[np.ndarray, int]:
    """
    Run DBSCAN with eps estimated from the 5th percentile of pairwise distances.

    Returns
    -------
    labels        : (N,) int  — cluster IDs; noise points get label -1
    n_clusters    : int       — number of non-noise clusters found
    """
    from scipy.spatial.distance import pdist

    dists = pdist(accent_matrix)
    eps = float(np.percentile(dists, 5))
    eps = max(eps, 1e-4)

    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(accent_matrix)
    n_clusters = len(set(labels.tolist()) - {-1})
    noise_count = int((labels == -1).sum())
    log.info("DBSCAN  eps=%.4f  clusters=%d  noise=%d", eps, n_clusters, noise_count)
    return labels, n_clusters


# ---------------------------------------------------------------------------
# Silhouette score
# ---------------------------------------------------------------------------

def silhouette(
    accent_matrix: np.ndarray,
    labels: np.ndarray,
) -> float:
    """
    Silhouette score for a given labelling.

    Returns -1.0 when fewer than 2 distinct labels exist or data is trivial.
    """
    unique = set(labels.tolist()) - {-1}
    if len(unique) < 2:
        return -1.0
    mask = labels != -1
    if int(mask.sum()) < 2:
        return -1.0
    return float(silhouette_score(accent_matrix[mask], labels[mask]))


# ---------------------------------------------------------------------------
# Cluster overview figure
# ---------------------------------------------------------------------------

def plot_cluster_overview(
    x_final: np.ndarray,
    labels: np.ndarray,
    topology: str,
    out_path: Path,
) -> None:
    """
    2-D UMAP projection of final accent states, coloured by dialect cluster.

    Parameters
    ----------
    x_final  : (N, 6) float32 — final accent vectors
    labels   : (N,) int       — cluster IDs (from k-means or DBSCAN)
    topology : str            — run topology name for the title
    out_path : Path           — output PNG path
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    reducer = UMAP(n_components=2, random_state=42, n_neighbors=15, min_dist=0.1)
    embedding: np.ndarray = reducer.fit_transform(x_final)

    unique_labels = sorted(set(labels.tolist()))
    n_real = len([k for k in unique_labels if k != -1])
    cmap = plt.cm.get_cmap("tab10", max(n_real, 1))  # type: ignore[attr-defined]

    fig, ax = plt.subplots(figsize=(7, 6))
    real_idx = 0
    for k in unique_labels:
        mask = labels == k
        if k == -1:
            color = "#AAAAAA"
            lab   = "noise"
        else:
            color = cmap(real_idx)
            lab   = f"Cluster {k}"
            real_idx += 1
        ax.scatter(
            embedding[mask, 0],
            embedding[mask, 1],
            c=[color],
            s=28,
            alpha=0.75,
            label=lab,
            edgecolors="none",
        )

    ax.set_title(
        f"Dialect Clusters ({topology.replace('_', ' ').title()}) — UMAP projection",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel("UMAP 1", fontsize=10)
    ax.set_ylabel("UMAP 2", fontsize=10)
    ax.legend(fontsize=9, markerscale=1.5, framealpha=0.9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    log.info("Cluster map saved: %s", out_path)
