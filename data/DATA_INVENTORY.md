# Agentic Actuarial Testbed — verified data inventory

**Project:** *When the model runs itself: quantifying error propagation and operational
risk capital for agentic artificial intelligence in actuarial workflows*  
**Verified:** 1 September 2026

The four originally supplied archives contained only about 25 MB compressed and did not
match the former 2.8 GB inventory claim. The collection has been repaired from open
upstream sources with exact provenance.

## Measured holdings

| Area | Files | Size | Verification |
|---|---:|---:|---|
| Git source snapshots | 69,507 | 4.04 GiB | 34 clean repositories pinned to commits |
| Hugging Face open datasets | 454 | 0.23 GiB | six public snapshots pinned to revisions |
| Official/open direct downloads | 42 | 0.19 GiB | SHA-256 per file |
| Portable processed outputs | 804 | 0.77 GiB | row/schema checks and conversion manifests |

The source-level manifest contains 298 verified acquisition records and no failed records.

## 01 — Reserving and known-truth generation

- CRAN ChainLadder, insuranceData, actuar and raw/Schedule P datasets.
- SynthETIC individual-claim generator and SPLICE case-estimate development extension.
- Kasa AI SimulationMachine independent individual-claim history generator.
- reservetestr/Meyers benchmarks and DeepTriangle published baselines.
- Direct CAS Schedule P source CSVs and six loss-reserving lines.

**Research role:** known true ultimate, realistic triangles, smoke tests, independent
generator robustness and external model-error benchmarks.

## 02 — Motor pricing

- Full CASdatasets source including freMTPL/freMTPL2, European/Brazilian/Australian motor,
  pricing competitions, catastrophe and triangle data.
- ActuarialDataScience code/data collection.

Previously unreadable Brazilian motor partitions and the Arrow-encoded 1,999,028-row
European telematics table were recovered with native R and converted to verified Parquet.

## 03 — Operational risk, EVT and capital context

- OpVaR loss cells: four verified tables totalling 7,926 records.
- evir, evd, ReIns, copula, rugarch and ggsolvencyii datasets/code.
- Basel 2002/2008 LDCE reports, 2008 AMA range-of-practice report, BCBS 195/196 and
  standardised-approach references.
- EIOPA annual/quarterly own-funds, balance-sheet, premium/claim/expense tables.

**Limitation:** open sources do not contain granular insurer agentic-loss events or firm
exposure denominators. They support methodology, scale and calibration bounds—not an
empirical industry capital parameter.

## 04 — AI incidents and risk taxonomies

- Dated AI Incident Database snapshot and workbook: 16,537 profiled rows across five
  sheets, including 1,654 incidents and 7,680 reports.
- Butterfly Labs open incident mirror: 6,865 records.
- VCDB: 10,596 validated structured incidents.
- AVID, MIT AI Risk Repository converter/data and MITRE ATLAS.
- Seven primary research papers and NIST/IMDA governance sources.

**Research role:** taxonomy triangulation, discovery/control analogues and qualitative
severity evidence. Incident-report selection bias prevents occurrence-rate inference.

## 05 — Agentic failures

- MAST/MAD: 1,642 full traces across seven frameworks/eight benchmarks, plus 19
  human-labelled inter-annotator records; CC-BY-4.0.
- MAST repository trace tree: 7,500 JSON files (including task/configuration files).
- Who&When: 126 algorithm-generated and 58 hand-crafted annotated failures.
- tau-bench and tau2-bench, including 26 final-result JSON files and trajectory artifacts.
- ToolEmu, AgentBench and Agent Security Bench.

**Research role:** fault taxonomy, stage/agent attribution, tool-use failure patterns and
benchmark-conditioned success/failure denominators. Failure-only sets such as Who&When
cannot estimate production occurrence rates.

## 06 — Prompt injection and adversarial behavior

- AgentDojo: 36,679 JSON run artifacts for defended/undefended tool-use experiments.
- InjecAgent: 2,108 base/enhanced rows representing 1,054 underlying scenarios.
- AgentHarm: 176 harmful and 176 benign public test tasks.
- Deepset prompt-injection train/test: 546/116 records.
- Jailbreak classification and jailbreak_llms collections; OWASP LLM Top 10 definitions.

## Portable conversions

- `manifests/rdata_conversion_manifest.csv`: 373 converted Python-readable R objects,
  112 byte-identical duplicate records and all initially incompatible objects identified.
- `manifests/rdata_native_fallback_manifest.csv`: ten residual tabular objects converted
  to verified Parquet; 21 non-tabular package internals preserved as base-R text.
- `manifests/open_table_conversion_manifest.csv`: 17 official/open tables, 451,504 total
  rows, converted to verified Parquet.
- `manifests/data_object_manifest.csv`: 421 processed Parquet/non-tabular objects with
  schema, size, row count, missingness and read-verification status; zero failures.
- `manifests/key_dataset_profile.csv`: record counts, schemas, roles and limitations for
  the 25 load-bearing datasets.

## Licensing and publication

Licence declarations are stored per source in `manifests/source_manifest.csv`. Most primary
sources are MIT, Apache, GPL/MPL or Creative Commons. Who&When and four Git repositories
do not clearly declare a root/data licence. Their raw files must not be redistributed;
use citations and derived statistics only. The CC-BY MAST/MAD corpus is the primary trace
dataset for a reproducible public bundle.

## Gate documents

- `DATA_READINESS_REPORT.md` — final go/no-go by research question.
- `DATA_GAP_REGISTER.md` — resolved and irreducible data gaps.
- `REVISED_RESEARCH_SCOPE.md` — claims supportable by independent open data.
- `ACQUISITION_PLAN.md` — acquisition policy and deliverables.
