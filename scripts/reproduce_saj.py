from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from aat.probabilistic.dataset import build_transition_observations
from aat.probabilistic.diagnostics import held_out_scores
from aat.probabilistic.optimise import enumerate_stage_controls
from aat.probabilistic.propagation_model import fit_markov_additive
from aat.probabilistic.recursion import terminal_distribution
from aat.probabilistic.simulation_study import run_recovery_study
from aat.probabilistic.transition_model import HierarchicalDirichletTransitionModel, STATES


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "saj_methodology"


def write(frame: pd.DataFrame, name: str) -> None:
    target = OUTPUT / "tables" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target.with_suffix(".csv"), index=False)
    frame.to_parquet(target.with_suffix(".parquet"), index=False)


def main() -> None:
    figures = OUTPUT / "figures"; figures.mkdir(parents=True, exist_ok=True)
    observations = build_transition_observations(
        ROOT / "outputs/scaled/runs.parquet", ROOT / "outputs/scaled/stage_metrics.parquet",
        OUTPUT / "transition_observations.parquet",
    )
    model = HierarchicalDirichletTransitionModel().fit(observations)
    transitions = model.summary(); write(transitions, "transition_posterior")
    propagation = fit_markov_additive(observations); write(propagation, "propagation_posterior")
    scores = held_out_scores(observations, [6, 7]); write(scores, "held_out_model_comparison")
    recovery = run_recovery_study(); write(recovery, "parameter_recovery")
    recovery_summary = recovery.groupby("topology", as_index=False).agg(
        bias=("estimate", lambda x: float((x - recovery.loc[x.index, "truth"]).mean())),
        rmse=("estimate", lambda x: float(np.sqrt(np.square(x - recovery.loc[x.index, "truth"]).mean()))),
        coverage_90=("covered_90", "mean"), coverage_95=("covered_95", "mean"),
    ); write(recovery_summary, "parameter_recovery_summary")
    optimisation = enumerate_stage_controls(observations); write(optimisation, "control_optimisation")

    matrices = []
    for stage in sorted(observations["stage"].unique(), key=lambda x: int(x[1])):
        matrix = np.eye(4); matrix[1] = model.mean(stage, "F1_DATA", "T2_VALIDATOR", "E")
        matrices.append(matrix)
    initial = np.array([0.0, 1.0, 0.0, 0.0]); analytic = terminal_distribution(initial, matrices)
    rng = np.random.default_rng(20260923); states = np.ones(200_000, dtype=int)
    for matrix in matrices:
        mask = states == 1
        states[mask] = rng.choice(4, size=mask.sum(), p=matrix[1])
    monte = np.bincount(states, minlength=4) / len(states)
    recursion = pd.DataFrame({"state": STATES, "analytic": analytic, "monte_carlo": monte, "absolute_difference": np.abs(analytic-monte)})
    write(recursion, "recursion_validation")

    plt.figure(figsize=(9, 4.8))
    means = transitions.loc[(transitions.state_before == "E") & (transitions.state_after == "R")].groupby("topology").agg(mean=("posterior_mean","mean"),lo=("ci_05","mean"),hi=("ci_95","mean")).sort_values("mean")
    plt.errorbar(means.index, means["mean"], yerr=[means["mean"]-means["lo"], means["hi"]-means["mean"]], fmt="o", capsize=3)
    plt.xticks(rotation=30, ha="right"); plt.ylabel("Posterior recovery probability"); plt.tight_layout(); plt.savefig(figures/"figure2_transition_intervals.png", dpi=300); plt.close()

    plt.figure(figsize=(6.5, 4.5)); rs = recovery_summary.set_index("topology")
    plt.bar(rs.index, rs.coverage_90); plt.axhline(.9, color="black", ls="--"); plt.ylim(0,1); plt.ylabel("Empirical coverage of 90% interval"); plt.tight_layout(); plt.savefig(figures/"figure3_parameter_recovery.png", dpi=300); plt.close()

    plt.figure(figsize=(7, 4.5)); pareto = optimisation.loc[optimisation.pareto]
    plt.scatter(optimisation.annual_cost, optimisation.tail_risk_index, alpha=.25)
    plt.plot(pareto.annual_cost, pareto.tail_risk_index, marker="o"); plt.yscale("log"); plt.xlabel("Annual control cost index"); plt.ylabel("Posterior tail-risk index (log scale)"); plt.tight_layout(); plt.savefig(figures/"figure5_pareto_frontier.png", dpi=300); plt.close()

    selected = optimisation.loc[optimisation.selected].iloc[0]
    report = {
        "observations": len(observations), "worlds": int(observations.world_id.nunique()),
        "hierarchical_log_score": float(scores.loc[scores.model=="hierarchical","log_score"].iloc[0]),
        "global_log_score": float(scores.loc[scores.model=="global","log_score"].iloc[0]),
        "mean_90_coverage": float(recovery_summary.coverage_90.mean()),
        "mean_95_coverage": float(recovery_summary.coverage_95.mean()),
        "max_recursion_difference": float(recursion.absolute_difference.max()),
        "selected_placement": selected.placement, "selected_cost": float(selected.annual_cost),
        "selected_silent_probability": float(selected.posterior_mean_silent_probability),
    }
    (OUTPUT/"RESULTS.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    manifest = {}
    for path in sorted(OUTPUT.rglob("*")):
        if path.is_file(): manifest[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (OUTPUT/"run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
