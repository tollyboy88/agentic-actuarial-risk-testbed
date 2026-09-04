# TOPIC 2 — Agentic AI in the actuarial control cycle: error propagation and operational risk capital

**Working title:** *When the model runs itself: quantifying error propagation and operational risk capital for agentic artificial intelligence in actuarial workflows*

**Attacks gap:** G2 · **Simulation required: YES — load-bearing**

### 2.1 The practitioner problem

The 2026 deployment pattern is no longer "actuary prompts a chatbot." It is a chained, tool-using pipeline: an agent ingests a bordereau, another cleans and reconciles it, another fits and selects a model, another drafts the commentary, another writes it into the reporting pack. Each hand-off is an unmonitored joint. A small classification error at stage 1 becomes a materially wrong reserve at stage 5, and because every intermediate artefact looks plausible, nobody notices.

Insurers must hold capital for operational risk and must describe their risk profile in the ORSA. There is no accepted method for doing this for agentic systems.

### 2.2 What exists, and what is missing

BAJ has nothing on agentic systems at all. Outside BAJ, the Society of Actuaries opened a 2026 research call on *Agentic AI for Actuarial Workflows*, and there is a small arXiv literature on multi-agent risk taxonomies, silent-failure detection in agent trajectories, and runtime uncertainty monitoring using Bayesian networks. Singapore's IMDA published the first agentic-AI governance framework in January 2026. All of this is either governance-qualitative or ML-technical.

**The gap:** nobody has connected agentic failure modes to an **operational risk loss distribution** and hence to a **capital and ORSA** consequence under the UK regime. That connection is precisely BAJ's territory and precisely nobody else's.

### 2.3 Research questions

**RQ1 (primary).** How does error introduced at one stage of an agentic actuarial pipeline propagate to the final actuarial output, and what does the resulting loss distribution imply for operational risk capital and ORSA disclosure?

- **RQ2.1 — Amplification.** Is error amplified, attenuated or transformed at each hand-off? Is there a measurable "amplification factor" per stage archetype (ingest / clean / model / select / narrate)?
- **RQ2.2 — Topology.** Do pipeline topologies differ materially in robustness — linear chain vs supervisor-and-workers vs debate/critic vs blackboard — at equal capability and equal cost?
- **RQ2.3 — Detectability.** At which stage is an injected error cheapest to detect, and does the cheapest detection point coincide with where firms actually place their controls? (Hypothesis: it does not.)
- **RQ2.4 — Autonomy dose-response.** As human-in-the-loop checkpoints are removed one at a time, how does the tail of the output-error distribution behave — smoothly, or with a threshold effect?
- **RQ2.5 — Capital.** Fitting a frequency–severity model to simulated agentic failures, what operational risk capital charge results, and how does it compare with a firm's existing scenario-based op-risk assessment? Is the marginal capital impact of automation positive or negative once the reduction in *human* error is netted off?
- **RQ2.6 — Correlation and systemic risk.** If many firms adopt the same foundation model and the same agent framework, are their operational losses correlated? What does that do to the sector-level tail, and is it a matter for the PRA and the Bank's macroprudential AI work?

RQ2.6 is the ambitious one and the one that will get the paper discussed at a sessional meeting.

### 2.4 Contribution claim

The first quantitative bridge from agentic-AI failure modes to an actuarial capital number, comprising: a **fault taxonomy for agentic actuarial pipelines**, a **fault-injection testbed**, an estimated **operational risk loss distribution**, a **control-placement optimisation**, and drafted **ORSA disclosure language**.

### 2.5 Data

Open reserving data (`chainladder` sample triangles, Schedule P style, or the IFoA/ABI public aggregates), plus a synthetic bordereau generator you control (necessary — you need known ground truth to measure error). Open motor datasets for the pricing variant.

### 2.6 Architecture — the Agentic Actuarial Testbed (AAT)

```
╔══════════════════════════════════════════════════════════════════════╗
║ A. GROUND-TRUTH WORLD                                                ║
║   Synthetic insurer: policy file, exposure, claim transactions with   ║
║   KNOWN generating process → therefore a KNOWN true ultimate.         ║
║   Emit: raw bordereaux with realistic defects (dupes, currency mix,   ║
║   late notifications, coding drift, reopened claims, unit errors).    ║
║   Seeded; N = 500 independent worlds.                                 ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
╔══════════════════════════════════════════════════════════════════════╗
║ B. AGENT PIPELINE (the system under test)                            ║
║                                                                       ║
║   S1 INGEST     → parse & schema-map bordereau                       ║
║   S2 RECONCILE  → dedupe, currency, dates, exposure alignment        ║
║   S3 SEGMENT    → assign claims to reserving classes                 ║
║   S4 MODEL      → fit development pattern, select method             ║
║   S5 SELECT     → choose ultimate, apply judgement/blend             ║
║   S6 NARRATE    → produce reserve commentary + uncertainty statement ║
║                                                                       ║
║   Each stage = {LLM planner + typed tools + output schema}.           ║
║   Tools are REAL and deterministic: pandas ops, chainladder fits,     ║
║   validators. The LLM decides; the tool computes. (This mirrors       ║
║   how firms actually build, and isolates reasoning error from         ║
║   arithmetic error.)                                                  ║
║                                                                       ║
║   Topologies to compare:                                              ║
║     T1 linear chain (no oversight)                                    ║
║     T2 chain + per-stage validator agent                              ║
║     T3 supervisor/orchestrator + specialist workers                   ║
║     T4 critic-debate at S4/S5                                         ║
║     T5 human checkpoint at k stages, k ∈ {0,1,2,3}                    ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
╔══════════════════════════════════════════════════════════════════════╗
║ C. FAULT INJECTION ENGINE                                            ║
║   Inject one fault at a chosen stage, drawn from the taxonomy:        ║
║     F1 data      : silent unit change, truncated field, encoding      ║
║     F2 semantic  : misclassified peril / class of business            ║
║     F3 tool      : wrong tool selected, right tool wrong args         ║
║     F4 reasoning : plausible but wrong development factor judgement   ║
║     F5 hand-off  : schema drift, field silently dropped               ║
║     F6 context   : stale document retrieved, wrong period             ║
║     F7 adversarial: prompt injection inside a claim description       ║
║   Design: full factorial {7 fault types × 6 stages × 5 topologies}    ║
║           × 500 worlds, plus a no-fault control arm.                  ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
╔══════════════════════════════════════════════════════════════════════╗
║ D. MEASUREMENT                                                       ║
║   Per run capture:                                                    ║
║    · reserve_error = (ultimate_hat − ultimate_true)/ultimate_true     ║
║    · stage_of_first_deviation, stage_of_detection (if any)            ║
║    · amplification_k = |err_out(stage k)| / |err_in(stage k)|         ║
║    · detected? by whom? cost of detection (tokens, £, analyst-mins)   ║
║    · silent vs hard failure                                           ║
║    · full agent trajectory persisted for post-hoc analysis            ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
╔══════════════════════════════════════════════════════════════════════╗
║ E. ACTUARIAL AGGREGATION  ← the part only an actuary would write     ║
║   1. Frequency: fit Poisson / negative binomial to fault occurrence   ║
║      rates (calibrated to published op-risk event frequencies and     ║
║      to observed detection rates from D).                             ║
║   2. Severity: empirical distribution of |reserve_error| × exposure,  ║
║      with a fitted tail (GPD above threshold).                        ║
║   3. Aggregate: Monte Carlo compound distribution → VaR 99.5%.        ║
║   4. Dependence: copula across fault types and across firms sharing   ║
║      a common foundation model → sector-level tail (RQ2.6).           ║
║   5. Net position: subtract the modelled reduction in human-error     ║
║      losses from automation → MARGINAL capital impact.                ║
║   6. Control optimisation: knapsack over control placements —         ║
║      minimise capital + control cost subject to a residual-risk cap.  ║
╚══════════════════════════════════════════════════════════════════════╝
                              │
╔══════════════════════════════════════════════════════════════════════╗
║ F. PAPER OUTPUTS                                                     ║
║   Fig 1 amplification factor by stage (the headline chart)           ║
║   Fig 2 error distribution by topology — violin, log scale           ║
║   Fig 3 detection probability × cost heatmap by (fault, stage)       ║
║   Fig 4 autonomy dose–response: VaR99.5 vs number of human           ║
║         checkpoints removed                                          ║
║   Fig 5 sector tail under common-model correlation, ρ ∈ {0,.3,.6,.9} ║
║   Tab 1 agentic fault taxonomy for actuarial pipelines               ║
║   Tab 2 optimal control placement                                    ║
║   App  drafted ORSA disclosure paragraphs                            ║
╚══════════════════════════════════════════════════════════════════════╝
```

**Cost control.** The full factorial is large. Use a **screening design first** (Plackett–Burman or a fractional factorial) to find the 8–10 (fault, stage, topology) cells that matter, then run those at full replication. Cache aggressively; use a small open-weight model for the bulk runs and a frontier model for a validation subset, and report the sensitivity. Realistically £400–£900 of inference.

**Stack.** `langgraph` or a hand-rolled typed state machine (I would hand-roll it — it makes the paper's method section far clearer and removes a framework dependency reviewers can't inspect) · `pydantic` schemas at every hand-off · `chainladder-python` · `scipy`/`copulas` for Section E · `sqlite` trajectory store.

### 2.7 Context engineering specification

- **Typed hand-offs.** Every inter-agent message is a Pydantic model with explicit units and provenance fields. A schema violation is a *hard* failure and must be recorded as such — this lets you show that schema discipline converts silent failures into hard ones, which is itself a finding worth a paragraph in the recommendations.
- **Bounded context per stage.** Each agent sees only its input artefact plus a stage-specific instruction — never the whole conversation history. Measure the effect of relaxing this (the "context contamination" arm).
- **Tool-first arithmetic.** No agent is permitted to compute a number in prose. All arithmetic goes through a tool. This is both good engineering and a recommendation the paper can make to the profession.
- **Provenance chain.** Every field in the final reserve pack carries a lineage pointer back to a raw bordereau row. The paper can then report *lineage completeness* as a control metric.
- **Adversarial arm (F7).** Claim free-text fields containing injected instructions — realistic, since claim narratives are customer-supplied. Almost nobody in the actuarial literature has considered this.

---