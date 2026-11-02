# Reviewer revision analyses

## Public actuarial validation

The CAS CLRD2025 retrospective test uses 6 lines of business and 772 insurer–line combinations. Development through calendar year 2007 forms the observed upper triangle; development through lag 10 is retrospective ground truth. Chain Ladder, Mack Chain Ladder point estimates, Bornhuetter-Ferguson and latest-paid baselines are compared. Insurer-cluster bootstrap intervals use 100 resamples per line.

## Public-data fault audit

The deterministic schema, sign, development-consistency, completeness, extreme-increment and local scale-consistency checks detected 94.8% of 750 injected CLRD faults across six lines of business. The local scale-consistency check detected 74.0% of injected ×1,000 unit faults.

## Sensitivity and uncertainty

Detection effectiveness is rerun at 60%, 80%, 100%, 120% and 140% of base probabilities. Capital is stressed over 5 detection levels, 3 frequency multipliers, 3 loss-conversion ratios and 3 remediation costs, producing 1,080 topology-scenario estimates with Monte Carlo bootstrap intervals. The control topology with the lowest VaR is reported by scenario rather than assumed from the base case.

## Ablation

Nine controlled runs remove schema/lineage validation, prompt sanitisation, stage validation, replay/recovery, supervisor review or human checkpoints one at a time. The main outcome is unresolved paired error, so detection without repair is not misclassified as risk removal.

## Ranking stability

     topology  share_best
 T2_VALIDATOR    0.400000
  T5_HUMAN_K2    0.311111
T3_SUPERVISOR    0.288889

## Evidential boundary

The CLRD experiment validates the reserving and audit mechanics on public insurer data. It does not convert benchmark errors into production agent-fault frequencies. The study remains an agentic-workflow risk simulation, not an empirical measurement of deployed language-model agents.
