# Isolated R fallback runtime

Some CRAN `.rda` files use R promises, non-UTF-8 strings, spatial classes, or Arrow
ALTREP vectors that cannot be decoded by `rdata` or `pyreadr`. They were recovered
with the following open runtime:

- R 4.6.1 for Windows (released 24 June 2026)
- Official installer: `https://cran.r-project.org/bin/windows/base/R-4.6.1-win.exe`
- Verified MD5: `7907f3a20ec8ec88cd0da279024b8e27`
- Per-user runtime location: `C:/Users/user/AppData/Local/Programs/R/R-4.6.1`
- Project library: `data/_tools/R-library`
- Required binary packages: `arrow` 25.0.1 and `sp` 2.2-3 (plus Arrow's open CRAN dependencies)

The native fallback is reproducible with `data/_scripts/convert_residual_rdata.R`.
Portable Parquet verification is performed by
`data/_scripts/native_csv_to_parquet.py`. Native fallback results are recorded in
`data/manifests/rdata_native_fallback_manifest.csv`.
