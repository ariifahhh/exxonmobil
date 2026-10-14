import pandas as pd

from src.person4_baseline_forecast import annual_decline_rate, forecast_case


def test_annual_decline_rate_is_positive_and_bounded():
    dates = pd.date_range("2000-01-01", periods=8, freq="QS")
    rates = pd.Series([100, 90, 80, 70, 60, 50, 40, 30])
    assert 0.02 <= annual_decline_rate(pd.Series(dates), rates) <= 0.35


def test_forecast_case_produces_increasing_cumulative_values():
    dates = pd.date_range("2006-01-01", periods=8, freq="QS")
    history = []
    for fluid, rate in [("oil", 100.0), ("gas", 200.0), ("water", 50.0)]:
        for index, date in enumerate(dates):
            history.append({"date": date, "fluid": fluid, "rate": rate, "cumulative": rate * 90 * (index + 1)})
    output, _ = forecast_case(pd.DataFrame(history), pd.date_range("2008-01-01", periods=4, freq="QS"))
    assert (output.groupby("fluid")["cumulative"].diff().dropna() >= 0).all()
