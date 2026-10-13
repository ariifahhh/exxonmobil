import pandas as pd

from src.stage2_history_matching import calculate_ranking


def test_calculate_ranking_prefers_exact_match():
    history = pd.DataFrame(
        {
            "date": pd.to_datetime(["2000-01-01", "2000-04-01"]),
            "oil_rate_stb_d": [10.0, 20.0],
            "gas_rate_mscf_d": [20.0, 40.0],
            "water_rate_stb_d": [5.0, 10.0],
        }
    )
    records = []
    for case_id, multiplier in [(1, 1.0), (2, 1.2)]:
        for fluid, values in {"oil": [10.0, 20.0], "gas": [20.0, 40.0], "water": [5.0, 10.0]}.items():
            for date, rate in zip(history["date"], values):
                records.append({"case_id": case_id, "date": date, "fluid": fluid, "rate": rate * multiplier})
    ranking, components = calculate_ranking(history, pd.DataFrame(records))
    assert ranking.loc[0, "case_id"] == 1
    assert ranking.loc[0, "history_match_score"] == 0
    assert len(components) == 6
