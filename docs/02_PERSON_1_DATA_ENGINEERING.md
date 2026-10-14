# Person 1 — Data Engineering Lead

## Mission

Deliver a reliable, reproducible, and documented data pipeline so the ML, history-matching, and forecasting work can run without manually opening source Excel files.

**Primary owner:** Person 1
**Handover to:** Persons 2, 3, and 4

## Current progress

- [x] Load uncertainty values for 100 cases.
- [x] Load 41 historical field-production observations.
- [x] Load six simulated production-output sheets.
- [x] Standardize case IDs, dates, and numeric production columns.
- [x] Convert simulation curves from wide to tidy/long format.
- [x] Separate `RAMP_History` from simulated cases.
- [x] Produce quarterly-aligned production curves.
- [x] Avoid extrapolating beyond the source period.
- [x] Create core and production-curve audit files.
- [x] Inspect Train, Validation, and Test grid workbook structure.
- [x] Confirm 100 case sheets, 29 columns, and 90,365 grid rows per case.
- [x] Implement a streaming grid feature-extraction method.
- [x] Identify and implement analytical handling for `-999.25` sentinels.
- [x] Rebuild grid features for all 100 cases using the sentinel-safe rule.
- [ ] Complete Person 1 handover and reproducibility checks.

## Excel 01 — uncertainty parameters

- [x] Read `Uncertainty Values`.
- [x] Preserve 100 case records.
- [x] Convert `Case n` labels to integer `case_id`.
- [x] Standardize parameter names.
- [x] Validate unique case IDs and missing values.
- [x] Save `data/processed/person1_case_uncertainties.csv`.
- [x] Record source inventory and cleaning audit.
- [ ] Add a formal audit for negative/unexpected parameter values if the team needs it.

Required schema:

`case_id`, `fault_transmissibility`, `porosity_multiplier`, `permeability_multiplier`, `aquifer_pore_volume`

## Excel 02 — historical production

- [x] Read `Field Production`.
- [x] Standardize dates and rate columns.
- [x] Preserve water injection as a separate variable.
- [x] Check chronological order, duplicate dates, missing values, and negative rates.
- [x] Save `data/processed/person1_field_history.csv`.

## Excel 02 — six simulated production sheets

- [x] Read row 2 as the real header row.
- [x] Identify `Case_1` through `Case_100`.
- [x] Separate `RAMP_History`.
- [x] Standardize fluid to `gas`, `oil`, or `water`.
- [x] Standardize metric to `rate` or `cumulative`.
- [x] Convert dates and values to usable types.
- [x] Convert wide sheets to tidy long data.
- [x] Check duplicate case/date/fluid/metric records.
- [x] Audit missing values, negatives, and decreasing cumulative values.
- [x] Save raw-long and quarterly-aligned tables.

### Quarterly alignment

- [x] Use documented linear interpolation inside each source curve's date range.
- [x] Preserve source records in `person1_case_production_raw_long.csv`.
- [x] Flag exact, interpolated, and outside-source-range records.
- [x] Do not extrapolate beyond 1 January 2008.
- [ ] Compare interpolated values with source values at a representative set of exact timestamps.
- [ ] Add a formal rate-versus-cumulative consistency check if required by the team.

## Excel 03–08 — reservoir grids

### File and schema inventory

- [x] Enumerate source workbooks and worksheets.
- [x] Map worksheet/file to case ID and fixed split.
- [x] Verify all 100 expected cases are present.
- [x] Verify 29 columns and 90,365 data rows per case.
- [x] Save `person1_grid_manifest.csv` and `person1_grid_schema_audit.csv`.
- [ ] Add source file sizes to the manifest if needed for delivery documentation.

### Grid-coordinate and physical QA

- [ ] Validate I/J/K data types and missing coordinate values.
- [ ] Check duplicate `(I, J, K)` grid locations.
- [ ] Check spatial alignment across cases.
- [ ] Audit porosity, saturation, permeability, pore-volume, pressure, region, and transmissibility ranges.
- [ ] Flag physical anomalies without deleting them.

### Sentinel and inactive-cell handling

- [x] Detect `-999.25` in the selected grid features.
- [x] Confirm it occurs consistently across 14 non-PORV feature columns in the same Case 1 rows.
- [x] Exclude confirmed sentinel values from means, standard deviations, minima, and maxima.
- [x] Preserve raw Excel values unchanged.
- [x] Record sentinel count, active/inactive row count, and active-cell fraction in the extraction audit.
- [x] Rebuild the existing partial Case 1–5 output using the sentinel-safe implementation.
- [x] Verify the same sentinel rule across Cases 6–100.

### Feature extraction

- [x] Define 15 selected grid properties.
- [x] Compute mean, standard deviation, minimum, and maximum for valid values.
- [x] Join four uncertainty inputs by `case_id`.
- [x] Define train (1–70), validation (71–85), and test (86–100) labels.
- [x] Extract Cases 1–70.
- [x] Extract Cases 71–85.
- [x] Extract Cases 86–100.
- [x] Confirm one feature row per case, no duplicates, and no missing model features.
- [ ] Consider optional active-cell, pore-volume-weighted, or regional features after the baseline is complete.

## Performance and reproducibility

- [x] Use read-only streaming for grid workbooks.
- [x] Process one workbook/sheet at a time instead of loading all grid cells together.
- [x] Support rebuilding all features or resuming verified feature extraction.
- [ ] Benchmark full 100-case extraction time and record it.
- [ ] Run the complete pipeline from a clean environment.
- [x] Run all automated tests after installing requirements.

## Required outputs and handover

- [x] `person1_case_uncertainties.csv`
- [x] `person1_field_history.csv`
- [x] `person1_case_production_raw_long.csv`
- [x] `person1_case_production_quarterly.csv`
- [x] `person1_core_cleaning_audit.csv`
- [x] `person1_production_curve_cleaning_audit.csv`
- [x] `person1_grid_manifest.csv`
- [x] `person1_grid_schema_audit.csv`
- [x] `person1_grid_case_features.csv` for all 100 cases.
- [x] `person1_grid_feature_audit.csv` for all 100 cases.
- [x] Confirm Person 2 can load the final feature table and understand sentinel handling.

## Official command

Run core data and grid-schema checks:

```powershell
python src\person1_data_pipeline.py
```

Run the complete pipeline including sentinel-safe grid features:

```powershell
python src\person1_data_pipeline.py --with-grid-features
```
