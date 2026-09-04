# Restricted and optional sources

The independent core dataset is now acquired. **No manual download, account, payment,
or gate acceptance is required before prototype work.** Open official downloads are stored
under `_scripts/aat_data_remote/`; public Hugging Face snapshots are under
`raw/huggingface/`; exact Git snapshots are under `raw/github/`.

## Excluded gated sources

- TRAIL (`PatronusAI/TRAIL`) — gated Hugging Face dataset.
- GAIA (`gaia-benchmark/GAIA`) — gated Hugging Face dataset.
- AgentRx (`microsoft/AgentRx`) — access-gated Hugging Face dataset.
- Kaggle mirrors/competitions — require accounts or acceptance of competition terms.
- OECD AIM bulk export and registered-only ORX publications.

These are optional future external-validation sources. MAST/MAD, Who&When, tau2,
AgentDojo, InjecAgent, AgentHarm, AIID and VCDB provide open substitutes for the core
taxonomy, trace, benchmark and incident roles.

## Excluded paid/confidential sources

- ORX Global Loss Database.
- SAS OpRisk Global Data / Algo OpData.
- Advisen/Verisk cyber and operational-loss data.
- DIPO and confidential insurer ORSA/internal-loss records.
- Full statutory data not lawfully available as an open bulk source.

No open substitute identifies granular agentic-AI operational losses, insurer exposure
denominators, human-error offsets or shared-model cross-firm correlation. The corresponding
claims were narrowed or moved to future work in `DATA_GAP_REGISTER.md` and
`REVISED_RESEARCH_SCOPE.md`.

## Re-running open acquisition

Use the pinned project environment and the idempotent downloader:

```powershell
data\_tools\.venv\Scripts\python.exe data\_scripts\fetch_remaining.py
```

The downloader now uses live official BIS URLs and the current IMDA Version 1.5 document.
Check `manifests/source_manifest.csv` for exact hashes and source URLs.
