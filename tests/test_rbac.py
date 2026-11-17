
import pytest
from src.api import CLEARANCE_ACCESS


@pytest.mark.parametrize("clearance, expected", [
    ("public", ["public"]),
    ("internal", ["public", "internal"]),
    ("confidential", ["public", "internal", "confidential"]),
])
def test_clearance_access_policy(clearance, expected):
    assert CLEARANCE_ACCESS[clearance] == expected


def test_all_clearance_levels_are_defined():
    assert set(CLEARANCE_ACCESS.keys()) == {
        "public", "internal", "confidential"
    }


def test_higher_clearance_includes_lower_clearance():
    assert set(CLEARANCE_ACCESS["public"]).issubset(
        set(CLEARANCE_ACCESS["internal"])
    )
    assert set(CLEARANCE_ACCESS["internal"]).issubset(
        set(CLEARANCE_ACCESS["confidential"])
    )
