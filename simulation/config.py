"""
simulation/config.py
====================
SimConfig — the single source of truth for all simulation parameters.

Every run begins by instantiating a SimConfig.  All defaults are defined here;
no magic numbers should appear anywhere else in the codebase.
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Valid topology names — referenced in __post_init__ validation
# ---------------------------------------------------------------------------
VALID_TOPOLOGIES: frozenset[str] = frozenset(
    {"er", "watts_strogatz", "ba", "sbm"}
)


@dataclass
class SimConfig:
    """
    All parameters required to run one Mosaic simulation.

    Topology keys
    -------------
    ``"er"``            Erdős-Rényi random graph
    ``"watts_strogatz"``Watts-Strogatz small-world graph
    ``"ba"``            Barabási-Albert scale-free graph
    ``"sbm"``           Stochastic Block Model (2-community)

    Serialisation
    -------------
    Use ``to_dict()`` to write a ``config.json`` at the start of every run,
    and ``from_dict()`` to reconstruct the object when reading saved runs.
    """

    # ------------------------------------------------------------------
    # Population
    # ------------------------------------------------------------------
    N: int = 200
    """Number of agents (speakers) in the simulation."""

    # ------------------------------------------------------------------
    # Network topology
    # ------------------------------------------------------------------
    topology: str = "watts_strogatz"
    """Graph topology.  Must be one of VALID_TOPOLOGIES."""

    # Erdős-Rényi
    p_er: float = 0.05
    """ER edge probability."""

    # Watts-Strogatz
    k_ws: int = 6
    """WS number of nearest neighbours (before rewiring)."""
    p_rewire: float = 0.1
    """WS rewiring probability."""

    # Barabási-Albert
    m_ba: int = 3
    """BA edges added per new node (controls hub formation)."""

    # Stochastic Block Model
    p_in: float = 0.15
    """SBM intra-community edge probability."""
    p_out: float = 0.02
    """SBM inter-community edge probability (bridge density)."""
    n_communities: int = 2
    """SBM number of communities.  Default = 2."""

    # ------------------------------------------------------------------
    # Simulation runtime
    # ------------------------------------------------------------------
    T: int = 10_000
    """Maximum number of timesteps (hard cutoff)."""
    log_every: int = 100
    """Log agent states every N timesteps."""

    # ------------------------------------------------------------------
    # Model parameters  (see model.md §6)
    # ------------------------------------------------------------------
    gamma: float = 1.0
    """Prestige weight — scales influence of degree centrality.  Range [0, 2]."""
    theta: float = 0.30
    """Bounded confidence threshold — max accent distance for interaction.  Range (0, 1]."""
    sigma: float = 0.01
    """Phonetic drift noise std deviation.  Range [0, 0.05]."""
    initial_sigma: float = 0.15
    """Initial accent vector spread across the population. Range [0.05, 0.5]."""
    
    # ------------------------------------------------------------------
    # Convergence Policy
    # ------------------------------------------------------------------
    W: int = 20
    """Window of logged timesteps to monitor for stationarity (for noisy runs)."""
    epsilon_max: float = 1e-4
    """Maximum permitted agent displacement over the window W to declare stationarity."""
    epsilon_distance: float = 1e-6
    """Maximum pairwise distance tolerance to declare absolute consensus (when sigma=0)."""

    # ------------------------------------------------------------------
    # Reproducibility
    # ------------------------------------------------------------------
    seed: int = 42
    """Base random seed.  Monte Carlo runs increment this by run index."""

    # ------------------------------------------------------------------
    # Monte Carlo
    # ------------------------------------------------------------------
    n_runs: int = 25
    """Number of independent replicates per experimental condition."""

    # ------------------------------------------------------------------
    # Experiment flags
    # ------------------------------------------------------------------
    symmetric: bool = False
    """Ablation A4: if True, both agents update per interaction (symmetric accommodation)."""

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def __post_init__(self) -> None:
        """Validate parameter constraints immediately after construction."""
        if self.topology not in VALID_TOPOLOGIES:
            raise ValueError(
                f"Invalid topology '{self.topology}'. "
                f"Must be one of: {sorted(VALID_TOPOLOGIES)}"
            )
        if self.N < 2:
            raise ValueError(f"N must be >= 2, got {self.N}")
        if self.T < 1:
            raise ValueError(f"T must be >= 1, got {self.T}")
        if self.log_every < 1:
            raise ValueError(f"log_every must be >= 1, got {self.log_every}")
        if not (0 < self.theta):
            raise ValueError(f"theta must be > 0, got {self.theta}")
        if self.sigma < 0:
            raise ValueError(f"sigma must be >= 0, got {self.sigma}")
        if self.gamma < 0:
            raise ValueError(f"gamma must be >= 0, got {self.gamma}")
        if self.n_runs < 1:
            raise ValueError(f"n_runs must be >= 1, got {self.n_runs}")
        if self.n_communities < 2:
            raise ValueError(
                f"n_communities must be >= 2, got {self.n_communities}"
            )

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        """
        Return a plain Python dict representation of this config.

        Suitable for JSON serialisation via ``json.dumps(config.to_dict())``.
        All field types are JSON-serialisable (int, float, str).
        """
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "SimConfig":
        """
        Construct a SimConfig from a dict (e.g. parsed from config.json).

        Unknown keys are silently ignored to allow forward compatibility —
        a config saved by a future version of Mosaic can still be loaded.
        """
        known_fields = {f.name for f in dataclasses.fields(cls)}
        filtered = {k: v for k, v in d.items() if k in known_fields}
        return cls(**filtered)

    def to_json(self) -> str:
        """Return a pretty-printed JSON string of this config."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "SimConfig":
        """Construct a SimConfig from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: str) -> None:
        """Write config.json to ``path``."""
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "SimConfig":
        """Load a SimConfig from a config.json file at ``path``."""
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_json(fh.read())

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    @property
    def run_id(self) -> str:
        """
        Deterministic run identifier: ``{topology}_{seed}``.

        Used as the sub-directory name inside ``runs/``.
        Deterministic means the same config always produces the same run_id,
        making results reproducible and easily cross-referenceable.
        """
        return f"{self.topology}_{self.seed}"
