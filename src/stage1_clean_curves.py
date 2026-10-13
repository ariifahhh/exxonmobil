"""Clean simulated production curves and align them to quarterly target dates.

Original workbooks in TestCases/ remain read-only. Generated outputs are written
to data/processed/ and outputs/.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from openpyxl import load_workbook


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CURVE_SHEETS = {
    "Gas production cumulative": ("gas", "cumulative"),
    "Gas production rate": ("gas", "rate"),
    "Oil production cumulative": ("oil", "cumulative"),
    "Oil production rate": ("oil", "rate"),
    "Water production cumulative": ("water", "cumulative"),
    "Water production rate": ("water", "rate"),
}


def parse_case_header(value: object) -> int | None:
    """Return an integer case ID for headers such as Case_17."""
    match = re.fullmatch(r"Case_(\d+)", str(value))
    return int(match.group(1)) if match else None


def extract_curve_rows(source_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Extract sparse production sheets using row 2 as their real headers."""
    case_records: list[dict[str, object]] = []
    ramp_records: list[dict[str, object]] = []
    workbook = load_workbook(source_path, read_only=True, data_only=True)

    for sheet_name, (fluid, metric) in CURVE_SHEETS.items():
        worksheet = workbook[sheet_name]
        headers = [cell.value for cell in worksheet[2]]
        case_columns = {index: parse_case_header(header) for index, header in enumerate(headers)}
        ramp_columns = {index for index, header in enumerate(headers) if header == "RAMP_History"}

        if set(case_id for case_id in case_columns.values() if case_id is not None) != set(range(1, 101)):
            raise ValueError(f"{sheet_name} does not contain Case_1 through Case_100 in row 2.")

        for row in worksheet.iter_rows(min_row=4, values_only=True):
            if not row or row[0] is None:
                continue
            date = pd.Timestamp(row[0])
            for index, value in enumerate(row[1:], start=1):
                if value is None:
                    continue
                if case_columns.get(index) is not None:
                    case_records.append(
                        {
                            "date": date,
                            "case_id": case_columns[index],
                            "fluid": fluid,
                            "metric": metric,
                            "value": float(value),
                        }
                    )
                elif index in ramp_columns:
                    ramp_records.append({"date": date, "fluid": fluid, "metric": metric, "value": float(value)})

    workbook.close()
    cases = pd.DataFrame(case_records).sort_values(["case_id", "fluid", "metric", "date"]).reset_index(drop=True)
    ramp = pd.DataFrame(ramp_records).sort_values(["fluid", "metric", "date"]).reset_index(drop=True)
    return cases, ramp


def validate_raw_curves(curves: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate raw values and return a clean table plus a transparent audit."""
    keys = ["case_id", "date", "fluid", "metric"]
    duplicate_rows = int(curves.duplicated(keys, keep=False).sum())
    conflicts = int(
        curves.groupby(keys, dropna=False)["value"].nunique().gt(1).sum()
    )
    if conflicts:
        raise ValueError(f"Found {conflicts} conflicting duplicate curve records. Resolve before continuing.")

    clean = curves.drop_duplicates(keys).copy()
    cumulative = clean.loc[clean["metric"] == "cumulative"].copy()
    cumulative["movement"] = cumulative.groupby(["case_id", "fluid"])["value"].diff()
    decreasing_cumulative = int((cumulative["movement"] < -1e-9).sum())

    audit = pd.DataFrame(
        [
            ("case_ids", clean["case_id"].nunique(), 100, "error"),
            ("fluids", clean["fluid"].nunique(), 3, "error"),
            ("metrics", clean["metric"].nunique(), 2, "error"),
            ("missing_values", int(clean.isna().sum().sum()), 0, "error"),
            ("negative_values", int((clean["value"] < 0).sum()), 0, "warning"),
            ("duplicate_records", duplicate_rows, 0, "warning"),
            ("decreasing_cumulative_values", decreasing_cumulative, 0, "warning"),
        ],
        columns=["check", "observed", "expected", "severity"],
    )
    audit["status"] = np.where(audit["observed"].astype(str) == audit["expected"].astype(str), "pass", "flag")
    return clean, audit


def load_target_dates(processed_dir: Path, template_path: Path) -> pd.DatetimeIndex:
    history = pd.read_csv(processed_dir / "field_history.csv", parse_dates=["date"])
    template = pd.read_excel(template_path, sheet_name="Case 1", usecols="A", engine="openpyxl")
    template_dates = pd.to_datetime(template.iloc[:, 0], errors="coerce").dropna()
    return pd.DatetimeIndex(pd.concat([history["date"], template_dates]).drop_duplicates().sort_values())


def interpolate_to_dates(curves: pd.DataFrame, target_dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Linearly interpolate within each curve's observed date range; never extrapolate."""
    target_ns = target_dates.astype("int64").to_numpy()
    records: list[pd.DataFrame] = []
    for (case_id, fluid, metric), group in curves.groupby(["case_id", "fluid", "metric"], sort=True):
        group = group.sort_values("date")
        source_ns = group["date"].astype("int64").to_numpy()
        source_values = group["value"].to_numpy(dtype=float)
        inside_range = (target_ns >= source_ns.min()) & (target_ns <= source_ns.max())
        values = np.full(len(target_dates), np.nan)
        values[inside_range] = np.interp(target_ns[inside_range], source_ns, source_values)
        exact_dates = set(source_ns)
        source_status = np.where(
            ~inside_range,
            "outside_source_range",
            np.where(np.isin(target_ns, list(exact_dates)), "exact", "linear_interpolation"),
        )
        records.append(
            pd.DataFrame(
                {
                    "case_id": case_id,
                    "date": target_dates,
                    "fluid": fluid,
                    "metric": metric,
                    "value": values,
                    "source_status": source_status,
                }
            )
        )
    return pd.concat(records, ignore_index=True)


def make_raw_curve_plot(curves: pd.DataFrame, output_path: Path) -> None:
    """Create a raw, pre-resampling visual sample of cumulative curves."""
    sample_cases = [1, 50, 100]
    figure, axes = plt.subplots(1, 3, figsize=(16, 4.5), sharex=True)
    for axis, fluid in zip(axes, ["gas", "oil", "water"]):
        subset = curves.loc[
            (curves["metric"] == "cumulative")
            & (curves["fluid"] == fluid)
            & (curves["case_id"].isin(sample_cases))
        ]
        for case_id, group in subset.groupby("case_id"):
            axis.plot(group["date"], group["value"], label=f"Case {case_id}")
        axis.set_title(f"Raw {fluid} cumulative sample")
        axis.set_ylabel("Cumulative value (source units)")
        axis.legend()
        axis.tick_params(axis="x", rotation=30)
    figure.suptitle("Simulated production curves before quarterly resampling", fontsize=14, fontweight="bold")
    figure.tight_layout(rect=(0, 0, 1, 0.92))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def run(input_dir: Path, processed_dir: Path, output_dir: Path) -> pd.DataFrame:
    source_path = input_dir / "02 Field Production.xlsx"
    template_path = input_dir / "09 Template Deliverable.xlsx"
    if not source_path.exists() or not template_path.exists():
        raise FileNotFoundError("Expected Field Production and Template Deliverable workbooks in input directory.")
    if not (processed_dir / "field_history.csv").exists():
        raise FileNotFoundError("Run src/stage1_load_core.py before cleaning production curves.")

    raw_curves, ramp_history = extract_curve_rows(source_path)
    clean_curves, audit = validate_raw_curves(raw_curves)
    target_dates = load_target_dates(processed_dir, template_path)
    quarterly_long = interpolate_to_dates(clean_curves, target_dates)
    field_history = pd.read_csv(processed_dir / "field_history.csv", parse_dates=["date"])
    history_cutoff = field_history["date"].max()
    forecast_rows = quarterly_long.loc[quarterly_long["date"] > history_cutoff]
    coverage_audit = pd.DataFrame(
        [
            {
                "check": "raw_curve_start_date",
                "observed": clean_curves["date"].min().strftime("%Y-%m-%d"),
                "expected": "1998-01-01",
                "severity": "info",
                "status": "pass",
            },
            {
                "check": "raw_curve_end_date",
                "observed": clean_curves["date"].max().strftime("%Y-%m-%d"),
                "expected": history_cutoff.strftime("%Y-%m-%d"),
                "severity": "info",
                "status": "pass",
            },
            {
                "check": "future_template_values_in_source",
                "observed": int(forecast_rows["value"].notna().sum()),
                "expected": 0,
                "severity": "info",
                "status": "review",
            },
        ]
    )
    audit = pd.concat([audit, coverage_audit], ignore_index=True)
    quarterly_wide = (
        quarterly_long.pivot(index=["case_id", "date", "fluid"], columns="metric", values="value")
        .reset_index()
        .sort_values(["case_id", "date", "fluid"])
    )
    coverage = (
        quarterly_long.groupby("source_status").size().rename("records").reset_index()
    )
    coverage.to_csv(processed_dir / "case_production_quarterly_coverage.csv", index=False)

    processed_dir.mkdir(parents=True, exist_ok=True)
    clean_curves.to_csv(processed_dir / "case_production_raw_long.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S")
    ramp_history.to_csv(processed_dir / "ramp_history_raw_long.csv", index=False, date_format="%Y-%m-%dT%H:%M:%S")
    quarterly_long.to_csv(processed_dir / "case_production_quarterly_long.csv", index=False, date_format="%Y-%m-%d")
    quarterly_wide.to_csv(processed_dir / "case_production_quarterly.csv", index=False, date_format="%Y-%m-%d")
    audit.to_csv(processed_dir / "production_curve_cleaning_audit.csv", index=False)
    make_raw_curve_plot(clean_curves, output_dir / "production_curves_before_quarterly_resampling.png")
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean and resample DataWorks simulated production curves.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "TestCases")
    parser.add_argument("--processed-dir", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run(args.input_dir, args.processed_dir, args.output_dir)
    print(result.to_string(index=False))
    print("\nCompleted. Review data/processed/production_curve_cleaning_audit.csv")
