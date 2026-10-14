"""Person 3: optimize new reservoir parameters against observed field-rate history."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

try:
    from src.person2_ml_proxy import FLUIDS, PARAMETERS, load_proxy
except ModuleNotFoundError:
    from person2_ml_proxy import FLUIDS, PARAMETERS, load_proxy


ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {"oil": 0.40, "gas": 0.35, "water": 0.25}
OBSERVED_COLUMNS = {"oil_rate_stb_d": "oil", "gas_rate_mscf_d": "gas", "water_rate_stb_d": "water"}


def observed_long(field_history: pd.DataFrame) -> pd.DataFrame:
    """Convert Person 1 historical rates into date/fluid/observed-rate rows."""
    required = {"date", *OBSERVED_COLUMNS}
    missing = required - set(field_history.columns)
    if missing:
        raise ValueError(f"person1_field_history.csv is missing: {sorted(missing)}")
    frame = field_history.melt(id_vars="date", value_vars=list(OBSERVED_COLUMNS), var_name="source", value_name="observed_rate")
    frame["fluid"] = frame["source"].map(OBSERVED_COLUMNS)
    return frame[["date", "fluid", "observed_rate"]].sort_values(["date", "fluid"]).reset_index(drop=True)


def parameter_bounds(uncertainties: pd.DataFrame) -> list[tuple[float, float]]:
    """Use supplied case ranges as transparent, non-extrapolative optimizer bounds."""
    missing = set(PARAMETERS) - set(uncertainties.columns)
    if missing:
        raise ValueError(f"person1_case_uncertainties.csv is missing: {sorted(missing)}")
    return [(float(uncertainties[name].min()), float(uncertainties[name].max())) for name in PARAMETERS]


def predict_rates(bundle: dict[str, object], vector: np.ndarray, dates: pd.DatetimeIndex, start: pd.Timestamp) -> pd.DataFrame:
    """Use the loaded Person 2 pipeline repeatedly without reloading its joblib file."""
    rows = [{"date": date, "fluid": fluid, **dict(zip(PARAMETERS, vector, strict=True)), "elapsed_days": int((date - start).days)} for date in dates for fluid in FLUIDS]
    frame = pd.DataFrame(rows)
    predicted = np.maximum(bundle["model"].predict(frame[bundle["feature_columns"]]), 0)
    frame["predicted_rate"] = predicted
    return frame[["date", "fluid", "predicted_rate"]]


def loss_components(predicted: pd.DataFrame, observed: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    """Calculate the agreed weighted normalized-RMSE objective."""
    merged = predicted.merge(observed, on=["date", "fluid"], validate="one_to_one")
    merged["squared_error"] = (merged["predicted_rate"] - merged["observed_rate"]) ** 2
    components = merged.groupby("fluid", as_index=False).agg(points=("observed_rate", "size"), rmse=("squared_error", lambda value: float(np.sqrt(value.mean()))), observed_min=("observed_rate", "min"), observed_max=("observed_rate", "max"))
    components["range_scale"] = components["observed_max"] - components["observed_min"]
    if (components["range_scale"] <= 0).any():
        raise ValueError("Observed rate range must be positive for all fluids.")
    components["nrmse"] = components["rmse"] / components["range_scale"]
    components["weight"] = components["fluid"].map(WEIGHTS)
    components["weighted_nrmse"] = components["nrmse"] * components["weight"]
    return float(components["weighted_nrmse"].sum()), components


def run(processed_dir: Path, model_path: Path, maxiter: int = 40, popsize: int = 10, seed: int = 42) -> dict[str, object]:
    """Optimize only against observed history and export a reproducible Person 3 handover."""
    uncertainties = pd.read_csv(processed_dir / "person1_case_uncertainties.csv")
    history = pd.read_csv(processed_dir / "person1_field_history.csv", parse_dates=["date"])
    metadata = json.loads(model_path.with_name("person2_production_proxy_metadata.json").read_text(encoding="utf-8"))
    observed = observed_long(history)
    dates = pd.DatetimeIndex(sorted(observed["date"].unique()))
    start, end = pd.Timestamp(metadata["supported_date_start"]), pd.Timestamp(metadata["supported_date_end"])
    if dates.min() < start or dates.max() > end:
        raise ValueError("Observed history must be inside the Person 2 proxy date support.")
    bundle = load_proxy(model_path)
    bounds = parameter_bounds(uncertainties)
    evaluations: list[dict[str, float]] = []

    def objective(vector: np.ndarray) -> float:
        predicted = predict_rates(bundle, vector, dates, start)
        loss, _ = loss_components(predicted, observed)
        evaluations.append({**dict(zip(PARAMETERS, vector, strict=True)), "history_match_loss": loss})
        return loss

    result = differential_evolution(objective, bounds=bounds, seed=seed, maxiter=maxiter, popsize=popsize, polish=True, updating="immediate", workers=1)
    best_vector = np.asarray(result.x, dtype=float)
    predicted = predict_rates(bundle, best_vector, dates, start)
    best_loss, components = loss_components(predicted, observed)
    predicted_history = predicted.merge(observed, on=["date", "fluid"], validate="one_to_one")
    predicted_history["residual"] = predicted_history["predicted_rate"] - predicted_history["observed_rate"]
    parameters = pd.DataFrame([{**dict(zip(PARAMETERS, best_vector, strict=True)), "history_match_loss": best_loss, "optimizer": "differential_evolution", "random_seed": seed, "evaluations": result.nfev, "converged": bool(result.success), "message": result.message}])
    history_table = pd.DataFrame(evaluations)
    history_table.insert(0, "evaluation", np.arange(1, len(history_table) + 1))
    config = {"optimizer": "differential_evolution", "parameter_order": PARAMETERS, "bounds_from_person1_case_range": dict(zip(PARAMETERS, bounds, strict=True)), "weights": WEIGHTS, "random_seed": seed, "maxiter": maxiter, "popsize": popsize, "proxy_model": str(model_path).replace("\\", "/"), "proxy_date_support": [str(start.date()), str(end.date())], "test_set_usage": "No Person 2 test targets were used for optimizer selection or fitting."}
    audit_rows = [
        ("optimizer_evaluations_recorded", len(history_table), result.nfev, "pass" if len(history_table) == result.nfev else "fail"),
        ("best_loss_matches_history_minimum", best_loss, float(history_table["history_match_loss"].min()), "pass" if np.isclose(best_loss, history_table["history_match_loss"].min()) else "fail"),
        ("parameters_within_person1_bounds", all(low <= value <= high for value, (low, high) in zip(best_vector, bounds, strict=True)), True, "pass" if all(low <= value <= high for value, (low, high) in zip(best_vector, bounds, strict=True)) else "fail"),
        ("predicted_history_records", len(predicted_history), len(dates) * len(FLUIDS), "pass" if len(predicted_history) == len(dates) * len(FLUIDS) else "fail"),
        ("predicted_history_missing_values", int(predicted_history.isna().sum().sum()), 0, "pass" if not predicted_history.isna().any().any() else "fail"),
    ]
    audit = pd.DataFrame(audit_rows, columns=["check", "observed", "expected", "status"])
    parameters.to_csv(processed_dir / "person3_optimized_parameters.csv", index=False)
    history_table.to_csv(processed_dir / "person3_optimization_history.csv", index=False)
    components.to_csv(processed_dir / "person3_history_match_metrics.csv", index=False)
    predicted_history.to_csv(processed_dir / "person3_predicted_history.csv", index=False)
    audit.to_csv(processed_dir / "person3_optimization_audit.csv", index=False)
    (processed_dir / "person3_optimizer_config.json").write_text(json.dumps(config, indent=2, default=str), encoding="utf-8")
    return {"parameters": parameters, "metrics": components, "history": history_table, "predicted_history": predicted_history, "audit": audit}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Optimize Person 2 proxy parameters against field history.")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--model-path", type=Path, default=ROOT / "models" / "person2_production_proxy.joblib")
    parser.add_argument("--maxiter", type=int, default=40)
    parser.add_argument("--popsize", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run(args.processed_dir, args.model_path, args.maxiter, args.popsize, args.seed)
    print(result["parameters"].to_string(index=False))
    print(result["metrics"].to_string(index=False))
