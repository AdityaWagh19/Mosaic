"""
tests/test_config.py
====================
Unit tests for simulation/config.py (SimConfig).

These tests are part of Phase 1 (Foundation) and verify:
  1. Default field values match architecture.md §3.1
  2. JSON round-trip serialisation is lossless
  3. from_dict silently ignores unknown keys
  4. Invalid topology raises ValueError

All tests run without any simulation, network, or ML dependencies.
"""

import json

import pytest

from simulation.config import SimConfig, VALID_TOPOLOGIES


# ---------------------------------------------------------------------------
# Test 1 — Default values
# ---------------------------------------------------------------------------
class TestDefaultValues:
    """SimConfig() must match every default in architecture.md §3.1."""

    def test_population_defaults(self):
        cfg = SimConfig()
        assert cfg.N == 200

    def test_network_topology_default(self):
        cfg = SimConfig()
        assert cfg.topology == "watts_strogatz"

    def test_er_param_defaults(self):
        cfg = SimConfig()
        assert cfg.p_er == pytest.approx(0.05)

    def test_ws_param_defaults(self):
        cfg = SimConfig()
        assert cfg.k_ws == 6
        assert cfg.p_rewire == pytest.approx(0.1)

    def test_ba_param_defaults(self):
        cfg = SimConfig()
        assert cfg.m_ba == 3

    def test_sbm_param_defaults(self):
        cfg = SimConfig()
        assert cfg.p_in == pytest.approx(0.15)
        assert cfg.p_out == pytest.approx(0.02)
        assert cfg.n_communities == 2

    def test_simulation_runtime_defaults(self):
        cfg = SimConfig()
        assert cfg.T == 10_000
        assert cfg.log_every == 100

    def test_model_param_defaults(self):
        cfg = SimConfig()
        assert cfg.gamma == pytest.approx(1.0)
        assert cfg.theta == pytest.approx(0.30)
        assert cfg.sigma == pytest.approx(0.01)

    def test_reproducibility_defaults(self):
        cfg = SimConfig()
        assert cfg.seed == 42

    def test_monte_carlo_defaults(self):
        cfg = SimConfig()
        assert cfg.n_runs == 25


# ---------------------------------------------------------------------------
# Test 2 — JSON round-trip
# ---------------------------------------------------------------------------
class TestSerialisation:
    """to_dict / from_dict must be perfectly inverse operations."""

    def test_round_trip_default_config(self):
        original = SimConfig()
        recovered = SimConfig.from_dict(original.to_dict())
        assert original == recovered

    def test_round_trip_custom_config(self):
        original = SimConfig(
            N=100, topology="ba", gamma=1.5, theta=0.20,
            sigma=0.005, seed=99, n_runs=10, m_ba=5
        )
        recovered = SimConfig.from_dict(original.to_dict())
        assert original == recovered

    def test_to_dict_returns_plain_types(self):
        """All values in the dict must be JSON-serialisable without custom encoders."""
        d = SimConfig().to_dict()
        # This should not raise
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_json_string_round_trip(self):
        original = SimConfig(topology="sbm", p_out=0.05, seed=7)
        recovered = SimConfig.from_json(original.to_json())
        assert original == recovered

    def test_run_id_format(self):
        cfg = SimConfig(topology="er", seed=123)
        assert cfg.run_id == "er_123"

    def test_save_and_load(self, tmp_path):
        """save() writes a file that load() can reconstruct identically."""
        path = str(tmp_path / "config.json")
        original = SimConfig(topology="sbm", gamma=2.0, seed=55)
        original.save(path)
        loaded = SimConfig.load(path)
        assert original == loaded


# ---------------------------------------------------------------------------
# Test 3 — Extra keys in from_dict are silently ignored
# ---------------------------------------------------------------------------
class TestForwardCompatibility:
    """from_dict must not raise when the dict contains unknown fields."""

    def test_extra_keys_ignored(self):
        d = SimConfig().to_dict()
        d["unknown_future_field"] = "some_value"
        d["another_unknown"] = 42
        result = SimConfig.from_dict(d)  # must not raise
        assert result == SimConfig()

    def test_partial_dict_uses_defaults(self):
        """from_dict with only a subset of keys fills the rest with defaults."""
        result = SimConfig.from_dict({"topology": "er", "seed": 10})
        assert result.topology == "er"
        assert result.seed == 10
        # All other fields should be at their defaults
        defaults = SimConfig()
        assert result.N == defaults.N
        assert result.T == defaults.T


# ---------------------------------------------------------------------------
# Test 4 — Validation: invalid inputs raise ValueError
# ---------------------------------------------------------------------------
class TestValidation:
    """__post_init__ must enforce parameter constraints."""

    def test_invalid_topology_raises(self):
        with pytest.raises(ValueError, match="topology"):
            SimConfig(topology="random_graph")

    def test_all_valid_topologies_accepted(self):
        for topo in VALID_TOPOLOGIES:
            cfg = SimConfig(topology=topo)
            assert cfg.topology == topo

    def test_n_less_than_2_raises(self):
        with pytest.raises(ValueError, match="N"):
            SimConfig(N=1)

    def test_t_zero_raises(self):
        with pytest.raises(ValueError, match="T"):
            SimConfig(T=0)

    def test_theta_zero_raises(self):
        with pytest.raises(ValueError, match="theta"):
            SimConfig(theta=0.0)

    def test_negative_sigma_raises(self):
        with pytest.raises(ValueError, match="sigma"):
            SimConfig(sigma=-0.01)

    def test_negative_gamma_raises(self):
        with pytest.raises(ValueError, match="gamma"):
            SimConfig(gamma=-1.0)

    def test_n_runs_zero_raises(self):
        with pytest.raises(ValueError, match="n_runs"):
            SimConfig(n_runs=0)
