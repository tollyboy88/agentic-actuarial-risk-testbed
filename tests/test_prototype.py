from __future__ import annotations

import sqlite3

import numpy as np
import pandas as pd

from aat.capital import simulate_capital
from aat.config import SimulationConfig, load_config
from aat.enums import FaultType, Stage, Topology
from aat.experiment import run_experiment
from aat.ground_truth import generate_world
from aat.models import RunSpec
from aat.pipeline import run_pipeline


def test_config_and_world_are_reproducible():
    config = load_config("configs/smoke.yaml")
    first = generate_world(0, config.experiment.seed, config.world)
    second = generate_world(0, config.experiment.seed, config.world)
    assert first.true_ultimate == second.true_ultimate
    pd.testing.assert_frame_equal(first.raw_transactions, second.raw_transactions)


def test_pipeline_has_six_auditable_stages():
    config = SimulationConfig()
    world = generate_world(0, config.experiment.seed, config.world)
    result = run_pipeline(world, RunSpec(0, Topology.LINEAR), config)
    assert not result.hard_failure
    assert len(result.snapshots) == 6
    assert np.isfinite(result.final_ultimate)
    assert {snapshot.stage for snapshot in result.snapshots} == set(Stage)


def test_fault_run_is_paired_and_detectable():
    config = SimulationConfig()
    world = generate_world(1, config.experiment.seed, config.world)
    baseline = run_pipeline(world, RunSpec(1, Topology.VALIDATOR), config)
    faulty = run_pipeline(world, RunSpec(1, Topology.VALIDATOR, FaultType.DATA, Stage.INGEST), config)
    assert baseline.run_id != faulty.run_id
    assert any(event["event_type"] == "fault_injected" for event in faulty.events)
    assert np.isfinite(faulty.final_ultimate)


def test_end_to_end_tiny_experiment(tmp_path):
    config = SimulationConfig.model_validate({
        "output_dir": tmp_path,
        "world": {"n_policies": 50},
        "experiment": {
            "n_worlds": 1, "topologies": ["T1_LINEAR"],
            "stages": ["S1_INGEST"], "fault_types": ["F1_DATA"],
        },
        "capital": {"annual_simulations": 2000, "systemic_simulations": 2000},
    })
    runs, stages = run_experiment(config)
    assert len(runs) == 2
    assert len(stages) == 12
    assert "paired_final_delta" in runs
    with sqlite3.connect(tmp_path / "trajectories.sqlite") as connection:
        assert connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 2
    capital, annual, severity = simulate_capital(runs, config)
    assert len(capital) == 1 and len(annual) == 2000 and len(severity) == 1
