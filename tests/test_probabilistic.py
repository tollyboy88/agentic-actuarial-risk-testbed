import numpy as np
import pandas as pd

from aat.probabilistic.recursion import terminal_distribution
from aat.probabilistic.simulation_study import run_recovery_study
from aat.probabilistic.transition_model import HierarchicalDirichletTransitionModel


def test_transition_model_probabilities_sum_to_one():
    frame = pd.DataFrame([
        {"stage":"S1_INGEST","fault_type":"F1_DATA","topology":"T1_LINEAR","state_before":"E","state_after":"E"},
        {"stage":"S1_INGEST","fault_type":"F1_DATA","topology":"T1_LINEAR","state_before":"E","state_after":"R"},
    ])
    model = HierarchicalDirichletTransitionModel().fit(frame)
    assert np.isclose(model.mean("S1_INGEST","F1_DATA","T1_LINEAR","E").sum(), 1.0)


def test_recursion_matches_manual_product():
    p = np.array([[1,0],[0.2,0.8]], float)
    assert np.allclose(terminal_distribution(np.array([0,1.0]), [p,p]), np.array([0.36,0.64]))


def test_recovery_study_has_expected_columns():
    result = run_recovery_study(replications=2, n_per_cell=20)
    assert {"truth","estimate","covered_90","covered_95"}.issubset(result.columns)
    assert len(result) == 4
