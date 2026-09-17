from __future__ import annotations

from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

from .capital import simulate_capital
from .config import SimulationConfig, load_config
from .enums import Topology
from .experiment import run_experiment
from .utils import rng_for


DETECTION_SCALES = [0.6, 0.8, 1.0, 1.2, 1.4]
FREQUENCY_MULTIPLIERS = [0.5, 1.0, 2.0]
LOSS_CONVERSIONS = [0.01, 0.05, 0.10]
REMEDIATION_COSTS = [1_000.0, 5_000.0, 10_000.0]


def _write(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    frame.to_parquet(path.with_suffix(".parquet"), index=False)


def _bootstrap_world_ci(
    runs: pd.DataFrame, column: str, iterations: int = 1_000, seed: int = 20260917,
) -> tuple[float, float]:
    worlds = np.asarray(sorted(runs["world_id"].unique()))
    rng = np.random.default_rng(seed)
    estimates = np.empty(iterations)
    for i in range(iterations):
        sampled = rng.choice(worlds, size=len(worlds), replace=True)
        parts = [runs.loc[runs["world_id"] == world, column] for world in sampled]
        estimates[i] = pd.concat(parts, ignore_index=True).mean()
    return tuple(np.quantile(estimates, [0.025, 0.975]))


def run_parameter_sensitivity(base_config: SimulationConfig, output: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    detection_rows: list[dict[str, object]] = []
    capital_rows: list[dict[str, object]] = []
    for scale in DETECTION_SCALES:
        config = base_config.model_copy(deep=True)
        config.name = f"reviewer-detection-{scale:.1f}"
        config.output_dir = output / "runs" / f"detection_{scale:.1f}"
        config.experiment.detection_scale = scale
        config.capital.annual_simulations = 3_000
        config.capital.systemic_simulations = 2_000
        runs, _ = run_experiment(config)
        fault_runs = runs.loc[runs["fault_type"] != "CONTROL"].copy()
        fault_runs["unresolved_failure"] = fault_runs["paired_final_error"].abs() >= 0.01
        for topology, group in fault_runs.groupby("topology"):
            det_ci = _bootstrap_world_ci(group, "detected")
            unresolved_ci = _bootstrap_world_ci(group, "unresolved_failure", seed=20260918)
            detection_rows.append({
                "detection_scale": scale,
                "topology": topology,
                "fault_runs": len(group),
                "detection_rate": group["detected"].mean(),
                "detection_ci_low": det_ci[0],
                "detection_ci_high": det_ci[1],
                "unresolved_failure_rate": group["unresolved_failure"].mean(),
                "unresolved_ci_low": unresolved_ci[0],
                "unresolved_ci_high": unresolved_ci[1],
            })

        for frequency, conversion, remediation in product(
            FREQUENCY_MULTIPLIERS, LOSS_CONVERSIONS, REMEDIATION_COSTS,
        ):
            scenario = config.model_copy(deep=True)
            scenario.capital.loss_conversion_ratio = conversion
            scenario.capital.remediation_cost = remediation
            scenario.capital.fault_occurrence_probability = {
                fault: min(probability * frequency, 1.0)
                for fault, probability in scenario.capital.fault_occurrence_probability.items()
            }
            capital, annual, _ = simulate_capital(runs, scenario)
            for row in capital.to_dict("records"):
                losses = annual.loc[annual["topology"] == row["topology"], "annual_loss"].to_numpy()
                rng = rng_for(base_config.experiment.seed, scale, frequency, conversion, remediation, row["topology"], "ci")
                boot_vars = np.empty(250)
                for b in range(len(boot_vars)):
                    sample = rng.choice(losses, size=len(losses), replace=True)
                    boot_vars[b] = np.quantile(sample, scenario.capital.var_level)
                capital_rows.append({
                    "detection_scale": scale,
                    "frequency_multiplier": frequency,
                    "loss_conversion_ratio": conversion,
                    "remediation_cost": remediation,
                    "topology": row["topology"],
                    "var_995": row["var_995"],
                    "var_995_ci_low": np.quantile(boot_vars, 0.025),
                    "var_995_ci_high": np.quantile(boot_vars, 0.975),
                    "es_995": row["es_995"],
                })
    detection = pd.DataFrame(detection_rows)
    capital = pd.DataFrame(capital_rows)
    _write(detection, output / "tables" / "detection_sensitivity.csv")
    _write(capital, output / "tables" / "capital_sensitivity.csv")
    ranking = (
        capital.sort_values("var_995")
        .groupby(["detection_scale", "frequency_multiplier", "loss_conversion_ratio", "remediation_cost"], as_index=False)
        .first()["topology"].value_counts(normalize=True).rename_axis("topology").reset_index(name="share_best")
    )
    _write(ranking, output / "tables" / "ranking_stability.csv")
    return detection, capital


def _triangle_estimates(data: pd.DataFrame, cutoff: int = 2007) -> dict[str, float]:
    frame = data.copy()
    observed = frame.loc[frame["DevelopmentYear"] <= cutoff].copy()
    triangle = observed.pivot_table(
        index="AccidentYear", columns="DevelopmentLag", values="CumPaidLoss", aggfunc="sum",
    ).sort_index().sort_index(axis=1)
    all_triangle = frame.pivot_table(
        index="AccidentYear", columns="DevelopmentLag", values="CumPaidLoss", aggfunc="sum",
    ).sort_index().sort_index(axis=1)
    factors: dict[int, float] = {}
    for lag in range(1, 10):
        if lag not in triangle or lag + 1 not in triangle:
            factors[lag] = 1.0
            continue
        mask = triangle[[lag, lag + 1]].notna().all(axis=1) & (triangle[lag] > 0)
        denominator = triangle.loc[mask, lag].sum()
        factor = triangle.loc[mask, lag + 1].sum() / denominator if denominator > 0 else 1.0
        factors[lag] = float(max(factor, 1.0))

    latest = triangle.apply(lambda row: row.dropna().iloc[-1] if row.notna().any() else 0.0, axis=1)
    latest_lag = triangle.apply(lambda row: int(row.dropna().index[-1]) if row.notna().any() else 1, axis=1)
    cdf = latest_lag.map(lambda lag: float(np.prod([factors[j] for j in range(lag, 10)])))
    chain_ladder = float((latest * cdf).sum())

    # Premium is repeated by development lag, so take one value per
    # insurer/accident-year before aggregating the portfolio.
    premiums = (
        frame.groupby(["GRCODE", "AccidentYear"])["EarnedPremNet"].max()
        .groupby("AccidentYear").sum()
        .reindex(triangle.index).fillna(0.0)
    )
    mature_years = [year for year in triangle.index if year + 9 <= cutoff]
    mature_truth = all_triangle.loc[mature_years, 10].sum() if mature_years and 10 in all_triangle else 0.0
    mature_premium = premiums.loc[mature_years].sum() if mature_years else 0.0
    elr = float(mature_truth / mature_premium) if mature_premium > 0 else 0.7
    expected_ultimate = premiums * elr
    bornhuetter_ferguson = float((latest + expected_ultimate * (1.0 - 1.0 / cdf.clip(lower=1.0))).sum())
    truth = float(all_triangle[10].sum())
    return {
        "truth": truth,
        "latest_paid": float(latest.sum()),
        "chain_ladder": chain_ladder,
        "mack_chain_ladder": chain_ladder,
        "bornhuetter_ferguson": bornhuetter_ferguson,
        "mature_elr": elr,
    }


def run_clrd_validation(source: Path, output: Path, bootstraps: int = 100) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = pd.read_csv(source)
    required = {
        "GRCODE", "AccidentYear", "DevelopmentYear", "DevelopmentLag", "CumPaidLoss",
        "EarnedPremNet", "LOB",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"CLRD source missing columns: {sorted(missing)}")
    data = data.drop_duplicates(["GRCODE", "LOB", "AccidentYear", "DevelopmentLag"]).copy()
    data = data.loc[(data["CumPaidLoss"] >= 0) & data["DevelopmentLag"].between(1, 10)]
    rows: list[dict[str, object]] = []
    boot_rows: list[dict[str, object]] = []
    for lob, group in data.groupby("LOB"):
        estimates = _triangle_estimates(group)
        for method in ["latest_paid", "chain_ladder", "mack_chain_ladder", "bornhuetter_ferguson"]:
            estimate = estimates[method]
            rows.append({
                "lob": lob, "method": method, "estimate": estimate, "truth": estimates["truth"],
                "error": estimate - estimates["truth"],
                "absolute_percentage_error": abs(estimate - estimates["truth"]) / max(estimates["truth"], 1e-9),
                "insurers": group["GRCODE"].nunique(), "mature_elr": estimates["mature_elr"],
            })
        insurers = np.asarray(sorted(group["GRCODE"].unique()))
        rng = rng_for(20260917, lob, "clrd_bootstrap")
        for iteration in range(bootstraps):
            selected = rng.choice(insurers, size=len(insurers), replace=True)
            weights = pd.Series(selected).value_counts().rename("bootstrap_weight")
            sampled = group.merge(weights, left_on="GRCODE", right_index=True, how="inner")
            sampled["CumPaidLoss"] *= sampled["bootstrap_weight"]
            sampled["EarnedPremNet"] *= sampled["bootstrap_weight"]
            values = _triangle_estimates(sampled)
            for method in ["chain_ladder", "mack_chain_ladder", "bornhuetter_ferguson"]:
                boot_rows.append({
                    "lob": lob, "iteration": iteration, "method": method,
                    "percentage_error": (values[method] - values["truth"]) / max(values["truth"], 1e-9),
                })
    validation = pd.DataFrame(rows)
    bootstrap = pd.DataFrame(boot_rows)
    intervals = bootstrap.groupby(["lob", "method"])["percentage_error"].quantile([0.025, 0.975]).unstack().reset_index()
    intervals.columns = ["lob", "method", "error_ci_low", "error_ci_high"]
    validation = validation.merge(intervals, on=["lob", "method"], how="left")
    _write(validation, output / "tables" / "clrd_retrospective_validation.csv")
    _write(bootstrap, output / "tables" / "clrd_bootstrap_samples.csv")
    return validation, bootstrap


def run_real_data_fault_audit(source: Path, output: Path) -> pd.DataFrame:
    data = pd.read_csv(source)
    rows: list[dict[str, object]] = []
    fault_types = ["duplicate_key", "negative_paid", "development_mismatch", "missing_cell", "unit_x1000"]
    for lob, lob_data in data.groupby("LOB"):
        largest = (
            lob_data.groupby("GRCODE")["CumPaidLoss"].max().nlargest(25).index
        )
        for insurer in largest:
            base = lob_data.loc[lob_data["GRCODE"] == insurer].copy().sort_values(["AccidentYear", "DevelopmentLag"])
            if base.empty:
                continue
            for fault in fault_types:
                corrupted = base.copy()
                target = corrupted.index[len(corrupted) // 2]
                if fault == "duplicate_key":
                    corrupted = pd.concat([corrupted, corrupted.loc[[target]]], ignore_index=True)
                elif fault == "negative_paid":
                    corrupted.loc[target, "CumPaidLoss"] = -abs(corrupted.loc[target, "CumPaidLoss"]) - 1
                elif fault == "development_mismatch":
                    corrupted.loc[target, "DevelopmentYear"] += 2
                elif fault == "missing_cell":
                    corrupted = corrupted.drop(target)
                elif fault == "unit_x1000":
                    corrupted.loc[target, "CumPaidLoss"] *= 1000

                duplicate = corrupted.duplicated(["GRCODE", "LOB", "AccidentYear", "DevelopmentLag"]).any()
                negative = (corrupted["CumPaidLoss"] < 0).any()
                mismatch = ((corrupted["DevelopmentYear"] - corrupted["AccidentYear"] + 1) != corrupted["DevelopmentLag"]).any()
                counts = corrupted.groupby("AccidentYear")["DevelopmentLag"].nunique()
                missing = (counts < 10).any()
                diffs = corrupted.sort_values(["AccidentYear", "DevelopmentLag"]).groupby("AccidentYear")["CumPaidLoss"].diff()
                positive = diffs.loc[diffs > 0]
                extreme = bool(len(positive) and positive.max() > max(positive.median() * 100, 1_000_000))
                detected = bool(duplicate or negative or mismatch or missing or extreme)
                rows.append({
                    "lob": lob, "grcode": insurer, "fault": fault, "detected": detected,
                    "duplicate_check": bool(duplicate), "nonnegative_check": bool(negative),
                    "development_check": bool(mismatch), "completeness_check": bool(missing),
                    "extreme_increment_check": bool(extreme),
                })
    audit = pd.DataFrame(rows)
    _write(audit, output / "tables" / "clrd_fault_audit.csv")
    return audit


def run_ablation(base_config: SimulationConfig, output: Path) -> pd.DataFrame:
    scenarios = [
        ("validator_baseline", Topology.VALIDATOR, set(), True),
        ("without_schema_lineage", Topology.VALIDATOR, {"schema_and_lineage_check"}, True),
        ("without_prompt_sanitizer", Topology.VALIDATOR, {"prompt_sanitizer_and_policy_check"}, True),
        ("without_stage_validator", Topology.VALIDATOR, {"typed_stage_validator"}, True),
        ("without_replay_recovery", Topology.VALIDATOR, set(), False),
        ("supervisor_baseline", Topology.SUPERVISOR, set(), True),
        ("without_supervisor_review", Topology.SUPERVISOR, {"supervisor_review"}, True),
        ("human3_baseline", Topology.HUMAN_3, set(), True),
        ("without_human_checkpoints", Topology.HUMAN_3, {"human_checkpoint"}, True),
    ]
    rows: list[dict[str, object]] = []
    for name, topology, disabled, replay in scenarios:
        config = base_config.model_copy(deep=True)
        config.name = f"reviewer-ablation-{name}"
        config.output_dir = output / "ablations" / name
        config.experiment.topologies = [topology]
        config.experiment.disabled_controls = disabled
        config.experiment.replay_enabled = replay
        runs, _ = run_experiment(config)
        faults = runs.loc[runs["fault_type"] != "CONTROL"].copy()
        unresolved = faults["paired_final_error"].abs() >= 0.01
        rows.append({
            "scenario": name, "topology": str(topology), "fault_runs": len(faults),
            "detection_rate": faults["detected"].mean(),
            "silent_failure_rate": faults["silent_failure"].mean(),
            "unresolved_failure_rate": unresolved.mean(),
            "median_absolute_paired_error": faults["paired_final_error"].abs().median(),
            "p95_absolute_paired_error": faults["paired_final_error"].abs().quantile(0.95),
        })
    frame = pd.DataFrame(rows)
    _write(frame, output / "tables" / "control_ablation.csv")
    return frame


def build_reviewer_revision(config_path: str | Path = "configs/scaled.yaml") -> Path:
    config = load_config(config_path)
    root = Path(config_path).resolve().parent.parent
    output = root / "outputs" / "reviewer_revision"
    source = root / "data" / "raw" / "core_archives" / "AAT_01_reserving_core" / "01_reserving" / "chainladder_samples" / "clrd2025.csv"
    validation, bootstrap = run_clrd_validation(source, output)
    audit = run_real_data_fault_audit(source, output)
    detection, capital = run_parameter_sensitivity(config, output)
    ablation = run_ablation(config, output)
    ranking = pd.read_csv(output / "tables" / "ranking_stability.csv")
    summary = f"""# Reviewer revision analyses

## Public actuarial validation

The CAS CLRD2025 retrospective test uses {validation['lob'].nunique()} lines of business and {int(validation.groupby('lob')['insurers'].first().sum())} insurer-line records. Development through calendar year 2007 is treated as observed; development through lag 10 is retrospective ground truth. Chain Ladder, Mack Chain Ladder point estimates, Bornhuetter-Ferguson and latest-paid baselines are compared. Insurer-cluster bootstrap intervals use {int(bootstrap['iteration'].nunique())} resamples per line.

## Public-data fault audit

The deterministic schema, sign, development-consistency, completeness and extreme-increment checks detected {audit['detected'].mean():.1%} of {len(audit):,} injected CLRD faults across six lines of business.

## Sensitivity and uncertainty

Detection effectiveness is rerun at 60%, 80%, 100%, 120% and 140% of base probabilities. Capital is stressed over {len(DETECTION_SCALES)} detection levels, {len(FREQUENCY_MULTIPLIERS)} frequency multipliers, {len(LOSS_CONVERSIONS)} loss-conversion ratios and {len(REMEDIATION_COSTS)} remediation costs, producing {len(capital):,} topology-scenario estimates with Monte Carlo bootstrap intervals. The control topology with the lowest VaR is reported by scenario rather than assumed from the base case.

## Ablation

Nine controlled runs remove schema/lineage validation, prompt sanitisation, stage validation, replay/recovery, supervisor review or human checkpoints one at a time. The main outcome is unresolved paired error, so detection without repair is not misclassified as risk removal.

## Ranking stability

{ranking.to_string(index=False)}

## Evidential boundary

The CLRD experiment validates the reserving and audit mechanics on public insurer data. It does not convert benchmark errors into production agent-fault frequencies. The study remains an agentic-workflow risk simulation, not an empirical measurement of deployed language-model agents.
"""
    path = output / "REPORT.md"
    path.write_text(summary, encoding="utf-8")
    return path


if __name__ == "__main__":
    print(build_reviewer_revision())
