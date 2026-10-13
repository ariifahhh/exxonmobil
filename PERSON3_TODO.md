# Person 3 — forecast benchmark and improvement

## What is ready

Run `notebooks/dataworks_workflow.ipynb` with **Run All**. Stage 3 writes:

- `case_forecast_baseline_long.csv` — 80 quarterly cumulative values for each selected forecast.
- `baseline_forecast_parameters.csv` — fitted decline and water parameters.
- `baseline_forecast_audit.csv` — missing-value and monotonicity checks.
- `outputs/baseline_forecast_ensemble.png` — comparison of all ten forecasts.

## Important data limit

All supplied simulated production curves stop on **1 Jan 2008**. There is no true 2008–2028 production target. Therefore, forecast modelling must be justified with historical back-testing and physical plausibility; it cannot claim direct validation against future source data.

## Your work

- [ ] Review the approved top-10 list from Person 2 before making forecasts.
- [ ] Treat the current baseline as the benchmark: gas/oil bounded exponential decline; water moves smoothly to a bounded plateau.
- [ ] Back-test alternative forecast assumptions by hiding a late historical period and comparing it with the known earlier curve data.
- [ ] If using grid features, first create case-level summaries only. Keep the 15 test cases out of feature/model tuning.
- [ ] Retain the simpler baseline unless another method improves back-test error and preserves non-decreasing cumulative output.
- [ ] Document every tested method, cutoff, metric, result, and decision.
- [ ] Hand Person 4 an approved long table with exactly 10 forecasts × 80 dates × 3 fluids, plus assumptions and QA results.

## Non-negotiable QA

- No blanks or negative cumulative values.
- Each gas, oil, and water cumulative curve is non-decreasing.
- Forecast begins from the final historical cumulative base, rather than resetting to zero.
- Preserve the mapping between `forecast_number` (1–10) and original `case_id`.
