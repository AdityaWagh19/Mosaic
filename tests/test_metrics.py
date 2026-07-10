"""
tests/test_metrics.py
=====================
5 tests (+ 2 extras) covering all Plan-3 metrics requirements:
  - shannon_diversity = 0 for identical accents (single cluster)
  - mean_pairwise_distance = 0 for identical accents
  - cross_community_distance = 0 when communities share the same accent
  - influence_residual_scores shape is (N,)
  - logistic_fit returns R² in [0, 1] for valid sigmoid data
"""
from __future__ import annotations

import numpy as np
import pytest

from simulation import metrics as m


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def identical_accents():
    """All agents share the same accent vector → fully converged population."""
    return np.tile([0.4, 0.5, 0.6, 0.3, 0.2, 0.1], (20, 1))


@pytest.fixture
def random_accents():
    """Diverse accent vectors drawn from a fixed RNG."""
    rng = np.random.default_rng(0)
    return rng.random((20, 6))


# ---------------------------------------------------------------------------
# Test 1 — shannon_diversity = 0 for identical accents
# ---------------------------------------------------------------------------

def test_shannon_diversity_zero_for_identical_accents(identical_accents):
    """
    When all agents share one accent, k-means puts them in a single cluster.
    H = -1·log(1) = 0.
    """
    h = m.shannon_diversity(identical_accents)
    assert h == pytest.approx(0.0, abs=1e-9)


# ---------------------------------------------------------------------------
# Test 2 — mean_pairwise_distance = 0 for identical accents
# ---------------------------------------------------------------------------

def test_mean_pairwise_distance_zero_for_identical_accents(identical_accents):
    """D(t) = 0 iff all agents share the same accent vector."""
    d = m.mean_pairwise_distance(identical_accents)
    assert d == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# Test 3 — cross_community_distance = 0 when communities converge
# ---------------------------------------------------------------------------

def test_cross_community_distance_zero_when_converged(identical_accents):
    """
    When both communities have the same mean accent, D_cross = ||μ_0 - μ_1|| = 0.
    """
    community_ids = np.array([0] * 10 + [1] * 10)
    d_cross = m.cross_community_distance(identical_accents, community_ids)
    assert d_cross == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# Test 4 — influence_residual_scores shape is (N,)
# ---------------------------------------------------------------------------

def test_influence_residual_scores_shape(random_accents):
    N = len(random_accents)
    final_mean = random_accents.mean(axis=0)
    scores = m.influence_residual_scores(random_accents, final_mean)
    assert scores.shape == (N,), f"Expected shape ({N},), got {scores.shape}"


# ---------------------------------------------------------------------------
# Test 5 — logistic_fit returns R² in [0, 1] for valid sigmoid data
# ---------------------------------------------------------------------------

def test_logistic_fit_r2_in_unit_interval():
    """
    Fit a logistic curve to near-perfect sigmoid data; R² should be close to 1.
    """
    t = np.arange(1, 51, dtype=float)
    # Ground-truth sigmoid: L=1, k=0.3, t0=25
    adoption = 1.0 / (1.0 + np.exp(-0.3 * (t - 25)))
    adoption += np.random.default_rng(0).normal(0, 0.01, len(t))
    adoption = np.clip(adoption, 0, 1)

    r2, params = m.logistic_fit(t, adoption)
    assert 0.0 <= r2 <= 1.0, f"R² = {r2} is outside [0, 1]"
    assert params.shape == (3,), "logistic_fit should return 3 parameters"


# ---------------------------------------------------------------------------
# Bonus 1 — mean_pairwise_distance is positive for diverse accents
# ---------------------------------------------------------------------------

def test_mean_pairwise_distance_positive_for_diverse_accents(random_accents):
    d = m.mean_pairwise_distance(random_accents)
    assert d > 0.0, "Expected positive pairwise distance for diverse accents"


# ---------------------------------------------------------------------------
# Bonus 2 — shannon_diversity_from_labels matches shannon_diversity
# ---------------------------------------------------------------------------

def test_shannon_diversity_from_labels_consistent(random_accents):
    """
    shannon_diversity_from_labels(labels) should equal shannon_diversity
    when both use the same KMeans fit.
    """
    from sklearn.cluster import KMeans

    km = KMeans(n_clusters=5, n_init=5, random_state=42)
    labels = km.fit_predict(random_accents)

    h_direct = m.shannon_diversity(random_accents, random_state=42)
    h_labels = m.shannon_diversity_from_labels(labels)

    # Both should be equal (same labels → same entropy)
    assert h_labels == pytest.approx(h_direct, abs=1e-9)
