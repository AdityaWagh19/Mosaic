# Mosaic — Project Context

## What is Mosaic?

Mosaic is an open-source, modular simulation framework for studying how accents
and dialects evolve across socially-structured populations. It models a community
of agents, each holding a phonetically-inspired accent representation, interacting
across a social network and gradually converging toward or diverging from one
another's speech patterns — depending on social structure, prestige, and
communication dynamics.

The project integrates four technical domains into a single cohesive system:
- **Agent-Based Modelling** — Mesa-based simulation of individual speaker behaviour
- **Network Science** — Social graph topologies (ER, WS, BA, SBM) shaping who
  influences whom
- **Machine Learning** — GCN trajectory predictor, unsupervised dialect zone
  discovery, UMAP visualization
- **Software Engineering** — Modular Python codebase, FastAPI backend, React
  web interface with D3.js network visualization

---

## The Problem This Addresses

Accent and dialect change are emergent phenomena — they arise from millions of
individual conversations, not top-down rules. Understanding *how* social network
structure, prestige, and contact between communities shapes these dynamics is
an open question in computational sociolinguistics.

Existing work falls into two camps:
1. **Pure ABM studies** (Axelrod 1997, Buzato & Cunha 2024) — simulate cultural
   or linguistic diffusion but use abstract trait labels or scalar "idiolect"
   values with no phonetic grounding
2. **ML/speech studies** (Lesnichaia et al. 2022, Gubian et al. 2023) — model
   phonetic features but in isolation from social network structure

No unified open-source framework couples **phonetically-informed accent
representation**, **structured social network dynamics**, and an **ML analytics
pipeline** in a single reproducible Python system. Mosaic fills that gap.

---

## Research Questions

Three concrete questions guide the entire project. Every experiment, metric,
and model component is designed to address at least one of these.

**RQ1 — Topology:**
How does social network structure (Erdős-Rényi, Watts-Strogatz, Barabási-Albert,
Stochastic Block Model) affect the rate, pattern, and final diversity of accent
convergence across a population?

**RQ2 — Prestige:**
Does an agent's network centrality (a proxy for social prestige) correlate with
the speed at which its accent influences its local community? And how does the
strength of prestige weighting (γ) interact with network topology?

**RQ3 — Predictability:**
Can a Graph Convolutional Network, trained on simulation outputs, predict an
agent's final accent cluster from its initial network position and accent vector
better than a structure-agnostic MLP baseline — demonstrating that network
topology is predictive of individual accent outcomes?

---

## Theoretical Grounding

**Communication Accommodation Theory (Giles et al. 1991)**
Speakers unconsciously converge their accent toward a conversation partner's to
gain social approval, and diverge to assert distinctiveness. Crucially,
accommodation is asymmetric — lower-status speakers accommodate more toward
higher-status ones. Mosaic's prestige-weighted update rule operationalizes this
directly.

**Axelrod's Cultural Diffusion Model (1997)**
Agents interact with probability proportional to similarity; upon interaction,
they become more alike. Mosaic extends this with continuous phonetic vectors,
prestige weighting, and realistic network topologies instead of a 2D grid.

**Watts-Strogatz & Barabási-Albert Networks**
Small-world networks (WS) have high local clustering and short path lengths,
mirroring real social communities. Scale-free networks (BA) have a few
highly-connected hubs — analogous to influential speakers. Both predict
qualitatively different diffusion dynamics.

**Bounded Confidence (Hegselmann-Krause model)**
Agents only accommodate to neighbours whose accent is within a confidence
threshold θ. This produces realistic accent cluster formation rather than
universal convergence.

---

## Non-Goals

The following are explicitly out of scope for this project:

- Real-time speech processing or audio input
- Actual phoneme transcription or acoustic feature extraction from recordings
- LLM-driven or GPT-powered agents
- Multi-user collaboration or authentication
- Persistent database storage (runs saved as CSVs)
- Formal publication submission or academic peer review
- Reproducing specific real-world dialect change events
- Inter-generational transmission dynamics (deferred to future work)

---

## Future Directions

The following ideas are tracked here to avoid scope creep but are not planned
for the current implementation:

- **Dynamic network rewiring** — links form/dissolve based on accent similarity,
  creating co-evolving network + accent dynamics
- **Inter-generational transmission** — a `GenerationScheduler` periodically
  replaces a fraction of agents with new learners, introducing generation-based
  dynamics
- **wav2vec2 phonetic grounding** — replace synthetic accent initialization with
  real formant statistics extracted from the Speech Accent Archive (Weinberger 2015)
- **GAT upgrade** — `GATConv` instead of `GCNConv`; attention weights become
  an interpretable learned prestige map
- **Multiplex networks** — two-layer graph (offline + online social ties)
  producing qualitatively richer diffusion dynamics
- **arXiv preprint** — a 4-page system demonstration paper once all three phases
  are complete

---

## Technology Stack Summary

| Layer | Technology |
|---|---|
| ABM simulation | Python, Mesa |
| Graph computation | NetworkX |
| ML (GCN) | PyTorch, PyTorch Geometric |
| Dimensionality reduction | umap-learn |
| API backend | FastAPI |
| Frontend | React + Vite |
| Network visualization | D3.js |
| Charts | Recharts |
| Scientific visualization | matplotlib, seaborn |
| Testing | pytest |

---

*Last updated: 2026-07-09*
