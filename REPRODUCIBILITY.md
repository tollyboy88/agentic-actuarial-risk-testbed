# Reproducibility

Use Python 3.11 or newer. From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python scripts\reproduce_naaj.py
.venv\Scripts\python scripts\reproduce_saj.py
.venv\Scripts\pytest
```

The NAAJ profile writes its frozen experiment to `outputs/naaj_final/`; the Bayesian methodology pipeline writes `outputs/saj_methodology/`. Each pipeline records machine-readable tables and a SHA-256 manifest. The checked-in `outputs/scaled/` run is the fixed input for Paper 2 so that statistical-method development does not silently change the Paper 1 experimental engine.

Data archive: https://doi.org/10.5281/zenodo.22821051  
Source repository: https://github.com/tollyboy88/agentic-actuarial-risk-testbed
