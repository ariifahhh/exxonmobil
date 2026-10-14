"""Person 3: rank reservoir realizations by their field-history match."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = {"oil": 0.40, "gas": 0.35, "water": 0.25}
FIELD_RATE_COLUMNS = {
    "oil_rate_stb_d": "oil",
    "gas_rate_mscf_d": "gas",
    "water_rate_stb_d": "water",
}


def make_observed_long(field_history: pd.DataFrame) -> pd.DataFrame:
    """Convert observed field-rate columns into date, fluid, observed_rate rows."""
    missing = set(FIELD_RATE_COLUMNS).difference(field_history.columns)
    if missing:
        raise ValueError(f"person1_field_history.csv is missing columns: {sorted(missing)}")
    observed = field_history.melt(
        id_vars="date",
        value_vars=list(FIELD_RATE_COLUMNS),
        var_name="source_column",
        value_name="observed_rate",
    )
    observed["fluid"] = observed["source_column"].map(FIELD_RATE_COLUMNS)
    return observed[["date", "fluid", "observed_rate"]]


def calculate_ranking(field_history: pd.DataFrame, case_quarterly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate per-fluid normalized RMSE and one weighted score per case."""
    observed = make_observed_long(field_history)
    simulated = case_quarterly[["case_id", "date", "fluid", "rate"]].dropna(subset=["rate"])
    merged = simulated.merge(observed, on=["date", "fluid"], how="inner", validate="many_to_one")
    if merged.empty:
        raise ValueError("No simulated rates align with observed field history dates.")

    scales = (
        observed.groupby("fluid")["observed_rate"].agg(lambda values: values.max() - values.min()).rename("range_scale")
    )
    if (scales <= 0).any():
        raise ValueError("Cannot normalize RMSE because an observed fluid rate has zero range.")

    merged["squared_error"] = (merged["rate"] - merged["observed_rate"]) ** 2
    components = (
        merged.groupby(["case_id", "fluid"])
        .agg(points=("observed_rate", "size"), rmse=("squared_error", lambda values: float(np.sqrt(values.mean()))))
        .reset_index()
        .merge(scales, on="fluid", how="left", validate="many_to_one")
    )
    components["nrmse"] = components["rmse"] / components["range_scale"]
    components["weight"] = components["fluid"].map(WEIGHTS)
    components["weighted_nrmse"] = components["nrmse"] * components["weight"]

    ranking = (
        components.groupby("case_id", as_index=False)
        .agg(history_match_score=("weighted_nrmse", "sum"), observation_points=("points", "sum"))
        .sort_values(["history_match_score", "case_id"])
        .reset_index(drop=True)
    )
    ranking.insert(0, "rank", np.arange(1, len(ranking) + 1))
    return ranking, components.sort_values(["case_id", "fluid"]).reset_index(drop=True)


def plot_top_matches(field_history: pd.DataFrame, case_quarterly: pd.DataFrame, ranking: pd.DataFrame, output_path: Path) -> None:
    """Plot observed rates against the top three history-matched cases."""
    observed = make_observed_long(field_history)
    top_cases = ranking.head(3)["case_id"].tolist()
    figure, axes = plt.subplots(1, 3, figsize=(16, 4.5), sharex=True)

    for axis, fluid in zip(axes, ["oil", "gas", "water"]):
        actual = observed.loc[observed["fluid"] == fluid]
        axis.plot(actual["date"], actual["observed_rate"], color="black", linewidth=2.5, label="Observed field")
        for case_id in top_cases:
            simulated = case_quarterly.loc[
                (case_quarterly["case_id"] == case_id) & (case_quarterly["fluid"] == fluid)
            ]
            axis.plot(simulated["date"], simulated["rate"], linestyle="--", linewidth=1.5, label=f"Case {case_id}")
        axis.set_title(f"{fluid.title()} production rate")
        axis.set_ylabel("Rate (source units)")
        axis.tick_params(axis="x", rotation=30)
        axis.legend(fontsize=8)

    figure.suptitle("Top three history matches against observed field history", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.92))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def run(processed_dir: Path, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run the baseline history-match ranking and save handover outputs."""
    field_path = processed_dir / "person1_field_history.csv"
    curves_path = processed_dir / "person1_case_production_quarterly.csv"
    if not field_path.exists() or not curves_path.exists():
        raise FileNotFoundError("Run src/person1_data_pipeline.py before history matching.")

    field_history = pd.read_csv(field_path, parse_dates=["date"])
    case_quarterly = pd.read_csv(curves_path, parse_dates=["date"])
    ranking, components = calculate_ranking(field_history, case_quarterly)

    ranking.to_csv(processed_dir / "person3_curve_history_ranking.csv", index=False)
    components.to_csv(processed_dir / "person3_curve_history_components.csv", index=False)
    plot_top_matches(field_history, case_quarterly, ranking, output_dir / "person3_top_history_matches.png")
    return ranking, components


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank DataWorks cases by historical production-rate match.")
    parser.add_argument("--processed-dir", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result, _ = run(args.processed_dir, args.output_dir)
    print(result.head(10).to_string(index=False))
    print("\nCompleted. Review data/processed/person3_curve_history_ranking.csv")
