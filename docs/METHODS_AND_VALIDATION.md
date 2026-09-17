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
7. CLRD2025 retrospective validation completed across six lines and 772 insurer-line records, with 100 insurer-cluster resamples per line.
8. A 750-case public-data fault audit, five-level detection sensitivity, 135-combination capital grid, and nine control ablations completed.

## Reviewer-revision robustness work

The robustness command rescales detection probabilities to 60%, 80%, 100%, 120%, and 140% of base and crosses these with fault-occurrence multipliers 0.5/1/2, economic-conversion ratios 1%/5%/10%, and remediation costs GBP 1,000/5,000/10,000. World-bootstrap intervals cover detection and unresolved failure; Monte Carlo resampling covers VaR. Ablations separately remove broad stage validation, replay/recovery, supervisor review, and human checkpoints. Run with `aat-sim robustness --config configs/scaled.yaml`.

Remaining work for external calibration requires partner-firm incidents and review outcomes. A future live-agent study should preregister frozen prompts and tools and repeat trials across multiple model families. Until then, conclusions remain scenario-conditioned.
