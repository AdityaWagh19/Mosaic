"""
simulation/model.py
===================
MosaicModel — the simulation orchestrator.

Owns the network, all agents, the random edge scheduler, and the simulation
loop.  Implements entropy-based convergence detection with a cached k-means.

Key design decisions (implementation plan §Plan 2):
  - Edge-based scheduling: one edge sampled per step, only listener updates.
    This sidesteps all Mesa 2.x scheduler complexity.
  - k-means refitted every 500 steps for H(t); cached predict() on off-steps.
  - Convergence window: last 200 logged H values, std < δ = 0.001.
  - All random calls go through self.rng (np.random.default_rng(seed)) for
    full reproducibility across agents and model.
"""

from __future__ import annotations

import collections
import logging
from dataclasses import replace
from typing import TYPE_CHECKING

import mesa
import numpy as np
from sklearn.cluster import KMeans

from simulation import metrics as m
from simulation.agent import AccentAgent
from simulation.config import SimConfig
from simulation.network import (
    COMMUNITY_PROTOTYPES,
    SIGMA_INIT_COMMUNITY,
    SIGMA_INIT_SINGLE,
    SINGLE_COMMUNITY_PROTOTYPE,
)

if TYPE_CHECKING:
    from simulation.logger import DataLogger

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Convergence constants (model.md §7, implementation plan §Plan 2)
# ---------------------------------------------------------------------------
_CONVERGENCE_DELTA: float = 0.001  # max std of H history to declare convergence
_CONVERGENCE_WINDOW: int = 200      # length of rolling H history (logged entries)
_CONVERGENCE_MIN_ENTRIES: int = 10  # minimum log entries before checking
_KMEANS_REFIT_EVERY: int = 500      # refit k-means every N timesteps
_KMEANS_N_CLUSTERS: int = 5         # number of accent clusters (model.md §8.1)
_KMEANS_N_INIT: int = 5             # k-means random restarts


class MosaicModel(mesa.Model):
    """
    The Mosaic ABM: population of AccentAgents on a social network.

    Parameters
    ----------
    config : SimConfig — all parameters for this run.
    G      : nx.Graph  — the social network (pre-built by make_network()).
    """

    def __init__(self, config: SimConfig, G) -> None:  # G: nx.Graph
        super().__init__()
        self.config = config
        self.G = G

        # All random operations go through this single RNG for reproducibility.
        self.rng = np.random.default_rng(config.seed)

        # Precompute edge list once — avoids repeated list(G.edges()) in the loop.
        self.edge_list: list[tuple[int, int]] = list(G.edges())
        self._n_edges: int = len(self.edge_list)

        if self._n_edges == 0:
            raise ValueError(
                f"Graph has no edges — simulation cannot proceed. "
                f"Check topology='{config.topology}' parameters."
            )

        # Instantiate one AccentAgent per graph node.
        self.agents_map: dict[int, AccentAgent] = {}
        for node_id in G.nodes():
            accent = self._init_accent(
                community_id=int(G.nodes[node_id]["community_id"])
            )
            agent = AccentAgent(
                unique_id=node_id,
                model=self,
                accent_vector=accent,
                community_id=int(G.nodes[node_id]["community_id"]),
                centrality=float(G.nodes[node_id]["centrality"]),
            )
            self.agents_map[node_id] = agent

        # k-means state for H(t) computation
        self._km: KMeans | None = None
        self._km_next_refit: int = 0  # refit when t >= this value

    # ------------------------------------------------------------------
    # Accent initialisation  (model.md §3)
    # ------------------------------------------------------------------

    def _init_accent(self, community_id: int) -> np.ndarray:
        """
        Draw an initial accent vector from the appropriate Gaussian.

        SBM (n_communities == 2):
            Community c ~ N(μ_c, σ_init²·I),  σ_init = 0.05
            μ_c from COMMUNITY_PROTOTYPES (model.md §3)

        Single-community (ER, WS, BA):
            ~ N([0.5]*6, σ_init²·I),  σ_init = 0.15
        """
        if self.config.topology == "sbm":
            prototype = COMMUNITY_PROTOTYPES.get(
                community_id,
                SINGLE_COMMUNITY_PROTOTYPE,   # fallback for unexpected community IDs
            )
            sigma = SIGMA_INIT_COMMUNITY
        else:
            prototype = SINGLE_COMMUNITY_PROTOTYPE
            sigma = SIGMA_INIT_SINGLE

        noise = self.rng.normal(0.0, sigma, size=6)
        return np.clip(prototype + noise, 0.0, 1.0)

    # ------------------------------------------------------------------
    # H(t) computation with k-means caching
    # ------------------------------------------------------------------

    def _get_accent_matrix(self) -> np.ndarray:
        """Stack all agent accent vectors into an (N, 6) matrix."""
        return np.stack(
            [self.agents_map[node].accent for node in sorted(self.agents_map)]
        )

    def _compute_h(self, accent_matrix: np.ndarray, t: int) -> tuple[float, np.ndarray]:
        """
        Compute H(t) using a cached k-means (refit every _KMEANS_REFIT_EVERY steps).

        Returns (h, labels) where labels is the cluster assignment per agent.
        """
        if self._km is None or t >= self._km_next_refit:
            self._km = KMeans(
                n_clusters=_KMEANS_N_CLUSTERS,
                n_init=_KMEANS_N_INIT,
                random_state=self.config.seed,
            )
            self._km.fit(accent_matrix)
            self._km_next_refit = t + _KMEANS_REFIT_EVERY

        labels = self._km.predict(accent_matrix)
        h = m.shannon_diversity_from_labels(labels)
        return h, labels

    # ------------------------------------------------------------------
    # Single simulation step  (model.md §5)
    # ------------------------------------------------------------------

    def step(self) -> None:
        """
        One timestep: sample a random edge, listener accommodates toward speaker.

        Edge direction: (i, j) → i is the listener, j is the speaker.
        Only i updates (asymmetric interaction, model.md §5).
        """
        idx = self.rng.integers(self._n_edges)
        i, j = self.edge_list[idx]
        self.agents_map[i].update(self.agents_map[j])

    # ------------------------------------------------------------------
    # Full simulation run  (model.md §7)
    # ------------------------------------------------------------------

    def run(self, log: "DataLogger") -> dict:
        """
        Execute the simulation for T steps or until convergence.

        Convergence criterion (model.md §7):
            std(last _CONVERGENCE_WINDOW logged H values) < _CONVERGENCE_DELTA
            with at least _CONVERGENCE_MIN_ENTRIES before checking.

        Logging (model.md §9):
            Every config.log_every steps: snapshot all agents to logger.

        Parameters
        ----------
        log : DataLogger — receives per-step snapshots and final metrics.

        Returns
        -------
        metrics : dict with keys:
            run_id, topology, gamma, theta, sigma, seed,
            convergence_time, converged,
            final_diversity, final_pairwise_distance, timeline
        """
        T = self.config.T
        log_every = self.config.log_every
        config = self.config

        h_history: collections.deque[float] = collections.deque(
            maxlen=_CONVERGENCE_WINDOW
        )
        timeline: list[dict] = []

        converged = False
        t_conv = T  # default: hit hard cutoff

        # ---- Log initial state (t=0) --------------------------------
        accent_mat = self._get_accent_matrix()
        h0, _ = self._compute_h(accent_mat, 0)
        d0 = m.mean_pairwise_distance(accent_mat)
        log.log(0, self.agents_map)
        h_history.append(h0)
        timeline.append({"timestep": 0, "diversity": round(h0, 6), "pairwise_distance": round(d0, 6)})

        # ---- Main loop ----------------------------------------------
        for t in range(1, T + 1):
            self.step()

            if t % log_every == 0:
                accent_mat = self._get_accent_matrix()
                h, _ = self._compute_h(accent_mat, t)
                d = m.mean_pairwise_distance(accent_mat)

                log.log(t, self.agents_map)
                h_history.append(h)
                timeline.append({
                    "timestep": t,
                    "diversity": round(h, 6),
                    "pairwise_distance": round(d, 6),
                })

                # Convergence check
                if (
                    len(h_history) >= _CONVERGENCE_MIN_ENTRIES
                    and float(np.std(h_history)) < _CONVERGENCE_DELTA
                ):
                    converged = True
                    t_conv = t
                    log.log(t, self.agents_map)  # ensure final state is logged
                    break

        # ---- Final metrics ------------------------------------------
        final_accent_mat = self._get_accent_matrix()
        final_h, _ = self._compute_h(final_accent_mat, t_conv)
        final_d = m.mean_pairwise_distance(final_accent_mat)

        metrics_dict = {
            "run_id":                  config.run_id,
            "topology":                config.topology,
            "gamma":                   config.gamma,
            "theta":                   config.theta,
            "sigma":                   config.sigma,
            "seed":                    config.seed,
            "N":                       config.N,
            "convergence_time":        t_conv,
            "converged":               converged,
            "final_diversity":         round(final_h, 6),
            "final_pairwise_distance": round(final_d, 6),
        }

        log.close(metrics_dict, timeline)

        logger.info(
            "Run %s complete | converged=%s | t_conv=%d | H=%.4f | D=%.4f",
            config.run_id, converged, t_conv, final_h, final_d,
        )

        return {**metrics_dict, "timeline": timeline}
