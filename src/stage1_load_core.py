"""Load and validate the two small source tables needed for Stage 1.

This script never writes to TestCases/. It writes cleaned CSVs and an audit log
to data/processed/ by default.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CASE_IDS = set(range(1, 101))

UNCERTAINTY_COLUMNS = {
    "Fault Transmissibility": "fault_transmissibility",
    "Porosity Multiplier": "porosity_multiplier",
    "Permeability Multiplier": "permeability_multiplier",
    "Aquifer Pore Volume": "aquifer_pore_volume",
}

FIELD_COLUMNS = {
    "Identifier": "identifier",
    "Date": "date",
    "Oil production rate (STB/d)": "oil_rate_stb_d",
    "Gas production rate (MSCF/d)": "gas_rate_mscf_d",
    "Water production rate (STB/d)": "water_rate_stb_d",
    "Water injection rate (STB/d)": "water_injection_rate_stb_d",
}


def normalise_case_id(value: object) -> int:
    """Convert labels such as 'Case 17' to integer 17."""
    match = re.fullmatch(r"\s*Case\s+(\d+)\s*", str(value))
    if not match:
        raise ValueError(f"Unexpected case label: {value!r}")
    return int(match.group(1))


def require_columns(frame: pd.DataFrame, expected: set[str], source: str) -> None:
    missing = expected.difference(frame.columns)
    if missing:
        raise ValueError(f"{source} is missing columns: {sorted(missing)}")


def load_uncertainties(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Uncertainty Values", engine="openpyxl")
    return clean_uncertainties(raw)


def clean_uncertainties(raw: pd.DataFrame) -> pd.DataFrame:
    require_columns(raw, {"Item", *UNCERTAINTY_COLUMNS}, "Uncertainty Values")

    clean = raw[["Item", *UNCERTAINTY_COLUMNS]].copy()
    clean = clean.rename(columns={"Item": "case_label", **UNCERTAINTY_COLUMNS})
    clean.insert(0, "case_id", clean.pop("case_label").map(normalise_case_id))
    clean = clean.sort_values("case_id").reset_index(drop=True)
    return clean


def load_field_history(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Field Production", engine="openpyxl")
    return clean_field_history(raw)


def clean_field_history(raw: pd.DataFrame) -> pd.DataFrame:
    require_columns(raw, set(FIELD_COLUMNS), "Field Production")

    clean = raw[list(FIELD_COLUMNS)].rename(columns=FIELD_COLUMNS).copy()
    clean["date"] = pd.to_datetime(clean["date"], errors="coerce")
    for column in FIELD_COLUMNS.values():
        if column not in {"identifier", "date"}:
            clean[column] = pd.to_numeric(clean[column], errors="coerce")
    return clean.sort_values("date").reset_index(drop=True)


def save_raw_source_profile(raw_uncertainties: pd.DataFrame, raw_history: pd.DataFrame, output_path: Path) -> None:
    """Save a visual profile of the original source tables before cleaning."""
    dates = pd.to_datetime(raw_history["Date"], errors="coerce")
    figure, axes = plt.subplots(2, 4, figsize=(18, 8))
    figure.suptitle("Core source profile before cleaning", fontsize=16, fontweight="bold")

    for column, label in [
        ("Oil production rate (STB/d)", "Oil"),
        ("Gas production rate (MSCF/d)", "Gas"),
        ("Water production rate (STB/d)", "Water"),
    ]:
        axes[0, 0].plot(dates, raw_history[column], marker="o", linewidth=1.5, label=label)
    axes[0, 0].set_title("Raw field production rates")
    axes[0, 0].set_ylabel("Rate (source units)")
    axes[0, 0].legend()

    axes[0, 1].plot(dates, raw_history["Water injection rate (STB/d)"], marker="o", color="#2c7fb8")
    axes[0, 1].set_title("Raw water injection rate")
    axes[0, 1].set_ylabel("STB/d")

    quality = pd.Series(
        {
            "Uncertainty\nmissing cells": int(raw_uncertainties.isna().sum().sum()),
            "Field history\nmissing cells": int(raw_history.isna().sum().sum()),
            "Field history\nduplicate dates": int(dates.duplicated().sum()),
        }
    )
    bars = axes[0, 2].bar(quality.index, quality.values, color="#4daf4a")
    axes[0, 2].set_title("Raw data quality checks")
    axes[0, 2].set_ylabel("Count")
    axes[0, 2].set_ylim(0, max(1, quality.max() * 1.25))
    for bar, value in zip(bars, quality.values):
        axes[0, 2].text(bar.get_x() + bar.get_width() / 2, value + 0.03, str(value), ha="center")

    axes[0, 3].axis("off")
    axes[0, 3].text(
        0,
        0.8,
        f"Field history rows: {len(raw_history)}\n"
        f"Date range: {dates.min():%d %b %Y} to {dates.max():%d %b %Y}\n"
        f"Uncertainty rows: {len(raw_uncertainties)}\n"
        "Source files are read-only.",
        va="top",
        fontsize=11,
    )
    axes[0, 3].set_title("Raw source summary")

    for axis, column in zip(axes[1], UNCERTAINTY_COLUMNS):
        axis.hist(raw_uncertainties[column].dropna(), bins=16, color="#756bb1", edgecolor="white")
        axis.set_title(column)
        axis.set_ylabel("Cases")

    figure.autofmt_xdate(rotation=30)
    figure.tight_layout(rect=(0, 0, 1, 0.94))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(figure)


def build_audit(uncertainties: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    """Create a transparent, row-level summary of validation checks."""
    expected_ids_present = set(uncertainties["case_id"])
    rate_columns = [column for column in history if column.endswith("_d")]
    checks = [
        ("case_uncertainties", "row_count", len(uncertainties), 100, "error"),
        ("case_uncertainties", "unique_case_ids", uncertainties["case_id"].nunique(), 100, "error"),
        ("case_uncertainties", "case_ids_1_to_100", expected_ids_present == EXPECTED_CASE_IDS, True, "error"),
        ("case_uncertainties", "missing_values", int(uncertainties.isna().sum().sum()), 0, "error"),
        ("field_history", "row_count", len(history), 41, "warning"),
        ("field_history", "duplicate_dates", int(history["date"].duplicated().sum()), 0, "error"),
        ("field_history", "missing_values", int(history.isna().sum().sum()), 0, "error"),
        ("field_history", "negative_rates", int((history[rate_columns] < 0).sum().sum()), 0, "warning"),
        ("field_history", "first_date", str(history["date"].min().date()), "1998-01-01", "warning"),
        ("field_history", "last_date", str(history["date"].max().date()), "2008-01-01", "warning"),
    ]
    audit = pd.DataFrame(checks, columns=["dataset", "check", "observed", "expected", "severity"])
    audit["status"] = audit.apply(
        lambda row: "pass" if str(row["observed"]) == str(row["expected"]) else "flag", axis=1
    )
    return audit


def run(input_dir: Path, output_dir: Path, visualisation_dir: Path) -> pd.DataFrame:
    """Run the core Stage 1 load, cleaning, and QA steps."""
    introduction_path = input_dir / "01 Introduction.xlsx"
    production_path = input_dir / "02 Field Production.xlsx"
    if not introduction_path.exists() or not production_path.exists():
        raise FileNotFoundError("Expected 01 Introduction.xlsx and 02 Field Production.xlsx in input directory.")

    raw_uncertainties = pd.read_excel(introduction_path, sheet_name="Uncertainty Values", engine="openpyxl")
    raw_history = pd.read_excel(production_path, sheet_name="Field Production", engine="openpyxl")
    uncertainties = clean_uncertainties(raw_uncertainties)
    history = clean_field_history(raw_history)
    audit = build_audit(uncertainties, history)

    output_dir.mkdir(parents=True, exist_ok=True)
    uncertainties.to_csv(output_dir / "case_uncertainties.csv", index=False)
    history.to_csv(output_dir / "field_history.csv", index=False, date_format="%Y-%m-%d")
    audit.to_csv(output_dir / "core_cleaning_audit.csv", index=False)

    inventory = pd.DataFrame(
        [
            {"source_file": introduction_path.name, "sheet": "Uncertainty Values", "rows": len(uncertainties), "columns": len(uncertainties.columns)},
            {"source_file": production_path.name, "sheet": "Field Production", "rows": len(history), "columns": len(history.columns)},
        ]
    )
    inventory.to_csv(output_dir / "core_source_inventory.csv", index=False)
    save_raw_source_profile(raw_uncertainties, raw_history, visualisation_dir / "core_data_before_cleaning.png")
    return audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean core DataWorks Stage 1 source tables.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "TestCases")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "processed")
    parser.add_argument("--visualisation-dir", type=Path, default=PROJECT_ROOT / "outputs")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run(args.input_dir, args.output_dir, args.visualisation_dir)
    print(result.to_string(index=False))
    if (result["status"] == "flag").any():
        print("\nCompleted with flags. Review data/processed/core_cleaning_audit.csv")
    else:
        print("\nCompleted successfully. All core checks passed.")
