from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd
import yaml


def _wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 1.0
    proportion = successes / total
    denominator = 1.0 + z**2 / total
    centre = (proportion + z**2 / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z**2 / (4 * total**2)) / denominator
    return max(0.0, centre - margin), min(1.0, centre + margin)


def calibrate_open_benchmarks(project_root: Path, output_dir: Path) -> dict[str, object]:
    tau_root = project_root / "data" / "raw" / "github" / "05_agentic_failures" / "tau2-bench" / "data" / "tau2" / "results" / "final"
    tau_rows: list[dict[str, object]] = []
    for path in sorted(tau_root.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        info = payload.get("info", {})
        model = info.get("agent_info", {}).get("llm", path.stem.split("_")[0])
        domain = info.get("environment_info", {}).get("domain_name", "unknown")
        for simulation in payload.get("simulations", []):
            reward = simulation.get("reward_info", {}).get("reward", 0.0)
            tau_rows.append({
                "source_file": path.name, "model": model, "domain": domain,
                "reward": float(reward or 0.0), "failed": float(reward or 0.0) < 1.0,
            })
    tau = pd.DataFrame(tau_rows)

    dojo_root = project_root / "data" / "raw" / "github" / "06_prompt_injection" / "agentdojo" / "runs"
    dojo_rows: list[dict[str, object]] = []
    for path in dojo_root.rglob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("injection_task_id") is None:
            continue
        security = payload.get("security")
        dojo_rows.append({
            "pipeline": payload.get("pipeline_name", path.relative_to(dojo_root).parts[0]),
            "suite": payload.get("suite_name", "unknown"),
            "attack_succeeded": security is False,
            "utility_succeeded": payload.get("utility") is True,
            "error": bool(payload.get("error")),
        })
    dojo = pd.DataFrame(dojo_rows)

    tau_failures = int(tau["failed"].sum()) if len(tau) else 0
    tau_ci = _wilson(tau_failures, len(tau))
    dojo_successes = int(dojo["attack_succeeded"].sum()) if len(dojo) else 0
    dojo_ci = _wilson(dojo_successes, len(dojo))
    summary = {
        "warning": (
            "Benchmark-conditioned external ranges only. These quantities are not production occurrence rates "
            "and are not used as annual capital frequencies."
        ),
        "tau2": {
            "simulations": len(tau), "failures": tau_failures,
            "failure_rate": tau_failures / len(tau) if len(tau) else None,
            "wilson_95": list(tau_ci), "result_files": len(list(tau_root.glob("*.json"))),
        },
        "agentdojo": {
            "injection_runs": len(dojo), "attack_successes": dojo_successes,
            "attack_success_rate": dojo_successes / len(dojo) if len(dojo) else None,
            "wilson_95": list(dojo_ci),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    tau.to_parquet(output_dir / "tau2_calibration_runs.parquet", index=False)
    dojo.to_parquet(output_dir / "agentdojo_calibration_runs.parquet", index=False)
    (output_dir / "benchmark_calibration.yaml").write_text(
        yaml.safe_dump(summary, sort_keys=False), encoding="utf-8",
    )
    return summary

