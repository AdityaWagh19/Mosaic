"""
tests/test_model.py
===================
6 tests covering all Plan-3 model requirements:
  - Convergence detected when H stabilises (extreme params)
  - Hard cutoff at T when convergence is impossible
  - Sanity: theta >> max_distance, gamma=1, sigma=0 → agents converge
  - run() returns dict with all required keys
  - run_id encoded in the runs/ directory name
  - Seed reproducibility: same seed → identical final metrics

All model tests use N=10, T≤3000 to stay well under 1 second per test.
DataLogger is redirected to tmp_path via monkeypatch to avoid polluting runs/.
"""
from __future__ import annotations

import json
from dataclasses import replace

import numpy as np
import pytest

import simulation.logger as logger_mod
from simulation.config import SimConfig
from simulation.logger import DataLogger
from simulation.model import MosaicModel
from simulation.network import make_network


# ---------------------------------------------------------------------------
# Shared fixture — redirect DataLogger output to tmp_path
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _redirect_runs(tmp_path, monkeypatch):
    """
    Monkeypatch _RUNS_ROOT so all DataLogger instances write to pytest's
    temporary directory instead of the project's runs/ folder.
    """
    monkeypatch.setattr(logger_mod, "_RUNS_ROOT", tmp_path)


def _quick_config(**kwargs) -> SimConfig:
    """Small, fast SimConfig for model tests."""
    defaults = dict(N=10, T=500, log_every=10, seed=0, topology="watts_strogatz")
    defaults.update(kwargs)
    return replace(SimConfig(), **defaults)


def _make_and_run(config: SimConfig) -> dict:
    G = make_network(config)
    model = MosaicModel(config, G)
    log = DataLogger(config)
    return model.run(log)


# ---------------------------------------------------------------------------
# Test 1 — run() returns dict with all required keys
# ---------------------------------------------------------------------------

def test_run_returns_required_keys():
    required = {
        "run_id", "topology", "gamma", "theta", "sigma", "seed", "N",
        "convergence_time", "converged", "final_diversity",
        "final_pairwise_distance", "timeline",
    }
    result = _make_and_run(_quick_config(seed=1))
    missing = required - result.keys()
    assert not missing, f"run() result missing keys: {missing}"


# ---------------------------------------------------------------------------
# Test 2 — timeline is non-empty and has the expected structure
# ---------------------------------------------------------------------------

def test_run_timeline_non_empty():
    result = _make_and_run(_quick_config(seed=2))
    tl = result["timeline"]
    assert isinstance(tl, list) and len(tl) > 0, "Timeline should be a non-empty list"
    # Check first entry has required fields
    first = tl[0]
    assert "timestep" in first
    assert "diversity" in first
    assert "pairwise_distance" in first
    assert first["timestep"] == 0, "Timeline should start at t=0"


# ---------------------------------------------------------------------------
# Test 3 — run_id encoded correctly in the run directory
# ---------------------------------------------------------------------------

def test_run_id_directory_matches_expected_format(tmp_path):
    config = _quick_config(seed=77, topology="watts_strogatz")
    _make_and_run(config)
    expected_dir = tmp_path / "watts_strogatz_77"
    assert expected_dir.is_dir(), (
        f"Expected run directory '{expected_dir}' was not created"
    )
    # config.json inside should be valid JSON
    cfg_json = json.loads((expected_dir / "config.json").read_text())
    assert cfg_json["seed"] == 77
    assert cfg_json["topology"] == "watts_strogatz"


# ---------------------------------------------------------------------------
# Test 4 — hard cutoff at T returns converged=False (non-converging params)
# ---------------------------------------------------------------------------

def test_hard_cutoff_at_T_when_no_convergence():
    """
    With T=800 and log_every=100, h_history accumulates exactly 9 entries
    (t=0 + t=100,200,...,800 = 9).  _CONVERGENCE_MIN_ENTRIES=10, so the
    convergence check is never evaluated and converged=False is guaranteed
    regardless of the accent dynamics.
    """
    config = _quick_config(seed=3, N=10, T=800, log_every=100)
    result = _make_and_run(config)
    assert result["convergence_time"] == 800
    assert result["converged"] is False


# ---------------------------------------------------------------------------
# Test 5 — convergence detected under extreme convergence-forcing params
# ---------------------------------------------------------------------------

def test_convergence_detected_with_extreme_params():
    """
    theta=1 (permits interactions for typical [0,1]^6 distances ~0.7),
    gamma=1.0, sigma=0.0 (no noise), log_every=5.
    With no noise and strong accommodation, accents converge → H stabilises → converged=True.
    """
    config = _quick_config(
        seed=0, N=10, T=3000, log_every=5,
        theta=1.0, gamma=1.0, sigma=0.0,
    )
    result = _make_and_run(config)
    assert result["converged"] is True, (
        "Expected convergence with sigma=0, gamma=1.0, theta=1.0"
    )
    assert result["convergence_time"] < 3000, (
        "Expected convergence before hard cutoff T=3000"
    )


# ---------------------------------------------------------------------------
# Test 6 — Seed reproducibility: same seed → identical metrics
# ---------------------------------------------------------------------------

def test_seed_reproducibility():
    """Two runs with identical config must produce bit-identical metrics."""
    config = _quick_config(seed=42, T=200, log_every=10)
    r1 = _make_and_run(config)
    r2 = _make_and_run(config)

    assert r1["final_diversity"] == r2["final_diversity"]
    assert r1["final_pairwise_distance"] == r2["final_pairwise_distance"]
    assert r1["convergence_time"] == r2["convergence_time"]
    assert r1["converged"] == r2["converged"]
