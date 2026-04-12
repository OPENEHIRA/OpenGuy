import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator import RobotSimulator


def test_move_forward_updates_position():
    robot = RobotSimulator(use_3d=False)
    result = robot.execute(action="move", direction="forward", distance_cm=10.0, angle_deg=None)
    assert robot.x == 0.0
    assert robot.y == 10.0
    assert "Moved forward 10 cm" in result["movement"]


def test_rotate_right_updates_facing():
    robot = RobotSimulator(use_3d=False)
    result = robot.execute(action="rotate", direction="right", distance_cm=None, angle_deg=90.0)
    assert robot.facing == 90.0
    assert "Rotated right 90°" in result["rotation"]


def test_grab_and_release_change_gripper_state():
    robot = RobotSimulator(use_3d=False)
    robot.execute(action="grab", direction=None, distance_cm=None, angle_deg=None)
    assert robot.gripper_open is False
    robot.execute(action="release", direction=None, distance_cm=None, angle_deg=None)
    assert robot.gripper_open is True


def test_invalid_move_raises_value_error():
    robot = RobotSimulator(use_3d=False)
    with pytest.raises(ValueError):
        robot.execute(action="move", direction=None, distance_cm=None, angle_deg=None)
