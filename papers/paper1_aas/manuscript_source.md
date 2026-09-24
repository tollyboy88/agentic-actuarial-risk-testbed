# A Reproducible Fault-Injection Testbed for Error Propagation and Control Evaluation in Agentic Actuarial Reserving Workflows

## Abstract

We introduce an open-source Python testbed for controlled fault injection and control evaluation in multi-stage actuarial reserving workflows. The software generates seeded known-truth portfolios or accepts public loss-development data, executes six auditable stages, injects seven fault classes, and compares automated and human controls using paired clean counterfactuals. Detected faults can be restored and replayed while event ledgers preserve lineage. Reproducible examples include 1,024 synthetic runs, retrospective validation on six CLRD2025 lines, public-data fault audits, detection sensitivity and component ablation. Per-stage validation reduced silent failure from 81.7% to 2.5%; removing replay raised unresolved validator failures from 0.8% to 40.0%. A new local scale check increased detection of ×1,000 unit faults from 22.7% to 74.0%. The package reports propagation, unresolved material error, control cost and scenario-conditioned tail-risk measures. It is a reusable experimental and audit toolbox, not an estimate of production agent-failure frequencies or regulatory capital.

**Keywords:** actuarial artificial intelligence; fault injection; claims reserving; model risk; workflow controls

**Practical applications:** The prototype lets actuarial teams inject defined faults into a replayable reserving workflow, observe where errors propagate or are detected, and stress the remaining effects under alternative frequency, economic-conversion, and remediation assumptions. Public CLRD2025 tests show that the data and reserving controls operate on real insurer triangles, while sensitivity and ablation results identify which conclusions depend on assumed control performance. The monetary outputs should be calibrated with firm evidence before any operational-risk or capital use.

**JEL classification:** C15; C63; G22

## 1. Introduction

Claims reserving is a useful stress environment for agentic artificial intelligence (AI). It combines data engineering, currency and unit handling, actuarial judgement, model selection, reconciliation, and communication. Classical reserving research makes uncertainty explicit and auditable (Mack, 1993; England & Verrall, 2002; Wüthrich & Merz, 2008), while newer machine-learning approaches increase automation and modelling flexibility (Kuo, 2019; Gabrielli et al., 2020; Feng & Li, 2024). An agentic implementation adds a different layer of risk: the system can select tools, pass state between components, respond to untrusted context, and produce a plausible report after an upstream failure.

Current AI governance frameworks rightly emphasize measurement, traceability, oversight, and lifecycle controls (NIST, 2023, 2024; ISO, 2023; European Union, 2024). Financial-sector frameworks similarly require firms to understand model limitations, operational dependencies, and severe but plausible scenarios (Basel Committee on Banking Supervision, 2021; EIOPA, 2015; Prudential Regulation Authority, 2023). These frameworks do not, however, prescribe an empirical mapping from a faulty multi-step agent trajectory to an actuarial misstatement, a detected remediation event, an annual loss distribution, or a tail-capital scenario.

The agent literature supplies increasingly realistic tests of tool use, planning, recovery, and adversarial interaction (Yao et al., 2023; Qin et al., 2024; Liu et al., 2024; Debenedetti et al., 2024; Yao et al., 2024). Benchmark scores are not operational loss frequencies. They rarely preserve an actuarial known truth, pair a faulty trajectory with a same-world counterfactual, or aggregate residual effects into a transparent capital scenario. Conversely, operational-risk models aggregate frequency and severity but typically start after loss events have already been defined (Moscadelli, 2004; Böcker & Klüppelberg, 2005; McNeil et al., 2015).

This paper asks four questions. First, how does a controlled error introduced at one stage of a simulated agentic actuarial workflow change downstream states and the final reserve? Second, how do alternative control architectures change detection, silent failure, and tail loss? Third, are the direction and ranking of results robust to plausible changes in detection, occurrence, conversion, and remediation assumptions? Fourth, do the reserving and validation mechanics operate sensibly on an unrestricted public actuarial dataset? The study contributes: (1) a fault taxonomy tailored to multi-stage actuarial work; (2) a seeded known-truth environment; (3) paired stage-level propagation measures; (4) replayable and ablated control responses; (5) compound frequency-severity and systemic-dependence stresses with uncertainty intervals; and (6) retrospective cross-line validation using public loss-reserving triangles.

The result is not a claim that agentic systems require a particular amount of regulatory capital. It is a measurement design that an insurer can calibrate with its own workflow, incident evidence, control performance, exposure conversion, and scenario frequencies. This distinction between a reproducible method and a universal parameter estimate is central to the study.

## 2. Related work and research gap

### 2.1 Actuarial automation and reserving

Traditional chain-ladder methods provide a transparent baseline and a well-developed treatment of prediction error (Mack, 1993; England & Verrall, 2002). Stochastic reserving methods formalize uncertainty around outstanding claims (Wüthrich & Merz, 2008). Neural-network reserving has since demonstrated how classical models may be embedded in flexible architectures and how heterogeneous information may be used in automated forecasts (Gabrielli et al., 2020; Kuo, 2019; Feng & Li, 2024). These contributions concern predictive models. The present problem is wider: an agentic workflow can alter the dataset, invoke the wrong tool arguments, omit a hand-off field, apply stale context, or write an unsupported narrative even when the reserving algorithm itself is sound.

### 2.2 Agentic systems and safety

ReAct integrates reasoning and acting with external tools (Yao et al., 2023); ToolLLM and AgentBench study tool-use and multi-environment capability (Qin et al., 2024; Liu et al., 2024). AgentDojo and tau-bench expose agents to realistic security and user-interaction conditions (Debenedetti et al., 2024; Yao et al., 2024). Reflection and multi-agent orchestration can improve task completion but add state, communication, and control surfaces (Shinn et al., 2023; Wu et al., 2023; Park et al., 2023; Xi et al., 2023). Safety research has long warned that reward specification, distribution shift, unsafe exploration, and scalable oversight can produce unexpected behaviour (Amodei et al., 2016).

System safety also depends on data and process quality. Data cascades describe how upstream problems compound through downstream work (Sambasivan et al., 2021), and hidden technical debt explains why apparently local machine-learning changes create wider system liabilities (Sculley et al., 2015). Documentation proposals such as model cards and datasheets improve transparency (Mitchell et al., 2019; Gebru et al., 2021), while algorithmic auditing seeks to close the gap between principles and verifiable evidence (Raji et al., 2020). The AAT operationalizes these ideas as typed states, fault events, validation evidence, and deterministic replay.

### 2.3 Operational risk and dependence

Loss-distribution approaches combine event frequency and severity; heavy-tail modelling and extreme-value methods are especially important for high quantiles (Embrechts et al., 1997; McNeil et al., 2015). Operational-risk data show strong heterogeneity and limited tail information (Moscadelli, 2004), while closed-form approximations clarify the sensitivity of capital to frequency and severity assumptions (Böcker & Klüppelberg, 2005). Dependence can materially change aggregate risk and diversification (Embrechts et al., 2002). The AAT does not estimate these quantities from public benchmark data. It uses them as visible scenario levers.

The gap is therefore a missing bridge between micro-level agent failures and macro-level actuarial risk measures. Existing agent benchmarks do not provide insurer-specific economic mappings; existing capital models do not identify how a loss arose from a sequence of agent actions. The proposed method joins the two without obscuring the assumptions required at the boundary.

## 3. Methods

### 3.1 Experimental system

The AAT is a seeded, typed state machine. Each synthetic world contains policy-year exposure, premiums, claim-level ultimate losses, incremental payments, reporting and payment dates, peril labels, currencies, and ambient data defects. The claim-level ultimate generated before observation noise is retained as known truth. Synthetic data avoid confidentiality restrictions and make fault effects identifiable, although they cannot establish external frequency or severity.

The six stages are ingestion, reconciliation, segmentation, reserving model, actuarial selection, and narrative. The deterministic tools perform arithmetic and reserving transformations; topology-specific control rules determine whether an active fault is detected and repaired. Every stage writes a snapshot and an event record containing identifiers, lineage, control actions, and financial outputs.

### 3.2 Fault taxonomy

Seven fault classes were defined from the intersection of actuarial workflow risks and agent-system failure surfaces: F1 data or unit corruption; F2 semantic mapping error; F3 incorrect tool arguments; F4 reasoning or judgement error; F5 hand-off loss; F6 stale or conflicting context; and F7 indirect prompt injection. One controlled fault is injected per treatment run. The taxonomy separates the mechanism that creates an error from its final monetary effect, allowing the same measurement design to be reused with different implementations.

The F1 scenario includes a deliberately severe multiplication-by-1,000 unit fault. This is a stress test rather than an estimate of normal processing error. F7 represents untrusted instructions arriving through data or retrieved content. The latter reflects a recognized security concern for tool-using language-model applications (OWASP Foundation, 2025; Debenedetti et al., 2024).

### 3.3 Control topologies

Eight topology variants were evaluated: an unreviewed linear chain (T1); a typed validator after each stage (T2); a supervisor capable of checking and replaying the workflow (T3); a critic concentrated around model and selection decisions (T4); and human-checkpoint variants with zero, one, two, or three checkpoints (T5-K0 to T5-K3). Detection probabilities and costs are configuration parameters, not empirical claims. When a control detects an active fault, the system restores the last clean state and deterministically replays later stages.

This architecture tests a practical proposition: detection is useful only if provenance and clean state make recovery possible. Logging alone may reveal an issue but does not undo contaminated calculations. Replay also reduces ambiguity about which downstream artifacts must be regenerated.

### 3.4 Design and estimands

The screening experiment used eight seeded worlds and deterministic fractional selection that retained every fault type, stage, and topology level. It produced 1,024 runs, 6,144 stage snapshots, and 16,530 auditable events. No run ended in a hard execution failure. Each fault-injected run was paired with a no-injected-fault run using the same world, seed, and topology.

Let Y_f denote the final reserve under an injected fault, Y_0 its paired no-fault result, and U the known ultimate. The paired final effect is (Y_f - Y_0)/U. A silent failure is an undetected, non-exception result for which absolute total error relative to U exceeds 1%. Detection records whether and where a control identifies and repairs the active fault. Stage amplification is the downstream deviation divided by the measurable deviation at the injection snapshot. Amplification is marked undefined when the fault is latent at injection or repaired before a measurable snapshot; only 9.9% of fault runs have a measurable injection signal under this strict definition.

The use of paired controls prevents ordinary stochastic reserving variation from being attributed to the injected fault. It also makes the experiment reproducible at the level of individual trajectories rather than only aggregate rates.

### 3.5 Loss aggregation and capital scenarios

For each topology and fault class, paired reserve movement is converted to economic severity by an explicit loss-conversion ratio plus a remediation amount. The demonstration uses 5% and GBP 5,000, respectively. The body distribution is resampled empirically. A generalized Pareto tail is fitted only when at least 20 threshold excesses are available; otherwise empirical resampling is retained.

Annual event counts follow a Poisson distribution with configured scenario frequencies. Aggregate annual loss is L = sum from i=1 to N of X_i plus annual control cost, where N is the event count and X_i is economic severity. Ten thousand annual simulations are used per topology. The outputs include mean loss, Value-at-Risk (VaR) at 99% and 99.5%, and Expected Shortfall (ES) at 99.5%. These measures follow standard quantitative-risk definitions (McNeil et al., 2015).

Cross-firm stress uses a Gaussian copula for 20 firms at prescribed correlations of 0, 0.3, 0.6, and 0.9, with 5,000 simulations per point. Copula correlation is a sensitivity parameter, not an estimate of shared-provider or sector dependence (Embrechts et al., 2002).

### 3.6 Reproducibility and validation

Validation gates test deterministic world reproduction, six finite stage snapshots, visible fault and repair events, Parquet and relational persistence, and successful capital aggregation. Configuration, seeds, paired outputs, tables, figures, and source code are versioned. The public repository is https://github.com/tollyboy88/agentic-actuarial-risk-testbed. No restricted insurer data are redistributed.

### 3.7 Public-data retrospective validation

External mechanics were tested with the unrestricted CLRD2025 sample distributed by the open-source Chainladder project and originating in the Casualty Actuarial Society Loss Reserve Database (Casualty Actuarial Society, n.d.; Chainladder contributors, 2026). The file contains paid-loss development for commercial auto, medical malpractice, other liability, private-passenger auto, products liability, and workers compensation. After removing duplicate insurer-line-accident-year-development keys and invalid values, the experiment retained 772 insurer-line records.

Calendar year 2007 was imposed as the valuation cutoff. Development visible by that date formed the lower triangle, while paid loss at development lag 10 was held out as retrospective ground truth. Portfolio estimates were produced by latest paid, volume-weighted Chain Ladder, the identical Mack Chain Ladder point estimate, and Bornhuetter–Ferguson using an expected loss ratio estimated only from mature accident years (Bornhuetter & Ferguson, 1972; Mack, 1993). Mack's contribution concerns distribution-free uncertainty; its point estimate is therefore not a fourth distinct forecast. Uncertainty was estimated by 100 insurer-cluster bootstrap resamples per line of business. This is a mechanics and cross-line robustness test, not a source of agent-fault frequencies.

A complementary fault audit injected duplicate keys, negative paid values, development-year inconsistencies, missing development cells, and a multiplication-by-1,000 unit error into the 25 largest insurer triangles per line. Deterministic schema, sign, development, completeness, and extreme-increment checks were applied without access to restricted data.

### 3.8 Sensitivity, uncertainty, and control ablation

Control-detection probabilities were rescaled to 60%, 80%, 100%, 120%, and 140% of their configured values, corresponding to the requested ±20% and ±40% stresses around base. Each level reran the complete screening experiment. World-cluster bootstrap intervals with 1,000 resamples were calculated for detection and unresolved failure.

For each detection level, capital was recomputed across fault-occurrence multipliers of 0.5, 1, and 2; economic-loss conversion ratios of 1%, 5%, and 10%; and remediation costs of GBP 1,000, GBP 5,000, and GBP 10,000. The resulting 135 assumption combinations produced 1,080 topology-scenario estimates. Each VaR estimate used 3,000 annual simulations and a 250-resample Monte Carlo interval. Ranking stability was evaluated by the topology with the lowest VaR within each combination.

Nine ablation runs removed schema/lineage validation, prompt sanitisation, the general typed-stage validator, replay/recovery, supervisor review, or human checkpoints one component at a time. The primary ablation outcome was unresolved paired error of at least 1%, because detection without repair does not remove financial contamination.

### 3.9 Implementation and user interface

The Python package exposes a command-line interface, YAML configuration, Parquet/CSV tables, SQLite event trajectories and a local operational dashboard. `scripts/reproduce_naaj.py` regenerates the fixed applied study. A run manifest stores SHA-256 hashes, and `REPRODUCIBILITY.md` gives installation and resource instructions.

### 3.10 Unit Testing and Validation

The test suite checks deterministic seeds, unique run identifiers, six stage records per run and required publication outputs. The smoke profile supports rapid installation checks; the scaled profile recreates the reported 1,024-run study.

## 4. Results

### 4.1 Detection and silent failure

Across fault-injected runs, the validator detected 96.7% of faults, compared with 9.2% for the unreviewed linear topology. Fault-only silent-failure rates were 81.7% for linear, 2.5% for validator, 4.2% for supervisor, and 17.5% for critic. When the eight no-injected-fault baselines per topology were also counted, total silent-outcome rates were 82.0%, 7.8%, 9.4%, and 21.9%, respectively. The difference shows that controls can detect injected faults without eliminating ordinary model error or ambient data defects. The critic's concentration around model and selection decisions left more exposure to data, hand-off, context, and adversarial failures than the per-stage validator.

Detection differed materially by fault class. The validator detected all semantic, hand-off, context, and adversarial faults in the screening design, 96.9% of tool faults, 91.7% of data faults, and 87.5% of reasoning faults. Small cell counts mean these are screening proportions, not stable population estimates. The result nevertheless shows how a fault-by-control matrix identifies residual weaknesses that a single average score conceals.

Human checkpoints produced a non-linear response. Silent failure declined from 88.3% with no checkpoints to 26.7%, 18.3%, and 16.7% with one, two, and three checkpoints. The marginal improvement from the second and third checkpoints was smaller than the first. Placement and fault coverage therefore matter at least as much as checkpoint count.

### 4.2 Capital scenarios

The unreviewed linear topology produced annual VaR 99.5% of GBP 2.462 billion and ES 99.5% of GBP 2.967 billion. The per-stage validator produced VaR of GBP 102,641 and ES of GBP 111,040; the supervisor produced GBP 116,079 and GBP 125,408; and the critic produced GBP 144,632 and GBP 159,036. Human K1, K2, and K3 produced VaR values of GBP 181,495, GBP 135,687, and GBP 145,756. Human K0 remained extreme at GBP 1.986 billion.

The orders-of-magnitude difference is mainly driven by whether the rare, severe F1 unit stress remains silent. It should not be generalized to expected production savings. The automated validator's annual control cost of GBP 0.65 is likewise a computational scenario assumption, whereas human variants use assumed analyst costs of GBP 1,360 to GBP 4,080. The cost comparison demonstrates the optimization interface but is not a procurement result.

### 4.3 Systemic dependence

The median sector VaR 99.5% across topologies rose from approximately GBP 1.52 million at prescribed dependence zero to GBP 2.06 million at 0.3, GBP 2.47 million at 0.6, and GBP 2.80 million at 0.9. Topology-specific effects were larger for the extreme unreviewed cases. The direction is consistent with reduced diversification under common shocks; the levels remain conditional on the marginal scenarios and the chosen copula.

### 4.4 Sensitivity and ranking stability

The principal control result was directionally robust, but its magnitude depended on assumed detection. When detection probabilities were scaled from 60% to 140% of base, validator detection rose from 89.2% (95% interval 84.2%–93.3%) to 100%, while unresolved failure fell from 5.0% (2.5%–6.7%) to 0%. The supervisor moved from 88.3% detection and 4.2% unresolved failure to 100% and 0%. In contrast, the unreviewed linear topology remained weak: unresolved failure changed only from 55.0% to 50.8% because it has few controls to scale.

Capital levels were highly assumption-sensitive. Across all stresses, validator VaR ranged from GBP 12,000 to GBP 472,267; supervisor VaR ranged from GBP 11,000 to GBP 452,178. Linear VaR ranged from GBP 151.5 million to GBP 6.87 billion. These intervals and ranges reinforce that the monetary output is a scenario surface rather than an estimate.

The lowest-VaR topology also changed: the validator ranked first in 40.0% of the 135 combinations, human K2 in 31.1%, and the supervisor in 28.9%. The defensible finding is therefore that structured validation/recovery dominates an unreviewed chain, not that one reviewed architecture is universally optimal.

### 4.5 Public CLRD2025 validation

Chain Ladder had mean absolute percentage error of 6.2% across the six lines, compared with 8.9% for Bornhuetter–Ferguson and 26.3% for latest paid. Cross-line performance was heterogeneous. Chain Ladder error was 0.008% for private-passenger auto, 0.16% for other liability, 0.31% for workers compensation, 1.99% for commercial auto, 5.54% for products liability, and 29.34% for medical malpractice. Bornhuetter–Ferguson reduced medical-malpractice error to 3.96% but increased products-liability error to 34.29%. The insurer-cluster intervals were correspondingly wider for the smaller and less stable lines. These results demonstrate functioning public-data mechanics while warning against a single universally preferred reserving method.

The legacy deterministic audit detected all duplicate-key, negative-paid, development-mismatch and missing-cell faults, but only 22.7% of multiplication-by-1,000 faults. A new local scale-consistency check compares the target cumulative payment with the median positive peer development value in the same accident year. With a deliberately conservative 100-fold threshold, unit-fault detection increased to 74.0%. The residual cases lacked a stable positive peer or did not cross the threshold, so unit metadata and reconciliation totals remain necessary.

### 4.6 Control ablation

Removing the typed-stage validator reduced validator detection from 96.7% to 35.0% and increased unresolved failure from 0.8% to 34.2%. Keeping detection but disabling replay/recovery left detection at 96.7% while unresolved failure rose to 40.0%, directly supporting the distinction between finding a fault and reversing its effects. Removing supervisor review increased unresolved failure from 1.7% to 35.8%; removing three human checkpoints increased it from 5.0% to 58.3%.

Removing schema/lineage validation or prompt sanitisation alone did not change aggregate rates in this design because the overlapping typed-stage validator detected the same selected treatments. This is not evidence that those controls are redundant in production; it shows that the current screening design cannot separately identify their marginal contribution when a broad downstream validator remains active.

## 5. Discussion

### 5.1 Main findings

First, control architecture can change the character of a failure from silent financial contamination to a detected remediation event. In this experiment that conversion dominated the tail. Second, recovery requires more than a detector: typed state, provenance, a clean checkpoint, and deterministic replay form a joint control. Third, controls should be evaluated against heterogeneous fault mechanisms. A critic that performs well on modelling judgements can still miss unit, context, and hand-off defects.

Fourth, capital results are highly sensitive to the boundary between technical error and economic loss. The 5% conversion ratio, remediation amount, event frequency, and unit-fault magnitude are assumptions. Treating them as parameters makes model risk visible and challengeable. Concealing them inside a single score would create false precision.

Finally, shared foundation models, tools, data providers, or orchestration frameworks create plausible common-cause pathways. The dependence stress shows why ORSA-style assessment should consider accumulation even where data do not support a central correlation estimate.

The robustness analyses qualify the base-case comparison. Reviewed architectures consistently outperform the unreviewed chain, but validator, supervisor, and two-checkpoint human review exchange first place across the assumption grid. Public-data validation similarly shows that a method performing well on five lines can be materially weaker on another. The useful output is therefore a transparent decision surface with uncertainty, not a single control or reserving-method league table.

### 5.2 Implications for actuarial practice

The testbed can support four practical activities. A model owner can map the production workflow into typed stages and define known invariants. Independent validation can inject faults and compare the resulting trajectory with a clean replay. Operational-risk teams can translate observed or elicited residual events into transparent frequency-severity scenarios. Governance committees can compare control packages using both residual tail risk and implementation cost.

The method also suggests minimum evidence for production: versioned prompts and tools, input and output lineage, stage-level validation results, recoverable clean state, replay tests, incident taxonomy, and periodic scenario challenge. These controls complement rather than replace professional actuarial judgement. Human approval is most valuable when its location and decision rights are specified, not when it is represented as an undifferentiated probability of detection.

### 5.3 Governance interpretation

NIST's measurement and risk-management functions, model-risk principles, and ORSA guidance all emphasize documented assumptions and ongoing monitoring (NIST, 2023; Prudential Regulation Authority, 2023; EIOPA, 2015). The AAT produces artifacts that can be attached to those processes: a resolved configuration, an event ledger, paired counterfactuals, control evidence, and sensitivity outputs. It is an internal experiment, not a substitute for a firm's approved capital model or statutory reserve opinion.

## 6. Limitations and future work

The AAT is a simulation testbed, not a deployed language-model experiment. Its stages and faults are deterministic software transformations, while control detection is drawn from configured probabilities. This improves reproducibility and mechanism isolation but omits model-version variation, latency, prompt sensitivity, emergent tool use, and the correlated behaviour of real agents. The softened title and claims reflect this evidential boundary. A small open-model experiment was not added because a single model and prompt set would not validate production agent behaviour; a preregistered multi-model extension with frozen prompts, tool traces, and repeated trials is more defensible future work.

The eight-world screening design yields small fault-stage cells, and its bootstrap intervals describe uncertainty across those seeded worlds rather than population-level confidence. The capital module assumes Poisson frequency, and the sensitivity grid does not exhaust fault magnitude, tail threshold, or dependence uncertainty. Future work should compare negative-binomial and contagion processes, vary tail thresholds and unit-fault magnitudes, and use alternative copulas or explicit common shocks where evidence permits.

CLRD2025 validates reserving and deterministic audit mechanics, not the incidence or economic severity of agent failures. The retrospective truth is paid loss at lag 10 rather than a final, fully settled ultimate; the Mack implementation reports the Chain Ladder point estimate with cluster-bootstrap uncertainty rather than Mack's analytic prediction error. The 100-resample line-level intervals are suitable for a prototype but should be increased for final inferential work. The unit-fault audit also shows that cross-sectional anomaly detection needs metadata and local calibration.

External calibration requires de-identified production evidence: incident and near-miss logs, review outcomes, workflow volumes, control placement, correction costs, and business-impact measures. If such data cannot be obtained without restriction, the study should retain scenario ranges and drop claims about empirical capital adequacy, net human-error offsets, or industry frequency. A multi-firm study could estimate hierarchical detection curves while preserving confidentiality through federated summaries.

The current prototype uses a reserving workflow. Extensions should test pricing, experience studies, capital reporting, and regulatory submissions. Live-agent experiments should be repeated across multiple open and proprietary model versions and include adversarial documents, access-control violations, and tool failures. Formal value-of-information analysis could then optimize checkpoint placement under uncertainty.

## 7. Conclusion

Agentic actuarial risk can be made experimentally observable without pretending that open data answer questions they cannot. The AAT traces a controlled fault from insertion through downstream propagation, detection, replay, and scenario-conditioned economic loss. In the screening experiment, per-stage validation sharply reduced silent failure and the severe tail generated by an uncorrected unit stress; sensitivity and ablation showed that recovery is as important as detection. Public CLRD2025 results confirmed that the reserving mechanics transfer across six real-data lines while exposing method and unit-check weaknesses. Prescribed common-model dependence eroded diversification.

The strongest contribution is methodological. The testbed supplies a common, auditable object that insurers, actuaries, validators, and operational-risk teams can calibrate and challenge. Its monetary outputs remain scenarios until firm-specific evidence replaces the explicit assumptions.

## Statements and declarations

**Funding.** This work received no specific grant from any funding agency, commercial or not-for-profit sectors.

**Competing interests.** The authors declare no competing interests.

**Author contributions.** Adebayo Aliu Adetola: conceptualisation, methodology, software, formal analysis, investigation, data curation, visualisation, writing—original draft, and writing—review and editing. Olugbenga Akinade: supervision, methodology, validation, and writing—review and editing.

**Data availability.** The study uses seeded synthetic data and the unrestricted CLRD2025 sample distributed with the open-source Chainladder project from the CAS Loss Reserve Database. The dataset archive is available at https://doi.org/10.5281/zenodo.22821051; configurations, source provenance, derived results and reproduction instructions are available at https://github.com/tollyboy88/agentic-actuarial-risk-testbed. No confidential insurer data are used.

**Code availability.** Source code version 1.0.0 is available at https://github.com/tollyboy88/agentic-actuarial-risk-testbed under the MIT License.

**AI-use disclosure.** OpenAI Codex was used to assist with software implementation, literature discovery, language editing, and preparation of submission files. The author remains responsible for verifying the analysis, references, and final text and for all claims in the submitted work.

This manuscript cites Figure 1 for the complete architecture; Figures 2–7 for propagation, detection, public-data validation, sensitivity, ablation and ranking stability; and Tables 1–7 for the corresponding definitions and numerical results.

## References

Amodei, D., Olah, C., Steinhardt, J., Christiano, P., Schulman, J., & Mané, D. (2016). Concrete problems in AI safety. arXiv. https://doi.org/10.48550/arXiv.1606.06565

Basel Committee on Banking Supervision. (2021). Revisions to the principles for the sound management of operational risk. Bank for International Settlements. https://www.bis.org/bcbs/publ/d515.htm

Böcker, K., & Klüppelberg, C. (2005). Operational VaR: A closed-form approximation. Risk, 18(12), 90–93.

Bornhuetter, R. L., & Ferguson, R. E. (1972). The actuary and IBNR. Proceedings of the Casualty Actuarial Society, 59, 181–195.

Casualty Actuarial Society. (n.d.). CAS Loss Reserve Database (NAIC loss reserving data). https://www.casact.org/publications-research/research/downloadable-programs-spreadsheets-and-workbooks

Chainladder contributors. (2026). Sample datasets: clrd2025. Chainladder-Python documentation. https://chainladder-python.readthedocs.io/main/library/sample_data.html

Debenedetti, E., Zhang, J., Balunović, M., Beurer-Kellner, L., Fischer, M., & Tramèr, F. (2024). AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents. Advances in Neural Information Processing Systems, 37. https://doi.org/10.52202/079017-2636

EIOPA. (2015). Guidelines on own risk and solvency assessment. European Insurance and Occupational Pensions Authority. https://www.eiopa.europa.eu/publications/guidelines-own-risk-and-solvency-assessment_en

Embrechts, P., Klüppelberg, C., & Mikosch, T. (1997). Modelling extremal events for insurance and finance. Springer. https://doi.org/10.1007/978-3-642-33483-2

Embrechts, P., McNeil, A. J., & Straumann, D. (2002). Correlation and dependence in risk management: Properties and pitfalls. In M. A. H. Dempster (Ed.), Risk management: Value at risk and beyond (pp. 176–223). Cambridge University Press. https://doi.org/10.1017/CBO9780511615337.008

England, P. D., & Verrall, R. J. (2002). Stochastic claims reserving in general insurance. British Actuarial Journal, 8(3), 443–518. https://doi.org/10.1017/S1357321700003809

European Union. (2024). Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence. Official Journal of the European Union. http://data.europa.eu/eli/reg/2024/1689/oj

Feng, Y., & Li, S. (2024). Advancing the use of deep learning in loss reserving: A generalized DeepTriangle approach. Risks, 12(1), 4. https://doi.org/10.3390/risks12010004

Gabrielli, A., Richman, R., & Wüthrich, M. V. (2020). Neural network embedding of the over-dispersed Poisson reserving model. Scandinavian Actuarial Journal, 2020(1), 1–29. https://doi.org/10.1080/03461238.2019.1633394

Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., & Crawford, K. (2021). Datasheets for datasets. Communications of the ACM, 64(12), 86–92. https://doi.org/10.1145/3458723

ISO. (2023). ISO/IEC 42001:2023 Information technology—Artificial intelligence—Management system. International Organization for Standardization. https://www.iso.org/standard/81230.html

Kuo, K. (2019). DeepTriangle: A deep learning approach to loss reserving. Risks, 7(3), 97. https://doi.org/10.3390/risks7030097

Liu, X., Yu, H., Zhang, H., Xu, Y., Lei, X., Lai, H., Gu, Y., Ding, H., Men, K., Yang, K., Zhang, S., Deng, X., Zeng, A., Du, Z., Zhang, C., Shen, S., Zhang, T., Su, Y., Sun, H., Huang, M., Dong, Y., & Tang, J. (2024). AgentBench: Evaluating LLMs as agents. International Conference on Learning Representations. https://openreview.net/forum?id=zAdUB0aCTQ

Mack, T. (1993). Distribution-free calculation of the standard error of chain ladder reserve estimates. ASTIN Bulletin, 23(2), 213–225. https://doi.org/10.2143/AST.23.2.2005092

McNeil, A. J., Frey, R., & Embrechts, P. (2015). Quantitative risk management: Concepts, techniques and tools (2nd ed.). Princeton University Press.

Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). Model cards for model reporting. Proceedings of the Conference on Fairness, Accountability, and Transparency, 220–229. https://doi.org/10.1145/3287560.3287596

Moscadelli, M. (2004). The modelling of operational risk: Experience with the analysis of the data collected by the Basel Committee. Banca d'Italia Temi di Discussione No. 517. https://doi.org/10.2139/ssrn.557214

NIST. (2023). Artificial Intelligence Risk Management Framework (AI RMF 1.0) (NIST AI 100-1). National Institute of Standards and Technology. https://doi.org/10.6028/NIST.AI.100-1

NIST. (2024). Artificial Intelligence Risk Management Framework: Generative Artificial Intelligence Profile (NIST AI 600-1). National Institute of Standards and Technology. doi:10.6028/NIST.AI.600-1

OWASP Foundation. (2025). OWASP Top 10 for LLM applications 2025. Available at: genai.owasp.org/llm-top-10/

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology. https://doi.org/10.1145/3586183.3606763

Prudential Regulation Authority. (2023). Model risk management principles for banks (Supervisory Statement SS1/23). Bank of England. https://www.bankofengland.co.uk/prudential-regulation/publication/2023/may/model-risk-management-principles-for-banks-supervisory-statement

Qin, Y., Liang, S., Ye, Y., Zhu, K., Yan, L., Lu, Y., Lin, Y., Cong, X., Tang, X., Qian, B., Zhao, S., Tian, R., Xie, R., Zhou, J., Gerstein, M., Li, D., Liu, Z., & Sun, M. (2024). ToolLLM: Facilitating large language models to master 16000+ real-world APIs. International Conference on Learning Representations. https://openreview.net/forum?id=dHng2O0Jjr

Raji, I. D., Smart, A., White, R. N., Mitchell, M., Gebru, T., Hutchinson, B., Smith-Loud, J., Theron, D., & Barnes, P. (2020). Closing the AI accountability gap: Defining an end-to-end framework for internal algorithmic auditing. Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency, 33–44. https://doi.org/10.1145/3351095.3372873

Sambasivan, N., Kapania, S., Highfill, H., Akrong, D., Paritosh, P., & Aroyo, L. M. (2021). “Everyone wants to do the model work, not the data work”: Data cascades in high-stakes AI. Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems. https://doi.org/10.1145/3411764.3445518

Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F., & Dennison, D. (2015). Hidden technical debt in machine learning systems. Advances in Neural Information Processing Systems, 28.

Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., & Yao, S. (2023). Reflexion: Language agents with verbal reinforcement learning. Advances in Neural Information Processing Systems, 36, 8634–8652.

Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. (2023). AutoGen: Enabling next-gen LLM applications via multi-agent conversation. arXiv. https://doi.org/10.48550/arXiv.2308.08155

Wüthrich, M. V., & Merz, M. (2008). Stochastic claims reserving methods in insurance. Wiley. https://doi.org/10.1002/9780470723834

Xi, Z., Chen, W., Guo, X., He, W., Ding, Y., Hong, B., Zhang, M., Wang, J., Jin, S., Zhou, E., Zheng, R., Fan, X., Wang, X., Xiong, L., Zhou, Y., Wang, W., Jiang, C., Zou, Y., Liu, X., Yin, Z., Dou, S., Weng, R., Cheng, W., Zhang, Q., Qin, W., Zheng, Y., Qiu, X., Huang, X., & Gui, T. (2023). The rise and potential of large language model based agents: A survey. arXiv. https://doi.org/10.48550/arXiv.2309.07864

Yao, S., Shinn, N., Razavi, P., & Narasimhan, K. (2024). τ-bench: A benchmark for tool-agent-user interaction in real-world domains. arXiv. https://doi.org/10.48550/arXiv.2406.12045

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. International Conference on Learning Representations. https://openreview.net/forum?id=WE_vluYUL-X
