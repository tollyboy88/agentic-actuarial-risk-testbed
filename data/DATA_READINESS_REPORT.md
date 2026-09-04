# Data readiness gate

**Status: CONDITIONALLY READY; SIMULATION REMAINS PAUSED.**  
**Gate date:** 1 September 2026

The data layer is ready for a scalable prototype **only under the revised scope in
`REVISED_RESEARCH_SCOPE.md`**. The proposal's original industry-level capital,
firm-control-placement, human-error-offset and empirically estimated systemic-correlation
claims are not supportable with unrestricted open data and have been moved to future work
or recast as sensitivity/stress analyses.

## Completed checks

- 34 GitHub sources are clean and pinned to exact commits.
- 298 acquired source records have verified provenance/checksums; no acquisition record is
  currently marked failed.
- Raw holdings measure approximately 4.04 GiB GitHub, 0.23 GiB Hugging Face and
  0.19 GiB official/web downloads. Processed portable outputs measure approximately
  0.77 GiB.
- All 472 discovered `.rda`/`.RData` files were audited. The Python pass produced 373
  converted object records and identified 112 byte-identical duplicates. Every residual
  source loads with native R; ten residual tabular outputs were converted to verified
  Parquet and 21 intrinsically non-tabular package objects were preserved as base-R text.
- Seventeen EIOPA, CAS, incident and AIID workbook tables were converted to verified
  Parquet (451,504 rows total).
- Twenty-five load-bearing datasets were schema/record profiled in
  `manifests/key_dataset_profile.csv`.
- All 421 processed data objects pass a Parquet/footer or non-tabular-preservation check;
  schema and missingness are recorded in `manifests/data_object_manifest.csv`.
- The current IMDA framework was verified as Version 1.5; live official Basel sources
  replaced three obsolete links.
- Licence declarations are recorded in `manifests/source_manifest.csv`. Unclear-licence
  sources are restricted to local analysis/derived statistics and will not be included in
  a redistributed raw-data bundle.

## Readiness by research question

| Question | Gate | Reason |
|---|---|---|
| RQ1 / amplification | **GO** | Known-truth generators, realistic triangles and fault corpora are available. |
| Topology comparison | **GO** | Experimental data will be generated under controlled equal-budget designs; open benchmarks provide external ranges. |
| Detection and optimal control placement | **GO, revised** | Detection can be measured experimentally; actual insurer placement cannot be estimated from open data. |
| Autonomy dose-response | **GO** | Fully identifiable inside the controlled experiment. |
| Operational-risk capital | **GO, scenario-conditioned** | Severity is generated from known reserve error; annual frequency/exposure must be disclosed as experimental/scenario inputs, not industry estimates. |
| Net capital after human-error reduction | **NO-GO as an empirical claim** | No open matched human-versus-agent operational-loss panel exists. Future work or sensitivity curve only. |
| Cross-firm systemic risk | **GO as stress test; NO-GO as empirical estimate** | Copula/common-shock scenarios are feasible, but open data cannot estimate shared-model loss correlation. |

## Reproducibility artefacts

- `manifests/source_manifest.csv` - source URLs, commits, checksums, sizes and licences.
- `manifests/rdata_conversion_manifest.csv` - Python R-object conversion and duplicates.
- `manifests/rdata_native_fallback_manifest.csv` - native-R residual recovery and Parquet verification.
- `manifests/open_table_conversion_manifest.csv` - official/open table conversions.
- `manifests/data_object_manifest.csv` - every processed object, schema and missingness.
- `manifests/key_dataset_profile.csv` - load-bearing record counts, schemas, roles and limitations.
- `_scripts/` - acquisition, conversion, profiling and manifest scripts.
- `acquisition-requirements.lock.txt` and `R_RUNTIME.md` - pinned Python and R tooling.

## Gate decision

Do **not** begin the simulation from the unmodified proposal. Once the revised scope is
accepted as the study specification, the data prerequisite is satisfied and prototype
engineering may begin. No paid or gated dataset is required for the independent core
study.
