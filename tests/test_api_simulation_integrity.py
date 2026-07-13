"""API-only simulation integrity contracts.

These tests deliberately exercise the same HTTP endpoints consumed by the
frontend, but contain no browser or frontend dependency.  They independently
recompute the persisted CSV metrics and assert that POST /run, GET /results,
JSON/CSV export, snapshots, network payloads, and UMAP identifiers all agree.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scipy.spatial.distance import pdist
from sklearn.cluster import KMeans

import simulation.logger as logger_mod
from api.main import app


ACCENT_COLUMNS = [f"d{i}" for i in range(6)]
LOG_EVERY = 100  # RunRequest currently exposes SimConfig's default cadence.
KMEANS_REFIT_EVERY = 500
# CSV is deliberately rounded to six decimal places for portability, whereas
# API metrics are computed from the model's float64 state. The maximum expected
# CSV-recomputation error plus metric rounding is below this budget.
CSV_METRIC_ABS_TOLERANCE = 2e-6
CONSENSUS_EPSILON = 1e-8
# A raw consensus state can spread by up to roughly sqrt(6) * 1e-6 after each
# CSV coordinate is rounded independently.
CSV_CONSENSUS_EPSILON = 3e-6


@pytest.fixture()
def client_and_runs_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Use a fresh artifact root for every API contract test."""
    monkeypatch.setattr("api.main.RUNS_ROOT", tmp_path)
    monkeypatch.setattr(logger_mod, "_RUNS_ROOT", tmp_path)
    return TestClient(app), tmp_path


@pytest.mark.parametrize(
    "payload",
    [
        {"topology": "er", "N": 20, "T": 1200, "p_er": 0.35, "seed": 1101},
        {"topology": "watts_strogatz", "N": 20, "T": 1200, "k_ws": 4, "p_rewire": 0.15, "seed": 1102},
        {"topology": "ba", "N": 20, "T": 1200, "m_ba": 2, "seed": 1103},
        {"topology": "sbm", "N": 20, "T": 1200, "p_in": 0.45, "p_out": 0.10, "seed": 1104},
        # Two behavioural boundary regimes: mostly rejected interactions and
        # maximal-confidence/no-noise accommodation.
        {"topology": "watts_strogatz", "N": 20, "T": 1200, "k_ws": 4, "theta": 0.05, "sigma": 0.01, "seed": 1105},
        {"topology": "watts_strogatz", "N": 20, "T": 1200, "k_ws": 4, "theta": 1.0, "sigma": 0.0, "seed": 1106},
        # Extreme boundary topologies that succeed
        {"topology": "er", "N": 20, "T": 1200, "p_er": 1.0, "seed": 1107},
        {"topology": "watts_strogatz", "N": 5, "T": 1200, "k_ws": 2, "p_rewire": 0.5, "seed": 1108},
    ],
)
def test_api_run_artifacts_are_mathematically_consistent(client_and_runs_root, payload):
    """Every API surface must agree with independent CSV recomputation."""
    client, _ = client_and_runs_root
    created = client.post("/run", json=payload)
    assert created.status_code == 200, created.text
    result = created.json()
    run_id = result["run_id"]

    # GET /results must be the same backend-visible run as POST /run.
    fetched = client.get(f"/results/{run_id}")
    assert fetched.status_code == 200
    assert fetched.json() == result

    exported_json = client.get(f"/runs/{run_id}/export?format=json")
    assert exported_json.status_code == 200
    assert exported_json.json() == result

    exported_csv = client.get(f"/runs/{run_id}/export?format=csv")
    assert exported_csv.status_code == 200
    rows = list(csv.DictReader(io.StringIO(exported_csv.text)))
    assert rows

    frame = pd.DataFrame(rows)
    numeric_columns = ["timestep", "agent_id", "community_id", "centrality", *ACCENT_COLUMNS]
    frame[numeric_columns] = frame[numeric_columns].apply(pd.to_numeric)
    timesteps = sorted(int(value) for value in frame["timestep"].unique())
    expected_n = result["config"]["N"]
    assert all(len(frame[frame["timestep"] == timestep]) == expected_n for timestep in timesteps)
    assert frame.duplicated(subset=["timestep", "agent_id"]).sum() == 0

    # Reproduce the model's metric semantics. H uses a cached KMeans fitted at
    # t=0 and refitted every 500 simulation steps; D is all-pairs Euclidean D.
    expected_timeline = []
    model_kmeans: KMeans | None = None
    next_refit = 0
    for timestep in timesteps:
        state = frame[frame["timestep"] == timestep].sort_values("agent_id")
        matrix = state[ACCENT_COLUMNS].to_numpy(dtype=float)
        distances = pdist(matrix)
        is_consensus = len(distances) == 0 or float(distances.max()) <= CSV_CONSENSUS_EPSILON
        if is_consensus:
            diversity = 0.0
        else:
            if model_kmeans is None or timestep >= next_refit:
                model_kmeans = KMeans(
                    n_clusters=5,
                    n_init=5,
                    random_state=result["config"]["seed"],
                ).fit(matrix)
                next_refit = timestep + KMEANS_REFIT_EVERY
            labels = model_kmeans.predict(matrix)
            counts = np.bincount(labels)
            probabilities = counts[counts > 0] / len(labels)
            diversity = float(-np.sum(probabilities * np.log(probabilities)))
        expected_timeline.append(
            {
                "timestep": timestep,
                "diversity": round(diversity, 6),
                "pairwise_distance": round(float(distances.mean()), 6),
            }
        )

    for actual, expected in zip(result["timeline"], expected_timeline):
        assert actual["timestep"] == expected["timestep"]
        assert actual["diversity"] == pytest.approx(expected["diversity"], abs=1e-6)
        assert actual["pairwise_distance"] == pytest.approx(
            expected["pairwise_distance"], abs=CSV_METRIC_ABS_TOLERANCE
        )
    assert result["metrics"]["final_diversity"] == pytest.approx(
        expected_timeline[-1]["diversity"], abs=1e-6
    )
    assert result["metrics"]["final_pairwise_distance"] == pytest.approx(
        expected_timeline[-1]["pairwise_distance"], abs=CSV_METRIC_ABS_TOLERANCE
    )

    # Final API states must be the final raw CSV states, modulo the documented
    # API-only cluster annotation.
    final_rows = frame[frame["timestep"] == timesteps[-1]].sort_values("agent_id")
    returned_states = sorted(result["final_agent_states"], key=lambda item: item["agent_id"])
    assert [state["agent_id"] for state in returned_states] == final_rows["agent_id"].tolist()
    for api_state, (_, csv_state) in zip(returned_states, final_rows.iterrows()):
        assert api_state["community_id"] == int(csv_state["community_id"])
        assert api_state["centrality"] == pytest.approx(float(csv_state["centrality"]), abs=1e-6)
        assert api_state["accent"] == pytest.approx([float(csv_state[column]) for column in ACCENT_COLUMNS], abs=1e-6)

    snapshots = client.get(f"/runs/{run_id}/snapshots")
    assert snapshots.status_code == 200
    snapshot_data = snapshots.json()
    assert snapshot_data["available_timesteps"] == timesteps
    assert len(snapshot_data["snapshots"]) == len(timesteps)
    for snapshot in snapshot_data["snapshots"]:
        expected = frame[frame["timestep"] == snapshot["timestep"]].sort_values("agent_id")
        assert [agent["agent_id"] for agent in snapshot["agents"]] == expected["agent_id"].tolist()

    # A network response may not contain dangling nodes or invalid edges.
    node_ids = {node["id"] for node in result["network"]["nodes"]}
    assert node_ids == set(final_rows["agent_id"])
    assert all(edge["source"] in node_ids and edge["target"] in node_ids for edge in result["network"]["edges"])

    # UMAP is a derivative, but its source records must reference exact saved
    # agent IDs and recorded timesteps rather than invented observations.
    umap_response = client.get(f"/umap/{run_id}")
    assert umap_response.status_code == 200, umap_response.text
    for snapshot in umap_response.json()["snapshots"]:
        assert snapshot["timestep"] in timesteps
        assert {point["agent_id"] for point in snapshot["points"]} == node_ids


def test_api_repeated_seed_is_reproducible(client_and_runs_root):
    """Identical requests must produce identical backend-visible state data."""
    client, _ = client_and_runs_root
    payload = {"topology": "watts_strogatz", "N": 20, "T": 1200, "k_ws": 4, "seed": 424242}
    first = client.post("/run", json=payload)
    second = client.post("/run", json=payload)
    assert first.status_code == second.status_code == 200

    left, right = first.json(), second.json()
    assert left["run_id"] != right["run_id"]
    left_config = {key: value for key, value in left["config"].items() if key != "run_id"}
    right_config = {key: value for key, value in right["config"].items() if key != "run_id"}
    assert left_config == right_config
    assert left["metrics"] == right["metrics"]
    assert left["timeline"] == right["timeline"]
    assert left["final_agent_states"] == right["final_agent_states"]
    assert left["network"] == right["network"]
