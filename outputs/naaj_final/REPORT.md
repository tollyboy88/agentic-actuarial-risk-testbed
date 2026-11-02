# Agentic actuarial workflow simulation — results

## Decision summary

This prototype executed **1,024 runs** across **8 synthetic insurer worlds** and **8 workflow topologies**. It preserves every stage trajectory and uses paired, same-world no-fault controls to isolate injected-fault effects.

The minimum-objective control package in this scenario is **T2_VALIDATOR**, with VaR 99.5% of **GBP 102,641**, expected shortfall 99.5% of **GBP 111,040**, and annual control cost **GBP 1**. The largest observed paired reserve movement was **GBP 34,244,668,786** (F1_DATA injected at S1_INGEST under T1_LINEAR).

## What is demonstrated

- Reproducible known-truth insurance worlds, including claims development, currencies, duplicates, and policy exposures.
- A six-stage reserving workflow with observable data, model, selection, and narrative states.
- Fault injection, detection, repair, lineage, silent-failure classification, and paired causal measurement.
- Compound-Poisson annual loss aggregation, empirical/GPD severity, VaR and expected shortfall.
- Prescribed Gaussian-copula dependence stress across firms and cost/risk control-package selection.

## Evidential boundary

All financial values are **scenario-conditioned simulation outputs**, not estimates of industry-wide operational loss or required regulatory capital. Open datasets informed mechanisms and benchmark ranges; they do not identify production fault frequencies, human-review effectiveness, firm control placement, or real cross-firm dependence. Those parameters are explicit assumptions and must be replaced or calibrated during a partner-firm validation study.

## ORSA interpretation

The output can support an ORSA-style scenario discussion: identify the agentic workflow, document fault pathways and controls, compare residual tail loss, and stress common-model dependence. It should be reported as an internal model experiment with sensitivity ranges, not as a stand-alone capital number. Model governance should require versioned configurations, replayable trajectories, independent validation, and approval before production use.

## Reproducibility

Resolved configuration: `config_resolved.yaml`. Machine-readable outputs are in `tables/`; full event trajectories are in `trajectories.sqlite`. Figures 1–5 are in `figures/`.
