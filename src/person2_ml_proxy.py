"""Person 2 production-rate proxy trained only on the fixed case-level split."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import TransformedTargetRegressor


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = ["fault_transmissibility", "porosity_multiplier", "permeability_multiplier", "aquifer_pore_volume"]
GRID_FEATURES = ["poro_mean", "poro_std", "permx_mean", "permz_mean", "porv_mean", "pressure_mean", "swat_mean", "active_cell_fraction"]
FLUIDS = ["oil", "gas", "water"]
TARGET = "rate"


def model_candidates() -> dict[str, tuple[list[str], object]]:
    """Return small deterministic candidates; grid models are diagnostics only."""
    candidates: dict[str, tuple[list[str], object]] = {}
    for label, static_features in {"parameter_only": PARAMETERS, "parameter_plus_grid": PARAMETERS + GRID_FEATURES}.items():
        numeric = ["elapsed_days", *static_features]
        preprocess = ColumnTransformer([
            ("numeric", StandardScaler(), numeric),
            ("fluid", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["fluid"]),
        ])
        for algorithm, estimator in {
            "ridge": Ridge(alpha=10.0),
            "extra_trees": ExtraTreesRegressor(n_estimators=300, max_depth=14, min_samples_leaf=2, n_jobs=-1, random_state=42),
        }.items():
            regressor = Pipeline([("preprocess", preprocess), ("model", estimator)])
            candidates[f"{label}_{algorithm}"] = (numeric + ["fluid"], TransformedTargetRegressor(
                regressor=regressor, func=np.log1p, inverse_func=np.expm1, check_inverse=False
            ))
    return candidates


def load_training_table(processed_dir: Path) -> pd.DataFrame:
    """Join Person 1 static inputs to supported simulated rate targets only."""
    features = pd.read_csv(processed_dir / "person1_grid_case_features.csv")
    curves = pd.read_csv(processed_dir / "person1_case_production_quarterly.csv", parse_dates=["date"])
    required = {"case_id", "split", *PARAMETERS, *GRID_FEATURES}
    missing = required - set(features.columns)
    if missing:
        raise ValueError(f"person1_grid_case_features.csv is missing: {sorted(missing)}")
    table = curves[["case_id", "date", "fluid", TARGET]].merge(
        features[["case_id", "split", *PARAMETERS, *GRID_FEATURES]], on="case_id", how="inner", validate="many_to_one"
    )
    table = table.loc[table["fluid"].isin(FLUIDS) & table[TARGET].notna()].copy()
    table[TARGET] = pd.to_numeric(table[TARGET], errors="raise")
    if (table[TARGET] < 0).any():
        raise ValueError("Production-rate targets must be non-negative.")
    start = table["date"].min()
    table["elapsed_days"] = (table["date"] - start).dt.days.astype(int)
    expected = {"train": 70, "validation": 15, "test": 15}
    if features["split"].value_counts().to_dict() != expected:
        raise ValueError("Expected the fixed Person 1 70/15/15 case split.")
    if table.groupby("split")["case_id"].nunique().to_dict() != expected:
        raise ValueError("Targets are missing one or more fixed-split cases.")
    return table.sort_values(["case_id", "date", "fluid"]).reset_index(drop=True)


def metric_rows(actual: pd.Series, predicted: np.ndarray, model: str, split: str) -> list[dict[str, object]]:
    """Calculate overall and per-fluid MAE/RMSE plus scale-independent NRMSE."""
    frame = pd.DataFrame({"actual": actual.to_numpy(float), "predicted": np.maximum(predicted, 0), "fluid": actual.index.get_level_values("fluid")})
    rows = []
    for fluid, group in frame.groupby("fluid", sort=True):
        rmse = float(mean_squared_error(group["actual"], group["predicted"]) ** 0.5)
        scale = max(float(group["actual"].max() - group["actual"].min()), 1.0)
        rows.append({"model": model, "split": split, "fluid": fluid, "records": len(group), "mae": float(mean_absolute_error(group["actual"], group["predicted"])), "rmse": rmse, "nrmse": rmse / scale})
    overall_rmse = float(mean_squared_error(frame["actual"], frame["predicted"]) ** 0.5)
    rows.append({"model": model, "split": split, "fluid": "all", "records": len(frame), "mae": float(mean_absolute_error(frame["actual"], frame["predicted"])), "rmse": overall_rmse, "nrmse": float(np.mean([row["nrmse"] for row in rows]))})
    return rows


def predict_frame(model: object, columns: list[str], frame: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    """Predict rates and return a compact, traceable prediction table."""
    predicted = np.maximum(model.predict(frame[columns]), 0)
    predictions = frame[["case_id", "split", "date", "fluid", TARGET]].copy()
    predictions["predicted_rate"] = predicted
    predictions["residual"] = predictions["predicted_rate"] - predictions[TARGET]
    return predicted, predictions


def run(processed_dir: Path, model_dir: Path) -> dict[str, pd.DataFrame]:
    """Select the deployable parameter-only proxy on validation, then test once."""
    table = load_training_table(processed_dir)
    train = table.loc[table["split"] == "train"].copy()
    validation = table.loc[table["split"] == "validation"].copy()
    test = table.loc[table["split"] == "test"].copy()
    metrics: list[dict[str, object]] = []
    candidates = model_candidates()
    for name, (columns, model) in candidates.items():
        model.fit(train[columns], train[TARGET])
        predicted, _ = predict_frame(model, columns, validation)
        indexed_actual = validation.set_index("fluid")[TARGET]
        metrics.extend(metric_rows(indexed_actual, predicted, name, "validation"))
    validation_metrics = pd.DataFrame(metrics).sort_values(["fluid", "nrmse", "model"]).reset_index(drop=True)
    deployable = validation_metrics.loc[(validation_metrics["fluid"] == "all") & validation_metrics["model"].str.startswith("parameter_only_")]
    selected_name = deployable.sort_values(["nrmse", "rmse", "model"]).iloc[0]["model"]
    selected_columns, validation_model = candidates[selected_name]
    validation_model.fit(train[selected_columns], train[TARGET])
    validation_predicted, validation_predictions = predict_frame(validation_model, selected_columns, validation)
    validation_selected = pd.DataFrame(metric_rows(validation.set_index("fluid")[TARGET], validation_predicted, selected_name, "validation"))
    final_model = model_candidates()[selected_name][1]
    final_model.fit(pd.concat([train, validation], ignore_index=True)[selected_columns], pd.concat([train, validation], ignore_index=True)[TARGET])
    test_predicted, test_predictions = predict_frame(final_model, selected_columns, test)
    test_metrics = pd.DataFrame(metric_rows(test.set_index("fluid")[TARGET], test_predicted, selected_name, "test"))
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final_model, "feature_columns": selected_columns, "parameters": PARAMETERS}, model_dir / "person2_production_proxy.joblib")
    metadata = {"selected_model": selected_name, "feature_columns": selected_columns, "target": "production rate", "units": {"oil": "STB/d", "gas": "MSCF/d", "water": "STB/d"}, "training_cases": 70, "validation_cases": 15, "test_cases": 15, "supported_date_start": str(table.date.min().date()), "supported_date_end": str(table.date.max().date()), "forecast_limitation": "The proxy rejects dates outside simulated source coverage; Person 4 must use an explicitly validated forecast method after 2008."}
    (model_dir / "person2_production_proxy_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    comparison = validation_metrics.loc[validation_metrics["fluid"] == "all"].copy()
    comparison["deployment_eligible"] = comparison["model"].str.startswith("parameter_only_")
    comparison["selected_for_deployment"] = comparison["model"].eq(selected_name)
    comparison.to_csv(processed_dir / "person2_model_comparison.csv", index=False)
    validation_selected.to_csv(processed_dir / "person2_validation_metrics.csv", index=False)
    test_metrics.to_csv(processed_dir / "person2_test_metrics.csv", index=False)
    validation_predictions.to_csv(processed_dir / "person2_validation_predictions.csv", index=False)
    test_predictions.to_csv(processed_dir / "person2_test_predictions.csv", index=False)
    pd.DataFrame([{"records": len(table), "train_records": len(train), "validation_records": len(validation), "test_records": len(test), "selected_model": selected_name, "random_seed": 42}]).to_csv(processed_dir / "person2_training_manifest.csv", index=False)
    return {"comparison": comparison, "validation_metrics": validation_selected, "test_metrics": test_metrics}


def load_proxy(model_path: Path) -> dict[str, object]:
    """Load the saved Person 2 model bundle without retraining."""
    return joblib.load(model_path)


def predict_production(parameters: dict[str, float], dates: object, model_path: Path = ROOT / "models" / "person2_production_proxy.joblib") -> pd.DataFrame:
    """Predict oil, gas, and water rates for new parameters inside supported dates."""
    missing = set(PARAMETERS) - set(parameters)
    if missing:
        raise ValueError(f"Missing proxy parameters: {sorted(missing)}")
    bundle = load_proxy(model_path)
    date_index = pd.DatetimeIndex(pd.to_datetime(dates, errors="raise"))
    metadata_path = model_path.with_name("person2_production_proxy_metadata.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    lower, upper = pd.Timestamp(metadata["supported_date_start"]), pd.Timestamp(metadata["supported_date_end"])
    if (date_index < lower).any() or (date_index > upper).any():
        raise ValueError(f"Proxy supports dates from {lower.date()} to {upper.date()} only.")
    rows = [{"date": date, "fluid": fluid, **{name: float(parameters[name]) for name in PARAMETERS}, "elapsed_days": int((date - lower).days)} for date in date_index for fluid in FLUIDS]
    frame = pd.DataFrame(rows)
    frame["predicted_rate"] = np.maximum(bundle["model"].predict(frame[bundle["feature_columns"]]), 0)
    return frame[["date", "fluid", "predicted_rate"]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the Person 2 deployable production-rate proxy.")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    results = run(args.processed_dir, args.model_dir)
    print(results["comparison"].to_string(index=False))
    print("\nFinal one-time test metrics:")
    print(results["test_metrics"].to_string(index=False))
