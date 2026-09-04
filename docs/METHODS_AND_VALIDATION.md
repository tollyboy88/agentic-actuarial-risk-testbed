# Methods and validation protocol

## Study design

The Agentic Actuarial Testbed (AAT) is a seeded, typed state machine. Each world contains policy-year exposure, premiums, claim-level ultimate losses, incremental payments, reporting and payment dates, peril labels, currency, and realistic ambient defects. The simulator retains the claim-level ultimate generated before observation noise, giving a known truth unavailable in real insurer data.

Each treatment run is paired with a no-injected-fault run using the same world, seed, and topology. The estimand is therefore the final or stage-level difference caused by the injected fault and its control response, rather than the total reserving error of the underlying method.

## Workflow and faults

The six stages are ingestion, reconciliation, segmentation, reserving model, actuarial selection, and narrative. Faults cover data/unit corruption, semantic mapping, tool arguments, reasoning judgement, hand-off loss, stale context, and indirect prompt injection. One controlled fault is injected per treatment run. Downstream validators and checkpoints can detect an earlier fault; repair restores the last clean state and deterministically replays subsequent stages.

The topology families are an unreviewed linear chain, typed stage validator, supervisor, model/selection critic, and zero-to-three human checkpoints. Detection probabilities and costs are transparent scenario assumptions in `src/aat/controls.py` and `configs/*.yaml`; they are not empirical insurer estimates.

## Measures

- Paired final error: `(faulty final − paired control final) / true ultimate`.
- Silent failure: undetected, non-exception outcome whose total error from known truth exceeds 1%.
- Amplification: stage deviation divided by the measurable scalar/vector deviation at the injection snapshot. It is undefined where a fault is latent at injection or was repaired before a measurable snapshot; those observations are flagged by `injection_signal_observed` and excluded from amplification summaries.
- Detection: whether a control identifies and repairs the active fault, plus detection stage and control cost.
- Lineage completeness: proportion of output rows retaining source lineage.

## Capital model

Simulated paired reserve movement is converted to economic severity using an explicit loss-conversion ratio plus remediation cost. For each fault class and topology, the body is resampled empirically and a generalized Pareto tail is fitted when at least 20 threshold excesses exist. Annual frequency is compound Poisson with user-specified scenario rates. The engine reports mean loss, VaR 99%, VaR 99.5%, and ES 99.5%.

Cross-firm stress uses a Gaussian copula with prescribed correlations of 0, 0.3, 0.6, and 0.9. This is a dependence sensitivity, not an estimate of sector correlation. Control optimization minimizes capital plus annual control cost subject to a residual-risk cap set at 75% of the unreviewed linear-chain VaR.

## Validation gates completed

1. Deterministic world reproduction under identical seeds.
2. Six complete, finite stage snapshots for a baseline run.
3. Fault and control events visible in the trajectory.
4. End-to-end persistence to Parquet and relational SQLite tables.
5. Capital aggregation produces the requested simulation count.
6. A 1,024-run scaled screening design completed with no execution failures.

## Required publication sensitivity work

Before treating numeric results as publishable estimates, run the full replication design and vary fault magnitudes, annual frequencies, detection curves, loss-conversion ratios, GPD thresholds, and dependence structures. Add bootstrap intervals by world, compare Poisson with negative-binomial frequency, and validate a subset against an independently implemented reserving engine. Partner-firm data are required for external calibration; absent that, conclusions must remain scenario-conditioned.
