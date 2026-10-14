# DataWorks Challenge 2026 — Master Plan

## Delivery path

1. Prepare auditable clean source tables and quarterly candidate curves.
2. Rank all 100 cases against observed oil, gas, and water rates.
3. Compare an ML diagnostic against the curve-based baseline without tuning on the test split.
4. Forecast the ten selected cases to 2028, validate cumulative behavior, and export the supplied template.

## Ownership

| Person | Scope | Current handover/output |
| --- | --- | --- |
| Person 1 | Data loading, cleaning, grid features | All 100 sentinel-safe grid feature rows are complete in `person1_grid_case_features.csv` |
| Person 2 | Proxy/ML modelling | Parameter-only production proxy, validation/test metrics, and reloadable artifact are complete; P3/P4 integration remains |
| Person 3 | History matching | Proxy-based Differential Evolution completed with saved parameters, history, metrics, and audit; Person 4 integration remains |
| Person 4 | Forecast, export, final QA | Provisional integration, 10-sheet template export, and automated audits complete; team approval and ZIP packaging remain |

## Current verified status

- Core uncertainty and field-history audits pass.
- All 100 simulated cases, three fluids, and two metrics were loaded; no duplicate records, missing values, negative values, or decreasing cumulative records were found.
- Curves are linearly interpolated only within their source dates. All forecast-period source values are intentionally unavailable.
- The baseline history-match ranking and baseline forecast outputs exist in `data/processed/`.
- Grid schema validation passes for all 100 case sheets. `person1_grid_case_features.csv` contains all 100 cases with a sentinel-safe feature audit.
- Person 2's deployable parameter-only proxy is saved in `models/person2_production_proxy.joblib`; its metrics and predictions use the `person2_` prefix in `data/processed/`.

## Immediate priorities

1. Person 2 should load and validate `person1_grid_case_features.csv`, then run the parameter-only and grid-feature baselines.
2. Person 3 should confirm the ten selected cases from the history-match ranking and document any scoring-weight change.
3. Test forecast assumptions using the backtest, then write and verify the final template workbook.

## Quality gates

- No test-set-based hyperparameter tuning.
- Every interpolation, model choice, and forecast assumption must have a file output or documented rationale.
- Cumulative forecast curves must be complete, non-decreasing, and continuous from the 2008 historical boundary.
