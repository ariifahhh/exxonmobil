# Person 4 — Forecasting & Integration Lead

## Mission

Integrate data, ML, and optimization modules into one executable pipeline; generate the 2008–2028 cumulative forecast; populate Template 09; and prepare the final source-code ZIP.

## 1. Final forecast requirement

- [x] Read Template 09 dates: 80 quarterly rows from 1 Apr 2008 to 1 Jan 2028.
- [x] Identify required columns: cumulative gas (MSCF), oil (STB), and water (STB).
- [x] Preserve final workbook sheet names, dates, labels, formulas, and layout during export.

## 2. Input contracts

- [x] Person 1 clean parameters, production tables, grid features, audits, and date definitions are available.
- [x] Load Person 2 saved model, metadata, prediction interface, and configuration without retraining.
- [x] Load Person 3 optimized parameters, bounds/configuration, metrics, and selected candidates.
- [x] Freeze and audit the machine-readable Person 1/2/3 inputs in `person4_integration_contract_audit.csv`.

## 3. Forecast generation

- [x] Implement baseline forecast in `src/person4_baseline_forecast.py`.
- [x] Forecast oil/gas with bounded exponential decline and water with approach-to-plateau behavior.
- [x] Save intermediate long forecast table and fitted parameters.
- [x] Load the saved Person 2 proxy and Person 3 optimized parameters for contract validation; do not request unsupported post-2008 proxy predictions.
- [x] Generate provisional cumulative forecasts at every Template 09 date for all ten Person 3 curve-ranked cases.
- [x] Preserve source units and save final intermediate results.

## 4. Extrapolation strategy

- [x] Document that source curves end at 1 Jan 2008 and future values are modelled, not observed.
- [x] Implement forecast backtest module for configuration comparison in `src/person4_forecast_backtest.py`.
- [ ] Select/approve extrapolation method with Person 2 and Person 3.
- [x] Document input constraints, behavior, uncertainty, and known limitations.

## 5. Rate-to-cumulative conversion

- [x] Use trapezoidal integration from each case's last historical cumulative value.
- [x] Do not restart cumulative production at zero in 2008.
- [x] Confirm source-unit continuity and the 1 Jan 2008 cumulative boundary with the exported forecast audit.

## 6. Forecast quality validation

- [x] Check baseline missing values and decreasing cumulative curves.
- [x] Verify all 80 dates, no duplicates, sorted dates, source units, non-negative predictions, and rate/cumulative consistency.
- [x] Verify Person 3 optimized parameters are within supported bounds and forecast curves are plausible/non-decreasing.

## 7. Template 09 export

- [x] Copy Template 09 without overwriting original.
- [x] Fill cumulative gas, oil, and water only.
- [x] Save completed workbook separately.
- [x] Reopen workbook and verify ten sheets, dates, values, and layout.

## 8. End-to-end integration

- [x] Create `src/person4_forecast_integration.py` as the load → contract-check → forecast → export entry point.
- [x] Support documented separate training/inference commands when compute is expensive.
- [x] Ensure inference uses saved artifacts without retraining.

## 9. Repository integration

- [x] Keep reusable modules in `src/`, processed outputs separate, and requirements/run instructions in repository.
- [ ] Remove unused scripts and add only final required modules/artifacts.
- [ ] Add final model and optimization artifacts without raw source data.

## 10. README responsibilities

- [x] Provide project overview, requirements, installation, inputs, preprocessing, outputs, and known limitations.
- [x] Add final model inference, optimization, forecast, artifact, seed, and reproducibility instructions.

## 11. Final integration tests

- [x] Imports/dependencies/syntax pass.
- [x] Features/schema/case IDs/dates load correctly.
- [x] Saved model reloads and predicts without retraining.
- [x] History matching uses the valid Person 2 parameter ordering.
- [x] Forecast produces validated cumulative outputs and a completed Excel workbook.
- [ ] Final ZIP extracts and runs without machine-specific paths.

## 12. Source-code ZIP packaging

**Deadline: 16 October 2026, 3:00 PM MYT.**

- [ ] Freeze tested source and record commit/model/optimizer versions.
- [ ] Confirm forecast schema, dependencies, and required artifacts.
- [ ] Package without unnecessary raw datasets.
- [ ] Extract ZIP elsewhere, follow README, test model/forecast/export, then submit with buffer.

## 13. Timeline

- [x] Build final template writer/main entry point and mock integration.
- [x] Integrate model/optimizer artifacts, generate forecast, and validate data.
- [ ] Freeze changes, execute integration tests, package, and submit before deadline.

## 14. After code submission

- [ ] Build Power BI, PowerPoint, video, and business explanation only from submitted code/results.

## 15. Definition of done

- [x] Team modules are integrated through documented Person 1/2/3 contracts.
- [x] Future production is generated, cumulatives are correct, and Template 09 is populated.
- [ ] Main pipeline executes; README is accurate; ZIP is tested after extraction; submission is verified.

## Current provisional integration

Run the final integration after Person 1, Person 2, Person 3 optimization, and the Person 4 back-test artifacts exist:

    python src\person4_forecast_integration.py

This command reads the Person 3 top-ten curve ranking (**69, 65, 47, 24, 19, 81, 32, 90, 99, 2**), loads the Person 2 model and Person 3 optimum to validate their handover contract, then uses the lowest historical back-test configuration (`conservative`) for post-2008 rate extrapolation. The Person 2 proxy is not used after 1 Jan 2008 because its documented support ends there.

Outputs are `person4_final_forecast_long.csv`, `person4_final_forecast_parameters.csv`, `person4_final_forecast_audit.csv`, `person4_integration_contract_audit.csv`, and `person4_template_export_audit.csv` in `data/processed/`. The separately written workbook is `outputs/person4_delivery/Template Deliverable - provisional forecast.xlsx`.

The current workbook is a **provisional, back-tested extrapolation benchmark**, not evidence that the Person 2 tree proxy can extrapolate to 2028. Team approval of the forecast method and final ZIP packaging remain open.
