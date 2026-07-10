"""
analysis/gcn.py
---------------
GCN and MLP model definitions + per-epoch training/evaluation helpers.

Models
------
GCN  — 2-layer Graph Convolutional Network (Kipf & Welling 2017)
MLP  — 2-layer Multi-Layer Perceptron baseline (no graph structure)

Both models target the same K-class node classification problem.
"""
from __future__ import annotations

import logging

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, SAGEConv, GATConv

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Model definitions
# ---------------------------------------------------------------------------

class GCN(nn.Module):
    """
    Two-layer GCN for per-node cluster prediction.

    Architecture:
        GCNConv(in -> 64) | BN | ReLU | Dropout
        GCNConv(64 -> 32) | BN | ReLU | Dropout
        Linear(32 -> K)
    """

    def __init__(
        self,
        in_channels: int,
        n_classes: int,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.conv1   = GCNConv(in_channels, 64)
        self.bn1     = nn.BatchNorm1d(64)
        self.conv2   = GCNConv(64, 32)
        self.bn2     = nn.BatchNorm1d(32)
        self.head    = nn.Linear(32, n_classes)
        self.dropout = dropout

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        return self.head(x)


class GraphSAGE(nn.Module):
    """
    Two-layer GraphSAGE (Hamilton et al. 2017).
    Uses mean aggregation via SAGEConv.
    """

    def __init__(
        self,
        in_channels: int,
        n_classes: int,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.conv1   = SAGEConv(in_channels, 64)
        self.bn1     = nn.BatchNorm1d(64)
        self.conv2   = SAGEConv(64, 32)
        self.bn2     = nn.BatchNorm1d(32)
        self.head    = nn.Linear(32, n_classes)
        self.dropout = dropout

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        return self.head(x)


class GAT(nn.Module):
    """
    Two-layer Graph Attention Network (Veličković et al. 2018).
    Uses GATConv with 2 attention heads.
    """

    def __init__(
        self,
        in_channels: int,
        n_classes: int,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.conv1   = GATConv(in_channels, 32, heads=2, dropout=dropout)
        self.bn1     = nn.BatchNorm1d(64)  # 32 * 2 heads
        self.conv2   = GATConv(64, 32, heads=1, concat=False, dropout=dropout)
        self.bn2     = nn.BatchNorm1d(32)
        self.head    = nn.Linear(32, n_classes)
        self.dropout = dropout

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        x = self.conv1(x, edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.conv2(x, edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        return self.head(x)


class ThresholdGNN(nn.Module):
    """
    Custom Threshold-GNN (Validation Experiment B).
    
    Dynamically prunes edge_index based on Euclidean distance of node features
    (ignoring the first dimension if it is community_id, matching theta logic).
    Then applies standard GCNConv.
    """

    def __init__(
        self,
        in_channels: int,
        n_classes: int,
        theta: float = 0.30,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.theta   = theta
        self.conv1   = GCNConv(in_channels, 64)
        self.bn1     = nn.BatchNorm1d(64)
        self.conv2   = GCNConv(64, 32)
        self.bn2     = nn.BatchNorm1d(32)
        self.head    = nn.Linear(32, n_classes)
        self.dropout = dropout

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
    ) -> torch.Tensor:
        # Mask edges where distance > theta (on the 6 accent dims)
        # x shape: (N, 7). Dim 0 is community_id, 1-6 are accent.
        accents = x[:, 1:]
        # Get source and target node accents for each edge
        src_accents = accents[edge_index[0]]
        dst_accents = accents[edge_index[1]]
        # Compute L2 distance
        dists = torch.norm(src_accents - dst_accents, p=2, dim=1)
        # Keep edges where dist <= theta
        mask = dists <= self.theta
        masked_edge_index = edge_index[:, mask]

        x = self.conv1(x, masked_edge_index)
        x = self.bn1(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.conv2(x, masked_edge_index)
        x = self.bn2(x)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)

        return self.head(x)


class MLP(nn.Module):
    """
    Two-layer MLP baseline — same depth as GCN but no graph convolutions.

    Architecture:
        Linear(in -> 64) | BN | ReLU | Dropout
        Linear(64 -> 32) | BN | ReLU | Dropout
        Linear(32 -> K)
    """

    def __init__(
        self,
        in_channels: int,
        n_classes: int,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_channels, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ---------------------------------------------------------------------------
# Training helpers
# ---------------------------------------------------------------------------

def train_gnn_epoch(
    model: nn.Module,
    loader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """
    One training epoch for any Graph Neural Network (GCN, GraphSAGE, GAT, ThresholdGNN).
    """
    model.train()
    total_loss = 0.0
    total_nodes = 0

    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        out  = model(batch.x, batch.edge_index)
        loss = criterion(out, batch.y)
        loss.backward()
        optimizer.step()
        n = int(batch.num_nodes)
        total_loss  += float(loss) * n
        total_nodes += n

    return total_loss / max(total_nodes, 1)


def train_mlp_epoch(
    model: MLP,
    loader: torch.utils.data.DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """One training epoch for the MLP over a TensorDataset loader."""
    model.train()
    total_loss = 0.0
    n_total    = 0

    for X_batch, y_batch in loader:
        X_batch = X_batch.to(device)
        y_batch = y_batch.to(device)
        optimizer.zero_grad()
        out  = model(X_batch)
        loss = criterion(out, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += float(loss) * len(y_batch)
        n_total    += len(y_batch)

    return total_loss / max(n_total, 1)


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

@torch.no_grad()
def eval_gnn(
    model: nn.Module,
    loader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, float, float, np.ndarray, np.ndarray]:
    """
    Evaluate any GNN model. Returns (loss, acc, macro_f1, all_preds, all_targets).
    """
    from sklearn.metrics import accuracy_score, f1_score

    model.eval()
    total_loss = 0.0
    total_nodes = 0
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index)
            loss = criterion(out, batch.y)
            n = int(batch.num_nodes)
            total_loss  += float(loss) * n
            total_nodes += n

            preds = out.argmax(dim=1).cpu().numpy()
            all_preds.append(preds)
            all_targets.append(batch.y.cpu().numpy())

    avg_loss = total_loss / max(total_nodes, 1)
    y_true = np.concatenate(all_targets)
    y_pred = np.concatenate(all_preds)
    
    acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    return avg_loss, acc, macro_f1, y_pred, y_true


def eval_mlp(
    model: MLP,
    X: torch.Tensor,
    y: torch.Tensor,
    device: torch.device,
) -> tuple[float, float]:
    """
    Evaluate MLP on flat tensors.

    Returns
    -------
    (accuracy, macro_f1)  both in [0, 1]
    """
    from sklearn.metrics import f1_score

    model.eval()
    X = X.to(device)
    y = y.to(device)
    logits = model(X)
    pred   = logits.argmax(dim=1).cpu().numpy()
    true   = y.cpu().numpy()
    acc    = float((pred == true).mean())
    f1     = float(f1_score(true, pred, average="macro", zero_division=0))
    return acc, f1
