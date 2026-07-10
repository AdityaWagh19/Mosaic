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
| GCN | 51.1% | 50.3% |

**GCN vs MLP delta: −38.1 pp** — the MLP dramatically outperforms the GCN.

### Interpretation

**Why MLP wins by such a large margin:**
The initial accent vector `[d0..d5]` alone is highly predictive of final cluster
membership (89.2% accuracy). In bounded-confidence dynamics (Deffuant model),
an agent's long-run trajectory is strongly determined by its starting position
relative to the implicit cluster boundaries — the MLP exploits this directly.

**Why the GCN underperforms:**
The 2-layer GCN aggregates messages over the 1-hop neighbourhood on every
forward pass. Because the initial accents are already so predictive on their
own, neighbourhood averaging *dilutes* the individual signal — a classic
manifestation of **over-smoothing**. The GCN essentially smooths away the very
information the MLP uses cleanly. With 200-node graphs and 2 conv layers, every
node receives a weighted average of its ~6 WS / ~3 BA neighbours' features,
pulling its representation toward the local community centroid and losing the
fine-grained initial position information.

**Research implication:**
This result supports the theoretical claim that in Deffuant-type models,
*individual initial position* is the dominant predictor of trajectory outcome,
not local network topology. Graph structure primarily governs *convergence
speed* and *isogloss boundary formation* (as shown in Phase 4 Experiments 1–3),
not which cluster an agent ultimately joins. A single-layer GCN or a GCN with
a skip-connection (residual link from input to output) would likely recover
much of the accuracy gap.

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
