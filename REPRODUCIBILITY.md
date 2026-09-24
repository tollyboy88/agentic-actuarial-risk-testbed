# Reproducibility

Use Python 3.11 or newer. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python scripts\reproduce_naaj.py
.venv\Scripts\pytest
```

The NAAJ profile writes its frozen experiment to `outputs/naaj_final/` and records machine-readable tables plus a SHA-256 manifest. The separate Paper 2 methodology is maintained at https://github.com/tollyboy88/bayesian-multistate-actuarial-workflows and cites the same Zenodo dataset archive.

Data archive: https://doi.org/10.5281/zenodo.22821051  
Source repository: https://github.com/tollyboy88/agentic-actuarial-risk-testbed
