# Mosaic — Mathematical & Simulation Model

This document is the authoritative specification of Mosaic's ABM. Every
implementation decision in `architecture.md` and every experiment in
`experiments.md` is traceable to a definition here.

---

## 1. Agent State

Each agent `i` holds:

| Attribute | Type | Description |
|---|---|---|
| `accent_vector` | `np.ndarray` shape `(6,)`, float ∈ [0,1] | Phonetic accent representation |
| `community_id` | int | Community membership (set at init, fixed) |
| `centrality` | float ∈ [0,1] | Degree centrality, normalised across all agents |
| `agent_id` | int | Unique identifier |

---

## 2. Accent Vector — Named Dimensions

The 6-dimensional accent vector encodes phonetically motivated features.
All dimensions are normalised to [0, 1].

| Index | Feature | Phonetic Meaning | Real-world range | Normalised range |
|---|---|---|---|---|
| 0 | F1 of /æ/ | First formant of the TRAP vowel | 600 – 1100 Hz | [0, 1] |
| 1 | F2 of /æ/ | Second formant of the TRAP vowel | 1500 – 2500 Hz | [0, 1] |
| 2 | F1 of /ɑ/ | First formant of the LOT vowel | 600 – 900 Hz | [0, 1] |
| 3 | F2 of /ɑ/ | Second formant of the LOT vowel | 900 – 1500 Hz | [0, 1] |
| 4 | VOT of /p/ | Voice Onset Time (stop consonant aspiration) | 20 – 90 ms | [0, 1] |
| 5 | Speaking rate | Normalised syllables per second proxy | 3 – 7 syl/s | [0, 1] |

**Why these features:** F1/F2 of two vowels captures vowel space position
(the primary dimension of cross-dialectal variation in English). VOT captures
consonant realisation differences. Speaking rate is a suprasegmental feature
that varies systematically across accents and is socially salient.

**Normalisation formula** for a raw value `v` with known range [v_min, v_max]:
```
normalised = (v - v_min) / (v_max - v_min)
```

---

## 3. Community Initialisation

Agents are initialised in communities. Each community has a **prototype accent
vector** — the centre of that community's initial accent distribution. Individual
agent accents are drawn from a multivariate Gaussian around the prototype.

```
a_i ~ N(μ_c, σ_init² · I)   for agent i in community c
```

Where:
- `μ_c` = prototype accent vector for community `c`
- `σ_init = 0.05` (tight initial clustering within a community)
- Vectors are clipped to [0, 1] after sampling

**Default community prototypes** (for 2-community SBM runs):

| Community | F1/æ | F2/æ | F1/ɑ | F2/ɑ | VOT | Rate |
|---|---|---|---|---|---|---|
| Community 0 | 0.30 | 0.35 | 0.40 | 0.30 | 0.25 | 0.40 |
| Community 1 | 0.70 | 0.65 | 0.60 | 0.70 | 0.75 | 0.60 |

Values chosen so communities are separated by ~0.4 in each dimension (clearly
distinct, but not at extreme ends), leaving room for convergence to be visible.

**For single-community runs** (ER, WS, BA topologies):
Agents are initialised from a single Gaussian centred at `μ = [0.5]*6` with
`σ_init = 0.15` (wider spread to generate initial diversity).

---

## 4. Network Topologies

Four topologies are supported. All are generated via NetworkX and returned as
`nx.Graph` objects with node attributes `community_id` and `centrality`.

| Topology | NetworkX call | Key parameters | Characteristic |
|---|---|---|---|
| Erdős-Rényi (ER) | `nx.erdos_renyi_graph(N, p)` | `p=0.05` | Random, low clustering |
| Watts-Strogatz (WS) | `nx.watts_strogatz_graph(N, k, p_rewire)` | `k=6, p_rewire=0.1` | Small-world: high clustering + short paths |
| Barabási-Albert (BA) | `nx.barabasi_albert_graph(N, m)` | `m=3` | Scale-free: power-law degree, influential hubs |
| Stochastic Block Model (SBM) | `nx.stochastic_block_model(sizes, probs)` | `sizes=[N//2, N//2]`, `p_in=0.15, p_out=0.02` | Explicit community structure |

**Default N = 200 agents** for all topologies.

**Centrality computation:** Degree centrality is computed once at initialisation
via `nx.degree_centrality(G)` and stored as a node attribute. Normalised to
[0, 1] by dividing by the maximum degree centrality in the graph.

---

## 5. Interaction Scheduling

At each timestep, one **edge** is sampled uniformly at random from the full edge
list. This models a dyadic conversation event.

```python
# In MosaicModel.step():
edge = random.choice(list(self.G.edges()))
i, j = edge
self.agents[i].update(self.agents[j])   # only i (listener) updates
```

This is asymmetric: agent `i` accommodates toward agent `j`, but `j` does not
change. Which agent is listener vs. speaker is determined by edge direction
(i is always the first node in the sampled edge tuple).

**Rationale:** Language change is driven by listening and accommodation, not
simultaneous mutual adjustment. Asymmetric interaction produces prestige effects
naturally — high-centrality agents appear more often as `j` (speaker), spreading
their accent to more listeners.

---

## 6. Update Rule — Prestige-Weighted Asymmetric Accommodation

The core model equation:

```
a_i(t+1) = a_i(t) + α_ij · (a_j(t) − a_i(t)) + ε
```

Where:

```
α_ij = γ · centrality(j) · 𝟙[‖a_j − a_i‖ < θ]
```

| Parameter | Symbol | Default | Range | Description |
|---|---|---|---|---|
| Prestige weight | γ | 1.0 | [0, 2] | Scales the influence of centrality on update strength |
| Confidence bound | θ | 0.30 | [0.05, 0.5] | Max accent distance for interaction to occur |
| Noise std | σ | 0.01 | [0, 0.05] | Phonetic drift — random perturbation per update |
| Noise term | ε | — | — | `ε ~ N(0, σ²·I)`, clipped so `a_i` stays in [0,1] |

**Bounded confidence (𝟙[...]):** If the Euclidean distance between `a_i` and
`a_j` exceeds θ, the update is suppressed entirely (α_ij = 0). This models the
sociolinguistic reality that speakers only accommodate to others whose accent is
sufficiently similar to their own.

**Centrality scaling:** `centrality(j) ∈ [0,1]` amplifies the update step for
high-centrality speakers. When γ = 0, all agents have equal influence regardless
of position. When γ = 2, a hub agent (centrality ≈ 1) can cause up to double
the accent shift of a peripheral agent.

**Noise term ε:** Represents natural phonetic variability — no two utterances
are identical. Kept small (σ = 0.01) so it does not dominate the interaction
signal but prevents the system from locking into an artificially stable state.

**Post-update clipping:** After every update, `a_i` is clipped to [0, 1]
element-wise to keep all dimensions within valid normalised range.

---

## 7. Convergence Criterion

The simulation terminates when one of three conditions is met:

1. **Perfect Consensus:** When noise `sigma == 0`, the system reaches consensus if the maximum pairwise distance between all agents is `<= epsilon_distance` (default `1e-6`).
2. **Stationary Distribution:** When noise `sigma > 0`, perfect consensus is impossible. The system reaches a stationary equilibrium if the maximum displacement of any agent over a window of `W` (default 20) logged timesteps is `<= epsilon_max` (default `1e-4`).
3. **Max steps reached:** `T = 10,000` timesteps (hard cutoff).

The convergence timestep `t_conv` is recorded alongside an exact `termination_reason`. If the simulation hits the hard cutoff without converging, it is flagged as `Maximum interactions reached`.

---

## 8. Metrics

All metrics are computed from agent state data collected every 100 timesteps.

### 8.1 Shannon Diversity Index

Measures the diversity of accent clusters across the population over time.

```
H(t) = −Σ_k p_k · log(p_k)
```

Where `p_k` = fraction of agents assigned to accent cluster `k` by k-means
(k=5, fitted at each logging step on the current accent vectors). Higher H =
more diverse accents. H → 0 as the population converges to one accent.

### 8.2 Mean Pairwise Accent Distance

Average Euclidean distance between all agent pairs' accent vectors:

```
D(t) = (2 / N(N-1)) · Σ_{i<j} ‖a_i(t) − a_j(t)‖
```

Computationally cheaper than per-cluster entropy; useful as a secondary
convergence signal and for parameter sweep comparisons.

### 8.3 Convergence Time

`t_conv` — the timestep at which the entropy convergence criterion is first met.
Reported per run; aggregated as mean ± SD over Monte Carlo replicates.

### 8.4 Cross-Community Accent Distance (SBM only)

```
D_cross(t) = ‖μ_0(t) − μ_1(t)‖
```

Where `μ_c(t)` = mean accent vector of all agents in community `c` at time `t`.
Tracks how far apart the two community accents remain over time. D_cross → 0
means full dialect merger.

### 8.5 Time-of-Adoption (for S-curve experiment)

For a seeded innovation: the first timestep at which agent `i`'s value on
dimension 0 exceeds a threshold of 0.2 above its initial value.
Adoption fraction `A(t)` = fraction of agents that have adopted by timestep `t`.

### 8.6 Influence Residual Score (for Experiment 2 — Prestige Effect)

Measures how much the final population accent resembles each agent's *initial*
accent — a direct proxy for how much that agent's starting accent "guided" the
population consensus.

```
s_i = −‖a_i(0) − μ_final‖
```

Where:
- `a_i(0)` = agent i's accent vector at timestep 0
- `μ_final` = mean accent vector across all agents at convergence
- The negation means higher `s_i` = population converged *toward* where agent i started

**Why this is a valid influence measure:** In an asymmetric, prestige-weighted
system, high-centrality agents speak to more listeners and shift the population
centroid toward their own accent. An agent with high influence leaves a smaller
residual between their initial accent and the final consensus.

**Usage:** Compute `s_i` for all agents in a run. Compute Spearman r between
`centrality(i)` and `s_i`. Average r across 25 runs per γ condition.

**Expected result:** Spearman r increases with γ (stronger when prestige weighting
is higher); r ≈ 0 when γ = 0 (no prestige effect).

---

## 9. Simulation Run Output

Each run produces files in `runs/{run_id}/`:

**`agent_states.csv`** — logged every 100 steps:
```
timestep, agent_id, community_id, centrality, d0, d1, d2, d3, d4, d5
```

**`config.json`** — full parameter record:
```json
{
  "N": 200, "topology": "watts_strogatz", "T": 10000,
  "gamma": 1.0, "theta": 0.3, "sigma": 0.01,
  "seed": 42, "n_runs": 25, "log_every": 100
}
```

**`metrics.json`** — scalar outputs:
```json
{
  "convergence_time": 4320,
  "converged": true,
  "final_diversity": 0.38,
  "final_pairwise_distance": 0.14
}
```

---

## 10. Resolved Open Questions

*(From progress.md Day 1)*

| Question | Decision | Rationale |
|---|---|---|
| Phonetic range values | Defined in Section 2 and 3 above | Grounded in published formant literature ranges |
| SBM community count | Default = 2 | Two-community contact is the core experiment; 3+ communities deferred |
| GCN vs GAT to start | Start with GCNConv | Simpler to debug; GAT is a 1-line upgrade once baseline works |
| Live frontend vs REST poll | REST polling | Simpler; simulation runs are short (<2 min) |

---

*Last updated: 2026-07-09*
