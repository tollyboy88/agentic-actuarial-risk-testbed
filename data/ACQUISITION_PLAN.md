# AAT open-data acquisition and readiness plan

**Status:** completed 1 September 2026. Simulation remains paused pending acceptance of the revised, data-feasible scope.

## Research rule

The study must be reproducible using public, ungated data. A source that requires a paid
subscription, institutional membership, account approval, or acceptance of gated terms is not a
required dependency. Such sources may be cited as unavailable evidence and assigned to future
work, but their absence must not be hidden or replaced by invented calibration.

## Required evidence and source decisions

| Evidence requirement | Primary open source | Open substitute / triangulation | Decision |
|---|---|---|---|
| Known-ground-truth claim generation | SynthETIC; SPLICE | SimulationMachine; independently specified Python DGP | Acquire all three open repositories. Use at least two generators for robustness. |
| Realistic reserving triangles | chainladder samples; CAS CLRD | CRAN ChainLadder/raw data | Retain current core data and acquire source repositories for provenance. |
| Pricing robustness arm | CASdatasets | ActuarialDataScience | Acquire, but keep outside the first reserving-paper critical path. |
| Operational-loss modelling examples | CRAN OpVaR, evir, evd, ReIns, copula | Public fire/reinsurance severity data | Acquire source repositories and convert every R object to CSV/Parquet. |
| Operational-event frequency calibration | BCBS Loss Data Collection Exercise aggregates | Transparent scenario ranges if a table cannot be extracted | Acquire public BCBS documents and extract auditable tables. |
| Capital scale and insurer context | EIOPA insurance statistics | Published aggregate SCR distributions | Acquire public CSV/XLSX series. Do not use confidential firm data. |
| AI risk taxonomy | MIT AI Risk Repository; MITRE ATLAS; AVID | OWASP LLM Top 10 | Acquire current open versions and preserve versions. |
| Agentic failure taxonomy and traces | MAST/MAD; Who&When | AgentRx | Acquire MAST-Data (ungated), repositories, and AgentRx only if it becomes ungated. |
| Pass/fail trajectory denominators | tau-bench; tau2-bench; AgentDojo | Public benchmark result files | Acquire repositories and published result artifacts. Do not estimate failure rates from failure-only datasets. |
| Tool-use risk | ToolEmu; AgentBench; ASB | InjecAgent | Acquire all open repositories; use only datasets with clear task denominators. |
| Prompt-injection attacks | AgentDojo; InjecAgent; jailbreak_llms | deepset prompt-injections; AgentHarm public split | Acquire all ungated sources and record model/version context for success-rate estimates. |
| AI incident base rates | AI Incident Database; AVID | VCDB; butterflylabs mirror | Acquire public snapshots. Treat incident databases as taxonomy evidence unless exposure denominators exist. |
| Governance | latest IMDA agentic framework; NIST AI RMF/GenAI profile | UK/PRA publications identified during literature review | Acquire current primary documents; retain publication dates and versions. |
| Granular insurer operational losses | ORX/SAS/Advisen | BCBS aggregates plus simulated losses and scenario analysis | Paid/restricted sources excluded; disclose as a limitation and future validation opportunity. |
| TRAIL and GAIA gated datasets | PatronusAI/TRAIL; GAIA | MAST/MAD, Who&When, tau/AgentDojo, AgentRx if open | Do not require or download gated data. Record as future external validation. |

## Required deliverables before simulation

1. `raw/` source snapshots with source URL and immutable revision/date.
2. `processed/` Python-readable CSV or Parquet copies, never overwriting raw sources.
3. `manifests/source_manifest.csv` with licence, version, checksum, size and acquisition result.
4. `manifests/data_object_manifest.csv` with row counts, columns, missingness and conversion status. **Completed: 421 objects, zero failures.**
5. `DATA_READINESS_REPORT.md` with methodological fitness and explicit exclusions.
6. A final go/no-go decision for each proposal research question.
