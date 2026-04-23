"""
gz_web.py - Gazebo web integration for OpenGuy.
Streams Gazebo simulation to browser using gz-web.
Contributed by Emmanuel Olutunmibi
"""

import subprocess
import os
import json
from ros2_bridge import command_to_ros2, get_gazebo_launch_config


def launch_gazebo(world: str = "empty.sdf") -> subprocess.Popen:
    """
    Launch Gazebo simulation.
    
    Args:
        world: Gazebo world file to load
        
    Returns:
        Gazebo process
    """
    config = get_gazebo_launch_config()
    
    try:
        process = subprocess.Popen(
            ["gz", "sim", world, "--headless-rendering"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"[Gazebo] Started with world: {world}")
        return process
    except FileNotFoundError:
        print("[Gazebo] gz not found — is Gazebo installed?")
        return None


def launch_gz_web(port: int = 9091) -> subprocess.Popen:
    """
    Launch gz-web server to stream Gazebo to browser.
    
    Args:
        port: Port to serve gz-web on
        
    Returns:
        gz-web process
    """
    try:
        process = subprocess.Popen(
            ["gz", "web", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print(f"[gz-web] Streaming on port {port}")
        return process
    except FileNotFoundError:
        print("[gz-web] gz web not found — is gz-web installed?")
        return None


def send_command_to_gazebo(parsed_command: dict) -> dict:
    """
    Convert parsed command and send to Gazebo via ROS2.
    
    Args:
        parsed_command: Parsed command dict
        
    Returns:
        Result dict
    """
    ros2_msg = command_to_ros2(parsed_command)
    action = parsed_command.get("action", "move")

    # Determine ROS2 topic based on action
    if action in ["move", "rotate"]:
        topic = "/robot/cmd_vel"
        msg_type = "geometry_msgs/msg/Twist"
    elif action == "grab":
        topic = "/robot/gripper/command"
        msg_type = "control_msgs/msg/GripperCommand"
    elif action == "release":
        topic = "/robot/gripper/command"
        msg_type = "control_msgs/msg/GripperCommand"
    else:
        return {"success": False, "error": f"Unknown action: {action}"}

    try:
        # Publish to ROS2 topic using ros2 CLI
        msg_json = json.dumps(ros2_msg)
        result = subprocess.run(
            ["ros2", "topic", "pub", "--once",
             topic, msg_type, msg_json],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return {
                "success": True,
                "message": f"Command sent to Gazebo: {action}",
                "topic": topic,
                "ros2_msg": ros2_msg
            }
        else:
            return {
                "success": False,
                "error": result.stderr
            }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "ROS2 command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "ROS2 not installed"}


def get_gz_web_embed_html(port: int = 9091) -> str:
    """
    Get HTML to embed gz-web stream in the UI.
    
    Returns:
        HTML iframe string
    """
    return f'''
    <div style="width:100%; height:400px; background:#000; border-radius:8px; overflow:hidden;">
        <iframe 
            src="http://localhost:{port}"
            style="width:100%; height:100%; border:none;"
            title="Gazebo Simulation">
        </iframe>
        <p style="color:#555; font-size:10px; text-align:center; margin:4px;">
            Gazebo Physics Simulation — gz-web
        </p>
    </div>
    '''


if __name__ == "__main__":
    # Test command conversion
    test_cmd = {
        "action": "move",
        "direction": "forward",
        "distance_cm": 30
    }

    print("Testing Gazebo command sending...")
    result = send_command_to_gazebo(test_cmd)
    print(f"Result: {result}")

    print("\nGz-web embed HTML:")
    print(get_gz_web_embed_html())
