from __future__ import annotations

import sqlite3
import subprocess
import sys
import threading
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .dashboard import build_dashboard_payload, export_dashboard_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALLOWED_PROFILES = {"smoke", "scaled"}
STATUS: dict[str, object] = {"state": "idle", "profile": None, "message": "Ready"}

app = FastAPI(title="AAT Dashboard API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class RunRequest(BaseModel):
    profile: Literal["smoke", "scaled"] = "smoke"


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"ok": True, **STATUS}


@app.get("/api/results")
def results(profile: str = Query("scaled")) -> dict[str, object]:
    if profile not in ALLOWED_PROFILES:
        raise HTTPException(400, "Unknown experiment profile")
    try:
        return build_dashboard_payload(PROJECT_ROOT, profile)
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Results for {profile} have not been generated") from exc


def _execute(profile: str) -> None:
    STATUS.update(state="running", profile=profile, message=f"Running {profile} experiment")
    try:
        config = PROJECT_ROOT / "configs" / f"{profile}.yaml"
        for command in ("run", "report"):
            subprocess.run(
                [sys.executable, "-m", "aat.cli", command, "--config", str(config)],
                cwd=PROJECT_ROOT, check=True, capture_output=True, text=True,
            )
        export_dashboard_payload(PROJECT_ROOT, profile)
        STATUS.update(state="complete", message=f"{profile.title()} results refreshed")
    except Exception as exc:
        STATUS.update(state="failed", message=str(exc))


@app.post("/api/run", status_code=202)
def run(request: RunRequest) -> dict[str, object]:
    if STATUS["state"] == "running":
        raise HTTPException(409, "An experiment is already running")
    threading.Thread(target=_execute, args=(request.profile,), daemon=True).start()
    return {"accepted": True, "profile": request.profile}


@app.get("/api/trajectories")
def trajectories(
    profile: str = Query("scaled"), topology: str | None = None,
    fault_type: str | None = None, limit: int = Query(100, ge=1, le=500),
) -> dict[str, object]:
    if profile not in ALLOWED_PROFILES:
        raise HTTPException(400, "Unknown experiment profile")
    database = PROJECT_ROOT / "outputs" / profile / "trajectories.sqlite"
    if not database.exists():
        raise HTTPException(404, "Trajectory database is unavailable")
    clauses, values = ["r.fault_type IS NOT NULL"], []
    if topology:
        clauses.append("r.topology = ?"); values.append(topology)
    if fault_type:
        clauses.append("r.fault_type = ?"); values.append(fault_type)
    query = f"""
        SELECT r.run_id, r.world_id, r.topology, r.fault_type, r.injection_stage,
               r.detected, r.detection_stage, e.sequence, e.stage, e.event_type, e.payload_json
        FROM runs r JOIN events e ON e.run_id = r.run_id
        WHERE {' AND '.join(clauses)}
        ORDER BY r.absolute_misstatement DESC, e.sequence ASC LIMIT ?
    """
    values.append(limit)
    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        rows = [dict(row) for row in connection.execute(query, values)]
    return {"rows": rows, "count": len(rows)}
