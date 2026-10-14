"""Assess whether supplied reservoir grids support a valid Person 2 3D-CNN experiment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = [("03 Train Cases 1.xlsx", "Case 1"), ("07  Validation Cases.xlsx", "Case 71"), ("08 Test Cases.xlsx", "Case 86")]


def inspect_sheet(path: Path, sheet_name: str) -> dict[str, object]:
    """Measure coordinate coverage and duplicate locations without loading a full grid."""
    book = load_workbook(path, read_only=True, data_only=True)
    sheet = book[sheet_name]
    header = [cell.value for cell in next(sheet.iter_rows(max_row=1))]
    required = ["I Index", "J Index", "K Index"]
    positions = {name: header.index(name) for name in required}
    coordinates: set[tuple[int, int, int]] = set()
    missing = 0
    for row in sheet.iter_rows(min_row=2, values_only=True):
        values = tuple(row[positions[name]] for name in required)
        if any(value is None for value in values):
            missing += 1
            continue
        coordinates.add(tuple(int(value) for value in values))
    book.close()
    axes = list(zip(*coordinates))
    return {"source_file": path.name, "sheet": sheet_name, "rows": sheet.max_row - 1, "columns": sheet.max_column, "coordinate_columns_present": True, "missing_coordinates": missing, "unique_coordinates": len(coordinates), "duplicate_coordinates": sheet.max_row - 1 - missing - len(coordinates), "i_range": [min(axes[0]), max(axes[0])], "j_range": [min(axes[1]), max(axes[1])], "k_range": [min(axes[2]), max(axes[2])], "coordinates": coordinates}


def run(input_dir: Path, processed_dir: Path) -> dict[str, object]:
    """Write a conservative CNN feasibility decision based on sampled true grids."""
    samples = [inspect_sheet(input_dir / file_name, sheet) for file_name, sheet in SAMPLES]
    reference = samples[0]["coordinates"]
    alignment = [sample["coordinates"] == reference for sample in samples[1:]]
    for sample in samples:
        sample.pop("coordinates")
    report = {"sampled_cases": samples, "sample_coordinate_alignment_to_case_1": alignment, "sentinel_rule": "-999.25 is handled in Person 1 summaries; a CNN would require a feature-specific inactive-cell mask.", "dynamic_feature_status": "Pressure and saturations may encode a simulated state; their timing is not documented as an inference-safe initial condition.", "cnn_ready": False, "deployment_eligible": False, "decision": "Do not train a 3D CNN for the deployable proxy.", "blockers": ["The optimizer receives new uncertainty parameters but has no raw grid realization for a new parameter combination.", "Person 1 coordinate/physical QA is not yet complete for all 100 cases.", "Grid dynamic-state timing must be confirmed before pressure or saturation can be used without target leakage.", "An inactive-cell mask and memory-safe tensor design are still required."], "next_step": "Keep CNN work experimental until a simulator or generative grid representation can provide inference-time grids for new parameters."}
    processed_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / "person2_cnn3d_assessment.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assess Person 2 3D-CNN feasibility from supplied grids.")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "TestCases")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(json.dumps(run(args.input_dir, args.processed_dir), indent=2, default=str))
