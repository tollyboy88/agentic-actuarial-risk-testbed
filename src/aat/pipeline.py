from __future__ import annotations

from copy import deepcopy
import traceback
import uuid

from .config import SimulationConfig
from .controls import inspect_fault, stage_control_cost
from .enums import FaultType, STAGE_ORDER, Stage, Topology
from .faults import inject_fault
from .models import PipelineState, RunResult, RunSpec, WorldData
from .stages import STAGE_FUNCTIONS
from .utils import rng_for, stable_seed


def _run_id(spec: RunSpec, experiment_seed: int) -> str:
    key = f"{experiment_seed}|{spec.world_id}|{spec.topology}|{spec.fault_type}|{spec.injection_stage}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, key))


def run_pipeline(world: WorldData, spec: RunSpec, config: SimulationConfig) -> RunResult:
    state = PipelineState(world=deepcopy(world))
    pre_fault_state: PipelineState | None = None
    for stage in STAGE_ORDER:
        base_tokens, base_minutes = stage_control_cost(spec.topology, stage, config.costs)
        state.token_cost += base_tokens
        state.analyst_minutes += base_minutes
        state.events.append({
            "stage": stage, "event_type": "stage_started", "topology": spec.topology,
            "control_tokens": base_tokens, "control_minutes": base_minutes,
        })

        if config.experiment.background_error_rate > 0:
            background_rng = rng_for(config.experiment.seed, world.world_id, spec.topology, stage, "background")
            if background_rng.random() < config.experiment.background_error_rate:
                state.fault_payload["selection_bias"] = 1.02
                state.events.append({"stage": stage, "event_type": "background_agent_error", "bias": 1.02})

        if spec.fault_type is not None and spec.injection_stage is stage:
            pre_fault_state = deepcopy(state)
            inject_fault(
                state, spec.fault_type, stage, config.experiment.fault_magnitude,
                config.experiment.seed,
            )

        # Controls may detect a fault at injection or at a later checkpoint. A
        # detected fault is repaired by replaying from the last clean state.
        if state.active_fault is not None and not state.detected:
            outcome = inspect_fault(
                state, spec.topology, stage, state.active_fault,
                config.experiment.seed, config.costs,
            )
            # Inspection cost is already included in the topology's routine stage cost.
            state.events.append({
                "stage": stage, "event_type": "control_inspection", "control": outcome.control,
                "probability": outcome.probability, "detected": outcome.detected,
            })
            if outcome.detected:
                prior_events = list(state.events)
                prior_tokens, prior_minutes = state.token_cost, state.analyst_minutes
                if pre_fault_state is None:
                    raise RuntimeError("fault recovery state is unavailable")
                state = deepcopy(pre_fault_state)
                state.events = prior_events
                state.token_cost = prior_tokens
                state.analyst_minutes = prior_minutes
                state.detected = True
                state.detection_stage = stage
                injection_index = STAGE_ORDER.index(spec.injection_stage) if spec.injection_stage else 0
                current_index = STAGE_ORDER.index(stage)
                for replay_stage in STAGE_ORDER[injection_index:current_index]:
                    STAGE_FUNCTIONS[replay_stage](state, config.world)
                    state.events.append({
                        "stage": replay_stage, "event_type": "stage_replayed_after_detection",
                    })
                state.events.append({
                    "stage": stage, "event_type": "fault_repaired",
                    "repair": "restore_and_replay_from_clean_state",
                })

        try:
            STAGE_FUNCTIONS[stage](state, config.world)
            state.events.append({"stage": stage, "event_type": "stage_completed"})
        except Exception as exc:
            state.hard_failure = True
            state.events.append({
                "stage": stage, "event_type": "stage_exception", "error_type": type(exc).__name__,
                "message": str(exc), "traceback": traceback.format_exc(limit=4),
            })
            break

    if state.report is not None:
        final_ultimate = float(state.report["ultimate_gbp"])
    elif state.snapshots:
        final_ultimate = float(state.snapshots[-1].estimate)
    else:
        final_ultimate = 0.0
    true_ultimate = max(float(world.true_ultimate), 1e-9)
    error = (final_ultimate - true_ultimate) / true_ultimate
    lineage = state.snapshots[-1].lineage_completeness if state.snapshots else 0.0
    silent = bool(not state.detected and not state.hard_failure and abs(error) >= 0.01)
    return RunResult(
        run_id=_run_id(spec, config.experiment.seed), world_id=world.world_id,
        topology=spec.topology, fault_type=spec.fault_type, injection_stage=spec.injection_stage,
        true_ultimate=true_ultimate, final_ultimate=final_ultimate, reserve_error=error,
        absolute_misstatement=abs(final_ultimate - true_ultimate), detected=state.detected,
        detection_stage=state.detection_stage, hard_failure=state.hard_failure,
        silent_failure=silent, token_cost=state.token_cost, analyst_minutes=state.analyst_minutes,
        lineage_completeness=lineage, snapshots=state.snapshots, events=state.events,
    )
