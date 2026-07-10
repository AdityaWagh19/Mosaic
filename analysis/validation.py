"""
analysis/validation.py
======================
Phase 5.5: ML Architecture Validation

Evaluates 5 architectures across 10 random seeds on the accent-prediction task:
1. MLP
2. GCN
3. GraphSAGE
4. GAT
5. Threshold-GNN

Calculates Mean, 95% CI, Wilcoxon signed-rank tests, and Cohen's d to rigorously
test the hypothesis that standard GNNs fail due to architectural blindness to the
theta threshold in bounded confidence models.
"""
import logging
import random
from pathlib import Path

import numpy as np
import scipy.stats as stats
import torch
import torch.nn as nn
from sklearn.cluster import KMeans
from torch.utils.data import DataLoader as FlatDataLoader
from torch.utils.data import TensorDataset
from torch_geometric.loader import DataLoader as GraphDataLoader

import analysis._umap_compat  # Runs the sys.modules patch side-effect

from analysis.data_loader import build_flat_dataset, build_graph_dataset, discover_exp1_runs, load_run
from analysis.gcn import GAT, GCN, MLP, GraphSAGE, ThresholdGNN, eval_gnn, eval_mlp, train_gnn_epoch, train_mlp_epoch

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# Constants
N_SEEDS = 10
N_CLUSTERS = 5
N_EPOCHS = 100
GNN_BATCH = 8
MLP_BATCH = 256
LR = 1e-3
WEIGHT_DECAY = 1e-4

def cohen_d(x: np.ndarray, y: np.ndarray) -> float:
    """Calculate Cohen's d for two independent samples."""
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    if dof == 0:
        return 0.0
    pooled_std = np.sqrt(((nx - 1) * np.std(x, ddof=1) ** 2 + (ny - 1) * np.std(y, ddof=1) ** 2) / dof)
    if pooled_std == 0:
        return 0.0
    return float((np.mean(x) - np.mean(y)) / pooled_std)


def mean_ci(data: list[float], confidence: float = 0.95) -> tuple[float, float, float]:
    """Return mean, lower CI, upper CI."""
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), stats.sem(a)
    if se == 0:
        return float(m), float(m), float(m)
    h = se * stats.t.ppf((1 + confidence) / 2., n-1)
    return float(m), float(m-h), float(m+h)  # type: ignore



def run_seed(seed: int, run_paths: list[Path], kmeans: KMeans, device: torch.device) -> dict:
    """Run full evaluation for all 5 models on a given train/test split."""
    # Split
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    
    indices = list(range(len(run_paths)))
    random.shuffle(indices)
    split_idx = int(0.8 * len(run_paths))
    train_runs = [run_paths[i] for i in indices[:split_idx]]
    test_runs  = [run_paths[i] for i in indices[split_idx:]]
    
    # Graph datasets
    train_graphs = build_graph_dataset(train_runs, kmeans)
    test_graphs  = build_graph_dataset(test_runs, kmeans)
    
    gnn_train_loader = GraphDataLoader(train_graphs, batch_size=GNN_BATCH, shuffle=True)
    gnn_test_loader  = GraphDataLoader(test_graphs, batch_size=GNN_BATCH, shuffle=False)
    
    # Flat datasets
    X_train, y_train = build_flat_dataset(train_runs, kmeans)
    X_test, y_test   = build_flat_dataset(test_runs, kmeans)
    
    X_train_t = torch.tensor(X_train, dtype=torch.float)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_test_t  = torch.tensor(X_test, dtype=torch.float).to(device)
    y_test_t  = torch.tensor(y_test, dtype=torch.long).to(device)
    
    mlp_train_loader = FlatDataLoader(TensorDataset(X_train_t, y_train_t), batch_size=MLP_BATCH, shuffle=True)
    
    criterion = nn.CrossEntropyLoss()
    results = {}
    
    models = {
        "MLP": MLP(in_channels=7, n_classes=N_CLUSTERS).to(device),
        "GCN": GCN(in_channels=7, n_classes=N_CLUSTERS).to(device),
        "GraphSAGE": GraphSAGE(in_channels=7, n_classes=N_CLUSTERS).to(device),
        "GAT": GAT(in_channels=7, n_classes=N_CLUSTERS).to(device),
        "ThresholdGNN": ThresholdGNN(in_channels=7, n_classes=N_CLUSTERS, theta=0.30).to(device),
    }
    
    for name, model in models.items():
        opt = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
        
        for _ in range(N_EPOCHS):
            if name == "MLP":
                import typing
                train_mlp_epoch(typing.cast(MLP, model), mlp_train_loader, opt, criterion, device)
            else:
                train_gnn_epoch(model, gnn_train_loader, opt, criterion, device)
                
        # Evaluate
        if name == "MLP":
            import typing
            acc, f1 = eval_mlp(typing.cast(MLP, model), X_test_t, y_test_t, device)
        else:
            _, acc, f1, _, _ = eval_gnn(model, gnn_test_loader, criterion, device)
            
        results[name] = {"acc": acc, "f1": f1}
        
    return results


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info(f"Validation running on {device}")
    
    runs_dir = Path("runs")
    run_paths = discover_exp1_runs(runs_dir)
    log.info(f"Loaded {len(run_paths)} runs")
    
    all_runs = [load_run(rp) for rp in run_paths]
    
    # Global KMeans
    all_x_final = np.concatenate([r["x_final"] for r in all_runs], axis=0)
    kmeans = KMeans(n_clusters=N_CLUSTERS, n_init=5, random_state=42)
    kmeans.fit(all_x_final)
    
    # Seed loop
    metrics = {m: {"acc": [], "f1": []} for m in ["MLP", "GCN", "GraphSAGE", "GAT", "ThresholdGNN"]}
    
    for seed in range(1, N_SEEDS + 1):
        log.info(f"Running seed {seed}/{N_SEEDS}...")
        res = run_seed(seed, run_paths, kmeans, device)
        for m_name, vals in res.items():
            metrics[m_name]["acc"].append(vals["acc"])
            metrics[m_name]["f1"].append(vals["f1"])
            
    # Statistics
    print("\n" + "="*80)
    print("  Phase 5.5: ML Architecture Validation (10 seeds)")
    print("="*80)
    print(f"{'Architecture':<15} | {'Accuracy (95% CI)':<25} | {'Macro F1 (95% CI)':<25}")
    print("-" * 71)
    
    for m in ["MLP", "GCN", "GraphSAGE", "GAT", "ThresholdGNN"]:
        acc_m, acc_l, acc_u = mean_ci(metrics[m]["acc"])
        f1_m, f1_l, f1_u = mean_ci(metrics[m]["f1"])
        
        acc_str = f"{acc_m*100:>5.1f}% [{acc_l*100:>4.1f}-{acc_u*100:>4.1f}]"
        f1_str  = f"{f1_m*100:>5.1f}% [{f1_l*100:>4.1f}-{f1_u*100:>4.1f}]"
        print(f"{m:<15} | {acc_str:<25} | {f1_str:<25}")
        
    print("\n--- Significance Tests (vs ThresholdGNN) ---")
    tg_acc = np.array(metrics["ThresholdGNN"]["acc"])
    
    for baseline in ["MLP", "GCN", "GraphSAGE", "GAT"]:
        b_acc = np.array(metrics[baseline]["acc"])
        
        # Wilcoxon signed-rank test (paired samples)
        # Using exact=False to avoid warnings with ties
        try:
            stat, pval = stats.wilcoxon(tg_acc, b_acc)
        except ValueError:
            # If all differences are exactly zero
            pval = 1.0
            
        d = cohen_d(tg_acc, b_acc)
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
        
        print(f"ThresholdGNN vs {baseline:<10}: p={pval:.4f} {sig:<3} | Cohen's d={d:>5.2f}")
        
    print("================================================================================\n")

if __name__ == "__main__":
    main()
