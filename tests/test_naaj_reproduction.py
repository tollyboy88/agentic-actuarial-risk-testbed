from pathlib import Path

import pandas as pd


def test_scaled_publication_outputs_are_complete():
    root = Path(__file__).resolve().parents[1]
    runs = pd.read_parquet(root / "outputs/scaled/runs.parquet")
    stages = pd.read_parquet(root / "outputs/scaled/stage_metrics.parquet")
    assert len(runs) == 1024
    assert len(stages) == 6144
    assert runs["run_id"].nunique() == len(runs)
    assert stages.groupby("run_id").size().eq(6).all()
    assert {"paired_final_error", "detected", "silent_failure"}.issubset(runs.columns)
