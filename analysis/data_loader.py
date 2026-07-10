"""
analysis/data_loader.py
-----------------------
Load simulation run data and build datasets for GCN and MLP training.

Public API
----------
load_run(run_dir)                          -> dict of arrays + metadata
fit_global_kmeans(run_dirs, n_clusters)    -> fitted KMeans
build_graph_dataset(run_dirs, kmeans)      -> list[torch_geometric.data.Data]
build_flat_dataset(run_dirs, kmeans)       -> (X: ndarray, y: ndarray)
discover_exp1_runs(runs_root)              -> list[Path]
train_test_split_runs(run_dirs, fraction)  -> (train_dirs, test_dirs)
"""
from __future__ import annotations

import json
import logging
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data

from simulation.config import SimConfig
from simulation.network import make_network

log = logging.getLogger(__name__)

ACCENT_COLS: list[str] = [f"d{i}" for i in range(6)]
FEATURE_COLS: list[str] = ACCENT_COLS + ["centrality"]
N_FEATURES: int = 7  # 6 accent dims + centrality


# ---------------------------------------------------------------------------
# Single-run loader
# ---------------------------------------------------------------------------

def load_run(run_dir: Path) -> dict:
    """
    Load one simulation run directory.

    Returns
    -------
    dict with keys:
        x_init      (N, 7) float32  — t=0 accent vector + centrality
        x_final     (N, 6) float32  — final-timestep accent only
        edge_index  (2, E) int64    — bidirectional edge list (reconstructed)
        config      SimConfig
        run_id      str
        topology    str
        df          full DataFrame (for UMAP snapshots)
    """
    run_dir = Path(run_dir)
    with open(run_dir / "config.json") as f:
        config_dict = json.load(f)
    config = SimConfig.from_dict(config_dict)

    df = pd.read_csv(run_dir / "agent_states.csv")

    t_final = int(df["timestep"].max())

    # Deduplicate: some runs have the final timestep logged twice (re-run
    # artifact from Phase 4).  Keep the last occurrence per agent per timestep.
    df = df.drop_duplicates(subset=["timestep", "agent_id"], keep="last")

    df_init  = df[df["timestep"] == 0].sort_values("agent_id").reset_index(drop=True)
    df_final = df[df["timestep"] == t_final].sort_values("agent_id").reset_index(drop=True)

    x_init  = df_init[FEATURE_COLS].values.astype(np.float32)   # (N, 7)
    x_final = df_final[ACCENT_COLS].values.astype(np.float32)   # (N, 6)

    # Reconstruct the exact graph that was used in the simulation.
    # make_network() is deterministic for a given config.seed.
    G = make_network(config)
    edges = list(G.edges())
    if edges:
        src, dst = zip(*edges)
        # Add reverse edges so the graph is bidirectional.
        edge_index = torch.tensor(
            [list(src) + list(dst), list(dst) + list(src)],
            dtype=torch.long,
        )
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)

    return {
        "x_init":     x_init,
        "x_final":    x_final,
        "edge_index": edge_index,
        "config":     config,
        "run_id":     run_dir.name,
        "topology":   config.topology,
        "df":         df,
        "N":          len(df_init),
    }


# ---------------------------------------------------------------------------
# Global k-means
# ---------------------------------------------------------------------------

def fit_global_kmeans(
    run_dirs: list[Path],
    n_clusters: int = 5,
    rng_seed: int = 42,
):
    """
    Fit k-means on the union of every run's final accent states.

    Using a global model ensures GCN and MLP share the same label space.
    """
    from sklearn.cluster import KMeans

    all_final: list[np.ndarray] = []
    for rd in run_dirs:
        try:
            run = load_run(rd)
            all_final.append(run["x_final"])
        except Exception as exc:
            log.warning("Skipping %s: %s", rd.name, exc)

    X = np.concatenate(all_final, axis=0)          # (N_total, 6)
    log.info("Fitting k-means(k=%d) on %d agent vectors ...", n_clusters, len(X))
    km = KMeans(n_clusters=n_clusters, n_init=10, random_state=rng_seed)
    km.fit(X)
    log.info("  Inertia: %.4f", km.inertia_)
    return km


# ---------------------------------------------------------------------------
# Dataset builders
# ---------------------------------------------------------------------------

def build_graph_dataset(
    run_dirs: list[Path],
    kmeans,
) -> list[Data]:
    """
    Build a list of torch_geometric.data.Data objects for GCN training.

    Each Data object represents one simulation run (one graph).
        data.x          : (N, 7) initial node features
        data.edge_index : (2, E) bidirectional edge list
        data.y          : (N,)   final cluster label
    """
    dataset: list[Data] = []
    for rd in run_dirs:
        try:
            run = load_run(rd)
        except Exception as exc:
            log.warning("Skipping %s: %s", rd.name, exc)
            continue

        labels = kmeans.predict(run["x_final"])            # (N,)
        x = torch.tensor(run["x_init"], dtype=torch.float)
        y = torch.tensor(labels, dtype=torch.long)
        N = int(x.size(0))
        # Set num_nodes explicitly so PyG 2.6.x doesn't infer it from edge_index
        data = Data(x=x, edge_index=run["edge_index"], y=y, num_nodes=N)
        data.run_id  = run["run_id"]    # type: ignore[attr-defined]
        data.topology = run["topology"] # type: ignore[attr-defined]
        dataset.append(data)

    log.info("Graph dataset: %d Data objects", len(dataset))
    return dataset


def build_flat_dataset(
    run_dirs: list[Path],
    kmeans,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build flat (X, y) arrays for MLP training (no graph structure).

    Each row is one agent node.  Labels come from the same global k-means.
    """
    X_list: list[np.ndarray] = []
    y_list: list[np.ndarray] = []

    for rd in run_dirs:
        try:
            run = load_run(rd)
        except Exception as exc:
            log.warning("Skipping %s: %s", rd.name, exc)
            continue

        labels = kmeans.predict(run["x_final"])
        X_list.append(run["x_init"])
        y_list.append(labels.astype(np.int64))

    X = np.concatenate(X_list, axis=0).astype(np.float32)
    y = np.concatenate(y_list, axis=0).astype(np.int64)
    log.info("Flat dataset: %d nodes", len(X))
    return X, y


# ---------------------------------------------------------------------------
# Run discovery + train/test split
# ---------------------------------------------------------------------------

def discover_exp1_runs(runs_root: Path) -> list[Path]:
    """
    Discover the 100 Exp-1 topology runs (25 per topology x 4).

    Seed ranges match experiments/exp1_topology.py:
        ER  1000-1024  |  WS  1100-1124  |  BA  1200-1224  |  SBM  1300-1324
    """
    exp1_ranges = [
        ("er",             range(1000, 1025)),
        ("watts_strogatz", range(1100, 1125)),
        ("ba",             range(1200, 1225)),
        ("sbm",            range(1300, 1325)),
    ]
    found: list[Path] = []
    for topology, seeds in exp1_ranges:
        for seed in seeds:
            rd = Path(runs_root) / f"{topology}_{seed}"
            if rd.exists():
                found.append(rd)
            else:
                log.debug("Missing: %s", rd)
    log.info("Discovered %d / 100 Exp-1 runs", len(found))
    return found


def train_test_split_runs(
    run_dirs: list[Path],
    test_fraction: float = 0.20,
    rng_seed: int = 42,
) -> tuple[list[Path], list[Path]]:
    """
    Stratified train/test split — preserves topology proportions.

    run_dirs whose directory name is `{topology}_{seed}` are grouped by
    topology prefix so each topology contributes equally to both splits.
    """
    rng = np.random.default_rng(rng_seed)

    by_topology: dict[str, list[Path]] = defaultdict(list)
    for rd in run_dirs:
        # watts_strogatz_1100 -> "watts_strogatz"
        prefix = rd.name.rsplit("_", 1)[0]
        by_topology[prefix].append(rd)

    train_dirs: list[Path] = []
    test_dirs:  list[Path] = []
    for topo, dirs in sorted(by_topology.items()):
        arr  = np.array(dirs, dtype=object)
        perm = rng.permutation(len(arr))
        n_test = max(1, int(len(arr) * test_fraction))
        test_dirs.extend(arr[perm[:n_test]].tolist())
        train_dirs.extend(arr[perm[n_test:]].tolist())

    log.info(
        "Split: %d train / %d test  (fraction=%.0f%%)",
        len(train_dirs), len(test_dirs), test_fraction * 100,
    )
    return train_dirs, test_dirs
