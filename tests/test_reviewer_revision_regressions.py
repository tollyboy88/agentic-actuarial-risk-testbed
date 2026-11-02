from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "reviewer_revision" / "tables"


def test_unit_fault_detection_is_frozen_at_74_percent():
    audit = pd.read_csv(TABLES / "clrd_fault_audit.csv")
    fault_column = "fault_type" if "fault_type" in audit.columns else "fault"
    unit = audit.loc[audit[fault_column] == "unit_x1000"]
    assert len(unit) == 150
    assert unit["detected"].mean() == 0.74


def test_ranking_stability_percentages_are_complete_and_frozen():
    ranking = pd.read_csv(TABLES / "ranking_stability.csv")
    share_column = "share_best_var" if "share_best_var" in ranking.columns else "share_best"
    shares = dict(zip(ranking["topology"], ranking[share_column]))
    counts = (ranking[share_column] * 135).round().astype(int)
    assert counts.sum() == 135
    assert abs(sum(shares.values()) - 1.0) < 1e-12
    assert dict(zip(ranking["topology"], counts)) == {
        "T2_VALIDATOR": 54,
        "T3_SUPERVISOR": 39,
        "T5_HUMAN_K2": 42,
    }
