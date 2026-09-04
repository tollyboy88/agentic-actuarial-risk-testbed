from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import yaml

from .config import SimulationConfig
from .enums import FaultType, STAGE_ORDER, Stage, Topology
from .ground_truth import generate_world
from .models import RunResult, RunSpec, StageSnapshot
from .pipeline import run_pipeline
from .storage import TrajectoryStore
from .utils import jsonable, stable_seed


def experiment_cells(config: SimulationConfig) -> list[tuple[FaultType, Stage]]:
    cells = [(fault, stage) for fault in config.experiment.fault_types for stage in config.experiment.stages]
    if config.experiment.design != "screening":
        return cells
    selected = [
        cell for cell in cells
        if stable_seed(config.experiment.seed, cell[0], cell[1], "screening") % 3 == 0
    ]
    # Guarantee that every factor level appears at least once.
    for fault in config.experiment.fault_types:
        if not any(cell[0] == fault for cell in selected):
            selected.append((fault, config.experiment.stages[stable_seed(fault) % len(config.experiment.stages)]))
    for stage in config.experiment.stages:
        if not any(cell[1] == stage for cell in selected):
            selected.append((config.experiment.fault_types[stable_seed(stage) % len(config.experiment.fault_types)], stage))
    return sorted(set(selected), key=lambda cell: (cell[0].value, cell[1].value))


def _run_world(world_id: int, config_payload: dict[str, object]) -> tuple[list[RunResult], dict[str, object]]:
    config = SimulationConfig.model_validate(config_payload)
    world = generate_world(world_id, config.experiment.seed, config.world)
    results: list[RunResult] = []
    for topology in config.experiment.topologies:
        results.append(run_pipeline(world, RunSpec(world_id, topology), config))
        for fault_type, injection_stage in experiment_cells(config):
            results.append(run_pipeline(
                world, RunSpec(world_id, topology, fault_type, injection_stage), config,
            ))
    summary = {
        "world_id": world_id, "seed": world.seed, "true_ultimate": world.true_ultimate,
        "raw_transactions": len(world.raw_transactions), "claims": len(world.truth_claims),
        "policy_years": len(world.policies),
    }
    return results, summary


def _stage_map(result: RunResult) -> dict[Stage, StageSnapshot]:
    return {snapshot.stage: snapshot for snapshot in result.snapshots}


def _snapshot_distance(treatment: StageSnapshot, control: StageSnapshot) -> float:
    keys = set(treatment.metric_vector) | set(control.metric_vector)
    vector_distance = sum(
        abs(treatment.metric_vector.get(key, 0.0) - control.metric_vector.get(key, 0.0))
        for key in keys
    )
    return max(abs(treatment.estimate - control.estimate), vector_distance)


def _result_row(result: RunResult) -> dict[str, object]:
    return {
        "run_id": result.run_id, "world_id": result.world_id, "topology": str(result.topology),
        "fault_type": "CONTROL" if result.fault_type is None else str(result.fault_type),
        "injection_stage": "CONTROL" if result.injection_stage is None else str(result.injection_stage),
        "true_ultimate": result.true_ultimate, "final_ultimate": result.final_ultimate,
        "reserve_error": result.reserve_error, "absolute_misstatement": result.absolute_misstatement,
        "detected": result.detected, "detection_stage": None if result.detection_stage is None else str(result.detection_stage),
        "hard_failure": result.hard_failure, "silent_failure": result.silent_failure,
        "token_cost": result.token_cost, "analyst_minutes": result.analyst_minutes,
        "lineage_completeness": result.lineage_completeness,
    }


def _paired_metrics(results: list[RunResult]) -> tuple[pd.DataFrame, pd.DataFrame]:
    baselines = {
        (result.world_id, result.topology): result
        for result in results if result.fault_type is None
    }
    run_rows: list[dict[str, object]] = []
    stage_rows: list[dict[str, object]] = []
    for result in results:
        row = _result_row(result)
        baseline = baselines[(result.world_id, result.topology)]
        treatment_stages = _stage_map(result)
        baseline_stages = _stage_map(baseline)
        injection_delta = 0.0
        if result.injection_stage is not None:
            treatment = treatment_stages.get(result.injection_stage)
            control = baseline_stages.get(result.injection_stage)
            if treatment is not None and control is not None:
                injection_delta = _snapshot_distance(treatment, control)
        minimum_signal = result.true_ultimate * 1e-9
        injection_observed = abs(injection_delta) > minimum_signal
        denominator = abs(injection_delta) if injection_observed else np.nan
        final_delta = result.final_ultimate - baseline.final_ultimate
        row["paired_final_delta"] = final_delta
        row["paired_final_error"] = final_delta / max(result.true_ultimate, 1e-9)
        row["injection_signal_observed"] = True if result.fault_type is None else injection_observed
        row["amplification_final"] = (
            0.0 if result.fault_type is None else abs(final_delta) / denominator
        )
        row["baseline_final_ultimate"] = baseline.final_ultimate
        run_rows.append(row)

        for order, stage in enumerate(STAGE_ORDER, start=1):
            treatment = treatment_stages.get(stage)
            control = baseline_stages.get(stage)
            if treatment is None or control is None:
                continue
            delta = treatment.estimate - control.estimate
            stage_rows.append({
                "run_id": result.run_id, "world_id": result.world_id, "topology": str(result.topology),
                "fault_type": "CONTROL" if result.fault_type is None else str(result.fault_type),
                "injection_stage": "CONTROL" if result.injection_stage is None else str(result.injection_stage),
                "stage": str(stage), "stage_order": order, "treatment_estimate": treatment.estimate,
                "baseline_estimate": control.estimate, "paired_delta": delta,
                "paired_relative_delta": delta / max(result.true_ultimate, 1e-9),
                "amplification_from_injection": (
                    0.0 if result.fault_type is None else abs(delta) / denominator
                ),
                "data_hash": treatment.data_hash, "row_count": treatment.row_count,
                "lineage_completeness": treatment.lineage_completeness,
            })
    return pd.DataFrame(run_rows), pd.DataFrame(stage_rows)


def run_experiment(config: SimulationConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    output = config.output_dir
    output.mkdir(parents=True, exist_ok=True)
    payload = config.model_dump(mode="json")
    all_results: list[RunResult] = []
    world_summaries: list[dict[str, object]] = []

    if config.experiment.workers > 1 and config.experiment.n_worlds > 1:
        with ProcessPoolExecutor(max_workers=config.experiment.workers) as pool:
            futures = {
                pool.submit(_run_world, world_id, payload): world_id
                for world_id in range(config.experiment.n_worlds)
            }
            for future in as_completed(futures):
                results, summary = future.result()
                all_results.extend(results)
                world_summaries.append(summary)
    else:
        for world_id in range(config.experiment.n_worlds):
            results, summary = _run_world(world_id, payload)
            all_results.extend(results)
            world_summaries.append(summary)

    with TrajectoryStore(output / "trajectories.sqlite") as store:
        for result in all_results:
            store.add(result)
        store.commit()

    runs, stages = _paired_metrics(all_results)
    runs.sort_values(["world_id", "topology", "fault_type", "injection_stage"]).to_parquet(
        output / "runs.parquet", index=False,
    )
    stages.sort_values(["world_id", "topology", "fault_type", "injection_stage", "stage_order"]).to_parquet(
        output / "stage_metrics.parquet", index=False,
    )
    pd.DataFrame(world_summaries).sort_values("world_id").to_parquet(output / "worlds.parquet", index=False)
    (output / "config_resolved.yaml").write_text(
        yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False), encoding="utf-8",
    )
    return runs, stages
