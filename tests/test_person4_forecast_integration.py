import pandas as pd

from src.person4_forecast_integration import validate_final_forecast


def test_final_forecast_audit_accepts_consistent_trapezoidal_curve():
    dates = pd.DatetimeIndex(["2008-04-01", "2008-07-01"])
    rows = []
    for fluid in ["gas", "oil", "water"]:
        rate = 10.0
        cutoff = 100.0
        for date in dates:
            cutoff += rate * 91.0
            rows.append({"forecast_number": 1, "case_id": 1, "fluid": fluid, "date": date, "rate": rate, "cumulative": cutoff, "cutoff_date": pd.Timestamp("2008-01-01"), "cutoff_rate": rate, "cutoff_cumulative": 100.0})
    audit = validate_final_forecast(pd.DataFrame(rows), dates)
    assert (audit["status"] == "pass").all()
