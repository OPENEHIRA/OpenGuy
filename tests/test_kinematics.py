"""
test_kinematics.py - Tests for kinematics module.
Written by Emmanuel Olutunmibi
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
from kinematics import forward_kinematics, inverse_kinematics

def test_forward_kinematics_basic():
    x, y = forward_kinematics(0, 0, 10, 10)
    assert x == 20.0
    assert y == 0.0
    print("test_forward_kinematics_basic PASSED")

def test_inverse_kinematics_basic():
    theta1, theta2 = inverse_kinematics(20, 0, 10, 10)
    assert theta1 is not None
    assert theta2 is not None
    print("test_inverse_kinematics_basic PASSED")

def test_unreachable_position():
    theta1, theta2 = inverse_kinematics(100, 100, 10, 10)
    assert theta1 is None
    assert theta2 is None
    print("test_unreachable_position PASSED")

if __name__ == "__main__":
    test_forward_kinematics_basic()
    test_inverse_kinematics_basic()
    test_unreachable_position()
    print("All tests passed!")
