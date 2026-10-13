from src.stage1_clean_curves import parse_case_header


def test_parse_case_header():
    assert parse_case_header("Case_1") == 1
    assert parse_case_header("Case_100") == 100


def test_parse_case_header_ignores_non_case_headers():
    assert parse_case_header("RAMP_History") is None
    assert parse_case_header("Date") is None
