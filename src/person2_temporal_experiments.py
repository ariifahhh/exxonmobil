"""Optional GRU/LSTM production-rate experiments with train-only normalization."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.person2_ml_proxy import FLUIDS, PARAMETERS, load_training_table, metric_rows
except ModuleNotFoundError:
    from person2_ml_proxy import FLUIDS, PARAMETERS, load_training_table, metric_rows


ROOT = Path(__file__).resolve().parents[1]


def sequence_arrays(table: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Convert each case into one chronological parameter-plus-time sequence."""
    rows, targets, keys = [], [], []
    for case_id, group in table.groupby("case_id", sort=True):
        wide = group.pivot(index="date", columns="fluid", values="rate").reindex(columns=FLUIDS).sort_index()
        parameters = group.iloc[0][PARAMETERS].to_numpy(float)
        elapsed = ((wide.index - table["date"].min()).days.to_numpy(float) / 365.25).reshape(-1, 1)
        rows.append(np.column_stack([np.repeat(parameters.reshape(1, -1), len(wide), axis=0), elapsed]))
        targets.append(wide.to_numpy(float))
        keys.append(pd.DataFrame({"case_id": case_id, "split": group.iloc[0]["split"], "date": wide.index}))
    return np.stack(rows), np.stack(targets), pd.concat(keys, ignore_index=True)


def run(processed_dir: Path, model_dir: Path, epochs: int = 200) -> dict[str, object]:
    """Train compact GRU/LSTM models when PyTorch is installed; otherwise document block."""
    status_path = processed_dir / "person2_temporal_experiment_status.json"
    try:
        import torch
        from torch import nn
    except ImportError:
        result = {"status": "not_run", "reason": "PyTorch with CUDA support is not installed.", "install_command": "python -m pip install torch --index-url https://download.pytorch.org/whl/cu126", "models": ["gru", "lstm"], "deployment_eligible": False}
        status_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    torch.manual_seed(42)
    np.random.seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    table = load_training_table(processed_dir)
    x, y, keys = sequence_arrays(table)
    train_cases = table.loc[table["split"].eq("train"), "case_id"].drop_duplicates().sort_values().to_numpy() - 1
    validation_cases = table.loc[table["split"].eq("validation"), "case_id"].drop_duplicates().sort_values().to_numpy() - 1
    x_mean, x_std = x[train_cases].mean(axis=(0, 1)), x[train_cases].std(axis=(0, 1)).clip(1e-8)
    y_mean, y_std = y[train_cases].mean(axis=(0, 1)), y[train_cases].std(axis=(0, 1)).clip(1e-8)
    x_scaled, y_scaled = (x - x_mean) / x_std, (y - y_mean) / y_std

    class TemporalProxy(nn.Module):
        def __init__(self, kind: str) -> None:
            super().__init__()
            recurrent = nn.GRU if kind == "gru" else nn.LSTM
            self.recurrent = recurrent(input_size=x.shape[2], hidden_size=32, num_layers=1, batch_first=True)
            self.head = nn.Linear(32, len(FLUIDS))
        def forward(self, values: object) -> object:
            hidden, _ = self.recurrent(values)
            return self.head(hidden)

    results, metric_frames, prediction_frames = [], [], []
    model_dir.mkdir(parents=True, exist_ok=True)
    for kind in ("gru", "lstm"):
        model = TemporalProxy(kind).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
        train_x = torch.tensor(x_scaled[train_cases], dtype=torch.float32, device=device)
        train_y = torch.tensor(y_scaled[train_cases], dtype=torch.float32, device=device)
        validation_x = torch.tensor(x_scaled[validation_cases], dtype=torch.float32, device=device)
        validation_y = torch.tensor(y_scaled[validation_cases], dtype=torch.float32, device=device)
        best_loss, best_state, stale = float("inf"), None, 0
        training_start = time.perf_counter()
        for _ in range(epochs):
            model.train(); optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(model(train_x), train_y)
            loss.backward(); optimizer.step()
            model.eval()
            with torch.no_grad():
                validation_loss = float(torch.nn.functional.mse_loss(model(validation_x), validation_y))
            if validation_loss < best_loss - 1e-6:
                best_loss, best_state, stale = validation_loss, {name: value.cpu() for name, value in model.state_dict().items()}, 0
            else:
                stale += 1
                if stale >= 20: break
        training_seconds = time.perf_counter() - training_start
        model.load_state_dict(best_state)
        torch.save({"state_dict": best_state, "kind": kind, "x_mean": x_mean, "x_std": x_std, "y_mean": y_mean, "y_std": y_std, "features": [*PARAMETERS, "elapsed_years"], "fluids": FLUIDS}, model_dir / f"person2_{kind}_experimental.pt")
        model.eval()
        inference_start = time.perf_counter()
        with torch.no_grad():
            predicted = (model(validation_x).cpu().numpy() * y_std) + y_mean
        inference_seconds = time.perf_counter() - inference_start
        rows = []
        for case_index, case_id in enumerate(validation_cases + 1):
            dates = sorted(table.loc[table["case_id"].eq(case_id), "date"].unique())
            for date_index, date in enumerate(dates):
                for fluid_index, fluid in enumerate(FLUIDS):
                    rows.append({"case_id": int(case_id), "split": "validation", "date": date, "fluid": fluid, "rate": y[case_id - 1, date_index, fluid_index], "predicted_rate": max(float(predicted[case_index, date_index, fluid_index]), 0.0), "model": kind})
        prediction_frame = pd.DataFrame(rows)
        prediction_frame["residual"] = prediction_frame["predicted_rate"] - prediction_frame["rate"]
        metrics = pd.DataFrame(metric_rows(prediction_frame.set_index("fluid")["rate"], prediction_frame["predicted_rate"].to_numpy(), kind, "validation"))
        metric_frames.append(metrics)
        prediction_frames.append(prediction_frame)
        results.append({"model": kind, "device": str(device), "validation_macro_nrmse": float(metrics.loc[metrics["fluid"].eq("all"), "nrmse"].iloc[0]), "best_validation_normalized_mse": best_loss, "epochs_completed": _ + 1, "training_seconds": training_seconds, "inference_seconds": inference_seconds, "artifact_path": f"models/person2_experimental/person2_{kind}_experimental.pt", "deployment_eligible": False, "notes": "Experimental sequence architecture; adapter for new-parameter optimizer is not yet validated."})
    pd.concat(metric_frames, ignore_index=True).to_csv(processed_dir / "person2_temporal_validation_metrics.csv", index=False)
    pd.concat(prediction_frames, ignore_index=True).to_csv(processed_dir / "person2_temporal_validation_predictions.csv", index=False)
    tree_comparison = pd.read_csv(processed_dir / "person2_experiment_comparison.csv")
    temporal_comparison = []
    for result, metrics in zip(results, metric_frames):
        by_fluid = metrics.set_index("fluid")
        temporal_comparison.append({"model": result["model"], "feature_representation": "parameters repeated across sequence + elapsed years", "validation_records": len(validation_cases) * y.shape[1] * len(FLUIDS), "gas_rmse": by_fluid.loc["gas", "rmse"], "oil_rmse": by_fluid.loc["oil", "rmse"], "water_rmse": by_fluid.loc["water", "rmse"], "overall_nrmse": result["validation_macro_nrmse"], "training_seconds": result["training_seconds"], "inference_seconds": result["inference_seconds"], "device": result["device"].upper(), "artifact_path": result["artifact_path"], "deployment_eligible": False, "selected_for_deployment": False, "notes": result["notes"]})
    pd.concat([tree_comparison, pd.DataFrame(temporal_comparison)], ignore_index=True).to_csv(processed_dir / "person2_all_model_comparison.csv", index=False)
    result = {"status": "completed", "device": str(device), "results": results, "case_split": {"train": 70, "validation": 15, "test_untouched": 15}, "normalization": "fit on training cases only"}
    status_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run optional Person 2 GRU/LSTM experiments.")
    parser.add_argument("--processed-dir", type=Path, default=ROOT / "data" / "processed")
    parser.add_argument("--model-dir", type=Path, default=ROOT / "models" / "person2_experimental")
    parser.add_argument("--epochs", type=int, default=200)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    print(json.dumps(run(args.processed_dir, args.model_dir, args.epochs), indent=2))
