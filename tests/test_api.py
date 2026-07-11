"""
tests/test_api.py
=================
Tests for the FastAPI backend.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from simulation.config import SimConfig


@pytest.fixture
def client():
    return TestClient(app)


def test_get_topologies(client):
    response = client.get("/topologies")
    assert response.status_code == 200
    data = response.json()
    assert "er" in data
    assert "watts_strogatz" in data
    assert "ba" in data
    assert "sbm" in data
    assert "params" in data["er"]


def test_run_endpoint_and_umap(client):
    """
    Test the POST /run endpoint with a very small simulation to ensure it completes quickly.
    Then test GET /results/{run_id} and GET /umap/{run_id}.
    """
    payload = {
        "N": 20,
        "T": 100,
        "topology": "er",
        "p_er": 0.5,
        "seed": 999
    }
    
    # 1. Run simulation
    response = client.post("/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "run_id" in data
    run_id = data["run_id"]
    
    assert data["config"]["N"] == 20
    assert data["config"]["T"] == 100
    assert data["config"]["topology"] == "er"
    
    assert "metrics" in data
    assert "convergence_time" in data["metrics"]
    
    assert "timeline" in data
    assert len(data["timeline"]) > 0
    
    assert "final_agent_states" in data
    assert len(data["final_agent_states"]) == 20
    assert len(data["final_agent_states"][0]["accent"]) == 6
    assert "cluster_id" in data["final_agent_states"][0]
    
    assert "network" in data
    assert "nodes" in data["network"]
    assert "edges" in data["network"]
    assert len(data["network"]["nodes"]) == 20
    
    # 2. Get results
    res_response = client.get(f"/results/{run_id}")
    assert res_response.status_code == 200
    res_data = res_response.json()
    assert res_data["run_id"] == run_id
    
    # 3. Get UMAP (should compute on the fly)
    umap_response = client.get(f"/umap/{run_id}")
    assert umap_response.status_code == 200
    umap_data = umap_response.json()
    
    snapshots = umap_data["snapshots"]
    assert len(snapshots) > 0
    assert len(snapshots[0]["points"]) == 20
    assert {"agent_id", "x", "y", "community_id"} <= set(snapshots[0]["points"][0])


def test_404_not_found(client):
    response = client.get("/results/non_existent_run_404")
    assert response.status_code == 404
    
    response = client.get("/umap/non_existent_run_404")
    assert response.status_code == 404
