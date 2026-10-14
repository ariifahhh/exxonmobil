"""Optional Person 2 tree-model experiments; never replace the deployed baseline."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.compose import TransformedTargetRegressor

try:  # Supports both ``python -m src...`` and direct Windows script execution.
    from src.person2_ml_proxy import FLUIDS, PARAMETERS, TARGET, load_training_table, metric_rows
except ModuleNotFoundError:
    from person2_ml_proxy import FLUIDS, PARAMETERS, TARGET, load_training_table, metric_rows


ROOT = Path(__file__).resolve().parents[1]
FEATURE_COLUMNS = [*PARAMETERS, "elapsed_days", "fluid_code"]


def feature_matrix(frame: pd.DataFrame) -> pd.DataFrame:
    """Use exactly the deployable parameter/time/fluid representation."""
    matrix = frame[[*PARAMETERS, "elapsed_days", "fluid"]].copy()
    matrix["fluid_code"] = matrix.pop("fluid").map({fluid: index for index, fluid in enumerate(FLUIDS)})
    return matrix[FEATURE_COLUMNS]


def optional_estimators(device: str, device_note: str) -> dict[str, tuple[object | None, str, str]]:
    """Create optional boosted-tree candidates without requiring their packages."""
    estimators: dict[str, tuple[object | None, str, str]] = {
        "random_forest": (RandomForestRegressor(n_estimators=300, max_depth=14, min_samples_leaf=2, n_jobs=-1, random_state=42), "CPU", "scikit-learn"),
    }
    try:
        from lightgbm import LGBMRegressor
        estimators["lightgbm"] = (LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, max_depth=-1, random_state=42, n_jobs=-1, verbosity=-1, device_type="cpu"), "CPU", "LightGBM CPU wheel; Windows GPU build not installed")
    except ImportError:
        estimators["lightgbm"] = (None, "unavailable", "Install lightgbm to run this candidate")
    try:
        from xgboost import XGBRegressor
        estimators["xgboost"] = (XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.9, colsample_bytree=1.0, objective="reg:squarederror", tree_method="hist", device=device, random_state=42, n_jobs=-1), device.upper(), device_note)
    except ImportError:
        estimators["xgboost"] = (None, "unavailable", "XGBoost is not installed; its wheel download was interrupted")
    return estimators


def xgboost_device() -> tuple[str, str]:
    """Smoke-test CUDA rather than assuming the installed XGBoost wheel can use it."""
    try:
        from xgboost import XGBRegressor
        probe = XGBRegressor(n_estimators=1, tree_method="hist", device="cuda", objective="reg:squarederror")
        probe.fit(np.array([[0.0], [1.0]]), np.array([0.0, 1.0]))
        configuration = json.loads(probe.get_booster().save_config())
        actual_device = configuration["learner"]["generic_param"]["device"]
        if actual_device.startswith("cuda"):
            return "cuda", "XGBoost CUDA smoke test passed"
        return "cpu", f"XGBoost requested CUDA but actually used {actual_device}"
    except Exception as error:  # Optional accelerator must never break CPU experiments.
        return "cpu", f"XGBoost CUDA unavailable: {type(error).__name__}: {error}"


def evaluate(model: object, name: str, train: pd.DataFrame, validation: pd.DataFrame) -> tuple[list[dict[str, object]], pd.DataFrame, float, float]:
    """Fit only train cases and evaluate validation cases with baseline metrics."""
    wrapped = TransformedTargetRegressor(regressor=model, func=np.log1p, inverse_func=np.expm1, check_inverse=False)
    start = time.perf_counter()
    wrapped.fit(feature_matrix(train), train[TARGET])
    training_seconds = time.perf_counter() - start
    start = time.perf_counter()
    predicted = np.maximum(wrapped.predict(feature_matrix(validation)), 0)
    inference_seconds = time.perf_counter() - start
    predictions = validation[["case_id", "split", "date", "fluid", TARGET]].copy()
    predictions["predicted_rate"] = predicted
    predictions["residual"] = predictions["predicted_rate"] - predictions[TARGET]
    metrics = metric_rows(validation.set_index("fluid")[TARGET], predicted, name, "validation")
    return metrics, predictions, training_seconds, inference_seconds, wrapped


def run(processed_dir: Path, model_dir: Path) -> pd.DataFrame:
    """Benchmark optional tree models on validation only; preserve Extra Trees baseline."""
    table = load_training_table(processed_dir)
    train, validation = table.loc[table["split"].eq("train")], table.loc[table["split"].eq("validation")]
    device, device_note = xgboost_device()
    model_dir.mkdir(parents=True, exist_ok=True)
    comparison_rows: list[dict[str, object]] = []
    metric_frames: list[pd.DataFrame] = []
    prediction_frames: list[pd.DataFrame] = []
    baseline = pd.read_csv(processed_dir / "person2_model_comparison.csv")
    baseline_row = baseline.loc[baseline.selected_for_deployment].iloc[0]
    baseline_metrics = pd.read_csv(processed_dir / "person2_validation_metrics.csv").set_index("fluid")
    comparison_rows.append({"model": baseline_row["model"], "feature_representation": "parameters + elapsed_days + fluid", "validation_records": len(validation), "gas_rmse": baseline_metrics.loc["gas", "rmse"], "oil_rmse": baseline_metrics.loc["oil", "rmse"], "water_rmse": baseline_metrics.loc["water", "rmse"], "overall_nrmse": baseline_row["nrmse"], "training_seconds": np.nan, "inference_seconds": np.nan, "device": "CPU", "artifact_path": "models/person2_production_proxy.joblib", "deployment_eligible": True, "selected_for_deployment": True, "notes": "Existing protected baseline; not retrained by this runner."})
    for name, (estimator, candidate_device, note) in optional_estimators(device, device_note).items():
        if estimator is None:
            comparison_rows.append({"model": name, "feature_representation": "parameters + elapsed_days + fluid", "validation_records": len(validation), "gas_rmse": np.nan, "oil_rmse": np.nan, "water_rmse": np.nan, "overall_nrmse": np.nan, "training_seconds": np.nan, "inference_seconds": np.nan, "device": candidate_device, "artifact_path": "", "deployment_eligible": False, "selected_for_deployment": False, "notes": note})
            continue
        metrics, predictions, train_seconds, infer_seconds, fitted = evaluate(estimator, name, train, validation)
        metrics_frame = pd.DataFrame(metrics)
        metric_frames.append(metrics_frame)
        prediction_frames.append(predictions.assign(model=name))
        metric_by_fluid = metrics_frame.set_index("fluid")
        artifact = model_dir / f"person2_{name}.joblib"
        joblib.dump({"model": fitted, "feature_columns": FEATURE_COLUMNS, "parameters": PARAMETERS}, artifact)
        comparison_rows.append({"model": name, "feature_representation": "parameters + elapsed_days + fluid", "validation_records": len(validation), "gas_rmse": metric_by_fluid.loc["gas", "rmse"], "oil_rmse": metric_by_fluid.loc["oil", "rmse"], "water_rmse": metric_by_fluid.loc["water", "rmse"], "overall_nrmse": metric_by_fluid.loc["all", "nrmse"], "training_seconds": train_seconds, "inference_seconds": infer_seconds, "device": candidate_device, "artifact_path": str(artifact.relative_to(ROOT)).replace("\\", "/"), "deployment_eligible": True, "selected_for_deployment": False, "notes": note})
    comparison = pd.DataFrame(comparison_rows).sort_values(["selected_for_deployment", "overall_nrmse"], ascending=[False, True], na_position="last")
    comparison.to_csv(processed_dir / "person2_experiment_comparison.csv", index=False)
    pd.concat(metric_frames, ignore_index=True).to_csv(processed_dir / "person2_experiment_validation_metrics.csv", index=False)
    pd.concat(prediction_frames, ignore_index=True).to_csv(processed_dir / "person2_experiment_validation_predictions.csv", index=False)
    hardware = {"gpu": "NVIDIA GeForce RTX 4060 Laptop GPU", "driver": "560.94", "cuda_driver": "12.6", "xgboost_device": device, "xgboost_device_note": device_note, "lightgbm_note": "CPU execution: Windows GPU build requires OpenCL, Boost, CMake, and build tools."}
    (processed_dir / "person2_experiment_hardware.json").write_text(json.dumps(hardware, indent=2), encoding="utf-8")
    return comparison


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run optional Person 2 tree-model validation experiments.")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models" / "person2_experimental")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(run(args.processed_dir, args.model_dir).to_string(index=False))
