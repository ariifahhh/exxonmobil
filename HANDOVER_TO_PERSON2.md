# Person 1 handover to Person 2 and Person 3

## Run the complete workflow

Open `notebooks/dataworks_workflow.ipynb`, select the `.venv` kernel, and use **Run All**. The original Excel files remain unchanged.

## Verified data outputs

| File | Use |
| --- | --- |
| `field_history.csv` | 41 observed quarterly field records, Jan 1998–Jan 2008 |
| `case_uncertainties.csv` | Four uncertainty drivers for Cases 1–100 |
| `case_production_raw_long.csv` | Clean irregular-timestamp simulated production data |
| `case_production_quarterly.csv` | Case curves at history/template quarterly dates |
| `grid_manifest.csv` | File, sheet, case ID, shape, and schema status for all grid cases |
| `case_history_match_ranking.csv` | Baseline ranking of all cases |
| `case_history_match_components.csv` | Per-fluid score components for every case |
| `case_forecast_baseline_long.csv` | Provisional quarterly cumulative forecast for the 10 selected cases |
| `baseline_forecast_parameters.csv` | Fitted rates and water-plateau assumptions |
| `baseline_forecast_audit.csv` | Forecast completeness and monotonicity checks |

## Checks passed

- 100 uncertainty cases, no missing values.
- 41 observed field-history records, no missing values, duplicate dates, or negative rates.
- 100 simulated cases, 3 fluids, 2 metrics, no duplicate records or decreasing cumulative values.
- 100 grid sheets, each with 90,365 cells and 29 validated columns.

## Person 2: baseline history-match method

The score is weighted normalized RMSE on historical production rates:

- Oil: 40%
- Gas: 35%
- Water: 25%

Lower score means a closer history match. The current top-10 baseline cases are 69, 65, 47, 24, 19, 81, 32, 90, 99, and 2.

Review `top_history_matches.png` and the per-fluid components before changing weights. Any score/weight change must be documented and compared against this baseline.

## Person 3: forecast limitation and starting point

The supplied simulated curves end on **1 Jan 2008**. They support history matching only. No future values exist for the Apr 2008–Jan 2028 template period.

Start from the baseline forecast in `case_forecast_baseline_long.csv`. It uses each selected case's final cumulative value and fits simple rate behaviour to historical data. Treat it as a transparent benchmark, then compare any ML or physics-informed improvement against it. Do not fill future dates by copying the last historical cumulative value.

## Remaining team checks

1. Review forecast assumptions and selected cases.
2. Generate the final template workbook from approved forecasts.
3. Build dashboard and presentation from final, not provisional, output.
4. Commit and push the project code/docs to GitHub. Raw and generated data stay ignored by Git.
