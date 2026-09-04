from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from .capital import simulate_capital
from .config import SimulationConfig
from .optimization import optimise_control_packages
from .systemic import systemic_stress


def _save_table(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path.with_suffix(".csv"), index=False)
    frame.to_parquet(path.with_suffix(".parquet"), index=False)


def _money(value: float) -> str:
    return f"GBP {value:,.0f}"


def build_report(config: SimulationConfig) -> Path:
    output = config.output_dir
    runs = pd.read_parquet(output / "runs.parquet")
    stages = pd.read_parquet(output / "stage_metrics.parquet")
    fault_runs = runs.loc[runs["fault_type"] != "CONTROL"].copy()
    figures = output / "figures"
    tables = output / "tables"
    figures.mkdir(exist_ok=True)
    tables.mkdir(exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    capital, annual_losses, severity = simulate_capital(runs, config)
    systemic = systemic_stress(annual_losses, config)
    optimisation = optimise_control_packages(capital)
    for name, frame in {
        "capital": capital, "annual_losses": annual_losses, "severity_models": severity,
        "systemic_stress": systemic, "control_optimisation": optimisation,
    }.items():
        _save_table(frame, tables / name)

    summary = fault_runs.groupby(["fault_type", "topology"], as_index=False).agg(
        runs=("run_id", "size"), detection_rate=("detected", "mean"),
        silent_failure_rate=("silent_failure", "mean"),
        median_abs_delta=("paired_final_delta", lambda x: float(np.median(np.abs(x)))),
        p95_abs_delta=("paired_final_delta", lambda x: float(np.quantile(np.abs(x), .95))),
        median_amplification=("amplification_final", "median"),
    )
    _save_table(summary, tables / "fault_topology_summary")

    stage_plot = stages.loc[stages["fault_type"] != "CONTROL"].copy()
    stage_plot["amplification_plot"] = stage_plot["amplification_from_injection"].clip(upper=100)
    plt.figure(figsize=(9, 5))
    sns.lineplot(data=stage_plot, x="stage_order", y="amplification_plot", hue="topology", estimator="median", errorbar=("pi", 50))
    plt.xticks(range(1, 7), [f"S{i}" for i in range(1, 7)])
    plt.ylabel("Median amplification (capped at 100 for display)")
    plt.xlabel("Workflow stage")
    plt.tight_layout(); plt.savefig(figures / "fig1_error_propagation.png", dpi=180); plt.close()

    plt.figure(figsize=(10, 5))
    plot = fault_runs.assign(abs_relative_error=fault_runs["paired_final_error"].abs() + 1e-10)
    sns.violinplot(data=plot, x="topology", y="abs_relative_error", inner="quartile", cut=0)
    plt.yscale("log"); plt.xticks(rotation=25, ha="right")
    plt.ylabel("Absolute paired final error (log scale)")
    plt.tight_layout(); plt.savefig(figures / "fig2_error_by_topology.png", dpi=180); plt.close()

    heat = fault_runs.pivot_table(index="fault_type", columns="injection_stage", values="detected", aggfunc="mean")
    plt.figure(figsize=(8, 5)); sns.heatmap(heat, vmin=0, vmax=1, annot=True, fmt=".2f", cmap="viridis")
    plt.xlabel("Injection stage"); plt.ylabel("Fault type")
    plt.tight_layout(); plt.savefig(figures / "fig3_detection_heatmap.png", dpi=180); plt.close()

    cap_plot = capital.loc[capital["topology"].str.startswith("T5_HUMAN_K")].copy()
    cap_plot["checkpoints"] = cap_plot["topology"].str.extract(r"K(\d+)").astype(int)
    cap_plot["checkpoints_removed"] = 3 - cap_plot["checkpoints"]
    plt.figure(figsize=(8, 5)); sns.lineplot(data=cap_plot, x="checkpoints_removed", y="var_995", marker="o")
    plt.xticks([0, 1, 2, 3]); plt.ylabel("Scenario-conditioned VaR 99.5% (GBP)")
    plt.xlabel("Human checkpoints removed from three-checkpoint design")
    plt.tight_layout(); plt.savefig(figures / "fig4_capital_by_topology.png", dpi=180); plt.close()

    plt.figure(figsize=(9, 5)); sns.lineplot(data=systemic, x="rho", y="var_995_sector", hue="topology", marker="o")
    plt.ylabel("Sector VaR 99.5% (GBP)"); plt.xlabel("Prescribed cross-firm dependence (rho)")
    plt.tight_layout(); plt.savefig(figures / "fig5_systemic_tail.png", dpi=180); plt.close()

    selected = optimisation.loc[optimisation["selected"]].iloc[0]
    worst = fault_runs.loc[fault_runs["paired_final_delta"].abs().idxmax()]
    report = f"""# Agentic actuarial workflow simulation — results

## Decision summary

This prototype executed **{len(runs):,} runs** across **{runs['world_id'].nunique()} synthetic insurer worlds** and **{runs['topology'].nunique()} workflow topologies**. It preserves every stage trajectory and uses paired, same-world no-fault controls to isolate injected-fault effects.

The minimum-objective control package in this scenario is **{selected['topology']}**, with VaR 99.5% of **{_money(selected['var_995'])}**, expected shortfall 99.5% of **{_money(selected['es_995'])}**, and annual control cost **{_money(selected['annual_control_cost'])}**. The largest observed paired reserve movement was **{_money(abs(worst['paired_final_delta']))}** ({worst['fault_type']} injected at {worst['injection_stage']} under {worst['topology']}).

## What is demonstrated

- Reproducible known-truth insurance worlds, including claims development, currencies, duplicates, and policy exposures.
- A six-stage reserving workflow with observable data, model, selection, and narrative states.
- Fault injection, detection, repair, lineage, silent-failure classification, and paired causal measurement.
- Compound-Poisson annual loss aggregation, empirical/GPD severity, VaR and expected shortfall.
- Prescribed Gaussian-copula dependence stress across firms and cost/risk control-package selection.

## Evidential boundary

All financial values are **scenario-conditioned simulation outputs**, not estimates of industry-wide operational loss or required regulatory capital. Open datasets informed mechanisms and benchmark ranges; they do not identify production fault frequencies, human-review effectiveness, firm control placement, or real cross-firm dependence. Those parameters are explicit assumptions and must be replaced or calibrated during a partner-firm validation study.

## ORSA interpretation

The output can support an ORSA-style scenario discussion: identify the agentic workflow, document fault pathways and controls, compare residual tail loss, and stress common-model dependence. It should be reported as an internal model experiment with sensitivity ranges, not as a stand-alone capital number. Model governance should require versioned configurations, replayable trajectories, independent validation, and approval before production use.

## Reproducibility

Resolved configuration: `config_resolved.yaml`. Machine-readable outputs are in `tables/`; full event trajectories are in `trajectories.sqlite`. Figures 1–5 are in `figures/`.
"""
    report_path = output / "REPORT.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path
