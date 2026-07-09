# Mosaic — Experimental Design

All experiments are specified here before any simulation runs to ensure the
analysis plan is pre-determined, not post-hoc. Every experiment maps to at
least one research question from `context.md`.

---

## 1. General Protocol

- **Monte Carlo replicates:** 25 runs per experimental condition
- **Reporting:** mean ± SD across runs unless stated otherwise
- **Default config:** N=200, T=10,000, θ=0.30, γ=1.0, σ=0.01, log_every=100
- **Figures:** saved to `results/figures/` as PNG at 300 DPI
- **Run outputs:** stored in `runs/` per `architecture.md §3.5`
- **Seed scheme:** base seed + run index (seed 42, 43, 44, ...)

---

## 2. Experiment 1 — Topology Comparison

**Research question:** RQ1 — How does network topology shape accent convergence?

**Design:**
- Independent variable: topology ∈ {ER, WS, BA, SBM}
- Fixed: θ=0.30, γ=1.0, σ=0.01, N=200
- 25 runs per topology → 100 total runs

**Metrics collected per run:**
- Convergence time (`t_conv`)
- Final Shannon diversity (`H_final`)
- Final mean pairwise distance (`D_final`)

**Outputs:**

| Figure | Type | Description |
|---|---|---|
| E1-A | Line plot | H(t) vs timestep for each topology (mean ± SD band) |
| E1-B | Boxplot | Convergence time distribution per topology |
| E1-C | Bar chart | Final diversity per topology (mean ± SD) |

**Expected results:**
- BA converges fastest (hub-driven influence propagation)
- WS retains most diversity (high local clustering resists global consensus)
- ER falls between WS and BA
- SBM shows two-phase convergence (rapid intra-community, slow inter-community)

**Acceptance criterion:** At least one topology shows a non-overlapping mean ± SD
range for convergence time compared to another topology.

---

## 3. Experiment 2 — Prestige and Centrality Effect

**Research question:** RQ2 — Does agent centrality correlate with the speed at
which its accent influences the population?

**Design:**
- Network: BA(N=300, m=3) — highest degree variance, clearest prestige gradient
- Independent variable: γ ∈ {0.0, 0.5, 1.0, 2.0}
- Fixed: θ=0.30, σ=0.01
- 25 runs per γ value → 100 total runs

**Influence metric — Influence Residual Score (`s_i`):**

For each agent `i` in a completed run:

```
s_i = −‖a_i(0) − μ_final‖
```

Where `a_i(0)` is agent i's initial accent and `μ_final` is the mean accent
vector of the full population at convergence. Higher `s_i` means the population
converged *toward* where agent i started — agent i had more influence.

See `model.md §8.6` for full definition and rationale.

**Why this operationalisation:** In the asymmetric update rule, high-centrality
agents are selected as speakers more often (proportional to degree), so they
shift the population centroid toward their initial accent more than peripheral
agents do. This is directly captured by the residual between the agent's initial
accent and the final consensus — no innovation seeding required, computable from
standard run output.

**Analysis per run:**
1. Load `agent_states.csv` for timestep 0 (initial accents)
2. Load final timestep accents (at `t_conv`)
3. Compute `μ_final` = mean accent vector over all agents
4. Compute `s_i` for each agent
5. Compute Spearman r between `centrality(i)` and `s_i`

**Outputs:**

| Figure | Type | Description |
|---|---|---|
| E2-A | Scatter + regression line | Centrality vs s_i per agent (one panel per γ, one representative run) |
| E2-B | Line plot | Mean Spearman r vs γ, with ± SD across 25 runs |
| E2-C | Network snapshot | BA network at convergence; node size ∝ centrality, colour = cluster |

**Expected results:**
- γ=0: Spearman r ≈ 0 (centrality has no effect on influence)
- γ>0: Spearman r increases monotonically as γ increases
- γ=2.0: strongest correlation — hub agents' initial accents dominate the consensus

---

## 4. Experiment 3 — Two-Community Dialect Contact

**Research question:** RQ1 (extended) — How does inter-community connection
density affect dialect merger speed and outcome?

**Design:**
- Network: SBM with 2 communities (100 agents each)
- Intra-community: p_in = 0.15 (fixed)
- Independent variable: p_out (bridge density) ∈ {0.005, 0.01, 0.02, 0.05}
- Community 0 initialised at prototype [0.30, 0.35, 0.40, 0.30, 0.25, 0.40]
- Community 1 initialised at prototype [0.70, 0.65, 0.60, 0.70, 0.75, 0.60]
- Fixed: γ=1.0, θ=0.30, σ=0.01
- 25 runs per p_out value → 100 total runs

**Metrics collected per run:**
- Cross-community accent distance D_cross(t) over time (`model.md §8.4`)
- Time-to-merger: first timestep where D_cross(t) < 0.1
- Whether full merger is achieved within T steps

**Outputs:**

| Figure | Type | Description |
|---|---|---|
| E3-A | 4-panel network grid | Snapshots at t=0, t=2000, t=6000, t=conv for one run (p_out=0.02). Nodes coloured by community_id at t=0, by cluster_id at later steps |
| E3-B | Line plot | D_cross(t) vs timestep for all 4 p_out values (mean ± SD band) |
| E3-C | Bar chart | Time-to-merger vs p_out |

**Expected results:**
- Higher p_out → faster dialect merger
- Very low p_out (0.005): communities may not merge within T=10,000 steps
- Relationship is non-linear: small increase in bridge density near the critical
  threshold has an outsized effect on merger speed

---

## 5. Ablation Studies

Four ablations test which model components are necessary for observed dynamics.
Each modifies exactly one parameter from the default config. 25 runs per
ablation, compared against 25 baseline runs (default config, WS topology).

| # | Name | Modification | What it isolates |
|---|---|---|---|
| A1 | No homophily | θ = ∞ (no bounded confidence) | Role of similarity threshold in dialect cluster formation |
| A2 | No prestige | γ = 0 (uniform influence) | Whether centrality-weighted influence affects dynamics |
| A3 | No noise | σ = 0 (deterministic) | Effect of phonetic drift on convergence |
| A4 | Symmetric | Both i and j update per interaction | Whether asymmetric accommodation changes outcomes |

**Output per ablation:**
- Comparison table: mean convergence_time and final_diversity vs baseline (± SD)
- Combined boxplot: all 4 ablations + baseline side by side (2 panels: time + diversity)

**Expected results:**
- A1 (no homophily): fastest convergence, lowest final diversity (single dominant accent)
- A2 (no prestige): slower, more symmetric convergence; no hub-driven acceleration
- A3 (no noise): slightly faster, more deterministic trajectories
- A4 (symmetric): faster convergence; lower diversity (both agents pull toward each other)

---

## 6. S-Curve Validation

**Purpose:** Verify that the model produces the logistic (S-shaped) innovation
adoption curve known from empirical sociolinguistics.

**Design:**
- Network: WS (N=200, k=6, p_rewire=0.1)
- At t=0: set dim 0 of a random 5% of agents to `initial_value + 0.4`
  (a seeded phonetic innovation: a shifted F1/æ value)
- Track adoption fraction A(t): fraction of agents with dim_0 > `initial_mean + 0.2`
- Run until A(t) = 1.0 or T steps reached
- 10 runs; fit logistic curve to mean A(t)

**Logistic fit:**
```
A(t) = 1 / (1 + exp(−k · (t − t₀)))
```
Fit using `scipy.optimize.curve_fit`. Report: k (growth rate), t₀ (inflection
point), R² for each run.

**Output:**
- Line plot: A(t) vs timestep (all 10 runs in grey, mean in colour, logistic
  fit overlaid as dashed line). R² reported in legend.

**Acceptance criterion:** R² > 0.85.

**Failure interpretation:** R² < 0.85 means the adoption curve is non-logistic —
likely caused by σ too high (noise disrupts smooth spread) or θ too small
(innovation can't propagate across accent-distant agents). Adjust before
running main experiments.

---

## 7. Parameter Heatmaps

Two systematic sweeps showing how key parameters interact with network topology.
These are **pre-computed offline** (run once, results saved as figures).
They are not re-run during demos — the PNG figures are the deliverable.

### Heatmap 1 — Convergence Time over (Topology × θ)

5 topologies × 5 θ values × 25 runs = **500 total runs**

| | θ=0.10 | θ=0.20 | θ=0.30 | θ=0.40 | θ=0.50 |
|---|---|---|---|---|---|
| ER | · | · | · | · | · |
| WS | · | · | · | · | · |
| BA | · | · | · | · | · |
| SBM | · | · | · | · | · |

- Cell value: mean convergence time over 25 runs
- Colour scale: sequential (light = fast convergence, dark = slow)
- Fixed: γ=1.0, σ=0.01, N=200

### Heatmap 2 — Final Diversity over (Topology × γ)

4 topologies × 5 γ values × 25 runs = **500 total runs**

| | γ=0.0 | γ=0.5 | γ=1.0 | γ=1.5 | γ=2.0 |
|---|---|---|---|---|---|
| ER | · | · | · | · | · |
| WS | · | · | · | · | · |
| BA | · | · | · | · | · |
| SBM | · | · | · | · | · |

- Cell value: mean final Shannon diversity over 25 runs
- Fixed: θ=0.30, σ=0.01, N=200

**Total run budget:** 1,000 runs. At <60s per run, parallelised with
`concurrent.futures.ProcessPoolExecutor` across available CPU cores, this is
feasible as a single overnight batch job. Results saved to `results/summary.csv`;
figures generated once and committed to the repo.

**Demo behaviour:** Heatmap figures are static PNGs shown from the repo.
Live demos use single on-demand runs (<60s each) via the frontend.

---

## 8. Metrics Reference

| Metric | Symbol | Definition | Reference |
|---|---|---|---|
| Shannon diversity | H(t) | −Σ pₖ log(pₖ) over k-means clusters | model.md §8.1 |
| Mean pairwise distance | D(t) | Mean ‖aᵢ − aⱼ‖ over all pairs | model.md §8.2 |
| Convergence time | t_conv | First timestep H stops changing | model.md §8.3 |
| Cross-community distance | D_cross(t) | ‖μ₀ − μ₁‖ | model.md §8.4 |
| Adoption fraction | A(t) | Fraction that adopted innovation | model.md §8.5 |
| Influence residual score | s_i | −‖a_i(0) − μ_final‖ | model.md §8.6 |
| Spearman r | r_s | Centrality vs s_i correlation | scipy.stats.spearmanr |
| Silhouette score | S | Clustering quality | sklearn.metrics |
| ARI | ARI | Cluster vs community alignment | sklearn.metrics |

---

## 9. Visualisation Plan Summary

| Figure | Experiment | Type | Key message |
|---|---|---|---|
| E1-A | Topology comparison | Line plot | Topologies produce qualitatively different diversity trajectories |
| E1-B | Topology comparison | Boxplot | BA converges faster than WS |
| E1-C | Topology comparison | Bar chart | Final diversity varies meaningfully by topology |
| E2-A | Prestige effect | Scatter | Centrality correlates with influence score when γ > 0 |
| E2-B | Prestige effect | Line plot | Spearman r increases monotonically with γ |
| E2-C | Prestige effect | Network snapshot | Hubs visually dominate the final accent at convergence |
| E3-A | Dialect contact | 4-panel network | Communities start distinct, progressively merge |
| E3-B | Dialect contact | Line plot | Higher bridge density → faster dialect merger |
| E3-C | Dialect contact | Bar chart | Merge time vs p_out (non-linear relationship) |
| A-all | Ablations | Boxplot | Contribution of each component to emergent dynamics |
| V1 | S-curve | Line + fit | Logistic innovation spread confirmed (R² > 0.85) |
| H1 | Heatmap | Heatmap | Convergence time landscape over topology × θ |
| H2 | Heatmap | Heatmap | Final diversity landscape over topology × γ |

---

*Last updated: 2026-07-09*
