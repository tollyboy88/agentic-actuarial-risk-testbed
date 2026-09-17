# Reviewer revision analyses

## Public actuarial validation

The CLRD2025 retrospective test covers six lines of business and 772 insurer-line records. Development visible through calendar year 2007 is compared with paid loss at development lag 10. Mean absolute percentage error is 6.2% for Chain Ladder, 8.9% for Bornhuetter–Ferguson, and 26.3% for latest paid. The Mack label reports the identical Chain Ladder point estimate; uncertainty is supplied by 100 insurer-cluster bootstrap resamples per line rather than Mack's analytic prediction error.

## Public-data fault audit

Deterministic controls detected 84.5% of 750 injected faults. Duplicate keys, negative paid values, development mismatches, and missing cells were all detected. Only 22.7% of multiplication-by-1,000 faults were detected, showing the need for unit metadata, reconciliation totals, and insurer-specific thresholds.

## Sensitivity and uncertainty

Detection effectiveness was rerun at 60%, 80%, 100%, 120%, and 140% of base probabilities. Capital was stressed over three fault-frequency multipliers, three economic-conversion ratios, and three remediation costs, producing 135 assumption combinations and 1,080 topology estimates with Monte Carlo intervals. The validator ranked lowest by VaR in 40.0% of combinations, human K2 in 31.1%, and the supervisor in 28.9%.

## Ablation

Nine controlled runs removed individual controls. Disabling replay/recovery left validator detection at 96.7% but raised unresolved failure from 0.8% to 40.0%. Removing the typed-stage validator raised unresolved failure to 34.2%; removing supervisor review raised it to 35.8%; and removing three human checkpoints raised it to 58.3%.

## Evidential boundary

The CLRD experiment validates reserving and audit mechanics on public insurer data. It does not convert benchmark errors into production agent-fault frequencies. The study remains an agentic-workflow risk simulation, not an empirical measurement of deployed language-model agents or insurer capital.
