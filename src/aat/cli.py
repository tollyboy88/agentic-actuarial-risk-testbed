from __future__ import annotations

import argparse
import json
import time

from .calibration import calibrate_open_benchmarks
from .config import load_config
from .experiment import run_experiment
from .reporting import build_report
from .dashboard import export_dashboard_payload


def main() -> None:
    parser = argparse.ArgumentParser(prog="aat-sim", description="Agentic actuarial workflow risk simulator")
    parser.add_argument("command", choices=["calibrate", "run", "report", "all"])
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    started = time.perf_counter()
    if args.command in {"calibrate", "all"}:
        project_root = config.output_dir.parent.parent
        result = calibrate_open_benchmarks(project_root, config.output_dir)
        print(json.dumps(result, indent=2, default=str))
    if args.command in {"run", "all"}:
        runs, _ = run_experiment(config)
        print(f"completed {len(runs):,} runs")
    if args.command in {"report", "all"}:
        print(build_report(config))
        print(export_dashboard_payload(config.output_dir.parent.parent, config.output_dir.name))
    print(f"elapsed_seconds={time.perf_counter() - started:.2f}")


if __name__ == "__main__":
    main()
