"""
api/schemas.py
==============
Pydantic models for request and response validation in the FastAPI backend.
"""
from typing import Any, Literal
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    """Request model matching simulation.config.SimConfig."""
    topology: Literal["er", "watts_strogatz", "ba", "sbm"] = "watts_strogatz"
    # Five clusters are computed by the current results pipeline, so smaller
    # populations cannot produce a valid response.
    N: int = Field(default=200, ge=5, le=2_000)
    T: int = Field(default=10_000, ge=1, le=100_000)
    gamma: float = Field(default=1.0, ge=0.0, le=2.0)
    theta: float = Field(default=0.3, gt=0.0, le=1.0)
    sigma: float = Field(default=0.01, ge=0.0, le=0.05)
    initial_sigma: float = Field(default=0.15, ge=0.05, le=0.5)
    seed: int = Field(default=42, ge=0)
    
    # Convergence Policy
    W: int = Field(default=20, ge=5, le=100)
    epsilon_max: float = Field(default=1e-4, ge=1e-6, le=1e-2)
    epsilon_distance: float = Field(default=1e-6, ge=1e-8, le=1e-2)
    
    # Topology-specific defaults (can be overridden)
    p_er: float = Field(default=0.05, gt=0.0, le=1.0)
    k_ws: int = Field(default=6, ge=2, le=200)
    p_rewire: float = Field(default=0.1, ge=0.0, le=1.0)
    m_ba: int = Field(default=3, ge=1, le=100)
    n_communities: int = Field(default=2, ge=2, le=2)
    p_in: float = Field(default=0.15, gt=0.0, le=1.0)
    p_out: float = Field(default=0.02, ge=0.0, le=1.0)


class NetworkNode(BaseModel):
    id: int
    community_id: int
    centrality: float


class NetworkEdge(BaseModel):
    source: int
    target: int


class NetworkData(BaseModel):
    nodes: list[NetworkNode]
    edges: list[NetworkEdge]


class AgentState(BaseModel):
    agent_id: int
    accent: list[float]
    community_id: int
    centrality: float
    cluster_id: int


class TimelineEntry(BaseModel):
    timestep: int
    diversity: float
    pairwise_distance: float
    accepted_interactions: int = 0
    rejected_interactions: int = 0
    eligible_edges_fraction: float = 0.0


class MetricsData(BaseModel):
    convergence_time: int
    converged: bool
    termination_reason: str = "Max steps reached"
    final_diversity: float
    final_pairwise_distance: float


class RunResponse(BaseModel):
    """Full payload returned by POST /run and GET /results/{id}."""
    run_id: str
    config: dict[str, Any]
    metrics: MetricsData
    timeline: list[TimelineEntry]
    final_agent_states: list[AgentState]
    network: NetworkData
