from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import genpareto

from .config import SimulationConfig
from .enums import FaultType
from .utils import rng_for


@dataclass
class SeverityModel:
    observations: np.ndarray
    threshold: float
    tail_probability: float
    shape: float | None
    scale: float | None

    def sample(self, size: int, rng: np.random.Generator) -> np.ndarray:
        if size <= 0:
            return np.empty(0)
        values = rng.choice(self.observations, size=size, replace=True)
        if self.shape is None or self.scale is None or self.tail_probability <= 0:
            return values
        tail_mask = rng.random(size) < self.tail_probability
        if tail_mask.any():
            excess = genpareto.rvs(
                self.shape, loc=0.0, scale=self.scale, size=int(tail_mask.sum()), random_state=rng,
            )
            values[tail_mask] = self.threshold + np.maximum(excess, 0.0)
        return values


def fit_severity(values: np.ndarray, threshold_quantile: float) -> SeverityModel:
    observations = np.asarray(values, dtype=float)
    observations = observations[np.isfinite(observations) & (observations >= 0)]
    if not len(observations):
        observations = np.array([0.0])
    threshold = float(np.quantile(observations, threshold_quantile))
    excess = observations[observations > threshold] - threshold
    if len(excess) >= 20 and np.any(excess > 0):
        shape, _, scale = genpareto.fit(excess, floc=0.0)
        shape = float(np.clip(shape, -0.45, 0.95))
        scale = float(max(scale, 1e-9))
        return SeverityModel(observations, threshold, len(excess) / len(observations), shape, scale)
    return SeverityModel(observations, threshold, len(excess) / len(observations), None, None)


def _control_cost_per_workflow(group: pd.DataFrame, config: SimulationConfig) -> float:
    tokens = float(group["token_cost"].median())
    minutes = float(group["analyst_minutes"].median())
    return (
        tokens / 1_000_000 * config.costs.token_price_per_million
        + minutes / 60 * config.costs.analyst_hourly_cost
    )


def simulate_capital(
    runs: pd.DataFrame, config: SimulationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fault_runs = runs.loc[runs["fault_type"] != "CONTROL"].copy()
    fault_runs["economic_severity"] = (
        fault_runs["paired_final_delta"].abs() * config.capital.loss_conversion_ratio
        + config.capital.remediation_cost
    )
    annual_frames: list[pd.DataFrame] = []
    capital_rows: list[dict[str, object]] = []
    severity_rows: list[dict[str, object]] = []
    for topology, group in fault_runs.groupby("topology"):
        annual = np.zeros(config.capital.annual_simulations, dtype=float)
        for fault in FaultType:
            fault_group = group.loc[group["fault_type"] == str(fault)]
            if fault_group.empty:
                continue
            model = fit_severity(
                fault_group["economic_severity"].to_numpy(), config.capital.tail_threshold_quantile,
            )
            probability = float(config.capital.fault_occurrence_probability[fault])
            annual_lambda = config.capital.annual_workflows * probability
            rng = rng_for(config.experiment.seed, topology, fault, "capital")
            counts = rng.poisson(annual_lambda, size=config.capital.annual_simulations)
            total_events = int(counts.sum())
            if total_events:
                severities = model.sample(total_events, rng)
                owners = np.repeat(np.arange(config.capital.annual_simulations), counts)
                annual += np.bincount(owners, weights=severities, minlength=len(annual))
            severity_rows.append({
                "topology": topology, "fault_type": str(fault), "observations": len(model.observations),
                "annual_lambda": annual_lambda, "threshold": model.threshold,
                "tail_probability": model.tail_probability, "gpd_shape": model.shape,
                "gpd_scale": model.scale, "mean_severity": float(model.observations.mean()),
            })
        var_level = config.capital.var_level
        var = float(np.quantile(annual, var_level))
        tail = annual[annual >= var]
        annual_control_cost = _control_cost_per_workflow(group, config) * config.capital.annual_workflows
        capital_rows.append({
            "topology": topology, "simulations": len(annual), "mean_annual_loss": float(annual.mean()),
            "std_annual_loss": float(annual.std(ddof=1)), "var_99": float(np.quantile(annual, 0.99)),
            "var_995": var, "es_995": float(tail.mean()) if len(tail) else var,
            "annual_control_cost": annual_control_cost,
            "total_cost_objective": var + annual_control_cost,
        })
        annual_frames.append(pd.DataFrame({
            "topology": topology, "simulation_id": np.arange(len(annual)), "annual_loss": annual,
        }))
    return pd.DataFrame(capital_rows), pd.concat(annual_frames, ignore_index=True), pd.DataFrame(severity_rows)

