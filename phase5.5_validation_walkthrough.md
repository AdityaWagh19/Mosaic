# Phase 5.5: ML Validation Results

The 10-seed benchmarking experiment has concluded. We trained 5 different architectures (MLP, GCN, GraphSAGE, GAT, and our custom Threshold-GNN) on the Phase 5 dataset for 100 epochs across 10 random train-test splits. 

Here are the definitive results.

## Statistical Benchmarking (10 seeds)

| Architecture | Accuracy (95% CI) | Macro F1 (95% CI) |
| :--- | :--- | :--- |
| **MLP** | **88.1%** [86.9–89.4] | **88.6%** [87.8–89.5] |
| **GCN** | 60.5% [56.9–64.2] | 61.9% [58.1–65.7] |
| **GraphSAGE** | 87.0% [85.8–88.2] | 87.5% [86.6–88.3] |
| **GAT** | 60.5% [56.7–64.3] | 61.8% [57.8–65.8] |
| **ThresholdGNN** | 83.5% [81.7–85.3] | 83.8% [82.2–85.4] |

### Significance Tests (vs Threshold-GNN)
We performed Wilcoxon signed-rank tests across the 10 splits, alongside Cohen's d to measure effect size:
* **vs MLP**: p=0.002 (**), Cohen's d = -2.17
* **vs GCN**: p=0.002 (**), Cohen's d = +5.77
* **vs GraphSAGE**: p=0.002 (**), Cohen's d = -1.66
* **vs GAT**: p=0.002 (**), Cohen's d = +5.52

---

## Scientific Interpretation

Based on these results, we can draw the following conclusions, ordered from strongest to most tentative.

### Strong conclusions (well supported)
1. **Model architecture has a major impact on predictive performance.** Performance ranges from 60.5% (GCN/GAT) to 88.1% (MLP). Architecture choice is a dominant factor for this prediction task.
2. **Vanilla GCN performs poorly on this bounded-confidence prediction task.** GCN and GAT achieve only ~60% accuracy, indicating that standard neighborhood aggregation is not well suited to this specific problem.
3. **GraphSAGE substantially outperforms GCN and GAT.** GraphSAGE reaches 87.0%, nearly matching the MLP. Not all GNN architectures behave similarly on bounded-confidence dynamics.
4. **Threshold-aware message passing improves over standard GCNs.** Threshold-GNN improves from 60.5% → 83.5%. Incorporating the simulator's interaction rule into the architecture appears highly beneficial.
5. **Initial node features are highly predictive of the final outcome.** The MLP, which ignores graph structure entirely, achieves the highest accuracy, indicating that the initial feature vectors contain substantial predictive information.

### Moderate conclusions (supported, but carefully worded)
6. **Topology provides limited additional predictive benefit for this particular prediction task.** Since the MLP remains the best performer, graph information does not clearly improve prediction beyond strong node features *for this specific task* (predicting final clusters).
7. **Architectures that preserve node identity perform better than those relying on indiscriminate neighborhood smoothing.** GraphSAGE and Threshold-GNN preserve more of the node's own information than a vanilla GCN, which is consistent with the observed results, though not yet definitively proven.

### Hypotheses supported (not proven)
8. **The poor performance of GCN is consistent with an architectural mismatch between vanilla message passing and bounded-confidence dynamics.** The large improvement from Threshold-GNN supports this hypothesis, though further experiments are needed to rule out all alternative explanations.
9. **Threshold-aware graph learning is a promising direction for modeling bounded-confidence simulations.** The custom Threshold-GNN performs much better than standard GCNs, suggesting that incorporating domain-specific interaction rules into GNNs may be valuable.
