# Person 1 — Data loading, cleaning, and handover

## Your purpose

Give Person 2 a trusted, documented dataset for history matching. Do **not** change the original Excel files or build the ML model yet.

## Recommended setup

- Use **local Python in VS Code** with a virtual environment and Jupyter notebooks for exploration.
- Use Git from the first day. Keep raw Excel in `TestCases/` and write outputs only to `data/processed/`.
- Recommended packages: `pandas`, `openpyxl`, `numpy`, `matplotlib`, `seaborn`, and `scikit-learn`.
- Use Google Colab only as a fallback for compute-heavy experiments. The supplied Excel files total about **1.6 GB**, so uploading/mounting them repeatedly will be slow and Colab sessions can reset.

## To-do list

### A. Project setup

- [ ] Create and activate a Python virtual environment.
- [ ] Create folders: `src/`, `notebooks/`, `data/processed/`, `outputs/`, and `tests/`.
- [ ] Add `.gitignore` entries for `data/processed/`, `outputs/`, `.venv/`, and notebook checkpoints.
- [ ] Create `requirements.txt` and a short `RUNBOOK.md` with one command to run the data pipeline.
- [ ] Confirm every original workbook opens and record its filename, sheet names, dimensions, and case range in a source inventory.

### B. Clean the small, high-priority data first

- [ ] Load `01 Introduction.xlsx` → `Uncertainty Values`; standardise `Case 1` … `Case 100` to an integer `case_id`.
- [ ] Load `02 Field Production.xlsx` → `Field Production`; parse `Date`, verify the 41 quarterly observations (Jan 1998–Jan 2008), and retain oil/gas/water production and water injection rates.
- [ ] Save this as `data/processed/field_history.csv`.
- [ ] Produce a short QA summary: missing values, duplicate dates, negative rates, date range, and units.

### C. Clean the six simulated production-curve sheets

- [ ] Read row 2 as the real headers (`Date`, `Case_1` … `Case_100`, `RAMP_History`); ignore plot labels in row 1.
- [ ] Convert every curve sheet to a tidy table with: `date`, `case_id`, `fluid`, `metric`, `value`.
- [ ] Standardise `fluid` to `gas`, `oil`, or `water`; standardise `metric` to `rate` or `cumulative`.
- [ ] Keep `RAMP_History` separate from case data and document what it contains.
- [ ] Check duplicate `case_id + date + fluid + metric` records, missing values, negative values, and cumulative curves that decrease.
- [ ] Save the cleaned raw curves as `data/processed/case_production_long.csv` and save all flags in `data/processed/cleaning_audit.csv`.

### D. Create the table Person 2 needs

- [ ] Create a common quarterly date index using the 41 history dates plus the 80 template dates.
- [ ] For every case, interpolate values to that index. Record the interpolation method and do not extrapolate outside each curve's available range. The source curves end on 1 Jan 2008, so all 2008–2028 template dates must remain flagged as unavailable rather than filled.
- [ ] Save `data/processed/case_production_quarterly.csv` with `case_id`, `date`, `fluid`, `rate`, and `cumulative`.
- [ ] Make coverage plots for a few cases and a table that flags incomplete date coverage.
- [ ] Confirm all final cumulative columns remain non-decreasing after resampling.

### E. Validate grid files without loading all cells into memory

- [ ] Create a manifest for cases 1–100: source file, sheet name, case ID, row count, column count, and header names.
- [ ] Confirm every case sheet has 90,365 rows of cells and the expected 29 columns.
- [ ] Standardise the typo `Connateg Gas Saturation (SGL)` to `SGL` only in the processed schema, never in the source Excel.
- [ ] Do **not** make a giant full CSV of every 3D grid cell yet. It will be large and is unnecessary for Person 2’s baseline. Person 3 can later read grid files in chunks for features.

### F. Handover to Person 2

- [ ] Give Person 2: `field_history.csv`, `case_production_quarterly.csv`, `case_uncertainties.csv`, `cleaning_audit.csv`, and the data dictionary.
- [ ] Demonstrate how to run the pipeline from a clean environment.
- [ ] Explain the date alignment and interpolation choices in a 10-minute walkthrough.
- [ ] Ask Person 2 to independently load the output and verify one case against the original workbook.

## Definition of done

Person 2 can run one command, load clean history and all case curves, calculate a history-match score, trace every output back to a source workbook, and understand every cleaning rule.
