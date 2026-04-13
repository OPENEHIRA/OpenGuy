import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from parser import parse


@pytest.mark.parametrize(
    "text,expected_action,expected_direction,expected_distance,expected_angle,expected_speed",
    [
        # Simple defaults
        ("go forward", "move", "forward", 10.0, None, 0.5),
        ("turn left", "rotate", "left", None, 45.0, 0.5),
        
        # Numeric extraction
        ("move 20cm forward", "move", "forward", 20.0, None, 0.5),
        ("rotate 90 degrees", "rotate", "right", None, 90.0, 0.5),
        ("turn 30° left", "rotate", "left", None, 30.0, 0.5),
        ("take 5 steps forward", "move", "forward", 25.0, None, 0.5), # 5cm per step
        
        # Semantic modifiers (vague terms)
        ("move a little forward", "move", "forward", 3.0, None, 0.5),
        ("go slightly left", "move", "left", 3.0, None, 0.5), # 'go' defaults to move
        ("rotate a bit right", "rotate", "right", None, 15.0, 0.5),
        ("move far back", "move", "backward", 30.0, None, 0.5),
        ("go a lot rear", "move", "backward", 30.0, None, 0.5),
        
        # Speed modifiers
        ("move forward slowly", "move", "forward", 10.0, None, 0.2),
        ("gently move left", "move", "left", 10.0, None, 0.2),
        ("turn right fast", "rotate", "right", None, 45.0, 0.9),
        ("rapidly advance 50 units", "move", "forward", 50.0, None, 1.0),
        
        # Synonyms
        ("walk ahead", "move", "forward", 10.0, None, 0.5),
        ("pivot 180", "rotate", "right", None, 180.0, 0.5),
        ("grasp the box", "grab", None, None, None, 0.5),
        ("hold this", "grab", None, None, None, 0.5),
        ("let go", "release", None, None, None, 0.5),
        ("halt", "stop", None, None, None, 0.5),
        
        # Complex combinations
        ("quickly turn slightly right", "rotate", "right", None, 10.0, 0.8),
        ("move 2 steps backward carefully", "move", "backward", 10.0, None, 0.3),
    ],
)
def test_improved_regex_parser(text, expected_action, expected_direction, expected_distance, expected_angle, expected_speed):
    result = parse(text, use_ai=False)
    assert result["action"] == expected_action
    assert result["direction"] == expected_direction
    assert result["distance_cm"] == expected_distance
    assert result["angle_deg"] == expected_angle
    assert result["speed"] == expected_speed
    assert result["confidence"] >= 0.5
