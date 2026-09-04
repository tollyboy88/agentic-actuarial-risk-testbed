from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

import pandas as pd

from .enums import FaultType, Stage, Topology


@dataclass
class WorldData:
    world_id: int
    seed: int
    valuation_date: pd.Timestamp
    raw_transactions: pd.DataFrame
    policies: pd.DataFrame
    truth_claims: pd.DataFrame
    true_ultimate: float
    fx_rates: dict[str, float]
    stale_fx_rates: dict[str, float]


@dataclass
class StageSnapshot:
    stage: Stage
    estimate: float
    metric_vector: dict[str, float]
    row_count: int
    data_hash: str
    lineage_completeness: float
    hard_failure: bool = False
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineState:
    world: WorldData
    transactions: pd.DataFrame | None = None
    segmented: pd.DataFrame | None = None
    triangle: pd.DataFrame | None = None
    model_estimates: pd.DataFrame | None = None
    selected_estimates: pd.DataFrame | None = None
    report: dict[str, Any] | None = None
    snapshots: list[StageSnapshot] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    active_fault: FaultType | None = None
    fault_payload: dict[str, Any] = field(default_factory=dict)
    detected: bool = False
    detection_stage: Stage | None = None
    token_cost: int = 0
    analyst_minutes: float = 0.0
    hard_failure: bool = False


@dataclass(frozen=True)
class RunSpec:
    world_id: int
    topology: Topology
    fault_type: FaultType | None = None
    injection_stage: Stage | None = None


@dataclass
class RunResult:
    run_id: str
    world_id: int
    topology: Topology
    fault_type: FaultType | None
    injection_stage: Stage | None
    true_ultimate: float
    final_ultimate: float
    reserve_error: float
    absolute_misstatement: float
    detected: bool
    detection_stage: Stage | None
    hard_failure: bool
    silent_failure: bool
    token_cost: int
    analyst_minutes: float
    lineage_completeness: float
    snapshots: list[StageSnapshot]
    events: list[dict[str, Any]]

