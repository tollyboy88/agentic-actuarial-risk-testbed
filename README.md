# Agentic Actuarial Testbed

A reproducible prototype for studying how errors propagate through agentic actuarial workflows and how alternative controls change scenario-conditioned operational risk capital.

Public repository: https://github.com/tollyboy88/agentic-actuarial-risk-testbed

## Scope

The model creates synthetic, known-truth insurance portfolios and passes them through six stages: ingestion, reconciliation, segmentation, reserving model, actuarial selection, and narrative. It injects seven fault classes, compares five control/topology families, saves complete trajectories, and measures outcomes against paired no-fault runs from the same synthetic world.

Capital results are scenarios—not estimates of real industry loss frequency or regulatory capital. Production occurrence frequencies, human-review performance, control placement, and cross-firm dependence require partner-firm evidence.

## Run

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\aat-sim all --config configs\smoke.yaml
```

For the larger demonstration, replace `smoke.yaml` with `scaled.yaml`. `full.yaml` is the publication-scale factorial design and is intentionally much more expensive.

## Outputs

- `runs.parquet`: run-level paired effects and failures
- `stage_metrics.parquet`: stage-by-stage propagation
- `trajectories.sqlite`: auditable events and snapshots
- `tables/`: severity, capital, systemic stress, and optimization outputs
- `figures/`: five publication-oriented figures
- `REPORT.md`: ORSA-oriented interpretation and evidential boundary

The random seed, resolved configuration, source inventories, and data-readiness/gap reports make each experiment replayable.

## Interactive dashboard

The local AAT Control Room is in `dashboard/`. It displays the verified result sets, compares architectures and fault classes, plots capital and systemic dependence, queries trajectory events, and can launch the approved smoke or scaled profiles.

See `dashboard/README.md` for installation and VS Code launch instructions. With the existing environment, use **Terminal → Run Task → AAT: Launch Dashboard**, then open `http://localhost:3000`.

## Journal submission package

The journal-targeted manuscript, title page, cover letter, supplementary material, editable tables, and high-resolution figures are in `submission/final/`. The package targets the standard subscription route of the *Scandinavian Actuarial Journal*; the research decision and evidence ledger are in `submission/research/`.
