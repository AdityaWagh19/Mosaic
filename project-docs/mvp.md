# Mosaic — MVP Specification (Phase 1)

The MVP is the complete, working simulation core. It is the deliverable that
makes Mosaic a real project — all subsequent phases build on top of it.

**MVP is Phase 1. Done means all acceptance criteria in Section 4 are met.**

---

## 1. What is Included

### Simulation Engine
- `SimConfig` dataclass with all parameters (topology, N, T, γ, θ, σ, seed, n_runs)
- `AccentAgent` with 6-dimensional phonetic accent vector and prestige-weighted update rule
- `MosaicModel` with edge-based random interaction scheduling
- `NetworkGenerator` producing all four topologies: ER, WS, BA, SBM
- Pairwise-distance consensus and windowed stationarity detection
- Hard timestep cutoff at T = 10,000

### Data Pipeline
- `DataLogger`: per-run CSV (agent states every 100 steps) + `config.json` + `metrics.json`
- `MonteCarloRunner`: 25 runs per condition, summary CSV with mean ± SD

### Experiments (from `experiments.md`)
- Experiment 1: Topology comparison (ER vs WS vs BA vs SBM)
- Experiment 2: Prestige/centrality effect (varying γ on BA network)
- Experiment 3: Two-community dialect contact (SBM, varying p_out)
- 4 ablation studies (no homophily, no prestige, no noise, symmetric)
- S-curve logistic fit validation

### Visualisations (matplotlib / seaborn)
- Diversity time series (H(t) vs timestep, mean ± SD band over 25 runs)
- Convergence time boxplots across topologies
- Network snapshot: nodes coloured by k-means accent cluster (spring layout)
- **Animated diffusion GIF** — nodes change colour over time as accents evolve
- Parameter heatmap: convergence time over (topology × θ) grid
- Parameter heatmap: final diversity over (topology × γ) grid
- Cross-community distance decay curve (SBM experiment)
- S-curve adoption plot with logistic fit overlay

### Software Quality
- `tests/` with ≥ 20 pytest unit tests
- `notebooks/demo.ipynb` — narrative walkthrough of one complete run
- `README.md` — project description, setup instructions, animated GIF, key figures
- `requirements.txt`

---

## 2. What is Excluded (Phase 2+)

| Feature | Phase |
|---|---|
| GCN trajectory predictor | Phase 2 |
| MLP baseline | Phase 2 |
| UMAP visualisation | Phase 2 |
| k-means / DBSCAN clustering scripts | Phase 2 |
| SHAP feature importance | Phase 2 (optional) |
| FastAPI backend | Phase 3 |
| React frontend | Phase 3 |
| D3.js network visualisation | Phase 3 |
| GitHub Actions CI/CD | Optional |

---

## 3. Build Order Within Phase 1

Build in this order — each step depends on the previous:

1. `config.py` — SimConfig dataclass
2. `network.py` — NetworkGenerator (all 4 topologies + node attributes)
3. `agent.py` — AccentAgent with update rule
4. `model.py` — MosaicModel with edge-based scheduling + convergence detection
5. `logger.py` — DataLogger (CSV + JSON output)
6. `runner.py` — MonteCarloRunner
7. `tests/` — Unit tests (write alongside each module)
8. Experiment scripts — topology comparison, prestige sweep, SBM contact, ablations
9. Visualisation scripts — all figures + animated GIF
10. `notebooks/demo.ipynb` — after all scripts work
11. `README.md` — after GIF and figures are generated

---

## 4. Acceptance Criteria

Phase 1 is complete when **all** of the following are true:

| # | Criterion | How to verify |
|---|---|---|
| AC1 | All ≥ 20 unit tests pass | `pytest tests/ -v` — all green |
| AC2 | Single run N=200, T=10,000 completes in < 60s | `time python -m simulation.runner` |
| AC3 | Diversity decreases monotonically on average across 25 runs (WS default config) | Check summary.csv: final_diversity < initial_diversity |
| AC4 | BA topology converges faster than ER topology at same θ (25 runs each) | Mean convergence_time(BA) < mean convergence_time(ER) |
| AC5 | S-curve logistic fit achieves R² > 0.85 | Check fit output in experiment script |
| AC6 | Animated diffusion GIF is generated and visually shows accent clusters forming | Review GIF manually |
| AC7 | Parameter heatmap shows at least one clear monotonic trend | Review figure manually |
| AC8 | `demo.ipynb` runs end-to-end without errors | `jupyter nbconvert --to notebook --execute demo.ipynb` |
| AC9 | All run outputs are reproducible: re-running with same seed produces identical CSVs | `diff run1/agent_states.csv run2/agent_states.csv` — empty |
| AC10 | README is complete with setup instructions and embedded GIF | Review on GitHub |

---

## 5. Known Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Convergence never triggered for some configs (θ too small) | Medium | Hard cutoff at T=10,000 handles this; flag `converged=False` in metrics |
| Edge sampling is slow for dense graphs (large E) | Low | Precompute edge list once at init; use numpy for random choice |
| Animated GIF file size too large for README | Low | Limit to N=100, 50fps, 5s duration; compress with Pillow |
| k-means for H(t) is slow if refit every 100 steps | Medium | Cache cluster centroids; only refit for final metric reporting |

---

*Last updated: 2026-07-13*
