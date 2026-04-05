import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import parse


@pytest.mark.parametrize(
    "text,expected_action,expected_direction,expected_distance,expected_angle",
    [
        ("go forward", "move", "forward", 10.0, None),
        ("move 10", "move", "forward", 10.0, None),
        ("turn left", "rotate", "left", None, 45.0),
        ("rotate 90", "rotate", "right", None, 90.0),
        ("spin 45", "rotate", "right", None, 45.0),
        ("pick up the object", "grab", None, None, None),
        ("release", "release", None, None, None),
    ],
)
def test_regex_parser_defaults(text, expected_action, expected_direction, expected_distance, expected_angle):
    result = parse(text, use_ai=False)
    assert result["action"] == expected_action
    assert result["direction"] == expected_direction
    assert result["distance_cm"] == expected_distance
    assert result["angle_deg"] == expected_angle
    assert result["confidence"] >= 0.6
