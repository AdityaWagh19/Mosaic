"""
api/schemas.py
==============
Pydantic models for request and response validation in the FastAPI backend.
"""
from typing import Any
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    """Request model matching simulation.config.SimConfig."""
    topology: str = Field(default="watts_strogatz")
    N: int = Field(default=200)
    T: int = Field(default=10000)
    gamma: float = Field(default=1.0)
    theta: float = Field(default=0.3)
    sigma: float = Field(default=0.01)
    seed: int = Field(default=42)
    
    # Topology-specific defaults (can be overridden)
    p_er: float = Field(default=0.05)
    k_ws: int = Field(default=6)
    p_rewire: float = Field(default=0.1)
    m_ba: int = Field(default=3)
    n_communities: int = Field(default=2)
    p_in: float = Field(default=0.3)
    p_out: float = Field(default=0.05)


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


class MetricsData(BaseModel):
    convergence_time: int
    converged: bool
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
