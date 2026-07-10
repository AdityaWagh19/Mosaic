"""
experiments/scurve.py
=====================
S-Curve Validation (Experiment V1)

Design   : WS(N=200), theta=0.50, gamma=5.0, 10 runs (seeds 5000-5009).

Key mechanisms for logistic S-curve:
  1. Persistent innovators: innovator accents reset after every step so the
     innovation signal is never diluted when innovators act as listeners.
  2. Bidirectional edge list: reversed edges added so ALL 6 neighbours of
     each innovator can receive the innovation (not just those where the
     innovator appears as 'j' in G.edges()).
  3. Cumulative adoption tracking: once an agent's dim_0 crosses the
     threshold, they stay counted even if accommodation later pulls them down.
  4. gamma=5.0: stronger prestige weight means ~2-3 contacts with an
     innovator (centrality=0.03 -> alpha=0.15) are enough for adoption.

Track A(t) cumulatively; fit logistic curve; report R2 (must be > 0.85).

Figure   : scurve.png
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit

from simulation.config import SimConfig
from simulation.model import MosaicModel
from simulation.network import make_network
from viz.figures import plot_scurve

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")

N_RUNS = 10
BASE_SEED = 5000

# Experiment parameters
THETA_SCURVE = 0.50       # wide gate: 0.4-distance contacts are within range
GAMMA_SCURVE = 5.0        # strong prestige -> alpha ~ 0.15 per contact
INNOVATION_SHIFT = 0.40   # innovators seeded at initial_mean + 0.40
ADOPTION_THRESHOLD = 0.10 # dim_0 must exceed initial_mean + 0.10 to count
LOG_EVERY = 100


def _logistic(t, L, k, t0):
    return L / (1.0 + np.exp(-k * (t - t0)))


def _compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return float(1.0 - ss_res / max(ss_tot, 1e-12))


def _run_scurve(seed: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Run one S-curve replicate.

    Mechanisms
    ----------
    - Bidirectional edges: model.edge_list is extended with reversed pairs
      so all 6 neighbours of each innovator can receive the innovation.
    - Persistent innovators: accent reset to seeded value after every step.
    - Cumulative adoption: ever_adopted set grows monotonically.

    Returns
    -------
    timesteps  : 1-D array of logged timesteps
    adoption   : 1-D array of cumulative A(t) at each logged timestep
    """
    config = SimConfig(
        topology="watts_strogatz", N=200, T=10_000,
        theta=THETA_SCURVE, gamma=GAMMA_SCURVE, sigma=0.01,
        log_every=LOG_EVERY, seed=seed,
    )

    G = make_network(config)
    model = MosaicModel(config, G)

    # ---- Make edge list bidirectional ----
    # NetworkX returns each undirected edge once; roughly half of innovator
    # neighbours appear on the "wrong" side.  Adding reversed pairs ensures
    # every neighbour can be a listener when the innovator is the speaker.
    original_edges = model.edge_list[:]
    reversed_edges = [(j, i) for i, j in original_edges]
    model.edge_list = original_edges + reversed_edges
    model._n_edges = len(model.edge_list)

    # ---- Seed phonetic innovation in 5% of agents ----
    all_agent_ids = list(model.agents_map.keys())
    n_all = len(all_agent_ids)
    init_dim0 = float(np.mean([model.agents_map[a].accent[0] for a in all_agent_ids]))

    n_seed = max(1, n_all // 20)   # 5%
    rng_seed = np.random.default_rng(seed + 9999)
    innovator_ids = set(
        int(x) for x in rng_seed.choice(all_agent_ids, size=n_seed, replace=False)
    )

    seeded_val = float(np.clip(init_dim0 + INNOVATION_SHIFT, 0.0, 1.0))
    for aid in innovator_ids:
        model.agents_map[aid].accent[0] = seeded_val

    # Save seeded accent vectors for reset after each step
    innovator_saved = {aid: model.agents_map[aid].accent.copy() for aid in innovator_ids}

    adoption_threshold_abs = init_dim0 + ADOPTION_THRESHOLD

    # ---- Custom simulation loop ----
    ever_adopted: set[int] = set(innovator_ids)  # innovators count from t=0

    timesteps_list: list[int] = []
    adoption_list: list[float] = []

    def _snapshot(t: int) -> None:
        for aid in all_agent_ids:
            if aid not in ever_adopted and model.agents_map[aid].accent[0] > adoption_threshold_abs:
                ever_adopted.add(aid)
        timesteps_list.append(t)
        adoption_list.append(len(ever_adopted) / n_all)

    _snapshot(0)

    for t in range(1, config.T + 1):
        model.step()

        # Reset innovator accents — persistent innovation source
        for aid in innovator_ids:
            model.agents_map[aid].accent[:] = innovator_saved[aid]

        if t % LOG_EVERY == 0:
            _snapshot(t)

    t_arr = np.array(timesteps_list, dtype=float)
    a_arr = np.array(adoption_list, dtype=float)

    log.info(
        "  Seed %d: A(0)=%.3f  A(T)=%.3f  (innovators=%d)",
        seed, a_arr[0], a_arr[-1], len(innovator_ids),
    )
    return t_arr, a_arr


def run_experiment() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    log.info(
        "S-curve: %d runs  theta=%.2f  gamma=%.1f  shift=%.2f  threshold=%.2f",
        N_RUNS, THETA_SCURVE, GAMMA_SCURVE, INNOVATION_SHIFT, ADOPTION_THRESHOLD,
    )

    all_timesteps: np.ndarray | None = None
    adoption_rows: list[np.ndarray] = []

    for i in range(N_RUNS):
        seed = BASE_SEED + i
        t_arr, a_arr = _run_scurve(seed)

        if len(t_arr) == 0:
            log.warning("  Run %d produced no data; skipping.", i + 1)
            continue

        if all_timesteps is None:
            all_timesteps = t_arr
        n = min(len(all_timesteps), len(t_arr))
        all_timesteps = all_timesteps[:n]
        adoption_rows.append(a_arr[:n])

    if not adoption_rows or all_timesteps is None:
        log.error("No valid S-curve data produced.")
        return

    min_len = min(len(r) for r in adoption_rows)
    adoption_matrix = np.vstack([r[:min_len] for r in adoption_rows])
    t_common = all_timesteps[:min_len]

    mean_adoption = adoption_matrix.mean(axis=0)
    L_max = float(mean_adoption.max())
    log.info("Mean adoption range: %.3f -> %.3f", mean_adoption[0], L_max)

    # ---- Fit logistic curve ----
    fit_params: dict = {}
    try:
        midpoint_guess = float(t_common[np.argmin(np.abs(mean_adoption - (mean_adoption[0] + L_max) / 2))])
        p0 = [L_max, 0.001, midpoint_guess]
        bounds = ([mean_adoption[0] * 0.5, 1e-7, t_common[0]], [1.0, 1.0, t_common[-1]])
        popt, _ = curve_fit(_logistic, t_common, mean_adoption, p0=p0, bounds=bounds, maxfev=20_000)
        L, k, t0 = popt
        fit_curve = _logistic(t_common, L, k, t0)
        r2 = _compute_r2(mean_adoption, fit_curve)
        fit_params = {"L": float(L), "k": float(k), "t0": float(t0), "r2": float(r2)}

        if r2 >= 0.85:
            log.info("S-curve PASS: R2=%.4f >= 0.85   L=%.3f  k=%.5f  t0=%.0f", r2, L, k, t0)
        else:
            log.warning("S-curve WARN: R2=%.4f < 0.85", r2)
    except Exception as exc:
        log.warning("Logistic fit failed: %s", exc)

    plot_scurve(t_common, adoption_matrix, fit_params, out_path=str(FIGURES_DIR / "scurve.png"))
    log.info("S-curve experiment complete.")

    if fit_params:
        # ASCII-only to avoid cp1252 encoding errors on Windows
        print(f"  R2 = {fit_params['r2']:.4f}   k = {fit_params['k']:.6f}   t0 = {fit_params['t0']:.0f}")


if __name__ == "__main__":
    run_experiment()
