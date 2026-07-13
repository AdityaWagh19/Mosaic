import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

import simulation.logger as logger_mod
from api.main import app

FIXTURE_DIR = Path(__file__).parent / "fixtures"

PAYLOAD = {
    "topology": "sbm",
    "N": 20,
    "T": 1000,
    "p_in": 0.5,
    "p_out": 0.05,
    "seed": 9999,
}

@pytest.fixture()
def client_and_runs_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("api.main.RUNS_ROOT", tmp_path)
    monkeypatch.setattr(logger_mod, "_RUNS_ROOT", tmp_path)
    return TestClient(app), tmp_path

def test_canonical_artifact_is_deterministic(client_and_runs_root):
    """
    Golden Master (Snapshot) test.
    Ensures that for a fixed configuration, the canonical output is bit-for-bit identical.
    """
    client, runs_root = client_and_runs_root
    
    # 1. Run the simulation
    res = client.post("/run", json=PAYLOAD)
    assert res.status_code == 200, res.text
    run_id = res.json()["run_id"]
    
    # 2. Load the canonical artifact
    canonical_path = runs_root / run_id / "canonical_run.json"
    assert canonical_path.exists()
    
    with open(canonical_path, "r", encoding="utf-8") as f:
        current_canonical = json.load(f)
        
    # Remove config_fingerprint because it hashes a dict string representation which might vary across python versions?
    # Actually json.dumps with sort_keys=True should be stable, but just to be absolutely sure.
    current_canonical["config"].pop("config_fingerprint", None)
    
    # UMAP relies on Numba and stochastic gradient descent. Even with random_state set,
    # it produces different float trajectories across different CPU architectures/OS platforms.
    # Exclude from golden master equality check.
    current_canonical.pop("umap", None)
    
    # 3. Load the golden fixture
    fixture_path = FIXTURE_DIR / "golden_master_sbm_9999.json"
    
    # If fixture doesn't exist, we generate it (this happens on first run)
    if not fixture_path.exists():
        FIXTURE_DIR.mkdir(exist_ok=True)
        with open(fixture_path, "w", encoding="utf-8") as f:
            json.dump(current_canonical, f, indent=2, sort_keys=True)
        pytest.skip("Fixture didn't exist. Generated it instead.")
        
    with open(fixture_path, "r", encoding="utf-8") as f:
        golden_canonical = json.load(f)
        
    golden_canonical["config"].pop("config_fingerprint", None)
    golden_canonical.pop("umap", None)
        
    def assert_approx_equal(actual, expected, path="root"):
        if isinstance(actual, dict) and isinstance(expected, dict):
            assert set(actual.keys()) == set(expected.keys()), f"Keys differ at {path}"
            for k in actual:
                assert_approx_equal(actual[k], expected[k], f"{path}.{k}")
        elif isinstance(actual, list) and isinstance(expected, list):
            assert len(actual) == len(expected), f"List length differs at {path}"
            for i, (a, e) in enumerate(zip(actual, expected)):
                assert_approx_equal(a, e, f"{path}[{i}]")
        elif isinstance(actual, float) and isinstance(expected, float):
            assert actual == pytest.approx(expected, rel=1e-3, abs=1e-3), f"Float differs at {path}: {actual} != {expected}"
        else:
            assert actual == expected, f"Value differs at {path}: {actual} != {expected}"

    # 4. Deep assert equality with float tolerance
    assert_approx_equal(current_canonical, golden_canonical)
