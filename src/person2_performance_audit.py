"""Audit held-out Person 2 performance and saved-model reload consistency."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

try:
    from src.person2_ml_proxy import PARAMETERS, metric_rows, predict_production
except ModuleNotFoundError:
    from person2_ml_proxy import PARAMETERS, metric_rows, predict_production


ROOT = Path(__file__).resolve().parents[1]


def group_metrics(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Compute the existing per-fluid metric definition for each requested group."""
    rows = []
    for value, group in frame.groupby(group_column, sort=True):
        metrics = metric_rows(group.set_index("fluid")["rate"], group["predicted_rate"].to_numpy(), "parameter_only_extra_trees", "test")
        rows.extend([{group_column: value, **metric} for metric in metrics])
    return pd.DataFrame(rows)


def reload_audit(processed_dir: Path, model_path: Path) -> pd.DataFrame:
    """Verify saved-model inference reproduces the saved held-out predictions."""
    features = pd.read_csv(processed_dir / "person1_grid_case_features.csv")
    expected = pd.read_csv(processed_dir / "person2_test_predictions.csv", parse_dates=["date"])
    rows = []
    for case_id, group in expected.groupby("case_id", sort=True):
        parameters = features.loc[features["case_id"].eq(case_id), PARAMETERS].iloc[0].to_dict()
        actual = predict_production(parameters, sorted(group["date"].unique()), model_path)
        merged = group.merge(actual, on=["date", "fluid"], validate="one_to_one", suffixes=("_saved", "_reloaded"))
        delta = (merged["predicted_rate_saved"] - merged["predicted_rate_reloaded"]).abs()
        rows.append({"case_id": case_id, "records": len(merged), "max_absolute_prediction_delta": float(delta.max()), "mean_absolute_prediction_delta": float(delta.mean()), "status": "pass" if float(delta.max()) < 1e-9 else "fail"})
    return pd.DataFrame(rows)


def run(processed_dir: Path, model_path: Path) -> dict[str, pd.DataFrame]:
    """Create retained test diagnostics; this does not retrain or select a model."""
    predictions = pd.read_csv(processed_dir / "person2_test_predictions.csv", parse_dates=["date"])
    by_case = group_metrics(predictions, "case_id")
    by_date = group_metrics(predictions, "date")
    reloads = reload_audit(processed_dir, model_path)
    by_case.to_csv(processed_dir / "person2_test_performance_by_case.csv", index=False)
    by_date.to_csv(processed_dir / "person2_test_performance_by_date.csv", index=False)
    reloads.to_csv(processed_dir / "person2_inference_reload_audit.csv", index=False)
    return {"by_case": by_case, "by_date": by_date, "reloads": reloads}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit held-out Person 2 performance without retraining.")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--model-path", type=Path, default=ROOT / "models" / "person2_production_proxy.joblib")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run(args.processed_dir, args.model_path)
    print(f"test cases audited: {result['reloads'].case_id.nunique()}")
    print(f"reload checks passing: {int(result['reloads'].status.eq('pass').sum())}/{len(result['reloads'])}")
    print(result["by_case"].loc[result["by_case"]["fluid"].eq("all")].sort_values("nrmse").head(3).to_string(index=False))
