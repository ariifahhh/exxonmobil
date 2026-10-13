# DataWorks 2026 runbook

## One-time setup (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Install the ML packages only when Stage 3 begins:

```powershell
python -m pip install -r requirements-ml.txt
```

If PowerShell blocks activation, run this for the current window only, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Project rules

- Source Excel files stay in `TestCases/` and must never be modified.
- Generated clean data goes in `data/processed/` and is ignored by Git.
- Charts, reports, and final artefacts go in `outputs/` and are ignored by Git.
- Reusable Python code goes in `src/`; exploratory work goes in `notebooks/`; tests go in `tests/`.

## GitHub team setup

The remote repository is `git@github.com:ariifahhh/exxonmobil.git`. Before the first push, set your own Git identity on this project:

```powershell
git config user.name "Your Name"
git config user.email "your-email@example.com"
ssh -T git@github.com
```

When SSH asks whether to trust GitHub's host key, verify that you intended to connect to `github.com`, then type `yes`. GitHub should confirm your account. After that:

```powershell
git add .
git commit -m "Set up Stage A and core data loader"
git push -u origin main
```

Do not stage anything under `TestCases/`, `data/processed/`, `outputs/`, or `.venv/`.

## Current status

Stage A is ready. Stage B core loading and cleaning:

```powershell
python src/stage1_load_core.py
pytest
```

This creates `case_uncertainties.csv`, `field_history.csv`, a source inventory, and a cleaning audit in `data/processed/`. It also saves the raw-data visual profile to `outputs/core_data_before_cleaning.png`.

## Stage B: production curves

Run this only after the core pipeline completes:

```powershell
python src/stage1_clean_curves.py
python -m pytest -q
```

This converts the six simulated production sheets into clean long and quarterly tables. It never edits the source workbook. Linear interpolation applies only within each curve's source-date coverage; missing coverage remains flagged rather than extrapolated.

## Jupyter option

Open `notebooks/dataworks_workflow.ipynb` in VS Code, choose the `.venv` Python kernel, and use **Run All**. The single notebook runs Stage 1 and Stage 2, displays the audits, visual checks, and history-match ranking. The `.py` files remain the single source of truth so the same pipeline can also run from the terminal and be reused by the team.
