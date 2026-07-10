"""
simulation/metrics.py
=====================
Pure metric functions for the Mosaic ABM.

All functions take NumPy arrays as input and return scalars or arrays.
No simulation state is read here — all inputs are passed explicitly.

Extracted to this module for:
  - Independent testability (Plan 3: test_metrics.py has no simulation deps)
  - Reuse across experiment scripts (Plan 4) and ML layer (Plan 5)
  - Clean separation between model mechanics and measurement logic

Seven public functions as specified in architecture.md §3 and model.md §8:
  1. shannon_diversity          — H(t) via k-means cluster entropy
  2. shannon_diversity_from_labels — H from pre-computed labels (model caching)
  3. mean_pairwise_distance     — D(t) via scipy pdist
  4. cross_community_distance   — D_cross(t) for SBM runs
  5. influence_residual_scores  — s_i per agent (Experiment 2)
  6. adoption_fraction          — A(t) for S-curve experiment
  7. spearman_centrality_influence — Spearman r (centrality vs influence)
  8. logistic_fit               — logistic curve fit, returns R²
"""

from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _shannon_from_labels(labels: np.ndarray) -> float:
    """
    Shannon entropy H = -Σ p_k · log(p_k) from integer cluster labels.

    H = 0 when all agents share one cluster (perfect convergence).
    H → log(K) when agents are evenly spread across K clusters (maximum diversity).
    """
    counts = np.bincount(labels)
    p = counts / counts.sum()
    p = p[p > 0]          # drop zero-count clusters to avoid log(0)
    return float(-np.sum(p * np.log(p)))


# ---------------------------------------------------------------------------
# 1. Shannon Diversity  (H(t))
# ---------------------------------------------------------------------------

def shannon_diversity(
    accent_matrix: np.ndarray,
    n_clusters: int = 5,
    random_state: int = 42,
) -> float:
    """
    Fit k-means on the accent matrix and return Shannon diversity H.

    This function fits a fresh KMeans every call.  For the hot path inside
    MosaicModel.run(), use the cached-KMeans approach with
    ``shannon_diversity_from_labels`` instead.

    Parameters
    ----------
    accent_matrix : shape (N, 6) — current accent vectors for all agents
    n_clusters    : number of accent clusters (default 5 per model.md §8.1)
    random_state  : RNG seed for KMeans reproducibility

    Returns
    -------
    h : Shannon diversity index (float ≥ 0)
    """
    k = min(n_clusters, len(accent_matrix))
    km = KMeans(n_clusters=k, n_init=5, random_state=random_state)
    labels = km.fit_predict(accent_matrix)
    return _shannon_from_labels(labels)


def shannon_diversity_from_labels(labels: np.ndarray) -> float:
    """
    Compute Shannon diversity from pre-computed k-means cluster labels.

    Called by MosaicModel when it uses cached KMeans centroids between refits
    (refit every 500 steps; predict on intervening log steps).

    Parameters
    ----------
    labels : integer cluster assignment per agent, shape (N,)

    Returns
    -------
    h : Shannon diversity index (float ≥ 0)
    """
    return _shannon_from_labels(labels)


# ---------------------------------------------------------------------------
# 2. Mean Pairwise Accent Distance  (D(t))
# ---------------------------------------------------------------------------

def mean_pairwise_distance(accent_matrix: np.ndarray) -> float:
    """
    Average Euclidean distance between all agent pairs.

    D(t) = (2 / N(N-1)) · Σ_{i<j} ||a_i(t) − a_j(t)||

    Uses scipy.spatial.distance.pdist for vectorised computation (~10x faster
    than nested Python loops for N=200).

    Parameters
    ----------
    accent_matrix : shape (N, 6) — current accent vectors

    Returns
    -------
    d : mean pairwise distance (float ≥ 0)
    """
    if len(accent_matrix) < 2:
        return 0.0
    return float(pdist(accent_matrix, metric="euclidean").mean())


# ---------------------------------------------------------------------------
# 3. Cross-Community Accent Distance  (D_cross(t))
# ---------------------------------------------------------------------------

def cross_community_distance(
    accent_matrix: np.ndarray,
    community_ids: np.ndarray,
) -> float:
    """
    Euclidean distance between the mean accent vectors of two communities.

    D_cross(t) = ||μ_0(t) − μ_1(t)||

    Meaningful only for SBM (2-community) runs.  Tracks dialect merger:
    D_cross → 0 means the two communities have fully converged to one accent.

    Parameters
    ----------
    accent_matrix  : shape (N, 6) — current accent vectors
    community_ids  : shape (N,)   — integer community label per agent

    Returns
    -------
    d_cross : float ≥ 0; 0.0 if fewer than 2 communities are present
    """
    unique_ids = np.unique(community_ids)
    if len(unique_ids) < 2:
        return 0.0
    mu0 = accent_matrix[community_ids == unique_ids[0]].mean(axis=0)
    mu1 = accent_matrix[community_ids == unique_ids[1]].mean(axis=0)
    return float(np.linalg.norm(mu0 - mu1))


# ---------------------------------------------------------------------------
# 4. Influence Residual Scores  (s_i)
# ---------------------------------------------------------------------------

def influence_residual_scores(
    initial_accents: np.ndarray,
    final_mean_accent: np.ndarray,
) -> np.ndarray:
    """
    Per-agent influence residual: s_i = −||a_i(0) − μ_final||

    High s_i (close to zero) means the population converged toward where
    agent i started — a direct proxy for how much that agent "guided" the
    population consensus (model.md §8.6).

    Used in Experiment 2: Spearman correlation between s_i and centrality
    tests whether high-centrality agents disproportionately shape outcomes.

    Parameters
    ----------
    initial_accents   : shape (N, 6) — accent vectors at t=0
    final_mean_accent : shape (6,)   — population mean at convergence

    Returns
    -------
    scores : shape (N,) — s_i per agent (more negative = less influential)
    """
    residuals = np.linalg.norm(initial_accents - final_mean_accent, axis=1)
    return -residuals  # negated: higher score → more influential


# ---------------------------------------------------------------------------
# 5. Adoption Fraction  (A(t))
# ---------------------------------------------------------------------------

def adoption_fraction(
    accent_matrix: np.ndarray,
    initial_dim0: float,
    threshold: float = 0.2,
) -> float:
    """
    Fraction of agents that have adopted a phonetic innovation on dimension 0.

    Adoption is defined as accent dimension 0 exceeding ``initial_dim0 + threshold``.
    Used in the S-curve experiment (model.md §8.5).

    Parameters
    ----------
    accent_matrix : current accent vectors, shape (N, 6)
    initial_dim0  : mean of dim-0 across all agents at t=0
    threshold     : adoption threshold above initial mean (default 0.2)

    Returns
    -------
    fraction : float in [0, 1]
    """
    adopted = int((accent_matrix[:, 0] > initial_dim0 + threshold).sum())
    return float(adopted / len(accent_matrix))


# ---------------------------------------------------------------------------
# 6. Spearman Centrality–Influence Correlation
# ---------------------------------------------------------------------------

def spearman_centrality_influence(
    centrality: np.ndarray,
    influence_scores: np.ndarray,
) -> tuple[float, float]:
    """
    Spearman rank correlation between agent centrality and influence scores.

    Expected result (model.md §8.6): Spearman r increases with γ; r ≈ 0 when γ = 0.

    Parameters
    ----------
    centrality       : shape (N,) — normalised degree centrality per agent
    influence_scores : shape (N,) — s_i scores from influence_residual_scores()

    Returns
    -------
    rho    : Spearman correlation coefficient (float in [-1, 1])
    pvalue : two-sided p-value (float in [0, 1])
    """
    result = stats.spearmanr(centrality, influence_scores)
    return float(result.statistic), float(result.pvalue)


# ---------------------------------------------------------------------------
# 7. Logistic Curve Fit  (S-curve experiment)
# ---------------------------------------------------------------------------

def logistic_fit(
    t: np.ndarray,
    adoption: np.ndarray,
) -> tuple[float, np.ndarray]:
    """
    Fit a three-parameter logistic curve to adoption-fraction-over-time data.

    f(t) = L / (1 + exp(−k · (t − t₀)))

    Parameters
    ----------
    t        : timesteps, shape (M,)
    adoption : adoption fraction at each timestep, shape (M,) ∈ [0, 1]

    Returns
    -------
    r_squared : goodness-of-fit R² (float; 1.0 = perfect fit)
    params    : ndarray [L, k, t0] — fitted logistic parameters

    Notes
    -----
    Returns (0.0, zeros) if curve_fit does not converge.
    AC5 (mvp.md) requires R² > 0.85 for the S-curve experiment.
    """
    def _logistic(t: np.ndarray, L: float, k: float, t0: float) -> np.ndarray:
        return L / (1.0 + np.exp(-k * (t - t0)))

    try:
        p0 = [float(adoption.max()), 1e-3, float(t[len(t) // 2])]
        params, _ = curve_fit(
            _logistic, t, adoption, p0=p0,
            bounds=([0, 0, t.min()], [1, np.inf, t.max()]),
            maxfev=10_000,
        )
        y_pred = _logistic(t, *params)
        ss_res = float(np.sum((adoption - y_pred) ** 2))
        ss_tot = float(np.sum((adoption - adoption.mean()) ** 2))
        r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    except (RuntimeError, ValueError):
        r_squared = 0.0
        params = np.zeros(3)

    return float(r_squared), params
