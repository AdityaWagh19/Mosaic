"""
analysis/evaluate.py
--------------------
Phase 5 main entrypoint: train GCN + MLP, compare accuracy, save all figures.

Usage
-----
    python -m analysis.evaluate

Outputs
-------
    results/figures/gcn_vs_mlp_accuracy.png
    results/figures/cluster_map.png
    results/figures/umap_4panel.png
    results/ml_results.json
"""
from __future__ import annotations

import json
import logging
import time
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.utils.data
from torch_geometric.loader import DataLoader as GraphDataLoader

from analysis.data_loader import (
    discover_exp1_runs,
    fit_global_kmeans,
    build_graph_dataset,
    build_flat_dataset,
    train_test_split_runs,
    load_run,
)
from analysis.clustering import run_dbscan, silhouette, plot_cluster_overview
from analysis.gcn import (
    GCN,
    MLP,
    train_gnn_epoch,
    train_mlp_epoch,
    eval_gnn,
    eval_mlp,
)
from analysis.umap_viz import plot_umap_4panel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-5s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RUNS_ROOT   = Path("runs")
FIGURES_DIR = Path("results/figures")
RESULTS_PATH = Path("results/ml_results.json")

N_CLUSTERS   = 5
N_EPOCHS     = 100
GCN_BATCH    = 8     # graphs per GCN mini-batch
MLP_BATCH    = 256   # nodes per MLP mini-batch
LR           = 1e-3
WEIGHT_DECAY = 1e-4

UMAP_REF_RUN = "watts_strogatz_1100"


# ---------------------------------------------------------------------------
# Figure helpers
# ---------------------------------------------------------------------------

def _save_accuracy_bar(
    gcn_acc: float,
    mlp_acc: float,
    gcn_f1:  float,
    mlp_f1:  float,
    out_path: Path,
) -> None:
    """Bar chart comparing GCN vs MLP on accuracy and macro-F1."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle(
        "GCN vs MLP — Dialect Cluster Prediction",
        fontsize=14,
        fontweight="bold",
    )

    models  = ["MLP (Baseline)", "GCN"]
    colors  = ["#6699CC", "#EE6644"]
    chance  = 100.0 / N_CLUSTERS

    # ── Accuracy panel ──
    bars = axes[0].bar(
        models,
        [mlp_acc * 100, gcn_acc * 100],
        color=colors,
        width=0.45,
        edgecolor="black",
        linewidth=0.8,
    )
    axes[0].axhline(
        chance,
        color="#888888",
        linestyle="--",
        linewidth=1.2,
        label=f"Random ({chance:.0f}%)",
    )
    axes[0].set_ylabel("Accuracy (%)", fontsize=11)
    axes[0].set_title("Node Accuracy", fontsize=12)
    axes[0].set_ylim(0, 108)
    axes[0].legend(fontsize=9)
    for bar, val in zip(bars, [mlp_acc * 100, gcn_acc * 100]):
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            val + 1.5,
            f"{val:.1f}%",
            ha="center",
            fontsize=11,
            fontweight="bold",
        )

    # ── Macro-F1 panel ──
    bars2 = axes[1].bar(
        models,
        [mlp_f1 * 100, gcn_f1 * 100],
        color=colors,
        width=0.45,
        edgecolor="black",
        linewidth=0.8,
    )
    axes[1].set_ylabel("Macro F1 (%)", fontsize=11)
    axes[1].set_title("Macro F1 Score", fontsize=12)
    axes[1].set_ylim(0, 108)
    for bar, val in zip(bars2, [mlp_f1 * 100, gcn_f1 * 100]):
        axes[1].text(
            bar.get_x() + bar.get_width() / 2,
            val + 1.5,
            f"{val:.1f}%",
            ha="center",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=300)
    plt.close()
    log.info("Accuracy figure saved: %s", out_path)


def _save_loss_curves(gcn_losses: list[float], mlp_losses: list[float], out_path: Path) -> None:
    """Training loss curves for both models (saved alongside accuracy figure)."""
    fig, ax = plt.subplots(figsize=(8, 4))
    epochs = range(1, len(gcn_losses) + 1)
    ax.plot(epochs, gcn_losses, color="#EE6644", label="GCN", linewidth=1.5)
    ax.plot(epochs, mlp_losses, color="#6699CC", label="MLP", linewidth=1.5)
    ax.set_xlabel("Epoch", fontsize=11)
    ax.set_ylabel("Cross-Entropy Loss", fontsize=11)
    ax.set_title("Training Loss Curves", fontsize=13, fontweight="bold")
    ax.legend(fontsize=10)
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    log.info("Loss curves saved: %s", out_path)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    t0 = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("Device: %s", device)
    os.makedirs(str(FIGURES_DIR), exist_ok=True)

    # ── 1. Discover Exp-1 runs ────────────────────────────────────────────
    run_dirs = discover_exp1_runs(RUNS_ROOT)
    if len(run_dirs) < 10:
        raise RuntimeError(
            f"Only {len(run_dirs)} Exp-1 runs found. "
            "Run 'python -m experiments.run_all' first."
        )
    train_dirs, test_dirs = train_test_split_runs(run_dirs, test_fraction=0.20)
    log.info("Train: %d runs  |  Test: %d runs", len(train_dirs), len(test_dirs))

    # ── 2. Fit global k-means ─────────────────────────────────────────────
    log.info("Fitting global k-means (k=%d) ...", N_CLUSTERS)
    kmeans = fit_global_kmeans(run_dirs, n_clusters=N_CLUSTERS)

    # ── 3. Build datasets ─────────────────────────────────────────────────
    log.info("Building graph dataset ...")
    train_graphs = build_graph_dataset(train_dirs, kmeans)
    test_graphs  = build_graph_dataset(test_dirs,  kmeans)

    log.info("Building flat dataset ...")
    X_tr_np, y_tr_np = build_flat_dataset(train_dirs, kmeans)
    X_te_np, y_te_np = build_flat_dataset(test_dirs,  kmeans)

    # ── 4. Cluster overview (DBSCAN on reference run) ─────────────────────
    log.info("Generating cluster overview figure ...")
    ref_run  = train_dirs[0]
    ref_data = load_run(ref_run)
    km_labels = kmeans.predict(ref_data["x_final"])
    db_labels, n_db = run_dbscan(ref_data["x_final"])
    sil_km = silhouette(ref_data["x_final"], km_labels)
    sil_db = silhouette(ref_data["x_final"], db_labels)
    log.info(
        "Silhouette — k-means: %.3f  |  DBSCAN (%d clusters): %.3f",
        sil_km, n_db, sil_db,
    )
    plot_cluster_overview(
        ref_data["x_final"],
        km_labels,
        ref_data["topology"],
        FIGURES_DIR / "cluster_map.png",
    )

    # ── 5. Train GCN ──────────────────────────────────────────────────────
    log.info("=" * 50)
    log.info("Training GCN for %d epochs ...", N_EPOCHS)
    gcn_loader = GraphDataLoader(train_graphs, batch_size=GCN_BATCH, shuffle=True)
    gcn_model  = GCN(in_channels=7, n_classes=N_CLUSTERS).to(device)
    gcn_opt    = torch.optim.Adam(gcn_model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    criterion  = nn.CrossEntropyLoss()

    gcn_losses: list[float] = []
    for epoch in range(1, N_EPOCHS + 1):
        loss = train_gnn_epoch(gcn_model, gcn_loader, gcn_opt, criterion, device)
        gcn_losses.append(loss)
        if epoch % 10 == 0 or epoch == 1:
            log.info("  GCN epoch %3d / %d  loss=%.4f", epoch, N_EPOCHS, loss)

    gcn_acc, gcn_f1, _, _, _ = eval_gnn(gcn_model, test_graphs, criterion, device)
    log.info("GCN  -> Accuracy: %.3f  Macro-F1: %.3f", gcn_acc, gcn_f1)

    # ── 6. Train MLP ──────────────────────────────────────────────────────
    log.info("=" * 50)
    log.info("Training MLP for %d epochs ...", N_EPOCHS)
    X_tr = torch.tensor(X_tr_np, dtype=torch.float)
    y_tr = torch.tensor(y_tr_np, dtype=torch.long)
    X_te = torch.tensor(X_te_np, dtype=torch.float)
    y_te = torch.tensor(y_te_np, dtype=torch.long)

    mlp_ds     = torch.utils.data.TensorDataset(X_tr, y_tr)
    mlp_loader = torch.utils.data.DataLoader(mlp_ds, batch_size=MLP_BATCH, shuffle=True)
    mlp_model  = MLP(in_channels=7, n_classes=N_CLUSTERS).to(device)
    mlp_opt    = torch.optim.Adam(mlp_model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    mlp_losses: list[float] = []
    for epoch in range(1, N_EPOCHS + 1):
        loss = train_mlp_epoch(mlp_model, mlp_loader, mlp_opt, criterion, device)
        mlp_losses.append(loss)
        if epoch % 10 == 0 or epoch == 1:
            log.info("  MLP epoch %3d / %d  loss=%.4f", epoch, N_EPOCHS, loss)

    mlp_acc, mlp_f1 = eval_mlp(mlp_model, X_te, y_te, device)
    log.info("MLP  -> Accuracy: %.3f  Macro-F1: %.3f", mlp_acc, mlp_f1)

    # ── 7. Save comparison figures ────────────────────────────────────────
    log.info("=" * 50)
    _save_accuracy_bar(
        gcn_acc, mlp_acc, gcn_f1, mlp_f1,
        FIGURES_DIR / "gcn_vs_mlp_accuracy.png",
    )
    _save_loss_curves(
        gcn_losses, mlp_losses,
        FIGURES_DIR / "gcn_vs_mlp_loss.png",
    )

    # ── 8. UMAP 4-panel ───────────────────────────────────────────────────
    umap_ref = RUNS_ROOT / UMAP_REF_RUN
    if umap_ref.exists():
        log.info("Generating UMAP 4-panel from %s ...", UMAP_REF_RUN)
        plot_umap_4panel(umap_ref, FIGURES_DIR / "umap_4panel.png")
    else:
        log.warning("UMAP reference run not found: %s", umap_ref)

    # ── 9. Save results JSON ──────────────────────────────────────────────
    results = {
        "gcn":  {"accuracy": round(gcn_acc, 4), "macro_f1": round(gcn_f1, 4)},
        "mlp":  {"accuracy": round(mlp_acc, 4), "macro_f1": round(mlp_f1, 4)},
        "n_clusters":    N_CLUSTERS,
        "n_train_runs":  len(train_dirs),
        "n_test_runs":   len(test_dirs),
        "n_epochs":      N_EPOCHS,
        "random_chance": round(1.0 / N_CLUSTERS, 4),
        "gcn_vs_mlp_delta_acc": round(gcn_acc - mlp_acc, 4),
        "clustering": {
            "kmeans_silhouette": round(sil_km, 4),
            "dbscan_n_clusters": n_db,
            "dbscan_silhouette": round(sil_db, 4),
        },
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(str(RESULTS_PATH), "w") as f:
        json.dump(results, f, indent=2)
    log.info("Results JSON saved: %s", RESULTS_PATH)

    elapsed = time.time() - t0

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 58)
    print("  Phase 5 — ML Analysis Results")
    print("=" * 58)
    print(f"  Task          : predict final cluster  (K={N_CLUSTERS})")
    print(f"  Random chance : {100/N_CLUSTERS:.0f}%")
    print(f"  MLP accuracy  : {mlp_acc*100:.1f}%   Macro-F1: {mlp_f1*100:.1f}%")
    print(f"  GCN accuracy  : {gcn_acc*100:.1f}%   Macro-F1: {gcn_f1*100:.1f}%")
    delta = (gcn_acc - mlp_acc) * 100
    print(f"  GCN vs MLP    : {delta:+.1f}pp accuracy delta")
    print(f"  Runtime       : {elapsed:.1f}s")
    print("=" * 58)
    print(f"\n  Figures -> {FIGURES_DIR}/")
    print(f"  Results -> {RESULTS_PATH}")


if __name__ == "__main__":
    main()
