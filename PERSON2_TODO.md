# Person 2 — history-match review and final ranking

## What is ready

- Run `notebooks/dataworks_workflow.ipynb` using **Run All** with the `.venv` kernel.
- Read `data/processed/case_history_match_ranking.csv` and `case_history_match_components.csv`.
- The reproducible baseline uses rate-based normalized RMSE: oil 40%, gas 35%, water 25%. Lower is better.

## Your work

- [ ] Independently verify Case 69 against the source curves and `Field Production` history.
- [ ] Inspect `outputs/top_history_matches.png`; check whether the top cases follow oil, gas, and water together, not only one fluid.
- [ ] Check the per-fluid columns in `case_history_match_components.csv` for a case with a surprisingly good or poor total score.
- [ ] If changing weights or the error formula, document the reason, rerun all 100 cases, and compare the revised top 10 with the baseline.
- [ ] Freeze one approved ranking for Person 3. Do not use Cases 86–100 to tune score weights.
- [ ] Give Person 3 the selected `case_id` list and a short explanation of why it was approved.

## Current baseline shortlist

`69, 65, 47, 24, 19, 81, 32, 90, 99, 2`

This is provisional until you complete the checks above.
