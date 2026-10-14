import pandas as pd

from src.person3_history_optimization import PARAMETERS, loss_components, parameter_bounds


def test_parameter_bounds_follow_supplied_case_range():
    cases = pd.DataFrame([{name: index for index, name in enumerate(PARAMETERS)}, {name: index + 1 for index, name in enumerate(PARAMETERS)}])
    assert parameter_bounds(cases) == [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0), (3.0, 4.0)]


def test_loss_components_is_zero_for_perfect_prediction():
    observed = pd.DataFrame({"date": pd.to_datetime(["2000-01-01"] * 3 + ["2000-04-01"] * 3), "fluid": ["oil", "gas", "water"] * 2, "observed_rate": [1.0, 2.0, 3.0, 2.0, 3.0, 4.0]})
    predicted = observed.rename(columns={"observed_rate": "predicted_rate"})
    loss, metrics = loss_components(predicted, observed)
    assert loss == 0
    assert metrics["rmse"].eq(0).all()
