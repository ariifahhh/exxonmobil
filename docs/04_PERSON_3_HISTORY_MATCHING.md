# Person 3 — History Matching & Optimization Lead

## Mission

Use the trained ML proxy to identify reservoir parameters that reproduce observed field production as closely as possible. The output must support forecasting.

## 1. Understand the optimization problem

History matching compares observed field production with production predicted for a candidate reservoir parameter set. The four uncertain inputs are fault transmissibility, porosity multiplier, permeability multiplier, and aquifer pore volume. Bounds must be justified by the supplied cases and organizer constraints.

## 2. Build the historical reference dataset

- [x] Load historical production.
- [x] Identify 41 observed quarterly dates.
- [x] Extract oil, gas, and water production rates.
- [x] Preserve/review water injection separately.
- [x] Check missing periods and source units.
- [x] Define the source matching window: 1 Jan 1998–1 Jan 2008.

No corresponding simulated water-injection curve is supplied; do not invent an injection target.

## 3. Align model outputs with observations

- [x] Align baseline simulated curves to observed dates by `date` and `fluid`.
- [x] Apply documented linear interpolation only inside source coverage.
- [x] Keep outside-source-range records unavailable.
- [x] Confirm comparisons are not based on spreadsheet row positions.
- [x] Confirm Person 2 uses elapsed days from 1 Jan 1998 for the fixed 1998–2008 date window.
- [x] Confirm proxy units (oil/water STB/d; gas MSCF/d) and rejection of unsupported dates.

## 4. Define loss function

The implemented baseline score is weighted normalized RMSE on historical rates:

`Loss = 0.40 × oil NRMSE + 0.35 × gas NRMSE + 0.25 × water NRMSE`

- [x] Compute RMSE per fluid and normalize by observed range.
- [x] Save overall ranking and per-fluid score components.
- [x] Plot leading cases against field history.
- [ ] Approve or revise fluid weights with the team.
- [x] Constrain inputs to Person 1 case ranges; the proxy rejects unsupported dates and clips rates non-negative.

## 5. Choose optimization algorithm

Candidates include Differential Evolution, Bayesian Optimization, Genetic Algorithm, or another bounded method. Start with **Differential Evolution** if the Person 2 proxy is sufficiently fast: it supports bounded continuous inputs and does not require gradients.

- [x] Select Differential Evolution with a fixed seed and bounded four-parameter vector.

## 6. Implement optimization

- [x] Define parameter-vector order and bounds from all 100 supplied Person 1 uncertainty cases.
- [x] Convert candidate vectors into the Person 2 parameter/time/fluid input representation.
- [x] Call the loaded Person 2 model, align responses by date/fluid, and calculate weighted NRMSE loss.
- [x] Run Differential Evolution with reproducible seed 42.
- [x] Record every objective evaluation, configuration, and best parameters.
- [x] Use the final saved Person 2 proxy directly; no temporary predictor remains.

## 7. Test the optimizer

- [ ] Add a public invalid-input API test if Person 3 exposes optimization as a service.
- [x] Verify parameter ordering and bounds.
- [x] Verify repeated fixed-seed runs.
- [x] Verify minimum objective loss agrees with the retained optimization history.
- [x] Verify 123 date/fluid prediction records and no Person 2 test targets in optimization.

## 8. Optimize reservoir parameters

- [x] Run initial optimization and confirm convergence after 245 objective evaluations.
- [x] Preserve every candidate vector and objective value.
- [x] Save chosen parameters and regenerated historical production curves.
- [x] Save final per-fluid RMSE/NRMSE mismatch metrics.

Different parameter combinations can produce similar matches; do not claim a unique physical solution without evidence.

## 9. Best forecast cases

- [x] Produce a curve-based ranking of all 100 cases.
- [x] Current provisional top ten: **69, 65, 47, 24, 19, 81, 32, 90, 99, 2**.
- [ ] Confirm organizer interpretation of the required ten cases.
- [x] Preserve optimized candidates, vectors, and objectives in person3_optimization_history.csv.
- [ ] Make final selection configurable and coordinate with Person 4.

## 10. Technical outputs

Existing baseline outputs:

- [x] `person3_curve_history_ranking.csv`
- [x] `person3_curve_history_components.csv`
- [x] `outputs/person3_top_history_matches.png`

Optimization outputs still required:

- [x] `person3_optimized_parameters.csv`
- [x] `person3_optimization_history.csv`
- [x] `person3_history_match_metrics.csv`
- [x] `person3_predicted_history.csv`, `person3_optimizer_config.json`, and `src/person3_history_optimization.py`.
- [x] `person3_optimization_audit.csv`

## 11. Handover to Person 4

- [ ] Provide selected parameter combinations, objectives, ranking, and matching dates.
- [ ] Provide predicted histories, bounds, model-artifact reference, and methodology notes.
- [ ] Agree one machine-readable handover schema.

## 12. Timeline

- [x] Implement loss, bounds, and optimizer.
- [x] Integrate the final Person 2 proxy, run optimization, and save candidates.
- [ ] Freeze settings, reproduce results, and include code/configuration in ZIP.

## 13. Definition of done

- [x] Objective, alignment, valid bounds, selected parameters, reproducible loss, and regenerated curves are complete.
- [ ] Person 4 can consume the selected solution.
- [ ] Code/configuration are included in the final ZIP.

The goal is a defensible and transparent reservoir-parameter solution, not only the numerically lowest loss.

## Current optimized result

Run:

    python src\person3_history_optimization.py

The initial fixed-seed run converged with weighted history-match loss 0.127038. Best parameters are fault transmissibility 0.114721, porosity multiplier 1.290793, permeability multiplier 0.846243, and aquifer pore volume 175.731619. This is a proxy-based historical match only; it does not validate a 2008–2028 forecast or establish a unique physical reservoir solution.
