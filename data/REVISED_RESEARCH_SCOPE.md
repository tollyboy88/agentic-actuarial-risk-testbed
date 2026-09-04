# Data-feasible research scope

This is the scope that the acquired independent, open data can support without
overclaiming.

## Confirmatory questions

- **Primary:** In a reproducible synthetic actuarial workflow with known truth, how do
  injected agentic faults propagate to reserve error, and what scenario-conditioned
  annual loss and 99.5% VaR follow under explicitly stated deployment exposure?
- **Amplification:** How do fault type and pipeline stage amplify, attenuate or transform
  error?
- **Topology:** How do linear, validator, supervisor and critic topologies differ at
  controlled model capability and compute budget?
- **Detection/control:** Which observable controls detect each fault earliest and most
  cost-effectively, and which placements minimise residual simulated loss plus control
  cost?
- **Autonomy:** How does removal of human checkpoints change the body and tail of the
  simulated output-error distribution?
- **Capital sensitivity:** How sensitive is scenario-conditioned capital to occurrence
  rate, deployment volume, tail threshold, severity mapping and detection effectiveness?
- **Systemic stress:** How does the sector tail respond to prescribed dependence and
  common-model/common-shock scenarios?

## Exploratory analyses only

- Compare experimental failure/detection rates with tau2, AgentDojo, MAST and related
  benchmark ranges. These are transferability checks, not production-rate estimates.
- Compare optimal controls with IMDA/NIST/OWASP recommendations and published case
  examples. This is not a representative survey of insurers.
- Show human-error offsets as optional break-even/sensitivity curves only, with no
  empirical claim about the offset's true value.

## Future work requiring restricted or newly collected data

- Confidential insurer ORSA scenarios and internal operational-loss records.
- ORX/SAS/Advisen granular loss data under a research agreement.
- A multi-firm production panel that identifies shared model/framework versions.
- A pre/post automation human-error study and actuarial time-and-motion/control-cost study.
- External validation on gated TRAIL, GAIA or AgentRx after access terms are accepted.

This revision preserves the core innovation, the quantitative bridge from controlled
agentic failure to actuarial error and capital mechanics—while changing unsupported
industry-wide estimates into transparent experimental and stress-test results.

