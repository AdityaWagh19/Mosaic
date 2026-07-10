# Phase 5.5: ML Validation

This phase focuses exclusively on validating the ML results from Phase 5 to determine whether the GCN's failure was an architectural flaw or a true reflection of the simulator underutilising graph topology.

## Proposed Changes

### ML Architecture Benchmarking
**Component:** `analysis/validation.py` (New File)
- **Objective:** Test the hypothesis that standard GNNs fail due to architectural blindness to the $\theta$ threshold, and compare against alternative message-passing mechanisms.
- **Setup:** Evaluate 5 architectures on the same final-cluster prediction task from Phase 5:
  1. **MLP** (Baseline, features only)
  2. **GCN** (Standard mean-pooling)
  3. **GraphSAGE** (Sampled aggregation)
  4. **GAT** (Attention-based)
  5. **Threshold-GNN** (Custom layer: computes Euclidean distance between nodes and mathematically masks edges where distance $> \theta$).

### Methodology & Rigour
- **10 Random Seeds:** Run all 5 architectures over 10 distinct random seeds for model initialisation and train-test splits.
- **Metrics:** Report **Mean Accuracy** and **Macro F1-score** with **95% Confidence Intervals** for all architectures.
- **Significance Testing:** Perform **Wilcoxon signed-rank tests** comparing the Threshold-GNN against the GCN and MLP baselines to prove statistical significance. 
- **Effect Size:** Report **Cohen's d** to quantify the magnitude of the performance difference.

### Interpretation Criteria
This experimental design ensures that every possible outcome is scientifically informative:
- **Threshold-GNN ≫ GCN (Significant):** Supports the hypothesis that threshold-aware message passing better matches the simulation dynamics.
- **Threshold-GNN ≈ GCN (Not Significant):** Suggests architecture alone does not explain the performance gap.
- **MLP still outperforms everything (Significant):** Suggests the prediction task is dominated by initial node features, or that topology contributes little to this specific task.
- **GAT or GraphSAGE outperform Threshold-GNN:** Suggests attention or alternative aggregation mechanisms are more important than explicit threshold masking.

## Verification Plan

- Run the `analysis/validation.py` script.
- Output a comprehensive results table comparing the 5 architectures (Accuracy, F1, 95% CIs).
- Output statistical test results (p-values and Cohen's d).
- Use the results to definitively validate or reject the Phase 5 interpretation based on the explicit criteria above.

## User Review Required
> [!NOTE]
> I have incorporated your optional improvements: reporting Macro F1 alongside Accuracy, and including Wilcoxon signed-rank tests and Cohen's d for rigorous significance testing.
> 
> Is this final, publication-quality validation plan approved for execution?
