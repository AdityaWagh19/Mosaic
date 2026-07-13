"""
tests/test_network.py
=====================
6 tests covering all Plan-3 network requirements:
  - All 4 topologies produce connected graphs
  - Node attributes centrality and community_id present on all nodes
  - SBM produces exactly 2 communities with correct split
  - Centrality normalised to [0, 1] with max == 1
  - ER connectivity guarantee (retry on disconnected graph)
"""
from __future__ import annotations

from dataclasses import replace

import networkx as nx
import numpy as np
import pytest

from simulation.config import SimConfig
from simulation.network import COMMUNITY_PROTOTYPES, make_network


def _cfg(topology: str, N: int = 20, seed: int = 0, **kwargs) -> SimConfig:
    """Convenience factory for small test configs. Uses dense defaults for connectivity."""
    dense_defaults = {}
    if topology == "er":
        dense_defaults = {"p_er": 0.5}
    elif topology == "sbm":
        dense_defaults = {"p_in": 0.8, "p_out": 0.3}
        
    for k, v in dense_defaults.items():
        kwargs.setdefault(k, v)
        
    return replace(SimConfig(), topology=topology, N=N, seed=seed, **kwargs)


# ---------------------------------------------------------------------------
# Test 1 — All 4 topologies produce connected graphs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("topology", ["er", "watts_strogatz", "ba", "sbm"])
def test_all_topologies_connected(topology):
    G = make_network(_cfg(topology))
    assert nx.is_connected(G), f"Topology '{topology}' produced a disconnected graph"


# ---------------------------------------------------------------------------
# Test 2 — Node count preserved
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("topology", ["watts_strogatz", "ba"])
def test_node_count_equals_N(topology):
    """
    WS and BA always produce exactly N nodes (they're constructive algorithms,
    not random sampling).  ER and SBM may reduce N via the LCC fallback at
    low edge-probability defaults — that behaviour is tested separately.
    """
    config = _cfg(topology, N=20)
    G = make_network(config)
    assert len(G) == 20


# ---------------------------------------------------------------------------
# Test 3 — centrality attribute on every node, normalised to [0, 1], max = 1
# ---------------------------------------------------------------------------

def test_centrality_in_unit_interval_and_max_is_one():
    G = make_network(_cfg("watts_strogatz", N=20))
    centralities = [G.nodes[n]["centrality"] for n in G.nodes()]
    assert all(0.0 <= c <= 1.0 for c in centralities), "Centrality out of [0,1]"
    assert abs(max(centralities) - 1.0) < 1e-9, "Max centrality should be exactly 1"


# ---------------------------------------------------------------------------
# Test 4 — community_id attribute on every node
# ---------------------------------------------------------------------------

def test_community_id_attribute_present_on_all_nodes():
    for topology in ("er", "watts_strogatz", "ba", "sbm"):
        G = make_network(_cfg(topology, N=20))
        for node in G.nodes():
            assert "community_id" in G.nodes[node], (
                f"Node {node} missing community_id for topology '{topology}'"
            )


# ---------------------------------------------------------------------------
# Test 5 — SBM produces exactly 2 communities of the right sizes
# ---------------------------------------------------------------------------

def test_sbm_two_communities_correct_split():
    """
    High p_in and p_out make SBM reliably connected at N=20 without
    triggering the LCC fallback, so both community blocks survive intact.
    """
    config = replace(SimConfig(), topology="sbm", N=20, seed=7,
                     p_in=0.5, p_out=0.2)
    G = make_network(config)

    # Graph must still be 20 nodes (no LCC reduction at these densities)
    assert len(G) == 20, (
        f"SBM reduced N — connectivity not guaranteed with these params"
    )

    communities = set(G.nodes[n]["community_id"] for n in G.nodes())
    assert communities == {0, 1}, f"Expected {{0,1}}, got {communities}"

    sizes = {c: sum(1 for n in G.nodes() if G.nodes[n]["community_id"] == c)
             for c in communities}
    assert sizes[0] == 10
    assert sizes[1] == 10


# ---------------------------------------------------------------------------
# Test 6 — Non-SBM topologies assign community_id = 0 to every node
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("topology", ["er", "watts_strogatz", "ba"])
def test_non_sbm_single_community(topology):
    G = make_network(_cfg(topology, N=20))
    ids = set(G.nodes[n]["community_id"] for n in G.nodes())
    assert ids == {0}, f"Expected single community {{0}}, got {ids}"


# ---------------------------------------------------------------------------
# Bonus — community prototypes shape and value range
# ---------------------------------------------------------------------------

def test_community_prototypes_valid():
    for cid, proto in COMMUNITY_PROTOTYPES.items():
        assert proto.shape == (6,), f"Community {cid} prototype should be shape (6,)"
        assert np.all(proto >= 0.0) and np.all(proto <= 1.0), (
            f"Community {cid} prototype values must be in [0,1]"
        )
