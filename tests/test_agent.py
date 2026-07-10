"""
tests/test_agent.py
===================
7 tests covering all Plan-3 agent requirements:
  - Accent moves toward speaker proportional to gamma * centrality_j
  - Update suppressed when dist >= theta
  - gamma=0 → zero influence (no movement)
  - Noise applied when sigma > 0 (stochastic)
  - Noise = 0 when sigma = 0 (deterministic)
  - Clipping: result always in [0, 1]
  - Same seed → same update (deterministic)
"""
from __future__ import annotations

from dataclasses import replace

import mesa
import numpy as np
import pytest

from simulation.agent import AccentAgent
from simulation.config import SimConfig


# ---------------------------------------------------------------------------
# Minimal Mesa Model stub
# ---------------------------------------------------------------------------

class _StubModel(mesa.Model):
    """Minimal mesa.Model subclass that satisfies AccentAgent's cast() needs."""

    def __init__(self, theta: float = 0.5, gamma: float = 1.0,
                 sigma: float = 0.0, seed: int = 0) -> None:
        super().__init__()
        self.config = SimConfig(theta=theta, gamma=gamma, sigma=sigma)
        self.rng = np.random.default_rng(seed)


def _make_agent(model: _StubModel, uid: int = 0,
                accent: list[float] | None = None,
                centrality: float = 1.0,
                community_id: int = 0) -> AccentAgent:
    vec = np.array(accent if accent else [0.5] * 6, dtype=float)
    return AccentAgent(uid, model, vec, community_id, centrality)


# ---------------------------------------------------------------------------
# Test 1 — Accent moves toward speaker by gamma * centrality_j * diff
# ---------------------------------------------------------------------------

def test_accent_moves_toward_speaker_proportional():
    """
    With sigma=0 and known centrality, the movement should be exactly
    alpha_ij * (speaker - listener), where alpha_ij = gamma * centrality_j.
    theta=2.0 is larger than the L2 distance between the test vectors (≈1.11),
    so the bounded-confidence gate does NOT suppress the update.
    """
    gamma, centrality_j = 0.5, 0.8
    model = _StubModel(theta=2.0, gamma=gamma, sigma=0.0, seed=0)

    listener_vec = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    speaker_vec  = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4])

    listener = _make_agent(model, uid=0, accent=listener_vec.tolist())
    speaker  = _make_agent(model, uid=1, accent=speaker_vec.tolist(),
                           centrality=centrality_j)

    alpha = gamma * centrality_j
    expected = np.clip(listener_vec + alpha * (speaker_vec - listener_vec), 0.0, 1.0)
    listener.update(speaker)

    np.testing.assert_allclose(listener.accent, expected, atol=1e-12)


# ---------------------------------------------------------------------------
# Test 2 — Update suppressed when distance >= theta
# ---------------------------------------------------------------------------

def test_update_suppressed_when_distance_exceeds_theta():
    """
    If ||a_j - a_i|| >= theta, listener should not move at all.
    """
    theta = 0.01  # very small threshold
    model = _StubModel(theta=theta, gamma=1.0, sigma=0.0, seed=0)

    listener_vec = np.array([0.0] * 6)
    speaker_vec  = np.array([1.0] * 6)   # L2 distance = sqrt(6) >> theta

    listener_orig = listener_vec.copy()
    listener = _make_agent(model, uid=0, accent=listener_vec.tolist())
    speaker  = _make_agent(model, uid=1, accent=speaker_vec.tolist(), centrality=1.0)

    listener.update(speaker)
    np.testing.assert_array_equal(listener.accent, listener_orig)


# ---------------------------------------------------------------------------
# Test 3 — gamma = 0 produces zero influence (no movement)
# ---------------------------------------------------------------------------

def test_gamma_zero_produces_no_movement():
    """alpha_ij = gamma * centrality = 0 * 1 = 0, so diff term vanishes."""
    model = _StubModel(theta=2.0, gamma=0.0, sigma=0.0, seed=0)

    listener_vec = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
    speaker_vec  = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4])
    orig = listener_vec.copy()

    listener = _make_agent(model, uid=0, accent=listener_vec.tolist())
    speaker  = _make_agent(model, uid=1, accent=speaker_vec.tolist(), centrality=1.0)

    listener.update(speaker)
    np.testing.assert_array_equal(listener.accent, orig)


# ---------------------------------------------------------------------------
# Test 4 — Noise is applied when sigma > 0
# ---------------------------------------------------------------------------

def test_noise_applied_when_sigma_positive():
    """
    With sigma > 0, multiple updates from the same positions should NOT
    all produce the same result (because noise is stochastic).
    """
    model = _StubModel(theta=2.0, gamma=0.0, sigma=0.05, seed=42)
    # gamma=0 removes the deterministic drift; only noise remains

    results = []
    for _ in range(10):
        listener = _make_agent(model, uid=0, accent=[0.5] * 6)
        speaker  = _make_agent(model, uid=1, accent=[0.5] * 6, centrality=1.0)
        listener.update(speaker)
        results.append(listener.accent.copy())

    # If noise is applied, not all results should be identical
    first = results[0]
    assert not all(np.allclose(r, first) for r in results[1:]), (
        "All noise samples were identical — noise is not being applied"
    )


# ---------------------------------------------------------------------------
# Test 5 — Noise = 0 when sigma = 0 (deterministic update)
# ---------------------------------------------------------------------------

def test_no_noise_when_sigma_zero():
    """With sigma=0, the same inputs must always produce the same output."""
    model = _StubModel(theta=2.0, gamma=0.5, sigma=0.0, seed=0)

    listener_vec = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
    speaker_vec  = [0.8, 0.7, 0.6, 0.5, 0.4, 0.3]

    outputs = []
    for run in range(5):
        # Re-seed model each time to get same rng state
        model.rng = np.random.default_rng(0)
        l = _make_agent(model, uid=0, accent=listener_vec)
        s = _make_agent(model, uid=1, accent=speaker_vec, centrality=1.0)
        l.update(s)
        outputs.append(l.accent.copy())

    for out in outputs[1:]:
        np.testing.assert_array_equal(outputs[0], out)


# ---------------------------------------------------------------------------
# Test 6 — Clipping: result always in [0, 1]
# ---------------------------------------------------------------------------

def test_update_clips_result_to_unit_interval():
    """
    Extreme speaker accent + large gamma should be clipped to [0, 1].
    """
    model = _StubModel(theta=2.0, gamma=2.0, sigma=0.0, seed=0)

    listener = _make_agent(model, uid=0, accent=[0.05] * 6)
    speaker  = _make_agent(model, uid=1, accent=[0.99] * 6, centrality=1.0)

    listener.update(speaker)
    assert np.all(listener.accent >= 0.0), "Accent below 0 after update"
    assert np.all(listener.accent <= 1.0), "Accent above 1 after update"


# ---------------------------------------------------------------------------
# Test 7 — Same seed → same update (deterministic)
# ---------------------------------------------------------------------------

def test_same_seed_produces_same_update():
    """Full reproducibility: identical seed → bit-identical accent after update."""
    listener_vec = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    speaker_vec  = [0.7, 0.6, 0.5, 0.4, 0.3, 0.2]

    results = []
    for seed_val in (99, 99):       # same seed twice
        model = _StubModel(theta=2.0, gamma=0.5, sigma=0.02, seed=seed_val)
        l = _make_agent(model, uid=0, accent=listener_vec)
        s = _make_agent(model, uid=1, accent=speaker_vec, centrality=0.8)
        l.update(s)
        results.append(l.accent.copy())

    np.testing.assert_array_equal(results[0], results[1])
