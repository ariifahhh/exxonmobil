"""Person 4: back-test forecast assumptions before extrapolating future production."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.person4_baseline_forecast import DEFAULT_FORECAST_CONFIG, forecast_case
BACKTEST_CUTOFF = pd.Timestamp("2004-01-01")
FLUID_WEIGHTS = {"oil": 0.40, "gas": 0.35, "water": 0.25}

CANDIDATE_CONFIGS = [
    {**DEFAULT_FORECAST_CONFIG, "name": "conservative", "decline_max": 0.25, "water_horizon_years": 5.0, "water_approach_rate": 0.12},
    DEFAULT_FORECAST_CONFIG,
    {**DEFAULT_FORECAST_CONFIG, "name": "responsive", "decline_tail": 8, "decline_max": 0.45, "water_tail": 6, "water_horizon_years": 10.0, "water_approach_rate": 0.20},
]


def normalized_rmse(actual: pd.Series, predicted: pd.Series) -> float:
    """Return RMSE scaled by the observed range, with a stable zero-range fallback."""
    actual = actual.to_numpy(dtype=float)
    predicted = predicted.to_numpy(dtype=float)
    scale = max(float(np.ptp(actual)), float(np.mean(np.abs(actual))), 1.0)
    return float(np.sqrt(np.mean((actual - predicted) ** 2)) / scale)


def run_backtest(processed_dir: Path, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Hide 2004-2008 case data and compare simple forecast configurations."""
    curves = pd.read_csv(processed_dir / "person1_case_production_quarterly.csv", parse_dates=["date"])
    actual = curves.loc[(curves["date"] > BACKTEST_CUTOFF) & (curves["date"] <= pd.Timestamp("2008-01-01"))]
    forecast_dates = pd.DatetimeIndex(sorted(actual["date"].unique()))
    rows: list[dict[str, object]] = []

    for config in CANDIDATE_CONFIGS:
        for case_id in sorted(curves["case_id"].unique()):
            history = curves.loc[(curves["case_id"] == case_id) & (curves["date"] <= BACKTEST_CUTOFF)]
            forecast, _ = forecast_case(history, forecast_dates, config)
            forecast["case_id"] = case_id
            comparison = actual.loc[actual["case_id"] == case_id].merge(
                forecast[["date", "fluid", "rate"]], on=["date", "fluid"], suffixes=("_actual", "_forecast")
            )
            for fluid, group in comparison.groupby("fluid"):
                rows.append({
                    "config": config["name"],
                    "case_id": case_id,
                    "fluid": fluid,
                    "nrmse_rate": normalized_rmse(group["rate_actual"], group["rate_forecast"]),
                })

    results = pd.DataFrame(rows)
    summary = results.pivot_table(index="config", columns="fluid", values="nrmse_rate", aggfunc="mean").reset_index()
    for fluid in FLUID_WEIGHTS:
        summary[fluid] = summary[fluid].fillna(np.inf)
    summary["weighted_nrmse"] = sum(summary[fluid] * weight for fluid, weight in FLUID_WEIGHTS.items())
    config_table = pd.DataFrame(CANDIDATE_CONFIGS).rename(columns={"name": "config"})
    summary = summary.merge(config_table, on="config", how="left").sort_values("weighted_nrmse").reset_index(drop=True)

    results.to_csv(processed_dir / "person4_forecast_backtest_results.csv", index=False)
    summary.to_csv(processed_dir / "person4_forecast_backtest_summary.csv", index=False)
    plot_backtest(summary, output_dir / "person4_forecast_backtest_comparison.png")
    return results, summary


def plot_backtest(summary: pd.DataFrame, output_path: Path) -> None:
    figure, axis = plt.subplots(figsize=(7, 4))
    axis.bar(summary["config"], summary["weighted_nrmse"], color=["#2f6db3", "#53a451", "#e58d2c"])
    axis.set_title("Historical back-test: 2004–2008 rate forecast error")
    axis.set_ylabel("Weighted normalized RMSE (lower is better)")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Back-test baseline forecast assumptions.")
    parser.add_argument("--processed-dir", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    _, summary = run_backtest(args.processed_dir, args.output_dir)
    print(summary.to_string(index=False))
