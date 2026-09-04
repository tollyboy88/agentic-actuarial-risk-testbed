# Independent open-data gap register

**Gate date:** 1 September 2026  
**Rule:** no paid, login-gated, approval-gated, confidential, or firm-proprietary data may be a required input.

This register separates gaps that were fixed from quantities that cannot be identified
with open data. The latter must not be presented as empirically estimated facts.

| Requirement | Resolution | Decision for the study |
|---|---|---|
| Known reserving ground truth | Acquired SynthETIC, SPLICE, and SimulationMachine source snapshots, plus their package test data. | **Resolved.** Use at least two generators to test robustness. |
| Real reserving/pricing benchmarks | Acquired ChainLadder, CAS Schedule P, CASdatasets, insuranceData, reservetestr, and DeepTriangle sources. | **Resolved.** Use as realism/external-behaviour checks, not as known-truth worlds. |
| Full agent failure traces | Acquired 1,642-record MAST/MAD corpus, 19-record human-labelled subset, repository traces, Who&When, tau/tau2, ToolEmu, AgentBench and ASB. | **Resolved for taxonomy and trace patterns.** Failure-enriched corpora do not identify real-world occurrence rates. |
| Prompt-injection evidence | Acquired AgentDojo run artifacts, InjecAgent, jailbreak collections, prompt-injection classification data, AgentHarm and OWASP definitions. | **Resolved.** Priors are benchmark-conditional and must be re-estimated in the actuarial testbed. |
| AI incident evidence | Acquired dated AIID export/snapshot, 6,865-record open mirror, VCDB, AVID, MIT AI Risk Repository and MITRE ATLAS. | **Resolved for taxonomy/triangulation.** Reporting and selection bias prevent population-rate estimation. |
| Open operational-risk observations | Acquired Basel 2002/2008 LDCE reports, AMA range-of-practice report, supervisory papers and 7,926 OpVaR package loss observations. | **Resolved for method and broad calibration bounds.** Public data do not contain granular insurer agentic-AI loss events. |
| Solvency-II scale/context | Acquired annual and quarterly EIOPA own-funds, balance-sheet and premium/claim/expense tables. | **Resolved for scale and contextual comparisons.** These are aggregates, not agentic loss data. |
| Dead regulator URLs | Replaced obsolete BIS links with live official publications; verified IMDA framework as Version 1.5, updated 5 June 2026. | **Resolved.** |
| R-only formats | Converted 373 objects directly; recorded 112 byte-identical duplicates; recovered all residual sources with native R 4.6.1, Arrow and `sp`; verified ten residual tabular Parquet outputs. | **Resolved.** Non-tabular package internals are preserved as base-R text rather than misrepresented as tables. |
| Gated TRAIL, GAIA and AgentRx data | Access requires authentication/terms approval; they are not necessary after acquiring MAST/MAD, Who&When, tau2 and AgentDojo. | **Excluded from dependencies.** Optional future external validation only. |
| Paid ORX, SAS OpRisk Global and Advisen losses | No legitimate open substitute provides granular, firm-level loss events with exposure denominators. | **Irreducible.** Do not claim empirical industry loss frequency or monetary severity. Future work with a regulated data partnership. |
| Actual insurer control placement | IMDA provides examples, not a representative firm-level control-placement dataset. | **Irreducible.** Replace the “firms actually place controls” comparison with optimisation plus comparison to public guidance. Survey/field study becomes future work. |
| Human-error loss reduction caused by automation | Open reserving benchmarks measure model error, not matched human operational-loss frequency/severity before and after automation. | **Irreducible.** Remove the net-human-error capital conclusion. Treat assumed offsets only as clearly labelled sensitivity analysis, or defer entirely. |
| Cross-firm common-model loss correlation | No open panel links foundation-model versions, firm exposures and contemporaneous operational losses. | **Irreducible.** Use common-shock and copula stress scenarios; do not estimate an empirical sector correlation coefficient. |
| A firm's existing scenario-based op-risk assessment | Firm ORSA scenarios and internal capital models are confidential. | **Irreducible.** Do not claim comparison with a representative firm's existing charge. Permit a user-supplied case study later, outside the independent core study. |
| Analyst-minute/control implementation costs | Token and compute cost can be measured; representative actuarial staff time and implementation cost cannot be inferred from open traces. | **Partly identifiable.** Optimise over measured compute cost and disclosed staff-cost sensitivity ranges. A time-and-motion study is future work. |
| Raw-data redistribution rights | Most primary sources declare open licences. Who&When and four Git repositories have no clear root/data licence. | **Publication constraint.** Do not redistribute unclear-licence raw files; cite their source and publish only derived statistics/code. Use CC-BY MAST/MAD as the primary trace dataset. |

## Claims that must be dropped or narrowed

1. Drop a universal or industry-estimated “agentic AI operational-risk capital charge.”
   Report a **scenario-conditioned capital estimate for the simulated insurer**, with all
   exposure and frequency assumptions disclosed.
2. Drop the claim that optimal controls differ from where firms actually place controls.
   The open study can compare the optimum with public governance recommendations and
   named case examples, not a population of firms.
3. Drop a conclusion that automation has positive or negative *net* capital after human
   error is removed. This requires matched human/agent production loss data.
4. Recast common-model correlation as a **sector stress test** over dependence and
   common-shock assumptions, not an empirically fitted market parameter.
5. Keep gated and paid data only in future work; none may be needed to reproduce the
   independent core results.

