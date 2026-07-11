"""
tests/test_api.py
=================
Tests for the FastAPI backend.

Marks:
  (none)  — fast unit/integration tests, run on every CI push
  slow    — run with: pytest -m slow
"""
import json
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from unittest.mock import patch


# ---------------------------------------------------------------------------
# App import and client fixture
# ---------------------------------------------------------------------------

from api.main import app, RUNS_ROOT
from simulation.config import SimConfig


@pytest.fixture(scope="module")
def client():
    """Single TestClient shared across all tests in this module."""
    return TestClient(app)


@pytest.fixture(scope="module")
def completed_run(client, tmp_path_factory):
    """
    Run one small simulation and return its run_id.
    Shared across all tests that need a real run artifact.
    Redirects RUNS_ROOT to a temp directory to avoid polluting runs/.
    """
    tmp = tmp_path_factory.mktemp("runs")
    with patch("api.main.RUNS_ROOT", tmp), \
         patch("simulation.logger._RUNS_ROOT", tmp):
        payload = {
            "N": 15,
            "T": 80,
            "topology": "er",
            "p_er": 0.5,
            "seed": 42,
        }
        response = client.post("/run", json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        yield data["run_id"], tmp


# ---------------------------------------------------------------------------
# /topologies
# ---------------------------------------------------------------------------

def test_get_topologies(client):
    response = client.get("/topologies")
    assert response.status_code == 200
    data = response.json()
    for key in ("er", "watts_strogatz", "ba", "sbm"):
        assert key in data, f"Missing topology: {key}"
    assert "params" in data["er"]
    assert "desc" in data["er"]


# ---------------------------------------------------------------------------
# /config/schema
# ---------------------------------------------------------------------------

def test_config_schema(client):
    response = client.get("/config/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["version"] == 1
    assert "defaults" in data
    assert "fields" in data
    defaults = data["defaults"]
    for field in ("N", "T", "gamma", "theta", "sigma", "topology"):
        assert field in defaults, f"Missing default field: {field}"
    fields = data["fields"]
    assert "N" in fields
    assert "min" in fields["N"]
    assert "max" in fields["N"]


# ---------------------------------------------------------------------------
# POST /run + GET /results + GET /umap
# ---------------------------------------------------------------------------

def test_run_endpoint_and_umap(client):
    """
    Test the POST /run endpoint with a very small simulation to ensure it
    completes quickly. Then test GET /results/{run_id} and GET /umap/{run_id}.
    """
    payload = {
        "N": 20,
        "T": 100,
        "topology": "er",
        "p_er": 0.5,
        "seed": 999,
    }

    # 1. Run simulation
    response = client.post("/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "run_id" in data
    run_id = data["run_id"]

    assert data["config"]["N"] == 20
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
    assert len(data["network"]["nodes"]) == 20

    # 2. Get results
    res = client.get(f"/results/{run_id}")
    assert res.status_code == 200
    assert res.json()["run_id"] == run_id

    # 3. UMAP (computed on the fly)
    umap_res = client.get(f"/umap/{run_id}")
    assert umap_res.status_code == 200
    snapshots = umap_res.json()["snapshots"]
    assert len(snapshots) > 0
    assert len(snapshots[0]["points"]) == 20
    assert {"agent_id", "x", "y", "community_id"} <= set(snapshots[0]["points"][0])


def test_run_uniqueness(client):
    """Two identical configs must produce two distinct run_ids."""
    payload = {"N": 10, "T": 50, "topology": "er", "p_er": 0.5, "seed": 77777}
    r1 = client.post("/run", json=payload)
    r2 = client.post("/run", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    id1 = r1.json()["run_id"]
    id2 = r2.json()["run_id"]
    assert id1 != id2, f"Expected unique run_ids, got {id1!r} twice"


# ---------------------------------------------------------------------------
# GET /runs (list + filter)
# ---------------------------------------------------------------------------

def test_runs_list(client):
    response = client.get("/runs")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)


def test_runs_list_topology_filter(client):
    # Topology filter must only return items with matching topology
    response = client.get("/runs?topology=er")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["topology"] == "er", f"Filter broken: got {item['topology']}"


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/export
# ---------------------------------------------------------------------------

def test_export_json(client, completed_run):
    run_id, _ = completed_run
    with patch("api.main.RUNS_ROOT", _):
        response = client.get(f"/runs/{run_id}/export?format=json")
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data


def test_export_csv(client, completed_run):
    run_id, tmp = completed_run
    with patch("api.main.RUNS_ROOT", tmp):
        response = client.get(f"/runs/{run_id}/export?format=csv")
    assert response.status_code == 200
    ct = response.headers.get("content-type", "")
    assert "text/csv" in ct or "csv" in ct


# ---------------------------------------------------------------------------
# GET /runs/{run_id}/snapshots
# ---------------------------------------------------------------------------

def test_snapshots_all(client, completed_run):
    run_id, tmp = completed_run
    with patch("api.main.RUNS_ROOT", tmp):
        response = client.get(f"/runs/{run_id}/snapshots")
    assert response.status_code == 200
    data = response.json()
    assert "available_timesteps" in data
    assert len(data["available_timesteps"]) > 0
    assert len(data["snapshots"]) > 0


def test_snapshots_selected(client, completed_run):
    run_id, tmp = completed_run
    with patch("api.main.RUNS_ROOT", tmp):
        # First find an available timestep
        all_resp = client.get(f"/runs/{run_id}/snapshots")
        first_t = all_resp.json()["available_timesteps"][0]
        response = client.get(f"/runs/{run_id}/snapshots?timesteps={first_t}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["snapshots"]) == 1
    assert data["snapshots"][0]["timestep"] == first_t


# ---------------------------------------------------------------------------
# GET /experiments
# ---------------------------------------------------------------------------

def test_experiments_list(client):
    response = client.get("/experiments")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    for item in data["items"]:
        assert "id" in item
        assert "title" in item
        assert "figures" in item
        assert "available" in item


# ---------------------------------------------------------------------------
# GET /figures/{filename}
# ---------------------------------------------------------------------------

def test_figures_allowlist_blocks_arbitrary(client):
    """Arbitrary filenames must return 404 — never expose filesystem paths."""
    response = client.get("/figures/../../etc/passwd")
    assert response.status_code == 404

    response = client.get("/figures/arbitrary_unknown_file.png")
    assert response.status_code == 404


def test_figures_known_name_is_not_500(client):
    """A filename from the allowlist returns 200 or 404 — never 500."""
    response = client.get("/figures/e1_diversity_timeseries.png")
    assert response.status_code in (200, 404)


# ---------------------------------------------------------------------------
# GET /analysis/summary
# ---------------------------------------------------------------------------

def test_analysis_summary_or_404(client):
    """Either 200 with expected keys, or 404 if ml_results.json not yet generated. Never 500."""
    response = client.get("/analysis/summary")
    assert response.status_code in (200, 404), f"Got unexpected status {response.status_code}"
    if response.status_code == 200:
        data = response.json()
        # Should contain at least one of the expected ML result keys
        assert any(k in data for k in ("gcn", "mlp", "figures", "accuracy"))


# ---------------------------------------------------------------------------
# Validation — invalid configs return 422
# ---------------------------------------------------------------------------

def test_invalid_config_N_too_small(client):
    response = client.post("/run", json={"N": 1, "T": 100, "topology": "er", "p_er": 0.5})
    assert response.status_code == 422


def test_invalid_topology(client):
    response = client.post("/run", json={"N": 20, "T": 100, "topology": "not_a_real_topology"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 404 not found
# ---------------------------------------------------------------------------

def test_404_not_found(client):
    response = client.get("/results/non_existent_run_404")
    assert response.status_code == 404

    response = client.get("/umap/non_existent_run_404")
    assert response.status_code == 404
