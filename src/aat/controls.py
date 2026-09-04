from __future__ import annotations

from dataclasses import dataclass

from .config import CostConfig
from .enums import FaultType, Stage, Topology
from .models import PipelineState
from .utils import rng_for


HUMAN_CHECKPOINTS = {
    Topology.HUMAN_0: set(),
    Topology.HUMAN_1: {Stage.SELECT},
    Topology.HUMAN_2: {Stage.RECONCILE, Stage.SELECT},
    Topology.HUMAN_3: {Stage.RECONCILE, Stage.MODEL, Stage.SELECT},
}


@dataclass(frozen=True)
class DetectionOutcome:
    detected: bool
    probability: float
    control: str
    token_cost: int
    analyst_minutes: float


def stage_control_cost(topology: Topology, stage: Stage, costs: CostConfig) -> tuple[int, float]:
    if topology is Topology.VALIDATOR:
        return costs.validator_tokens, 0.0
    if topology is Topology.SUPERVISOR:
        return costs.supervisor_tokens, 0.0
    if topology is Topology.CRITIC and stage in {Stage.MODEL, Stage.SELECT}:
        return costs.critic_tokens, 0.0
    if stage in HUMAN_CHECKPOINTS.get(topology, set()):
        return 0, costs.human_checkpoint_minutes
    return 0, 0.0


def detection_probability(topology: Topology, stage: Stage, fault: FaultType) -> tuple[float, str]:
    if topology is Topology.LINEAR or topology is Topology.HUMAN_0:
        probability, control = 0.025, "implicit_runtime_check"
    elif topology is Topology.VALIDATOR:
        probability, control = 0.72, "typed_stage_validator"
    elif topology is Topology.SUPERVISOR:
        probability, control = 0.84, "supervisor_review"
    elif topology is Topology.CRITIC:
        probability = 0.86 if stage in {Stage.MODEL, Stage.SELECT} else 0.16
        control = "critic_debate" if stage in {Stage.MODEL, Stage.SELECT} else "implicit_runtime_check"
    elif stage in HUMAN_CHECKPOINTS.get(topology, set()):
        probability, control = 0.96, "human_checkpoint"
    else:
        probability, control = 0.04, "implicit_runtime_check"

    modifiers = {
        FaultType.DATA: 1.08,
        FaultType.SEMANTIC: 0.88,
        FaultType.TOOL: 1.00,
        FaultType.REASONING: 0.78,
        FaultType.HANDOFF: 1.15,
        FaultType.CONTEXT: 0.72,
        FaultType.ADVERSARIAL: 0.62,
    }
    probability *= modifiers[fault]
    if fault is FaultType.ADVERSARIAL and topology in {Topology.VALIDATOR, Topology.SUPERVISOR}:
        probability = max(probability, 0.82)
        control = "prompt_sanitizer_and_policy_check"
    if fault is FaultType.HANDOFF and topology in {Topology.VALIDATOR, Topology.SUPERVISOR}:
        probability = max(probability, 0.93)
        control = "schema_and_lineage_check"
    return min(max(probability, 0.0), 0.995), control


def inspect_fault(
    state: PipelineState,
    topology: Topology,
    stage: Stage,
    fault: FaultType,
    experiment_seed: int,
    costs: CostConfig,
) -> DetectionOutcome:
    probability, control = detection_probability(topology, stage, fault)
    token_cost, analyst_minutes = stage_control_cost(topology, stage, costs)
    rng = rng_for(experiment_seed, state.world.world_id, topology, stage, fault, "detection")
    detected = bool(rng.random() < probability)
    return DetectionOutcome(detected, probability, control, token_cost, analyst_minutes)

