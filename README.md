# Agentic Actuarial Testbed

A reproducible simulation testbed for studying how errors propagate through agentic-style actuarial workflows and how alternative controls change scenario-conditioned operational risk. It does not claim to measure deployed language-model agents or insurer regulatory capital.

Public repository: https://github.com/tollyboy88/agentic-actuarial-risk-testbed

## Scope

The model creates synthetic, known-truth insurance portfolios and passes them through six stages: ingestion, reconciliation, segmentation, reserving model, actuarial selection, and narrative. It injects seven fault classes, compares five control/topology families, saves complete trajectories, and measures outcomes against paired no-fault runs from the same synthetic world.

Capital results are scenarios; not estimates of real industry loss frequency or regulatory capital. Production occurrence frequencies, human-review performance, control placement, and cross-firm dependence require partner-firm evidence.

The reviewer-revision analyses add unrestricted CLRD2025 retrospective validation across six lines of business, 750 public-data fault injections, ±20%/±40% detection stresses, a 135-combination capital grid, 95% bootstrap/Monte Carlo intervals, and component ablations. Run them with `aat-sim robustness --config configs\scaled.yaml`.

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
- `figures/`: publication-oriented figures
- `REPORT.md`: ORSA-oriented interpretation and evidential boundary
- `outputs/reviewer_revision/`: CLRD2025 validation, sensitivity, ranking-stability, and ablation results

The random seed, resolved configuration, source inventories, and data-readiness/gap reports make each experiment replayable.

## Interactive dashboard

The local AAT Control Room is in `dashboard/`. It displays the verified result sets, compares architectures and fault classes, plots capital and systemic dependence, queries trajectory events, and can launch the approved smoke or scaled profiles.

See `dashboard/README.md` for installation and VS Code launch instructions. With the existing environment, use **Terminal → Run Task → AAT: Launch Dashboard**, then open `http://localhost:3000`.
## Split-paper submission packages

The rejected combined article has been separated into two non-overlapping papers:

- **Paper 1 — empirical software testbed:** the primary package targets the *North American Actuarial Journal* in `papers/paper1_naaj/`; `papers/paper1_aas/` is a prepared fallback for the *Annals of Actuarial Science* software stream.
- **Paper 2 — Bayesian methodology:** maintained separately at [bayesian-multistate-actuarial-workflows](https://github.com/tollyboy88/bayesian-multistate-actuarial-workflows), with its own posterior-analysis code and Bayesian Workflow Laboratory dashboard.

The open dataset is shared through [Zenodo](https://doi.org/10.5281/zenodo.22821051). This repository contains the Paper 1 experimental engine and operational dashboard; Paper 2 has a separate code and visualisation repository.

Reproduce the frozen paper results with:

```powershell
python scripts/reproduce_naaj.py
```

The AAS fallback has a deliberate submission gate: before uploading there, confirm source-file ownership, relicense the repository under GPL-3.0-only, create a matching archival release, and update its DOI/version statements. See `papers/paper1_aas/README.md`.
