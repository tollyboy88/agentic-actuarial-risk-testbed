# Bayesian multistate modelling of error propagation and control placement in automated actuarial workflows

## Abstract

Automated actuarial workflows create a statistical control problem because errors may persist, be recovered, or terminate execution at successive stages. We develop a hierarchical Bayesian multistate model with clean, active-error, recovered, and hard-failure states, coupled to a Markov-additive model for the magnitude of surviving paired actuarial error. A conjugate Dirichlet hierarchy partially pools sparse stage–fault–control transition cells, while Student-t posterior predictions describe log-error increments. The terminal state distribution follows a matrix recursion, and posterior risk is used to choose stage controls under a budget constraint. In a known-parameter study, nominal 90% and 95% intervals achieved 92.5% and 96.9% coverage. In held-out synthetic insurer worlds, the hierarchical transition model reduced mean negative log score from 1.076 to 0.360 and Brier score from 0.652 to 0.195 relative to a global pooled baseline. Analytic and Monte Carlo terminal probabilities agreed within 0.0007. Exhaustive enumeration of 64 placements selected alternating validation at stages 2, 4, and 6 under the illustrative three-control budget, reducing estimated silent-error persistence to 0.0047. A public CLRD2025 case study illustrates downstream reserving consequences but is not used to infer production agent-failure rates. The framework replaces a fixed-topology comparison with uncertainty-aware estimation and a reproducible actuarial decision problem.

**Keywords:** Bayesian multistate model; Markov-additive process; actuarial workflow; silent failure; control optimisation

## 1. Introduction

Actuarial work is increasingly assembled as a sequence of data ingestion, reconciliation, segmentation, modelling, judgement and reporting tasks. When software agents or agentic-style automation coordinate these tasks, a local fault can persist through several stages, be detected and recovered, or produce an apparently valid but materially wrong result. Classical reserving research quantifies prediction uncertainty in claims estimates (Mack 1993; England and Verrall 2002; Wüthrich and Merz 2008), but it does not by itself estimate the probability that a workflow fault survives successive controls. Operational-risk models aggregate event frequency and severity (Böcker and Klüppelberg 2005; McNeil, Frey, and Embrechts 2015), but commonly begin after a loss event has already been defined.

The related software testbed supplies controlled fault injection, paired clean counterfactuals, stage snapshots and recovery logs (Adetola and Akinade 2026). Its original control probabilities were scenario inputs. That design is useful for controlled experiments, but it does not quantify parameter uncertainty and can make a preferred control architecture partly reflect the probabilities assigned by the modeller. The present paper therefore asks a different question: can transition and propagation quantities be estimated from trajectory evidence, and can the resulting posterior distribution support tail-risk-aware control placement?

We make four contributions. First, we formulate workflow execution as a four-state multistate process and estimate sparse stage–fault–control transitions with hierarchical partial pooling. Second, conditional on an active error, we model the evolution of paired actuarial error as a Markov-additive process. Third, we state a terminal-distribution recursion, establish a monotonicity result for recovery improvements, and verify the recursion against Monte Carlo simulation. Fourth, we convert control comparison into a finite Bayesian decision problem under cost and reliability constraints. The evidence consists of a known-parameter recovery study, held-out-world prediction, prior and model diagnostics, a controlled testbed application, and a public claims-reserving illustration.

The scope is deliberately bounded. The data identify behaviour in a simulated agentic-style workflow; they are not telemetry from deployed language-model agents. Public claims triangles validate downstream actuarial mechanics, not agent-error incidence. Monetary transformations are scenario functions until calibrated with firm evidence. These boundaries follow the distinction between model validation, process evidence and production measurement emphasized in model-risk and AI-governance guidance (NIST 2023; Basel Committee on Banking Supervision 2021).

## 2. Related work and methodological gap

Multistate models represent systems that move among a finite set of states and are widely used in survival, reliability and event-history analysis (Andersen et al. 1993; Jackson 2011). Markov chains provide the basic recursion for time-inhomogeneous transitions (Norris 1997), while Markov-additive processes combine a discrete state with an additive continuous component (Asmussen 2003). Reliability applications often treat failure and repair as transitions, but automated actuarial workflows add typed faults, stage-specific controls, paired financial effects and explicit replay.

Hierarchical Bayesian models stabilize sparse group estimates through partial pooling (Gelman et al. 2013; McElreath 2020). A multinomial-logit hierarchy is a natural general formulation, but a conjugate Dirichlet-multinomial hierarchy has practical advantages for a first auditable implementation: posterior distributions are exact conditional on the hierarchy, cell behaviour is transparent, and simulation recovery is inexpensive. The limitation is that additive covariate effects and interaction coefficients are not separately identified. We therefore treat the conjugate hierarchy as the estimable baseline and reserve a fully parameterized multinomial-logit extension for larger production datasets.

Posterior predictive checking and held-out scoring are central because parameter recovery alone does not establish predictive usefulness (Gelman et al. 2013). Proper log and Brier scores assess probabilistic forecasts (Gneiting and Raftery 2007). Simulation-based calibration and known-parameter experiments help detect biased computation or intervals with poor coverage (Talts et al. 2018). When likelihood-based models are fitted by general Bayesian computation, Hamiltonian Monte Carlo and diagnostics such as effective sample size and divergent transitions become important (Betancourt 2017; Carpenter et al. 2017). The conjugate model used here avoids sampler convergence error, allowing attention to focus on data construction and calibration.

Agent-system research evaluates tool use, planning and adversarial interaction (Yao et al. 2023; Liu et al. 2024; Debenedetti et al. 2024). These benchmarks expose realistic failure surfaces but do not preserve actuarial ground truth or map a trajectory to a reserve error. Systems research likewise shows how data cascades and hidden technical debt can propagate local problems (Sculley et al. 2015; Sambasivan et al. 2021). Audit frameworks call for traceable evidence across the lifecycle (Raji et al. 2020). The methodological gap is therefore not another agent score, but a probability model that connects auditable workflow states, error magnitude and a control decision.

## 3. Probabilistic model

### 3.1 State process and observability

For stages s = 1,…,S, define Zₛ in {C,E,R,H}: C denotes a clean state; E an active material error; R a detected and recovered state; and H a hard execution failure. In the controlled experiment, states are observable because the clean path, injection stage, detection event, recovery event and paired output are recorded. In production use, imperfect state observation would require a hidden Markov or state-space extension.

A terminal silent failure occurs when Zₛ = E at the final stage and the absolute paired final error exceeds a materiality threshold q. If M denotes that event, then P(silent) = Pr(Zₛ=E)Pr(M | Zₛ=E). The threshold is an actuarial decision parameter; q=1% is used for the application and is varied in sensitivity analysis.

### 3.2 Hierarchical transition estimator

Let n_{g,j} be the number of transitions from a given previous state to destination j in cell g=(stage, fault class, control architecture). For each previous state h, a global transition vector p_h is estimated from all observations. Cell probabilities satisfy

θ(g,h) ~ Dirichlet(κpₕ). (1)

(n(g,C), n(g,E), n(g,R), n(g,H)) | θ(g,h) ~ Multinomial(n(g), θ(g,h)). (2)

The posterior is Dirichlet(κ p_h+n_g). The concentration κ controls pooling. Weak, sceptical and benchmark-informed alternatives are checked. Empty cells revert to the corresponding global distribution rather than receiving an unstable zero-frequency estimate. This hierarchy estimates transition probabilities from trajectories; it does not treat the simulator's configured detection probabilities as observed production truth.

### 3.3 Markov-additive error magnitude

Let Δₛ be the difference between the treatment and same-world clean estimate. Define Yₛ=log(|Δₛ|+ε), where ε prevents an undefined log at zero. For transitions that remain in E,

Yₛ₊₁ = Yₛ + μ(g) + eₛ. (3)

where μ_g is a stage–fault–control increment and e_s follows a Student-t posterior predictive distribution. A normal-inverse-gamma prior produces a conjugate Student-t posterior for μ_g and a heavier-tailed predictive distribution. Recovery moves the state to R and terminates active propagation; a hurdle at zero is represented by the state process rather than by forcing zeros into the magnitude likelihood.

### 3.4 Terminal loss

For a posterior draw, a state path is simulated, active increments are accumulated, and terminal paired error is mapped through an explicit economic function ℓ(Δₛ,a), where a contains conversion and remediation assumptions. The posterior predictive loss L therefore includes process variation and parameter uncertainty. Value-at-Risk and Expected Shortfall at level u are

VaRᵤ(L)=inf{x:Pr(L≤x)≥u}; ESᵤ(L)=E[L | L≥VaRᵤ(L)]. (4)

Because public data do not identify firm-specific conversion or event frequency, absolute loss values remain scenario conditioned. The decision analysis emphasizes posterior silent-failure probability, relative risk and sensitivity.

## 4. Statistical inference and validation

The modelling table contains one row per run and stage: identifiers, topology, fault, injection stage, current stage, state before and after, detection, recovery, hard failure, paired error, lineage completeness, token cost, analyst minutes and final material failure. The fixed Paper 1 experiment contributes 6,144 stage records from 1,024 runs and eight seeded worlds.

The main transition fit uses κ=8, with posterior summaries based on 4,000 Dirichlet draws per observed cell. Markov-additive increments use a weak normal-inverse-gamma prior centred on the pooled active-error increment. The implementation writes all tables in CSV and Parquet, uses deterministic seeds and records SHA-256 hashes. No Markov chain Monte Carlo is required for the conjugate baseline.

Predictive evaluation holds out worlds 6 and 7, fits the hierarchy on the remaining six worlds, and scores all transitions in the held-out worlds. A global pooled destination distribution is the baseline. Mean negative log score and multiclass Brier score are reported; lower values are better. A separate known-parameter study generates E-state transitions for unreviewed and validator controls over 80 replications with 60 observations per cell. Bias, root mean square error, and empirical coverage of 90% and 95% intervals are calculated.

The validation design distinguishes recovery of known simulation parameters from application to the existing testbed. This separation prevents the estimator from being declared valid merely because it reconstructs probabilities embedded in the old simulation. Prior sensitivity changes κ and the increment scale. Held-out fault-cell checks deliberately remove selected fault cells so their predictions must borrow from the hierarchy. Posterior predictive checks compare destination frequencies, terminal E-state frequency and the distribution of paired terminal error.

## 5. Theoretical properties

**Proposition 1 (terminal-state recursion).** Let π₀ be the initial row distribution and Pₛ the row-stochastic transition matrix from stage s to s+1. Under the conditional Markov property, πₛ=π₀P₁…Pₛ₋₁. Consequently, P(silent)=πₛ[E]Pr(M|Zₛ=E). (5)

The proof follows by repeated application of the law of total probability. The supplementary material gives the induction explicitly and covers time-inhomogeneous matrices. In the application, analytic terminal probabilities were compared with 200,000 simulated paths; the largest absolute state-probability difference was 0.000635.

**Proposition 2 (monotonic recovery improvement).** Consider two transition systems that are identical except that, for every reachable active-error row, the improved system transfers probability mass from E to R without increasing transitions to H or back to E at later stages. Then the improved system's terminal probability of E cannot exceed the base system's terminal probability of E.

The result follows from a coupling that uses the same uniforms for both paths: every path recovered in the base system is recovered in the improved system, and additional paths may recover earlier. The ordering can fail if a control creates new errors, changes severity conditional on survival, or diverts probability from a benign state into E; those conditions are therefore part of the proposition rather than hidden assumptions.

**Proposition 3 (finite control optimum).** If the admissible catalogue contains finitely many control placements and the posterior risk-cost objective is finite for each, exhaustive enumeration returns a global minimizer. Posterior uncertainty in the selected policy can be summarized by the probability that each policy minimizes draw-specific loss and by posterior regret relative to the draw-specific optimum.

These propositions do not claim that matrix multiplication or finite enumeration is new. The contribution is their integration with estimated workflow transitions, Markov-additive actuarial error and uncertainty-aware control choice.

## 6. Control-placement decision

Let x(s,c) indicate whether control c is used at stage s, with annual cost Cost(x). The primary decision minimizes E[ES₀.₉₉₅(L|x)]+λCost(x), subject to Cost(x)≤B and Pr(P(silent|x)≤τ | data)≥1−α. (6) A constrained alternative minimizes cost subject to posterior risk limits. With six stages and one stage-validator choice, 2⁶=64 placements can be enumerated exactly.

For the reproducible demonstration, one stage validator costs 400 cost units and the budget permits three placements. Controlled stages use the estimated validator transition row; uncontrolled stages use the estimated linear row. The selected binary placement 010101 places controls after reconciliation, model execution and narrative generation. Its estimated terminal active-error persistence is 0.00468 under the application mapping. This result is not a universal staffing rule: it depends on the catalogue, costs, fault mix and state evidence. Its value is to show how those inputs lead to an auditable decision rather than a fixed topology label.

The complete Pareto frontier reports cost, terminal persistence and a tail-risk index. Designs beyond the budget remain visible so decision-makers can see the marginal risk reduction from additional controls. In larger catalogues, dynamic programming or mixed-integer optimization may replace enumeration, but exact enumeration is preferable here because it is transparent and guarantees the finite optimum.

## 7. Results

### 7.1 Parameter recovery and predictive comparison

Across the two known transition regimes, empirical coverage was 92.5% for nominal 90% intervals and 96.9% for nominal 95% intervals. Bias and RMSE were small relative to the 0.73 difference between the true E→E probabilities. Coverage above nominal reflects mildly conservative posterior intervals under the sparse-cell design; larger cell counts narrow them.

On 1,536 transitions from two held-out worlds, the hierarchical model achieved a mean negative log score of 0.360 and Brier score of 0.195. The global baseline produced 1.076 and 0.652, respectively. Partial pooling therefore added predictive information beyond the unconditional destination frequencies. The comparison is internal to the controlled testbed and does not establish performance on a production insurer.

### 7.2 Recursion and propagation

For an illustrative F1 data-fault path under the validator, the analytic final distribution across C, E, R and H was (0.0810, 0.1194, 0.7185, 0.0810). The corresponding Monte Carlo frequencies were (0.0811, 0.1192, 0.7191, 0.0806). Agreement within 0.0007 verifies the implementation of Proposition 1 at the simulation precision used.

The Markov-additive summaries show substantial heterogeneity by fault, stage and control. Sparse groups shrink toward the pooled active-error increment, while well-populated groups retain cell-specific evidence. This behaviour is important because a small number of extreme unit faults can otherwise dominate an unpooled magnitude estimate. Posterior predictive tails are therefore reported with the state frequency rather than as a single deterministic amplification factor.

### 7.3 Control placement

The budget-feasible optimum uses three validators in alternating stages, with cost 1,200 and estimated terminal active-error persistence 0.00468. The all-stage design reduces the risk index further but costs 2,400 and is infeasible under the stated budget. Several policies lie on the cost-risk frontier, demonstrating that the preferred design changes when the budget or control effectiveness changes. Fixed T1–T5 architectures remain useful comparators, but the decision variable is now placement rather than a pre-labelled architecture.

### 7.4 Actuarial application and CLRD2025

The downstream reserving illustration uses the public CLRD2025 sample across six lines. Retrospective Chain Ladder mean absolute percentage error was 6.2%, Bornhuetter–Ferguson 8.9%, and latest paid 26.3% in the testbed implementation. These differences demonstrate that the terminal economic consequence of a workflow state depends on line and reserving method. They do not estimate transition probabilities, because CLRD has no labels for agent faults or controls.

A deterministic data-quality audit also illustrates control evolution. The original extreme-increment rule detected 22.7% of injected ×1,000 unit faults. Adding a local scale-consistency check increased detection to 74.0% while preserving complete detection of duplicate, negative, development-mismatch and missing-cell injections. The remaining unit cases lacked a stable positive peer median or did not exceed the deliberately conservative 100-fold ratio. This result supports metadata and reconciliation controls rather than a claim that one anomaly threshold solves unit risk.

## 8. Discussion

The analysis changes the interpretation of control evidence in three ways. First, transition probabilities are distributions supported by trajectory counts, not fixed labels such as “validator detects 72%.” Second, uncertainty enters the terminal state and loss distribution, so a design can be judged by posterior constraint probability rather than a point estimate. Third, controls are chosen at stages under a budget rather than compared only as bundled topologies.

The held-out improvement is large because stage, fault and topology identify repeated structure absent from the global baseline. A stronger future comparison should include non-hierarchical cell estimates, multinomial logit, hidden-state variants and dynamic models. Information criteria such as leave-one-out cross-validation or WAIC are useful when full likelihood models are fitted (Vehtari, Gelman, and Gabry 2017; Watanabe 2010), but predictive scores on genuinely held-out worlds are the primary evidence here.

The conjugate hierarchy also has limitations. Global probabilities are estimated empirically rather than assigned a hyperprior, so uncertainty at the highest level is understated. The state construction treats detection followed by replay as recovery, although recovery quality may itself be uncertain. Hard failures are rare in the fixed run, making H-state estimates prior sensitive. The Markov assumption excludes path history beyond the current state and grouped covariates. A semi-Markov or hidden-state model may be necessary when dwell time, repeated interventions or latent contamination matter.

Production calibration requires trajectory logging, independent review outcomes, near misses, error materiality, control cost and exposure conversion. Governance frameworks emphasize documented assumptions, monitoring and independent challenge (NIST 2023; Prudential Regulation Authority 2023). The model can organize such evidence but cannot create it. Likewise, tail-risk measures should be embedded in a firm's approved model-risk and operational-risk process rather than treated as regulatory capital by default.

## 9. Conclusion

A multi-stage actuarial workflow can be represented as an estimable multistate process coupled to additive error magnitude. The hierarchical Bayesian model improves held-out probabilistic prediction, the known-parameter study supports interval calibration, and analytic recursion agrees with Monte Carlo simulation. Exhaustive control placement produces an auditable cost-risk frontier and a global optimum within the finite catalogue. The public reserving application demonstrates actuarial consequences without misusing CLRD as agent-failure telemetry.

The main methodological advance is the integration of partially pooled state transitions, Markov-additive paired error and posterior control choice. The next step is to replace controlled testbed trajectories with preregistered multi-model experiments and, where available, insurer workflow evidence, while retaining the same separation between observed transitions, actuarial consequences and scenario assumptions.

## Statements and declarations

**Funding.** This work received no specific grant from any funding agency, commercial or not-for-profit sectors.

**Competing interests.** The authors declare no competing interests.

**Data availability.** The study uses seeded synthetic data and the unrestricted CLRD2025 sample. The public dataset archive is https://doi.org/10.5281/zenodo.22821051. No confidential insurer data or personal information are used.

**Code availability.** Source code, fixed configurations, tests and reproduction instructions are available at https://github.com/tollyboy88/agentic-actuarial-risk-testbed.

**Author contributions.** Adebayo Aliu Adetola: conceptualisation, methodology, software, formal analysis, investigation, data curation, visualisation, writing—original draft, and writing—review and editing. Olugbenga Akinade: supervision, methodology, validation, and writing—review and editing.

**AI-use disclosure.** OpenAI Codex assisted with software implementation, literature discovery, language editing and preparation of submission files during September 2026. The authors verified the analysis, citations and final text and remain responsible for all claims.

## References

Adetola, A. A., and O. Akinade. 2026. Agentic Actuarial Testbed, version 1.0.0. GitHub. https://github.com/tollyboy88/agentic-actuarial-risk-testbed.

Amodei, D., C. Olah, J. Steinhardt, P. Christiano, J. Schulman, and D. Mané. 2016. Concrete problems in AI safety. arXiv:1606.06565. https://doi.org/10.48550/arXiv.1606.06565.

Andersen, P. K., Ø. Borgan, R. D. Gill, and N. Keiding. 1993. Statistical Models Based on Counting Processes. New York: Springer.

Asmussen, S. 2003. Applied Probability and Queues. 2nd ed. New York: Springer. https://doi.org/10.1007/b97236.

Basel Committee on Banking Supervision. 2021. Revisions to the Principles for the Sound Management of Operational Risk. Basel: Bank for International Settlements.

Betancourt, M. 2017. A conceptual introduction to Hamiltonian Monte Carlo. arXiv:1701.02434. https://doi.org/10.48550/arXiv.1701.02434.

Böcker, K., and C. Klüppelberg. 2005. Operational VaR: A closed-form approximation. Risk 18 (12): 90–93.

Carpenter, B., A. Gelman, M. D. Hoffman, D. Lee, B. Goodrich, M. Betancourt, M. Brubaker, J. Guo, P. Li, and A. Riddell. 2017. Stan: A probabilistic programming language. Journal of Statistical Software 76 (1): 1–32. https://doi.org/10.18637/jss.v076.i01.

Debenedetti, E., J. Zhang, M. Balunović, L. Beurer-Kellner, M. Fischer, and F. Tramèr. 2024. AgentDojo: A dynamic environment to evaluate prompt injection attacks and defenses for LLM agents. Advances in Neural Information Processing Systems 37.

England, P. D., and R. J. Verrall. 2002. Stochastic claims reserving in general insurance. British Actuarial Journal 8 (3): 443–518. https://doi.org/10.1017/S1357321700003809.

European Union. 2024. Regulation (EU) 2024/1689 laying down harmonised rules on artificial intelligence. Official Journal of the European Union.

Gelman, A., J. B. Carlin, H. S. Stern, D. B. Dunson, A. Vehtari, and D. B. Rubin. 2013. Bayesian Data Analysis. 3rd ed. Boca Raton, FL: CRC Press.

Gneiting, T., and A. E. Raftery. 2007. Strictly proper scoring rules, prediction, and estimation. Journal of the American Statistical Association 102 (477): 359–378. https://doi.org/10.1198/016214506000001437.

Jackson, C. H. 2011. Multi-state models for panel data: The msm package for R. Journal of Statistical Software 38 (8): 1–28. https://doi.org/10.18637/jss.v038.i08.

Liu, X., et al. 2024. AgentBench: Evaluating LLMs as agents. International Conference on Learning Representations. https://openreview.net/forum?id=zAdUB0aCTQ.

Mack, T. 1993. Distribution-free calculation of the standard error of chain ladder reserve estimates. ASTIN Bulletin 23 (2): 213–225. https://doi.org/10.2143/AST.23.2.2005092.

McElreath, R. 2020. Statistical Rethinking. 2nd ed. Boca Raton, FL: CRC Press.

McNeil, A. J., R. Frey, and P. Embrechts. 2015. Quantitative Risk Management. 2nd ed. Princeton, NJ: Princeton University Press.

NIST. 2023. Artificial Intelligence Risk Management Framework (AI RMF 1.0). NIST AI 100-1. https://doi.org/10.6028/NIST.AI.100-1.

Norris, J. R. 1997. Markov Chains. Cambridge: Cambridge University Press. https://doi.org/10.1017/CBO9780511810633.

Prudential Regulation Authority. 2023. Model Risk Management Principles for Banks. Supervisory Statement SS1/23. London: Bank of England.

Raji, I. D., A. Smart, R. N. White, M. Mitchell, T. Gebru, B. Hutchinson, J. Smith-Loud, D. Theron, and P. Barnes. 2020. Closing the AI accountability gap. Proceedings of the 2020 Conference on Fairness, Accountability, and Transparency, 33–44. https://doi.org/10.1145/3351095.3372873.

Sambasivan, N., S. Kapania, H. Highfill, D. Akrong, P. Paritosh, and L. M. Aroyo. 2021. Everyone wants to do the model work, not the data work: Data cascades in high-stakes AI. Proceedings of CHI 2021. https://doi.org/10.1145/3411764.3445518.

Sculley, D., G. Holt, D. Golovin, E. Davydov, T. Phillips, D. Ebner, V. Chaudhary, M. Young, J.-F. Crespo, and D. Dennison. 2015. Hidden technical debt in machine learning systems. Advances in Neural Information Processing Systems 28.

Talts, S., M. Betancourt, D. Simpson, A. Vehtari, and A. Gelman. 2018. Validating Bayesian inference algorithms with simulation-based calibration. arXiv:1804.06788. https://doi.org/10.48550/arXiv.1804.06788.

Vehtari, A., A. Gelman, and J. Gabry. 2017. Practical Bayesian model evaluation using leave-one-out cross-validation and WAIC. Statistics and Computing 27: 1413–1432. https://doi.org/10.1007/s11222-016-9696-4.

Watanabe, S. 2010. Asymptotic equivalence of Bayes cross validation and widely applicable information criterion. Journal of Machine Learning Research 11: 3571–3594.

Wüthrich, M. V., and M. Merz. 2008. Stochastic Claims Reserving Methods in Insurance. Chichester: Wiley. https://doi.org/10.1002/9780470723834.

Yao, S., J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao. 2023. ReAct: Synergizing reasoning and acting in language models. International Conference on Learning Representations. https://openreview.net/forum?id=WE_vluYUL-X.
