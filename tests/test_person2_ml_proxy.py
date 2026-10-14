import pandas as pd

from src.person2_ml_proxy import PARAMETERS, metric_rows


def test_proxy_parameter_contract_has_four_uncertainties():
    assert PARAMETERS == ["fault_transmissibility", "porosity_multiplier", "permeability_multiplier", "aquifer_pore_volume"]


def test_metric_rows_returns_fluid_and_overall_metrics():
    actual = pd.Series([1.0, 2.0, 3.0], index=pd.Index(["oil", "gas", "water"], name="fluid"))
    rows = metric_rows(actual, predicted=[1.0, 2.0, 3.0], model="demo", split="validation")
    assert {row["fluid"] for row in rows} == {"oil", "gas", "water", "all"}
    assert next(row for row in rows if row["fluid"] == "all")["rmse"] == 0
