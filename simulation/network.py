"""
simulation/network.py
=====================
Network generation for the Mosaic ABM.

Public API:
    make_network(config: SimConfig) -> nx.Graph

The returned graph always has two node attributes set on every node:
    ``centrality``   float ∈ [0, 1]  — normalised degree centrality
    ``community_id`` int              — community membership (SBM: 0 or 1; others: 0)

The returned graph is guaranteed to be connected (retries for ER and SBM).
"""

from __future__ import annotations

import logging
import warnings

import networkx as nx
import numpy as np

from simulation.config import SimConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Community prototype accents (model.md §3)
# ---------------------------------------------------------------------------
# Used by MosaicModel._init_accent() to initialise agent accents.
# Exported here because they belong to the network/community layer.

COMMUNITY_PROTOTYPES: dict[int, np.ndarray] = {
    0: np.array([0.30, 0.35, 0.40, 0.30, 0.25, 0.40], dtype=float),
    1: np.array([0.70, 0.65, 0.60, 0.70, 0.75, 0.60], dtype=float),
}

SINGLE_COMMUNITY_PROTOTYPE = np.array([0.5] * 6, dtype=float)
SIGMA_INIT_COMMUNITY = 0.05   # tight clustering within a community (model.md §3)
SIGMA_INIT_SINGLE    = 0.15   # wider spread for single-community runs (model.md §3)

_MAX_RETRIES = 5
_SEED_OFFSET  = 1000   # seed increment per retry (implementation plan)


# ---------------------------------------------------------------------------
# Internal topology builders
# ---------------------------------------------------------------------------

def _build_er(config: SimConfig, seed: int) -> nx.Graph:
    G = nx.erdos_renyi_graph(config.N, config.p_er, seed=seed)
    return G


def _build_ws(config: SimConfig, seed: int) -> nx.Graph:
    # WS is always connected (ring lattice before rewiring ensures connectivity)
    return nx.watts_strogatz_graph(config.N, config.k_ws, config.p_rewire, seed=seed)


def _build_ba(config: SimConfig, seed: int) -> nx.Graph:
    # BA growth model always produces a connected graph
    return nx.barabasi_albert_graph(config.N, config.m_ba, seed=seed)


def _build_sbm(config: SimConfig, seed: int) -> nx.Graph:
    n = config.N
    sizes = [n // 2, n - n // 2]      # handles odd N gracefully
    probs = [
        [config.p_in,  config.p_out],
        [config.p_out, config.p_in],
    ]
    return nx.stochastic_block_model(sizes, probs, seed=seed)


_BUILDERS = {
    "er":             _build_er,
    "watts_strogatz": _build_ws,
    "ba":             _build_ba,
    "sbm":            _build_sbm,
}


# ---------------------------------------------------------------------------
# Connectivity guarantee
# ---------------------------------------------------------------------------

def _ensure_connected(
    config: SimConfig,
    topology: str,
    initial_seed: int,
) -> nx.Graph:
    """
    Build a graph and retry with incrementing seeds if disconnected.

    For ER and SBM at low edge probabilities, graphs can be disconnected.
    WS and BA are structurally guaranteed to be connected, but we check
    them anyway for robustness.

    If all retries fail, the largest connected component is returned with
    a warning — rather than crashing a long experiment run.
    """
    builder = _BUILDERS[topology]
    seed = initial_seed

    for attempt in range(_MAX_RETRIES):
        G = builder(config, seed)
        if nx.is_connected(G):
            if attempt > 0:
                logger.warning(
                    "Topology '%s': graph connected after %d retries "
                    "(original seed=%d, used seed=%d).",
                    topology, attempt, initial_seed, seed,
                )
            return G
        seed += _SEED_OFFSET

    # Final fallback: strict failure instead of silent N reduction
    raise ValueError(
        f"Topology '{topology}' seed={initial_seed}: all {_MAX_RETRIES} retries "
        f"produced disconnected graphs. Please increase network density (e.g., higher edge probability or k)."
    )


# ---------------------------------------------------------------------------
# Node attribute annotation
# ---------------------------------------------------------------------------

def _annotate_centrality(G: nx.Graph) -> None:
    """
    Compute normalised degree centrality and store as a node attribute.

    NetworkX's degree_centrality() already divides by N-1, giving values in [0,1].
    We further normalise by the maximum so the most-connected node gets 1.0.
    This makes centrality meaningful across different graph sizes.
    """
    raw = nx.degree_centrality(G)          # dict {node: float}
    max_c = max(raw.values()) if raw else 1.0
    if max_c == 0:
        max_c = 1.0
    nx.set_node_attributes(
        G,
        {node: c / max_c for node, c in raw.items()},
        name="centrality",
    )


def _annotate_community(G: nx.Graph, topology: str, config: SimConfig) -> None:
    """
    Assign ``community_id`` node attribute.

    SBM: nodes 0 .. N//2−1 belong to community 0; the rest to community 1.
    All other topologies: every node is in community 0.
    """
    if topology == "sbm":
        half = config.N // 2
        community = {node: (0 if node < half else 1) for node in G.nodes()}
    else:
        community = {node: 0 for node in G.nodes()}
    nx.set_node_attributes(G, community, name="community_id")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def make_network(config: SimConfig) -> nx.Graph:
    """
    Build and return a NetworkX graph for the given SimConfig.

    The returned graph has two node attributes on every node:
      - ``centrality``   : float ∈ [0, 1]
      - ``community_id`` : int

    Connectivity is guaranteed (see _ensure_connected).

    Parameters
    ----------
    config : SimConfig — all network parameters are read from here.

    Returns
    -------
    G : nx.Graph with N nodes and all attributes set.

    Raises
    ------
    ValueError if config.topology is not one of VALID_TOPOLOGIES
        (this is already caught by SimConfig.__post_init__).
    """
    topology = config.topology
    G = _ensure_connected(config, topology, config.seed)

    _annotate_centrality(G)
    _annotate_community(G, topology, config)

    return G
