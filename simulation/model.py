"""
simulation/model.py
===================
MosaicModel — the simulation orchestrator.

Owns the network, all agents, the random edge scheduler, and the simulation
loop. Computes entropy with cached k-means and detects consensus from maximum
pairwise accent separation.

Key design decisions (implementation plan §Plan 2):
  - Edge-based scheduling: one edge sampled per step, only listener updates.
    This sidesteps all Mesa 2.x scheduler complexity.
  - k-means refitted every 500 steps for H(t); cached predict() on off-steps.
  - Convergence window: last 200 logged H values, std < δ = 0.001.
  - All random calls go through self.rng (np.random.default_rng(seed)) for
    full reproducibility across agents and model.
"""

from __future__ import annotations

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
    SINGLE_COMMUNITY_PROTOTYPE,
)

if TYPE_CHECKING:
    from simulation.logger import DataLogger

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Convergence constants (model.md §7, implementation plan §Plan 2)
# ---------------------------------------------------------------------------
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

        self._accepted_since_log: int = 0
        self._rejected_since_log: int = 0

    # ------------------------------------------------------------------
    # Accent initialisation  (model.md §3)
    # ------------------------------------------------------------------

    def _init_accent(self, community_id: int) -> np.ndarray:
        """
        Draw an initial accent vector from the appropriate Gaussian.

        SBM (n_communities == 2):
            Community c ~ N(μ_c, σ_init²·I),  σ_init = config.initial_sigma
            μ_c from COMMUNITY_PROTOTYPES (model.md §3)

        Single-community (ER, WS, BA):
            ~ N([0.5]*6, σ_init²·I),  σ_init = config.initial_sigma
        """
        if self.config.topology == "sbm":
            prototype = COMMUNITY_PROTOTYPES.get(
                community_id,
                SINGLE_COMMUNITY_PROTOTYPE,   # fallback for unexpected community IDs
            )
        else:
            prototype = SINGLE_COMMUNITY_PROTOTYPE

        sigma = self.config.initial_sigma
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

    def _compute_h(
        self,
        accent_matrix: np.ndarray,
        t: int,
        *,
        is_consensus: bool = False,
    ) -> tuple[float, np.ndarray]:
        """
        Compute H(t) using a cached k-means (refit every _KMEANS_REFIT_EVERY steps).

        Returns (h, labels) where labels is the cluster assignment per agent.
        """
        if is_consensus:
            # A fixed-k KMeans partition must not turn floating-point residue
            # into apparent accent diversity after the population agrees.
            return 0.0, np.zeros(len(accent_matrix), dtype=int)

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
        One timestep: update agent accents from a randomly sampled edge.

        Asymmetric mode: only the listener accommodates to the speaker.
        Symmetric mode: both agents update from pre-step accent snapshots.
        """
        import types

        idx = self.rng.integers(self._n_edges)
        i, j = self.edge_list[idx]  # type: ignore[misc]

        if not getattr(self.config, 'symmetric', False):
            accepted = self.agents_map[i].update(self.agents_map[j])
        else:
            # Capture pre-step accents so both updates are simultaneous.
            proxy_j = types.SimpleNamespace(
                accent=self.agents_map[j].accent.copy(),
                centrality=self.agents_map[j].centrality,
            )
            proxy_i = types.SimpleNamespace(
                accent=self.agents_map[i].accent.copy(),
                centrality=self.agents_map[i].centrality,
            )
            acc_i = self.agents_map[i].update(proxy_j)  # type: ignore[arg-type]
            acc_j = self.agents_map[j].update(proxy_i)  # type: ignore[arg-type]
            accepted = acc_i or acc_j

        if accepted:
            self._accepted_since_log += 1
        else:
            self._rejected_since_log += 1

    # ------------------------------------------------------------------
    # Full simulation run  (model.md §7)
    # ------------------------------------------------------------------

    def run(self, log: "DataLogger") -> dict:
        """
        Execute the simulation for T steps or until convergence.

        Convergence criteria:
            Consensus: If sigma == 0, maximum pairwise distance <= epsilon_distance.
            Stationarity: If sigma > 0, max displacement over window W <= epsilon_max.

        Logging (model.md §9):
            Every config.log_every steps: snapshot all agents to logger.

        Parameters
        ----------
        log : DataLogger — receives per-step snapshots and final metrics.

        Returns
        -------
        metrics : dict with keys:
            run_id, topology, gamma, theta, sigma, seed,
            convergence_time, converged, termination_reason,
            final_diversity, final_pairwise_distance, timeline
        """
        T = self.config.T
        log_every = self.config.log_every
        config = self.config

        timeline: list[dict] = []
        displacements: list[float] = []
        prev_accent_mat = self._get_accent_matrix()

        converged = False
        termination_reason = "Maximum interactions reached"
        t_conv = T

        # ---- Log initial state (t=0) --------------------------------
        d0, diameter0 = m.pairwise_distance_summary(prev_accent_mat)
        
        # Check eligibility for t=0
        eligible_edges = 0
        for i, j in self.edge_list:
            if np.linalg.norm(self.agents_map[i].accent - self.agents_map[j].accent) < config.theta:
                eligible_edges += 1
        eligible_frac0 = eligible_edges / self._n_edges if self._n_edges > 0 else 0.0

        h0, _ = self._compute_h(
            prev_accent_mat, 0, is_consensus=diameter0 <= config.epsilon_distance
        )
        log.log(0, self.agents_map)
        timeline.append({
            "timestep": 0, 
            "diversity": round(h0, 6), 
            "pairwise_distance": round(d0, 6),
            "accepted_interactions": 0,
            "rejected_interactions": 0,
            "eligible_edges_fraction": round(eligible_frac0, 4)
        })

        if config.sigma == 0 and diameter0 <= config.epsilon_distance:
            converged = True
            termination_reason = "Consensus reached"
            t_conv = 0

        # ---- Main loop ----------------------------------------------
        for t in range(1, T + 1):
            if converged:
                break
            self.step()

            if t % log_every == 0:
                accent_mat = self._get_accent_matrix()
                d, diameter = m.pairwise_distance_summary(accent_mat)
                
                # Max displacement since last log
                max_disp = float(np.max(np.linalg.norm(accent_mat - prev_accent_mat, axis=1)))
                displacements.append(max_disp)
                prev_accent_mat = accent_mat
                
                # Check eligibility
                eligible_edges = 0
                for i, j in self.edge_list:
                    if np.linalg.norm(self.agents_map[i].accent - self.agents_map[j].accent) < config.theta:
                        eligible_edges += 1
                eligible_frac = eligible_edges / self._n_edges if self._n_edges > 0 else 0.0

                h, _ = self._compute_h(
                    accent_mat, t, is_consensus=(config.sigma == 0 and diameter <= config.epsilon_distance)
                )

                log.log(t, self.agents_map)
                timeline.append({
                    "timestep": t,
                    "diversity": round(h, 6),
                    "pairwise_distance": round(d, 6),
                    "accepted_interactions": self._accepted_since_log,
                    "rejected_interactions": self._rejected_since_log,
                    "eligible_edges_fraction": round(eligible_frac, 4)
                })
                
                self._accepted_since_log = 0
                self._rejected_since_log = 0

                # Convergence checks
                if config.sigma == 0:
                    if diameter <= config.epsilon_distance:
                        converged = True
                        termination_reason = "Consensus reached"
                        t_conv = t
                        break
                else:
                    if len(displacements) >= config.W:
                        if all(disp <= config.epsilon_max for disp in displacements[-config.W:]):
                            converged = True
                            termination_reason = "Stationary distribution"
                            t_conv = t
                            break

        # ---- Final metrics ------------------------------------------
        final_accent_mat = self._get_accent_matrix()
        final_d, final_diameter = m.pairwise_distance_summary(final_accent_mat)
        final_h, _ = self._compute_h(
            final_accent_mat,
            t_conv,
            is_consensus=(config.sigma == 0 and final_diameter <= config.epsilon_distance),
        )

        metrics_dict = {
            "run_id":                  log.run_id,
            "topology":                config.topology,
            "gamma":                   config.gamma,
            "theta":                   config.theta,
            "sigma":                   config.sigma,
            "seed":                    config.seed,
            "N":                       config.N,
            "convergence_time":        t_conv,
            "converged":               converged,
            "termination_reason":      termination_reason,
            "final_diversity":         round(final_h, 6),
            "final_pairwise_distance": round(final_d, 6),
        }

        log.close(metrics_dict, timeline)

        logger.info(
            "Run %s complete | %s | t_conv=%d | H=%.4f | D=%.4f",
            log.run_id, termination_reason, t_conv, final_h, final_d,
        )

        return {**metrics_dict, "timeline": timeline}

    def run_stream(self, log: "DataLogger"):
        import json
        T = self.config.T
        log_every = self.config.log_every
        config = self.config

        timeline = []
        displacements = []
        prev_accent_mat = self._get_accent_matrix()

        converged = False
        termination_reason = "Maximum interactions reached"
        t_conv = T

        d0, diameter0 = m.pairwise_distance_summary(prev_accent_mat)
        
        eligible_edges = 0
        for i, j in self.edge_list:
            if np.linalg.norm(self.agents_map[i].accent - self.agents_map[j].accent) < config.theta:
                eligible_edges += 1
        eligible_frac0 = eligible_edges / self._n_edges if self._n_edges > 0 else 0.0

        h0, _ = self._compute_h(
            prev_accent_mat, 0, is_consensus=diameter0 <= config.epsilon_distance
        )
        log.log(0, self.agents_map)
        
        init_point = {
            "timestep": 0, 
            "diversity": round(h0, 6), 
            "pairwise_distance": round(d0, 6),
            "accepted_interactions": 0,
            "rejected_interactions": 0,
            "eligible_edges_fraction": round(eligible_frac0, 4)
        }
        timeline.append(init_point)
        yield json.dumps({"event": "snapshot", "data": init_point}) + "\n"

        if config.sigma == 0 and diameter0 <= config.epsilon_distance:
            converged = True
            termination_reason = "Consensus reached"
            t_conv = 0

        for t in range(1, T + 1):
            if converged:
                break
            self.step()

            if t % log_every == 0:
                accent_mat = self._get_accent_matrix()
                d, diameter = m.pairwise_distance_summary(accent_mat)
                
                max_disp = float(np.max(np.linalg.norm(accent_mat - prev_accent_mat, axis=1)))
                displacements.append(max_disp)
                prev_accent_mat = accent_mat
                
                eligible_edges = 0
                for i, j in self.edge_list:
                    if np.linalg.norm(self.agents_map[i].accent - self.agents_map[j].accent) < config.theta:
                        eligible_edges += 1
                eligible_frac = eligible_edges / self._n_edges if self._n_edges > 0 else 0.0

                h, _ = self._compute_h(
                    accent_mat, t, is_consensus=(config.sigma == 0 and diameter <= config.epsilon_distance)
                )

                log.log(t, self.agents_map)
                
                point = {
                    "timestep": t,
                    "diversity": round(h, 6),
                    "pairwise_distance": round(d, 6),
                    "accepted_interactions": self._accepted_since_log,
                    "rejected_interactions": self._rejected_since_log,
                    "eligible_edges_fraction": round(eligible_frac, 4)
                }
                timeline.append(point)
                yield json.dumps({"event": "snapshot", "data": point}) + "\n"
                
                self._accepted_since_log = 0
                self._rejected_since_log = 0

                if config.sigma == 0:
                    if diameter <= config.epsilon_distance:
                        converged = True
                        termination_reason = "Consensus reached"
                        t_conv = t
                        break
                else:
                    if len(displacements) >= config.W:
                        if all(disp <= config.epsilon_max for disp in displacements[-config.W:]):
                            converged = True
                            termination_reason = "Stationary distribution"
                            t_conv = t
                            break

        final_accent_mat = self._get_accent_matrix()
        final_d, final_diameter = m.pairwise_distance_summary(final_accent_mat)
        final_h, _ = self._compute_h(
            final_accent_mat,
            t_conv,
            is_consensus=(config.sigma == 0 and final_diameter <= config.epsilon_distance),
        )

        metrics_dict = {
            "run_id":                  log.run_id,
            "topology":                config.topology,
            "gamma":                   config.gamma,
            "theta":                   config.theta,
            "sigma":                   config.sigma,
            "seed":                    config.seed,
            "N":                       config.N,
            "convergence_time":        t_conv,
            "converged":               converged,
            "termination_reason":      termination_reason,
            "final_diversity":         round(final_h, 6),
            "final_pairwise_distance": round(final_d, 6),
        }

        log.close(metrics_dict, timeline)
        logger.info(
            "Run %s complete | %s | t_conv=%d | H=%.4f | D=%.4f",
            log.run_id, termination_reason, t_conv, final_h, final_d,
        )
        
        yield json.dumps({"event": "_model_complete", "data": {**metrics_dict, "timeline": timeline}}) + "\n"
