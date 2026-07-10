# Mosaic — ML Pipeline

Full documentation for the Phase 5 Machine Learning Analysis Layer.
Written from the actual implementation; updated with results after execution.

---

## 1. Task Definition

**Problem type:** Per-node multi-class classification.

**Question:** Given only an agent's state at t=0 (initial accent vector + network
centrality), can we predict which dialect cluster it will belong to at t=T?

**Why this matters:** If the GCN outperforms the flat MLP, it means the graph
structure (who your neighbours are at t=0) contains predictive signal about your
long-term linguistic trajectory — beyond what your individual starting accent conveys.

---

## 2. Data

### Source
100 simulation runs from Experiment 1 (topology comparison):
- 25 BA runs (seeds 1200–1224)
- 25 ER runs (seeds 1000–1024)
- 25 WS runs (seeds 1100–1124)
- 25 SBM runs (seeds 1300–1324)

Each run: N=200 agents, T=10,000 steps, log_every=100.

### Schema

**Node features (input):** 7-dimensional vector from agent_states.csv at t=0
```
[d0, d1, d2, d3, d4, d5, centrality]
```

**Node labels (target):** k-means cluster ID of the agent's final accent at t=T
- k=5 clusters fit globally on the union of all 100 runs' final accent matrices
- Same label space shared by GCN and MLP for fair comparison

### Split
Run-level stratified 80/20 split (stratified by topology):
- Train: 80 runs × 200 agents = 16,000 nodes
- Test:  20 runs × 200 agents = 4,000 nodes

Run-level split prevents leakage: nodes from the same simulation share a
correlated graph structure, so node-level split would leak structural information.

---

## 3. Models

### GCN (Graph Convolutional Network)
```
Input: x (N, 7), edge_index (2, E)

GCNConv(7  -> 64) + BatchNorm(64) + ReLU + Dropout(0.3)
GCNConv(64 -> 32) + BatchNorm(32) + ReLU + Dropout(0.3)
Linear(32 -> 5)   -> logits
```
Implementation: `torch_geometric.nn.GCNConv` (Kipf & Welling 2017)

Each graph convolution aggregates messages from 1-hop neighbours, giving the GCN
access to the initial accent distribution of each agent's direct social contacts.

### MLP (Baseline — no graph)
```
Input: x (N, 7)

Linear(7  -> 64) + BatchNorm(64) + ReLU + Dropout(0.3)
Linear(64 -> 32) + BatchNorm(32) + ReLU + Dropout(0.3)
Linear(32 -> 5)  -> logits
```
Identical parameter count, no access to graph structure.
Serves as the baseline: any accuracy gain from GCN quantifies the information
value of graph structure for predicting linguistic trajectory.

---

## 4. Training

| Parameter | Value |
|---|---|
| Loss | CrossEntropyLoss |
| Optimizer | Adam |
| Learning rate | 1e-3 |
| Weight decay | 1e-4 |
| Epochs | 100 |
| GCN batch size | 8 graphs per batch |
| MLP batch size | 256 nodes per batch |
| Device | CUDA if available, else CPU |

---

## 5. Evaluation

**Primary metric:** Per-node classification accuracy on held-out test runs.

**Secondary metric:** Macro-F1 score (balances across unequal cluster sizes).

**Baseline (random chance):** 1/K = 1/5 = 20%

---

## 6. Additional Analyses

### Unsupervised Clustering (analysis/clustering.py)
- **k-means (k=5):** Global fit across all 100 final states. Used for ML labels.
- **DBSCAN:** Density-based; epsilon estimated from 5th percentile of pairwise
  distances. Reports number of naturally occurring clusters without k constraint.
- **Silhouette score** reported for both methods.

### UMAP Accent-Space Trajectories (analysis/umap_viz.py)
- Reference run: `watts_strogatz_1100` (N=200, T=10,000)
- UMAP fitted on final accent state (t=10,000) — anchored embedding
- Transform applied to snapshots at t=0, 2500, 5000, 10000
- 4-panel figure shows how accent clusters form and tighten over time

---

## 7. Results

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Random chance | 20.0% | — |
| MLP (baseline) | **89.2%** | **89.5%** |
## 6. Results & Scientific Interpretation (Phase 5.5 Validation)

To definitively test the hypotheses raised by the initial Phase 5 results, we evaluated 5 architectures across 10 random seeds (train/test splits) over 100 runs.

### Statistical Benchmarking (10 seeds)

| Architecture | Accuracy (95% CI) | Macro F1 (95% CI) |
| :--- | :--- | :--- |
| **MLP** | **88.1%** [86.9–89.4] | **88.6%** [87.8–89.5] |
| **GCN** | 60.5% [56.9–64.2] | 61.9% [58.1–65.7] |
| **GraphSAGE** | 87.0% [85.8–88.2] | 87.5% [86.6–88.3] |
| **GAT** | 60.5% [56.7–64.3] | 61.8% [57.8–65.8] |
| **ThresholdGNN** | 83.5% [81.7–85.3] | 83.8% [82.2–85.4] |

### Strong conclusions (well supported)
1. **Model architecture has a major impact on predictive performance.** Performance ranges from 60.5% (GCN/GAT) to 88.1% (MLP). Architecture choice is a dominant factor for this prediction task.
2. **Vanilla GCN performs poorly on this bounded-confidence prediction task.** GCN and GAT achieve only ~60% accuracy, indicating that standard neighborhood aggregation is not well suited to this specific problem.
3. **GraphSAGE substantially outperforms GCN and GAT.** GraphSAGE reaches 87.0%, nearly matching the MLP. This shows that not all GNN architectures behave similarly on bounded-confidence dynamics.
4. **Threshold-aware message passing improves over standard GCNs.** Threshold-GNN improves from 60.5% → 83.5%. Incorporating the simulator's interaction rule into the architecture appears beneficial.
5. **Initial node features are highly predictive of the final outcome.** The MLP, which ignores graph structure entirely, achieves the highest accuracy, indicating that the initial feature vectors contain substantial predictive information for this task.

### Moderate conclusions (supported, but carefully worded)
6. **Topology provides limited additional predictive benefit for this particular prediction task.** Since the MLP remains the best performer, graph information does not clearly improve prediction beyond strong node features for this specific task (predicting final clusters), though this may not apply to the simulator as a whole.
7. **Architectures that preserve node identity perform better than those relying on indiscriminate neighborhood smoothing.** GraphSAGE and Threshold-GNN preserve more of the node's own information than a vanilla GCN, which is consistent with the observed results.

### Hypotheses supported (not proven)
8. **The poor performance of GCN is consistent with an architectural mismatch between vanilla message passing and bounded-confidence dynamics.** The large improvement from Threshold-GNN supports this hypothesis, though further experiments are needed to rule out all alternative explanations.
9. **Threshold-aware graph learning is a promising direction for modeling bounded-confidence simulations.** The custom Threshold-GNN performs much better than standard GCNs, suggesting that incorporating domain-specific interaction rules into GNNs may be valuable.

### Clustering Analysis

| Method | Silhouette | Clusters found |
|---|---|---|
| k-means (K=5) | 0.089 | 5 (forced) |
| DBSCAN | −1.000 | 1 (no clear separation) |

The near-zero silhouette and DBSCAN's failure to find multiple clusters reveal
that the final accent space is a **continuum**, not a set of discrete clusters.
The k-means K=5 partition is a useful but somewhat arbitrary discretisation for
the supervised ML task.

**Output figures:**
- `results/figures/gcn_vs_mlp_accuracy.png`
- `results/figures/gcn_vs_mlp_loss.png`
- `results/figures/cluster_map.png`
- `results/figures/umap_4panel.png`

**Results JSON:** `results/ml_results.json`
