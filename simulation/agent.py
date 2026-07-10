"""
simulation/agent.py
===================
AccentAgent — the individual speaker in the Mosaic ABM.

Each agent holds a 6-dimensional phonetic accent vector and implements the
prestige-weighted asymmetric accommodation rule (model.md §6):

    a_i(t+1) = a_i(t) + α_ij · (a_j(t) − a_i(t)) + ε

Where:
    α_ij = γ · centrality(j) · 𝟙[‖a_j − a_i‖ < θ]
    ε    ~ N(0, σ²·I)  (phonetic drift noise)

Design notes
------------
- The agent has NO step() method. Scheduling is edge-based and driven
  entirely by MosaicModel.step(). This sidesteps all Mesa 2.x scheduler
  complexity (implementation plan §Risk).
- Noise uses model.rng (np.random.default_rng) for full reproducibility.
- All operations are vectorised over the 6-dim accent vector.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import mesa
import numpy as np

if TYPE_CHECKING:
    # Avoid circular import at runtime; used only for type annotations.
    from simulation.model import MosaicModel


class AccentAgent(mesa.Agent):
    """
    A single speaker in the Mosaic simulation.

    Attributes
    ----------
    accent : np.ndarray, shape (6,), dtype float, values ∈ [0, 1]
        The agent's current phonetic accent vector (model.md §2).
    community_id : int
        Community membership — set at initialisation, fixed for the run.
    centrality : float ∈ [0, 1]
        Normalised degree centrality — used by other agents' update rules.
        This agent's *own* centrality affects how strongly it influences others.
    initial_accent : np.ndarray, shape (6,)
        Accent vector at t=0.  Read-only snapshot used by the influence
        residual score metric (model.md §8.6, Experiment 2).
    """

    # Narrow the type of self.model inherited from mesa.Agent (typed as mesa.Model)
    # so pyrefly resolves .config and .rng correctly.
    model: "MosaicModel"

    def __init__(
        self,
        unique_id: int,
        model: "MosaicModel",
        accent_vector: np.ndarray,
        community_id: int,
        centrality: float,
    ) -> None:
        super().__init__(unique_id, model)
        self.accent: np.ndarray = np.array(accent_vector, dtype=float)
        self.community_id: int = community_id
        self.centrality: float = centrality
        # Frozen snapshot at t=0 for influence residual score computation.
        self.initial_accent: np.ndarray = self.accent.copy()

    # ------------------------------------------------------------------
    # Core update rule (model.md §6)
    # ------------------------------------------------------------------

    def update(self, speaker: "AccentAgent") -> None:
        """
        Listener (self) accommodates toward speaker following model.md §6.

        Steps:
        1. Bounded confidence check: if ‖a_j − a_i‖ ≥ θ, return with no change.
        2. Compute accommodation step: α_ij = γ · centrality(j).
        3. Apply noise: ε ~ N(0, σ²·I).
        4. Update: a_i += α_ij · (a_j − a_i) + ε.
        5. Clip result to [0, 1].

        Parameters
        ----------
        speaker : AccentAgent — the agent being listened to (j in the equation).
        """
        diff = speaker.accent - self.accent
        distance = float(np.linalg.norm(diff))

        # Bounded confidence (model.md §6): no interaction if accents too distant
        if distance >= self.model.config.theta:
            return

        alpha_ij = self.model.config.gamma * speaker.centrality
        noise = self.model.rng.normal(0.0, self.model.config.sigma, size=6)

        self.accent = np.clip(
            self.accent + alpha_ij * diff + noise,
            0.0,
            1.0,
        )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AccentAgent(id={self.unique_id}, "
            f"community={self.community_id}, "
            f"centrality={self.centrality:.3f})"
        )
