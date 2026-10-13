"""Create a transparent 2008-2028 forecast benchmark for selected history matches."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


DEFAULT_FORECAST_CONFIG = {
    "name": "baseline",
    "decline_tail": 12,
    "decline_min": 0.02,
    "decline_max": 0.35,
    "water_tail": 8,
    "water_horizon_years": 8.0,
    "water_approach_rate": 0.15,
}


def annual_decline_rate(
    dates: pd.Series,
    rates: pd.Series,
    tail: int = 12,
    minimum: float = 0.02,
    maximum: float = 0.35,
) -> float:
    """Estimate a bounded annual exponential decline from recent positive rates."""
    sample = pd.DataFrame({"date": pd.to_datetime(dates), "rate": rates}).dropna()
    sample = sample.loc[sample["rate"] > 0].tail(tail)
    if len(sample) < 2:
        return 0.05
    years = (sample["date"] - sample["date"].iloc[0]).dt.days.to_numpy() / 365.25
    slope, _ = np.polyfit(years, np.log(sample["rate"].to_numpy()), 1)
    return float(np.clip(-slope, minimum, maximum))


def water_plateau_parameters(
    dates: pd.Series,
    rates: pd.Series,
    tail: int = 8,
    horizon_years: float = 8.0,
    approach_rate: float = 0.15,
) -> tuple[float, float]:
    """Estimate a conservative rising-water-rate plateau and approach speed."""
    sample = pd.DataFrame({"date": pd.to_datetime(dates), "rate": rates}).dropna().tail(tail)
    last_rate = float(sample["rate"].iloc[-1])
    if len(sample) < 2:
        return last_rate * 1.1, approach_rate
    years = (sample["date"] - sample["date"].iloc[0]).dt.days.to_numpy() / 365.25
    annual_growth, _ = np.polyfit(years, sample["rate"].to_numpy(), 1)
    plateau = max(last_rate * 1.05, last_rate + max(annual_growth, 0) * horizon_years)
    return float(plateau), approach_rate


def forecast_case(
    case_data: pd.DataFrame,
    forecast_dates: pd.DatetimeIndex,
    config: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, list[dict[str, float]]]:
    """Forecast gas/oil decline and water approach-to-plateau, then integrate rates."""
    config = {**DEFAULT_FORECAST_CONFIG, **(config or {})}
    cutoff = case_data["date"].max()
    rows: list[dict[str, object]] = []
    parameters: list[dict[str, float]] = []

    for fluid in ["gas", "oil", "water"]:
        history = case_data.loc[case_data["fluid"] == fluid].sort_values("date")
        last_rate = float(history["rate"].iloc[-1])
        cumulative = float(history["cumulative"].iloc[-1])
        previous_date = cutoff
        previous_rate = last_rate
        parameter: dict[str, float] = {"fluid": fluid, "cutoff_rate": last_rate, "cutoff_cumulative": cumulative}

        if fluid in {"gas", "oil"}:
            decline = annual_decline_rate(
                history["date"], history["rate"],
                tail=int(config["decline_tail"]),
                minimum=float(config["decline_min"]),
                maximum=float(config["decline_max"]),
            )
            parameter["annual_decline_rate"] = decline
        else:
            plateau, approach_rate = water_plateau_parameters(
                history["date"], history["rate"],
                tail=int(config["water_tail"]),
                horizon_years=float(config["water_horizon_years"]),
                approach_rate=float(config["water_approach_rate"]),
            )
            parameter["water_rate_plateau"] = plateau
            parameter["water_approach_rate"] = approach_rate

        for date in forecast_dates:
            years_from_cutoff = (date - cutoff).days / 365.25
            if fluid in {"gas", "oil"}:
                rate = last_rate * np.exp(-decline * years_from_cutoff)
            else:
                rate = plateau - (plateau - last_rate) * np.exp(-approach_rate * years_from_cutoff)
            days = (date - previous_date).days
            cumulative += ((previous_rate + rate) / 2) * days
            rows.append({"date": date, "fluid": fluid, "rate": rate, "cumulative": cumulative})
            previous_date, previous_rate = date, rate
        parameters.append(parameter)

    return pd.DataFrame(rows), parameters


def validate_forecasts(forecasts: pd.DataFrame) -> pd.DataFrame:
    """Check every forecast curve is populated and cumulative production never decreases."""
    checks = []
    for case_id, group in forecasts.groupby("case_id"):
        for fluid, fluid_group in group.groupby("fluid"):
            checks.append(
                {
                    "case_id": case_id,
                    "fluid": fluid,
                    "missing_values": int(fluid_group[["rate", "cumulative"]].isna().sum().sum()),
                    "decreasing_cumulative": int((fluid_group.sort_values("date")["cumulative"].diff() < -1e-9).sum()),
                }
            )
    audit = pd.DataFrame(checks)
    audit["status"] = np.where(
        (audit["missing_values"] == 0) & (audit["decreasing_cumulative"] == 0), "pass", "flag"
    )
    return audit


def plot_forecast_ensemble(forecasts: pd.DataFrame, output_path: Path) -> None:
    """Plot the 10 baseline cumulative forecast trajectories by fluid."""
    figure, axes = plt.subplots(1, 3, figsize=(16, 4.5), sharex=True)
    for axis, fluid in zip(axes, ["gas", "oil", "water"]):
        subset = forecasts.loc[forecasts["fluid"] == fluid]
        for case_id, group in subset.groupby("case_id"):
            axis.plot(group["date"], group["cumulative"], linewidth=1.2, label=f"Case {case_id}")
        axis.set_title(f"Baseline {fluid} cumulative forecast")
        axis.set_ylabel("Cumulative value (source units)")
        axis.tick_params(axis="x", rotation=30)
    axes[-1].legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
    figure.suptitle("Selected history-match cases: baseline forecast ensemble", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 0.9, 0.92))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def run(input_dir: Path, processed_dir: Path, output_dir: Path, top_n: int = 10) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate a baseline forecast for the top history-matched cases."""
    ranking = pd.read_csv(processed_dir / "case_history_match_ranking.csv")
    curves = pd.read_csv(processed_dir / "case_production_quarterly.csv", parse_dates=["date"])
    template = pd.read_excel(input_dir / "09 Template Deliverable.xlsx", sheet_name="Case 1", usecols="A", engine="openpyxl")
    forecast_dates = pd.DatetimeIndex(pd.to_datetime(template.iloc[:, 0], errors="raise"))
    selected = ranking.head(top_n).copy()
    config = DEFAULT_FORECAST_CONFIG.copy()
    backtest_summary_path = processed_dir / "forecast_backtest_summary.csv"
    if backtest_summary_path.exists():
        backtest_summary = pd.read_csv(backtest_summary_path).sort_values("weighted_nrmse")
        selected_config = backtest_summary.iloc[0]
        config.update({key: selected_config[key] for key in config if key in selected_config.index})
        config["name"] = str(selected_config["config"])

    forecasts, parameters = [], []
    for forecast_number, row in enumerate(selected.itertuples(index=False), start=1):
        case_history = curves.loc[(curves["case_id"] == row.case_id) & (curves["date"] <= pd.Timestamp("2008-01-01"))]
        case_forecast, case_parameters = forecast_case(case_history, forecast_dates, config)
        case_forecast.insert(0, "forecast_number", forecast_number)
        case_forecast.insert(1, "case_id", row.case_id)
        forecasts.append(case_forecast)
        for parameter in case_parameters:
            parameter.update({"forecast_number": forecast_number, "case_id": row.case_id, "forecast_config": config["name"]})
            parameters.append(parameter)

    forecast_output = pd.concat(forecasts, ignore_index=True)
    parameter_output = pd.DataFrame(parameters)
    audit = validate_forecasts(forecast_output)
    forecast_output.to_csv(processed_dir / "case_forecast_baseline_long.csv", index=False, date_format="%Y-%m-%d")
    parameter_output.to_csv(processed_dir / "baseline_forecast_parameters.csv", index=False)
    audit.to_csv(processed_dir / "baseline_forecast_audit.csv", index=False)
    plot_forecast_ensemble(forecast_output, output_dir / "baseline_forecast_ensemble.png")
    return forecast_output, parameter_output, audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a baseline forecast for selected history-match cases.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "TestCases")
    parser.add_argument("--processed-dir", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    parser.add_argument("--top-n", type=int, default=10)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    _, parameters, audit = run(args.input_dir, args.processed_dir, args.output_dir, args.top_n)
    print(parameters.to_string(index=False))
    print(audit.to_string(index=False))
