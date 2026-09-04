from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator

from .enums import FaultType, Stage, Topology


class WorldConfig(BaseModel):
    n_policies: int = Field(300, ge=30)
    accident_years: int = Field(6, ge=4, le=12)
    development_years: int = Field(6, ge=4, le=12)
    start_year: int = 2019
    valuation_year: int = 2025
    ambient_duplicate_rate: float = Field(0.005, ge=0, le=0.1)
    ambient_currency_rate: float = Field(0.15, ge=0, le=1)
    base_currency: str = "GBP"


class ExperimentConfig(BaseModel):
    seed: int = 20260901
    n_worlds: int = Field(4, ge=1)
    workers: int = Field(1, ge=1)
    design: Literal["smoke", "screening", "full"] = "smoke"
    topologies: list[Topology] = Field(default_factory=lambda: [
        Topology.LINEAR, Topology.VALIDATOR, Topology.SUPERVISOR,
        Topology.CRITIC, Topology.HUMAN_1,
    ])
    stages: list[Stage] = Field(default_factory=lambda: list(Stage))
    fault_types: list[FaultType] = Field(default_factory=lambda: list(FaultType))
    fault_magnitude: float = Field(0.15, gt=0, le=5)
    background_error_rate: float = Field(0.0, ge=0, le=0.25)
    persist_stage_artifacts: bool = False


class CapitalConfig(BaseModel):
    annual_workflows: int = Field(120, ge=1)
    annual_simulations: int = Field(20_000, ge=2_000)
    loss_conversion_ratio: float = Field(0.05, ge=0, le=1)
    remediation_cost: float = Field(5_000.0, ge=0)
    tail_threshold_quantile: float = Field(0.90, ge=0.7, lt=0.99)
    var_level: float = Field(0.995, gt=0.9, lt=1)
    fault_occurrence_probability: dict[FaultType, float] = Field(default_factory=lambda: {
        FaultType.DATA: 0.015,
        FaultType.SEMANTIC: 0.012,
        FaultType.TOOL: 0.010,
        FaultType.REASONING: 0.018,
        FaultType.HANDOFF: 0.010,
        FaultType.CONTEXT: 0.008,
        FaultType.ADVERSARIAL: 0.003,
    })
    systemic_firms: int = Field(20, ge=2)
    systemic_rhos: list[float] = Field(default_factory=lambda: [0.0, 0.3, 0.6, 0.9])
    systemic_simulations: int = Field(10_000, ge=2_000)

    @model_validator(mode="after")
    def validate_rhos(self) -> "CapitalConfig":
        if any(rho < 0 or rho >= 1 for rho in self.systemic_rhos):
            raise ValueError("systemic_rhos must lie in [0, 1)")
        return self


class CostConfig(BaseModel):
    token_price_per_million: float = Field(2.0, ge=0)
    analyst_hourly_cost: float = Field(85.0, ge=0)
    validator_tokens: int = Field(450, ge=0)
    supervisor_tokens: int = Field(800, ge=0)
    critic_tokens: int = Field(1100, ge=0)
    human_checkpoint_minutes: float = Field(8.0, ge=0)


class SimulationConfig(BaseModel):
    name: str = "aat-smoke"
    output_dir: Path = Path("outputs/smoke")
    world: WorldConfig = Field(default_factory=WorldConfig)
    experiment: ExperimentConfig = Field(default_factory=ExperimentConfig)
    capital: CapitalConfig = Field(default_factory=CapitalConfig)
    costs: CostConfig = Field(default_factory=CostConfig)


def load_config(path: str | Path) -> SimulationConfig:
    source = Path(path)
    payload = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    config = SimulationConfig.model_validate(payload)
    if not config.output_dir.is_absolute():
        config.output_dir = (source.resolve().parent.parent / config.output_dir).resolve()
    return config

