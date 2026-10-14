# Person 2 — Machine Learning Proxy Model Lead

## Mission

Build, train, validate, and save an ML model that predicts reservoir production responses from simulation inputs. The model must support history matching and forecasting; it must not merely memorize the 70 train case IDs.

## 1. Initial technical decisions

- [ ] Agree exact input features, targets, time representation, units, parameter ranges, and missing-feature handling with Persons 1, 3, and 4.
- [ ] Define an inference function usable for new candidate parameter combinations and the 2028 forecast horizon.

## 2. Dataset preparation

- [x] Person 1 delivered uncertainty parameters, quarterly simulated curves, and a sentinel-safe 100-case feature table.
- [x] Confirm fixed split: train 1–70, validation 71–85, test 86–100.
- [x] Preserve case-level splits; do not randomly split grid rows/timestamps.
- [x] Load production-rate targets and record units: oil/water in STB/d and gas in MSCF/d.
- [x] Use only four uncertainty parameters, `elapsed_days`, and fluid as deployable inference features; exclude `case_id` and target-derived inputs.
- [x] Validate target availability and case-ID alignment across all 100 fixed-split cases.

## 3. Establish baseline model

Baseline A uses four uncertainty parameters. Baseline B adds selected grid summary features. Add features only when validation improves.

- [x] Compare Ridge and Extra Trees parameter-only and selected-grid-feature production-rate candidates.
- [x] Apply scaling only inside the training pipeline where required.
- [x] Implement parameter-only production-response baseline.
- [x] Compare parameter-only and grid-feature models on validation.

## 4. Define prediction problem

Inputs may include uncertainty parameters, selected reservoir statistics, and time. Outputs must be explicitly defined as oil/gas/water rate, cumulative production, curve descriptors, or history-match score.

- [x] Choose pointwise regression: parameters + elapsed days + fluid → production rate.
- [x] Document log-target transformation, non-negative clipping, and source-date boundary behaviour.

## 5. Model training

- [x] Implement reproducible candidate-model code in `src/person2_ml_proxy.py`.
- [x] Implement validation-based selection and one-time test evaluation logic.
- [x] Implement MAE, RMSE, and per-fluid NRMSE metrics.
- [x] Run model comparison on the final 100-case Person 1 feature table.
- [x] Record train/validation/test counts, random seed, configuration, and metrics.
- [x] Save selected model checkpoint and feature-column order.

## 6. Advanced experiments

- [x] Benchmark Random Forest and LightGBM CPU candidates against the unchanged Extra Trees baseline.
- [x] Inspect 3D-CNN feasibility using true sampled grids; retain it as non-deployable.
- [x] Add GRU/LSTM experiment code with train-only normalization, fixed seeds, early stopping, checkpointing, and CUDA detection.
- [x] Install PyTorch CUDA and run the GRU/LSTM experiments.
- [x] Install XGBoost and run its validation experiment; record the actual CPU fallback after CUDA smoke test.
- [x] Compare temporal-model validation error, device utilization, and inference speed.

Prefer the simplest model with the best validation evidence.

## 7. Model evaluation

- [x] Produce model comparison, validation/test metric summaries, and row-level predicted-versus-simulated rates.
- [x] Audit held-out error by fluid, case, and date; verify saved-model reload consistency for all 15 test cases.
- [ ] Add charted error distributions and review cumulative/physical-consistency errors.
- [ ] Do not choose hyperparameters with test performance.

## 8. Forecast extrapolation

- [x] Use elapsed-time representation with a fixed source-date origin.
- [x] Reject unsupported dates and clip rates to non-negative values.
- [x] Document that this proxy does not forecast beyond the simulated source period; Person 4 must use a validated post-2008 method.

## 9. Required prediction interface

- [x] Deliver `predict_production(parameters, dates)`.
- [x] Support batched dates, labeled oil/gas/water outputs, units, parameter/date validation, and loading without retraining.

## 10. Model artifacts

- [x] Save model, preprocessing pipeline, metadata, comparison report, predictions, and validation/test metrics.
- [x] Include `scikit-learn` and `joblib` version constraints in `requirements-ml.txt`.

## 11. Handover to Person 3

- [x] Provide model artifact, prediction function, feature schema, time format, units, errors, and limitations in the metadata/output files.
- [ ] Test one complete optimization prediction request together.

## 12. Handover to Person 4

- [x] Provide batch inference, model-loading instructions, output units, source-date constraint, and saved transforms.

## 13. Timeline

- [x] Finalize parameter-only baseline, initial model, and inference prototype.
- [ ] Compare/tune on validation, save artifacts, test inference, and integrate with Persons 3–4.
- [ ] Freeze artifact, reload it, evaluate once, and include it in final ZIP.

## 14. Definition of done

- [x] Trained proxy exists and performance is measured with validation respected.
- [x] Model reloads without retraining and prediction interface works.
- [ ] Person 3 and Person 4 can call it.
- [ ] Metadata, dependencies, and artifacts are included in the final ZIP.

## Current verified artifacts

- [x] `src/person2_ml_proxy.py`
- [x] `src/person2_tree_experiments.py`
- [x] `src/person2_temporal_experiments.py`
- [x] `src/person2_cnn3d_assessment.py`
- [x] `src/person2_performance_audit.py`
- [x] `models/person2_production_proxy.joblib`
- [x] `models/person2_production_proxy_metadata.json`
- [x] `data/processed/person2_model_comparison.csv`
- [x] `data/processed/person2_validation_metrics.csv`
- [x] `data/processed/person2_test_metrics.csv`
- [x] `data/processed/person2_validation_predictions.csv`
- [x] `data/processed/person2_test_predictions.csv`
- [x] `data/processed/person2_training_manifest.csv`
- [x] `data/processed/person2_experiment_comparison.csv`
- [x] `data/processed/person2_experiment_validation_metrics.csv`
- [x] `data/processed/person2_experiment_validation_predictions.csv`
- [x] `data/processed/person2_experiment_hardware.json`
- [x] `data/processed/person2_cnn3d_assessment.json`
- [x] `data/processed/person2_temporal_experiment_status.json`
- [x] `data/processed/person2_temporal_validation_metrics.csv`
- [x] `data/processed/person2_temporal_validation_predictions.csv`
- [x] `data/processed/person2_all_model_comparison.csv`
- [x] `data/processed/person2_test_performance_by_case.csv`
- [x] `data/processed/person2_test_performance_by_date.csv`
- [x] `data/processed/person2_inference_reload_audit.csv`
- [x] `reports/person2_experiment_summary.md`

## Run and handover contract

```powershell
python -m pip install -r requirements-ml.txt
python src\person2_ml_proxy.py
```

The selected deployable model is `parameter_only_extra_trees`. It uses the four uncertainty parameters, `elapsed_days`, and `fluid`; it does **not** use `case_id` or require grid features at inference time. Its validation macro NRMSE is `0.006113`; the held-out test macro NRMSE is `0.008145`.

Persons 3 and 4 can load `models/person2_production_proxy.joblib` with `predict_production(parameters, dates)`. It returns `date`, `fluid`, and `predicted_rate`. Supported dates are 1 Jan 1998 through 1 Jan 2008 only; attempting a later forecast date deliberately raises an error instead of silently extrapolating.

## Optional experiment reproduction

```powershell
python -m pip install -r requirements-person2-experiments.txt
python src\person2_tree_experiments.py
python src\person2_cnn3d_assessment.py
```

GPU hardware was detected as NVIDIA RTX 4060 Laptop GPU with CUDA driver 12.6 and 8 GB VRAM. GRU and LSTM used CUDA, but their validation macro NRMSE values were 0.071048 and 0.077838, respectively. XGBoost was installed and trained, but its CUDA smoke test reported no visible GPU and it correctly fell back to CPU (NRMSE 0.009436). LightGBM also ran on CPU (NRMSE 0.009487). Random Forest reached 0.007789. All are weaker than the protected Extra Trees baseline 0.006113.

To rerun the GPU temporal experiments:

```powershell
python -m pip install torch --index-url https://download.pytorch.org/whl/cu126
python src\person2_temporal_experiments.py
```

The 3D-CNN assessment found coordinate alignment in sampled train/validation/test cases, but marks CNN as non-deployable because new optimizer parameters do not have corresponding raw grids and dynamic-state timing has not been confirmed leakage-safe.

## Held-out test performance audit

Run:

    python src\person2_performance_audit.py

The audit keeps the selected model fixed and does not retrain or tune it. All 15 test cases reload from the saved artifact and reproduce the saved predictions, with maximum absolute prediction delta 8.19e-11. Case 87 is the hardest test case (overall NRMSE 0.01948). The largest date-level relative errors occur early in 1999, where the cross-case target range is very small; inspect raw RMSE and MAE alongside NRMSE rather than treating that relative number alone as a model failure.
