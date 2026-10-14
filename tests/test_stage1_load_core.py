import pytest

from src.person1_data_pipeline import normalise_case_id


@pytest.mark.parametrize("label, expected", [("Case 1", 1), ("Case 100", 100), (" Case 7 ", 7)])
def test_normalise_case_id(label, expected):
    assert normalise_case_id(label) == expected


def test_normalise_case_id_rejects_invalid_label():
    with pytest.raises(ValueError, match="Unexpected case label"):
        normalise_case_id("Candidate 1")
