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
- Reusable Python code goes in `src/`; tests go in `tests/`.

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

## Person 1 data pipeline

Run core loading, production-curve cleaning, and the grid inventory with one command:

```powershell
python src/person1_data_pipeline.py
```

This creates Person 1-owned files such as `person1_case_uncertainties.csv`, `person1_field_history.csv`, the `person1_case_production_*.csv` tables, audits, and the 100-case grid manifest. It never edits the source workbooks. Linear interpolation applies only within each curve's source-date coverage; missing coverage remains flagged rather than extrapolated.

Grid feature extraction reads roughly 9 million cells and can take substantial time. It uses the confirmed `-999.25` sentinel rule and rebuilds the partial feature output:

```powershell
python src/person1_data_pipeline.py --with-grid-features
python -m pytest -q
```

## Person 2, Person 3, and Person 4 integration

After the Person 1 grid features have been created, run the reproducible downstream workflow:

```powershell
python -m pip install -r requirements-ml.txt
python src\person2_ml_proxy.py
python src\person3_curve_history_ranking.py
python src\person3_history_optimization.py
python src\person4_forecast_backtest.py
python src\person4_forecast_integration.py
python -m pytest -q
```

`person4_forecast_integration.py` reloads the Person 2 artifact without retraining and validates the Person 3 parameter contract. It intentionally does not call the Person 2 model beyond 1 Jan 2008; the post-2008 projection uses the best historical back-test configuration. The verified provisional workbook is written to `outputs/person4_delivery/Template Deliverable - provisional forecast.xlsx` while the original template remains unchanged.
