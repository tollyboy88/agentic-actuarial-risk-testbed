from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import RunResult
from .utils import jsonable


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    world_id INTEGER NOT NULL,
    topology TEXT NOT NULL,
    fault_type TEXT,
    injection_stage TEXT,
    true_ultimate REAL NOT NULL,
    final_ultimate REAL NOT NULL,
    reserve_error REAL NOT NULL,
    absolute_misstatement REAL NOT NULL,
    detected INTEGER NOT NULL,
    detection_stage TEXT,
    hard_failure INTEGER NOT NULL,
    silent_failure INTEGER NOT NULL,
    token_cost INTEGER NOT NULL,
    analyst_minutes REAL NOT NULL,
    lineage_completeness REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    stage TEXT,
    event_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (run_id, sequence),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
CREATE TABLE IF NOT EXISTS stage_snapshots (
    run_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    stage TEXT NOT NULL,
    estimate REAL NOT NULL,
    metric_vector_json TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    data_hash TEXT NOT NULL,
    lineage_completeness REAL NOT NULL,
    hard_failure INTEGER NOT NULL,
    details_json TEXT NOT NULL,
    PRIMARY KEY (run_id, sequence),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);
"""


class TrajectoryStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.executescript(SCHEMA)

    def add(self, result: RunResult) -> None:
        self.connection.execute(
            "INSERT OR REPLACE INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                result.run_id, result.world_id, str(result.topology),
                None if result.fault_type is None else str(result.fault_type),
                None if result.injection_stage is None else str(result.injection_stage),
                result.true_ultimate, result.final_ultimate, result.reserve_error,
                result.absolute_misstatement, int(result.detected),
                None if result.detection_stage is None else str(result.detection_stage),
                int(result.hard_failure), int(result.silent_failure), result.token_cost,
                result.analyst_minutes, result.lineage_completeness,
            ),
        )
        self.connection.execute("DELETE FROM events WHERE run_id = ?", (result.run_id,))
        self.connection.execute("DELETE FROM stage_snapshots WHERE run_id = ?", (result.run_id,))
        for sequence, event in enumerate(result.events):
            payload = dict(event)
            stage = payload.pop("stage", None)
            event_type = payload.pop("event_type", "event")
            self.connection.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (result.run_id, sequence, None if stage is None else str(stage), str(event_type),
                 json.dumps(jsonable(payload), sort_keys=True)),
            )
        for sequence, snapshot in enumerate(result.snapshots):
            self.connection.execute(
                "INSERT INTO stage_snapshots VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    result.run_id, sequence, str(snapshot.stage), snapshot.estimate,
                    json.dumps(jsonable(snapshot.metric_vector), sort_keys=True), snapshot.row_count,
                    snapshot.data_hash, snapshot.lineage_completeness, int(snapshot.hard_failure),
                    json.dumps(jsonable(snapshot.details), sort_keys=True),
                ),
            )

    def commit(self) -> None:
        self.connection.commit()

    def close(self) -> None:
        self.connection.commit()
        self.connection.close()

    def __enter__(self) -> "TrajectoryStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

