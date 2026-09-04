from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    return json.loads(frame.replace({np.nan: None}).to_json(orient="records"))


def build_dashboard_payload(project_root: Path, profile: str = "scaled") -> dict[str, object]:
    output = project_root / "outputs" / profile
    runs = pd.read_parquet(output / "runs.parquet")
    stages = pd.read_parquet(output / "stage_metrics.parquet")
    capital = pd.read_parquet(output / "tables" / "capital.parquet")
    systemic = pd.read_parquet(output / "tables" / "systemic_stress.parquet")
    optimisation = pd.read_parquet(output / "tables" / "control_optimisation.parquet")
    faults = runs.loc[runs["fault_type"] != "CONTROL"].copy()

    topology = faults.groupby("topology", as_index=False).agg(
        runs=("run_id", "size"), detection_rate=("detected", "mean"),
        silent_failure_rate=("silent_failure", "mean"), hard_failures=("hard_failure", "sum"),
        median_abs_delta=("paired_final_delta", lambda x: float(np.median(np.abs(x)))),
        p95_abs_delta=("paired_final_delta", lambda x: float(np.quantile(np.abs(x), .95))),
    ).merge(capital[["topology", "var_995", "es_995", "annual_control_cost"]], on="topology")
    fault_summary = faults.groupby("fault_type", as_index=False).agg(
        runs=("run_id", "size"), detection_rate=("detected", "mean"),
        silent_failure_rate=("silent_failure", "mean"),
        median_abs_delta=("paired_final_delta", lambda x: float(np.median(np.abs(x)))),
        p95_abs_delta=("paired_final_delta", lambda x: float(np.quantile(np.abs(x), .95))),
    )
    heatmap = faults.groupby(["fault_type", "injection_stage"], as_index=False).agg(
        detection_rate=("detected", "mean"), runs=("run_id", "size"),
    )
    propagation = stages.loc[stages["fault_type"] != "CONTROL"].groupby(
        ["topology", "stage", "stage_order"], as_index=False,
    ).agg(
        median_abs_relative_delta=("paired_relative_delta", lambda x: float(np.nanmedian(np.abs(x)))),
        p95_abs_relative_delta=("paired_relative_delta", lambda x: float(np.nanquantile(np.abs(x), .95))),
    )
    selected = optimisation.loc[optimisation["selected"]].iloc[0]
    return {
        "meta": {
            "profile": profile, "runs": int(len(runs)), "fault_runs": int(len(faults)),
            "worlds": int(runs["world_id"].nunique()), "snapshots": int(len(stages)),
            "hard_failures": int(runs["hard_failure"].sum()), "seed": 20260901,
            "selected_topology": selected["topology"], "selected_var_995": selected["var_995"],
            "selected_es_995": selected["es_995"],
        },
        "topologies": _records(topology), "faults": _records(fault_summary),
        "detection_heatmap": _records(heatmap), "propagation": _records(propagation),
        "capital": _records(capital), "systemic": _records(systemic),
        "optimisation": _records(optimisation),
        "recent_runs": _records(faults.sort_values("absolute_misstatement", ascending=False).head(100)[[
            "run_id", "world_id", "topology", "fault_type", "injection_stage", "detected",
            "detection_stage", "silent_failure", "paired_final_delta", "absolute_misstatement",
            "lineage_completeness",
        ]]),
    }


def export_dashboard_payload(project_root: Path, profile: str = "scaled") -> Path:
    destination = project_root / "dashboard" / "public" / "data" / f"{profile}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_dashboard_payload(project_root, profile), separators=(",", ":")),
        encoding="utf-8",
    )
    return destination
