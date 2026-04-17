"""
kinematics.py - Robot arm kinematics calculations.
Forward and inverse kinematics for 2DOF robot arm.
Contributed by Emmanuel Olutunmibi
"""

import math

def forward_kinematics(theta1_deg, theta2_deg, l1, l2):
    theta1 = math.radians(theta1_deg)
    theta2 = math.radians(theta2_deg)
    x = l1 * math.cos(theta1) + l2 * math.cos(theta1 + theta2)
    y = l1 * math.sin(theta1) + l2 * math.sin(theta1 + theta2)
    return round(x, 4), round(y, 4)

def inverse_kinematics(x, y, l1, l2):
    d = (x**2 + y**2 - l1**2 - l2**2) / (2 * l1 * l2)
    if abs(d) > 1:
        return None, None
    theta2 = math.acos(d)
    theta1 = math.atan2(y, x) - math.atan2(
        l2 * math.sin(theta2), l1 + l2 * math.cos(theta2)
    )
    return round(math.degrees(theta1), 4), round(math.degrees(theta2), 4)
