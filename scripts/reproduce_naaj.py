from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aat.config import load_config
from aat.experiment import run_experiment
from aat.reporting import build_report
from aat.robustness import build_reviewer_revision


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    config_path = ROOT / "configs/naaj_final.yaml"
    config = load_config(config_path)
    run_experiment(config); build_report(config); build_reviewer_revision(config_path)
    manifest = {}
    for path in sorted(config.output_dir.rglob("*")):
        if path.is_file(): manifest[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    (config.output_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(config.output_dir)


if __name__ == "__main__":
    main()
