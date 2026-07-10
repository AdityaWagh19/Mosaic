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
from torch_geometric.nn import GCNConv

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

def train_gcn_epoch(
    model: GCN,
    loader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> float:
    """
    One training epoch for the GCN over a GraphDataLoader of batched graphs.

    Prerequisite: all Data objects must have explicit num_nodes set so PyG 2.6.x
    does not infer node count from edge_index, which could cause y-size ambiguity.
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
def evaluate_gcn(
    model: GCN,
    dataset: list,
    device: torch.device,
) -> tuple[float, float]:
    """
    Evaluate GCN on a list of Data objects.

    Returns
    -------
    (accuracy, macro_f1)  both in [0, 1]
    """
    from sklearn.metrics import f1_score

    model.eval()
    all_pred: list[int] = []
    all_true: list[int] = []

    for data in dataset:
        data   = data.to(device)
        logits = model(data.x, data.edge_index)
        pred   = logits.argmax(dim=1).cpu().numpy().tolist()
        true   = data.y.cpu().numpy().tolist()
        all_pred.extend(pred)
        all_true.extend(true)

    p = np.array(all_pred)
    t = np.array(all_true)
    acc = float((p == t).mean())
    f1  = float(f1_score(t, p, average="macro", zero_division=0))
    return acc, f1


@torch.no_grad()
def evaluate_mlp(
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
