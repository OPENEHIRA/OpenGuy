"""
ros2_bridge.py - Converts parsed commands to ROS2 messages
and triggers Gazebo simulation via rclpy.
Contributed by Emmanuel Olutunmibi
"""

import json
import math


def command_to_ros2(parsed_command: dict) -> dict:
    """
    Convert parsed JSON command to ROS2 message format.
    
    Args:
        parsed_command: dict with action, direction, distance_cm
        
    Returns:
        ROS2 compatible message dict
    """
    action = parsed_command.get("action", "move")
    direction = parsed_command.get("direction", "forward")
    distance_cm = parsed_command.get("distance_cm", 10)
    angle_deg = parsed_command.get("angle_deg", 45)

    # Convert cm to meters for ROS2
    distance_m = distance_cm / 100.0

    if action == "move":
        return {
            "type": "geometry_msgs/Twist",
            "linear": {
                "x": distance_m if direction == "forward" else -distance_m if direction == "backward" else 0.0,
                "y": distance_m if direction == "left" else -distance_m if direction == "right" else 0.0,
                "z": distance_m if direction == "up" else -distance_m if direction == "down" else 0.0
            },
            "angular": {
                "x": 0.0,
                "y": 0.0,
                "z": 0.0
            }
        }

    elif action == "rotate":
        angle_rad = math.radians(angle_deg)
        return {
            "type": "geometry_msgs/Twist",
            "linear": {"x": 0.0, "y": 0.0, "z": 0.0},
            "angular": {
                "x": 0.0,
                "y": 0.0,
                "z": angle_rad if direction in ["left", "counterclockwise"] else -angle_rad
            }
        }

    elif action == "grab":
        return {
            "type": "control_msgs/GripperCommand",
            "command": {
                "position": 0.0,
                "max_effort": 50.0
            }
        }

    elif action == "release":
        return {
            "type": "control_msgs/GripperCommand",
            "command": {
                "position": 0.08,
                "max_effort": 50.0
            }
        }

    else:
        return {
            "type": "std_msgs/String",
            "data": json.dumps(parsed_command)
        }


def get_gazebo_launch_config(robot_model: str = "robot_arm") -> dict:
    """
    Get Gazebo launch configuration for the robot model.
    
    Args:
        robot_model: Name of robot model to spawn
        
    Returns:
        Gazebo launch config dict
    """
    return {
        "world": "empty.world",
        "robot_model": robot_model,
        "ros2_topics": {
            "cmd_vel": "/robot/cmd_vel",
            "gripper": "/robot/gripper/command",
            "joint_states": "/robot/joint_states",
            "camera": "/robot/camera/image_raw"
        },
        "websocket_port": 9090
    }


def ros2_to_websocket_msg(ros2_msg: dict, topic: str) -> dict:
    """
    Format ROS2 message for rosbridge WebSocket transmission.
    
    Args:
        ros2_msg: ROS2 message dict
        topic: ROS2 topic to publish to
        
    Returns:
        rosbridge protocol message
    """
    return {
        "op": "publish",
        "topic": topic,
        "msg": ros2_msg
    }


if __name__ == "__main__":
    # Test conversions
    test_commands = [
        {"action": "move", "direction": "forward", "distance_cm": 30},
        {"action": "move", "direction": "backward", "distance_cm": 10},
        {"action": "rotate", "direction": "left", "angle_deg": 45},
        {"action": "grab"},
        {"action": "release"}
    ]

    print("ROS2 Command Conversion Tests")
    print("=" * 40)

    for cmd in test_commands:
        ros2_msg = command_to_ros2(cmd)
        ws_msg = ros2_to_websocket_msg(
            ros2_msg,
            "/robot/cmd_vel"
        )
        print(f"\nInput: {cmd}")
        print(f"ROS2:  {json.dumps(ros2_msg, indent=2)}")
