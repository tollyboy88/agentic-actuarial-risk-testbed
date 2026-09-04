# AAT Control Room

Local research dashboard for running the approved AAT experiment profiles and exploring their paired errors, controls, capital, systemic stress, and SQLite trajectory evidence.

## Prerequisites

- Node.js 22.13 or newer (`node --version`)
- Python 3.11 or newer (`python --version`)
- npm, included with Node.js

No database server, Docker, API key, or cloud account is required. SQLite and generated Parquet/JSON files are local.

## First installation

From the project root in the VS Code terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dashboard.txt
Set-Location dashboard
npm install
```

If you create a new root `.venv`, change the Python path in `.vscode/tasks.json` from `data\_tools\.venv` to `.venv`.

## Launch with the existing project environment

Open the project folder in VS Code, then use **Terminal → Run Task → AAT: Launch Dashboard**. VS Code starts two terminals:

- API: `http://127.0.0.1:8765`
- Dashboard: `http://localhost:3000`

Open `http://localhost:3000` in your browser. Stop both task terminals with `Ctrl+C` when finished.

## Manual launch

Terminal 1, from the project root:

```powershell
.\data\_tools\.venv\Scripts\python.exe -m uvicorn aat.dashboard_api:app --host 127.0.0.1 --port 8765
```

Terminal 2:

```powershell
Set-Location dashboard
npm run dev
```

The dashboard falls back to generated read-only snapshots when the Python API is not running. Experiment buttons and full trajectory queries require the API.

## Available tests

- **Smoke**: 60 runs; suited to checking installation and workflow integrity.
- **Scaled**: 1,024 runs; suited to the research dashboard and screening results.

Only these named configurations can be launched by the API. The browser cannot pass arbitrary commands or file paths.
