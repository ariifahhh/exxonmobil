import pandas as pd

from src.person2_tree_experiments import FEATURE_COLUMNS, feature_matrix


def test_tree_experiment_uses_only_deployable_inputs():
    frame = pd.DataFrame([{
        "fault_transmissibility": 0.1,
        "porosity_multiplier": 1.0,
        "permeability_multiplier": 2.0,
        "aquifer_pore_volume": 100.0,
        "elapsed_days": 90,
        "fluid": "oil",
    }])
    matrix = feature_matrix(frame)
    assert matrix.columns.tolist() == FEATURE_COLUMNS
    assert matrix.loc[0, "fluid_code"] == 0
