"""
experiments/run_all.py
======================
Entry point: runs all 6 Phase-4 experiments sequentially then generates the GIF.

Order:
  1. S-curve (quick, validates parameters first)
  2. Exp 1 — Topology comparison
  3. Exp 2 — Prestige effect
  4. Exp 3 — Dialect contact
  5. Ablations
  6. Heatmaps (slowest — parallelised internally)
  7. Animated GIF

Usage:
    python -m experiments.run_all
    python experiments/run_all.py
"""
from __future__ import annotations

import logging

import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

FIGURES_DIR = Path("results/figures")


def _banner(title: str) -> None:
    log.info("")
    log.info("=" * 60)
    log.info("  %s", title)
    log.info("=" * 60)


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    total_start = time.monotonic()

    # 1. S-curve
    _banner("V1 — S-Curve Validation")
    t0 = time.monotonic()
    from experiments.scurve import run_experiment as run_scurve
    run_scurve()
    log.info("S-curve done in %.1fs", time.monotonic() - t0)

    # 2. Exp 1 — Topology comparison
    _banner("Exp 1 — Topology Comparison")
    t0 = time.monotonic()
    from experiments.exp1_topology import run_experiment as run_exp1
    run_exp1()
    log.info("Exp 1 done in %.1fs", time.monotonic() - t0)

    # 3. Exp 2 — Prestige effect
    _banner("Exp 2 — Prestige and Centrality Effect")
    t0 = time.monotonic()
    from experiments.exp2_prestige import run_experiment as run_exp2
    run_exp2()
    log.info("Exp 2 done in %.1fs", time.monotonic() - t0)

    # 4. Exp 3 — Dialect contact
    _banner("Exp 3 — Two-Community Dialect Contact")
    t0 = time.monotonic()
    from experiments.exp3_contact import run_experiment as run_exp3
    run_exp3()
    log.info("Exp 3 done in %.1fs", time.monotonic() - t0)

    # 5. Ablations
    _banner("Ablation Studies")
    t0 = time.monotonic()
    from experiments.ablations import run_experiment as run_ablations
    run_ablations()
    log.info("Ablations done in %.1fs", time.monotonic() - t0)

    # 6. Heatmaps (parallelised)
    _banner("Heatmaps  (parallelised, ~1,000 runs)")
    t0 = time.monotonic()
    from experiments.heatmaps import run_experiment as run_heatmaps
    run_heatmaps()
    log.info("Heatmaps done in %.1fs", time.monotonic() - t0)

    # 7. Animated GIF
    _banner("Animated GIF — Dialect Diffusion")
    t0 = time.monotonic()
    try:
        from viz.gif import make_diffusion_gif
        # Use a WS run from Exp 1 as the reference
        make_diffusion_gif(
            run_id="watts_strogatz_1100",
            runs_dir="runs",
            n_display=100,
            fps=20,
            n_frames=60,
            out_path=str(FIGURES_DIR / "diffusion.gif"),
        )
        log.info("GIF done in %.1fs", time.monotonic() - t0)
    except Exception as exc:
        log.error("GIF generation failed: %s", exc)

    # ---- Summary ----
    total = time.monotonic() - total_start
    _banner(f"Phase 4 complete in {total:.0f}s  ({total/60:.1f} min)")

    # Verify all expected figures exist
    expected = [
        "e1_diversity_timeseries.png",
        "e1_convergence_boxplot.png",
        "e1_final_diversity_bar.png",
        "e2_centrality_vs_influence.png",
        "e2_spearman_vs_gamma.png",
        "e2_network_snapshot.png",
        "e3_network_4panel.png",
        "e3_cross_community_distance.png",
        "e3_merger_time_bar.png",
        "ablation_boxplot.png",
        "scurve.png",
        "heatmap_convergence_theta.png",
        "heatmap_diversity_gamma.png",
        "diffusion.gif",
    ]
    log.info("")
    log.info("Figure check:")
    all_ok = True
    for fname in expected:
        p = FIGURES_DIR / fname
        if p.exists():
            size_kb = p.stat().st_size // 1024
            log.info("  ✓  %-45s  %d KB", fname, size_kb)
        else:
            log.error("  ✗  MISSING: %s", fname)
            all_ok = False

    if all_ok:
        log.info("")
        log.info("All 14 output files present. Phase 4 DONE.")
    else:
        log.error("Some files are missing — check errors above.")


if __name__ == "__main__":
    main()
