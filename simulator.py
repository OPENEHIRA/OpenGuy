"""
simulator.py - Robot arm simulator with state tracking and validation.
Tracks position, orientation, and gripper state.
"""

from typing import Optional, Dict, Any


class RobotSimulator:
    """Simulates a 2D robot arm with position, rotation, and gripper control."""
    
    # Workspace boundaries (in cm)
    MIN_X = -100.0
    MAX_X = 100.0
    MIN_Y = -100.0
    MAX_Y = 100.0
    
    def __init__(self):
        """Initialize robot at origin (0, 0) facing north."""
        self.x: float = 0.0
        self.y: float = 0.0
        self.facing: float = 0  # degrees, 0 = north
        self.gripper_open: bool = True
        self.command_count: int = 0
        print("[EchoArm] Robot initialized at position (0, 0)")

    def execute(
        self,
        action: str,
        direction: Optional[str] = None,
        distance_cm: Optional[float] = None,
        angle_deg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute a robot command.
        
        Args:
            action: One of "move", "rotate", "grab", "release", "stop"
            direction: For moves/rotations: "forward", "backward", "left", "right", "up", "down"
            distance_cm: Distance in centimetres (for moves)
            angle_deg: Angle in degrees (for rotations)
            
        Returns:
            Dict with execution result details
            
        Raises:
            ValueError: If parameters are invalid
        """
        self.command_count += 1
        result: Dict[str, Any] = {"success": True}

        if action == "move":
            if not direction or distance_cm is None:
                raise ValueError("Move requires direction and distance_cm")
            result["movement"] = self._execute_move(direction, distance_cm)

        elif action == "rotate":
            if not direction or angle_deg is None:
                raise ValueError("Rotate requires direction and angle_deg")
            result["rotation"] = self._execute_rotate(direction, angle_deg)

        elif action == "grab":
            result["gripper"] = self._execute_grab()

        elif action == "release":
            result["gripper"] = self._execute_release()

        elif action == "stop":
            result["status"] = "Robot stopped. Holding position."

        elif action == "unknown":
            raise ValueError("Unknown action")

        else:
            raise ValueError(f"Invalid action: {action}")

        # Always include current status
        result["status"] = self._get_status_str()
        return result

    def _execute_move(self, direction: str, distance: float) -> str:
        """Execute a movement command and return status message."""
        if distance <= 0:
            raise ValueError(f"Distance must be positive, got {distance}")
        if distance > 100:
            raise ValueError(f"Distance too large (max 100 cm), got {distance}")

        old_x, old_y = self.x, self.y

        if direction == "forward":
            self.y += distance
        elif direction == "backward":
            self.y -= distance
        elif direction == "left":
            self.x -= distance
        elif direction == "right":
            self.x += distance
        elif direction == "up":
            self.y += distance  # For 2D, treat up as forward
        elif direction == "down":
            self.y -= distance  # For 2D, treat down as backward
        else:
            self.x, self.y = old_x, old_y
            raise ValueError(f"Invalid direction: {direction}")

        # Enforce workspace boundaries
        self.x = max(self.MIN_X, min(self.MAX_X, self.x))
        self.y = max(self.MIN_Y, min(self.MAX_Y, self.y))

        moved_str = f"{distance} cm" if distance != int(distance) else f"{int(distance)} cm"
        return f"Moved {direction} {moved_str} → Position: ({self.x:.1f}, {self.y:.1f})"

    def _execute_rotate(self, direction: str, angle: float) -> str:
        """Execute a rotation command and return status message."""
        if angle <= 0:
            raise ValueError(f"Angle must be positive, got {angle}")
        if angle > 360:
            raise ValueError(f"Angle too large (max 360°), got {angle}")

        if direction == "left":
            self.facing = (self.facing - angle) % 360
        elif direction == "right":
            self.facing = (self.facing + angle) % 360
        else:
            raise ValueError(f"Invalid rotation direction: {direction}")

        angle_str = f"{int(angle)}°" if angle == int(angle) else f"{angle:.1f}°"
        return f"Rotated {direction} {angle_str} → Facing: {int(self.facing)}°"

    def _execute_grab(self) -> str:
        """Execute a grab/grasp command."""
        self.gripper_open = False
        return "Gripper CLOSED — object grabbed ✓"

    def _execute_release(self) -> str:
        """Execute a release/drop command."""
        self.gripper_open = True
        return "Gripper OPEN — object released ✓"

    def _get_status_str(self) -> str:
        """Get current robot status as a formatted string."""
        gripper = "Open" if self.gripper_open else "Closed"
        return f"Pos: ({self.x:.1f}, {self.y:.1f}) | Facing: {int(self.facing)}° | Gripper: {gripper}"

    def get_status(self) -> Dict[str, Any]:
        """Get current robot status as a dictionary."""
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "facing": round(self.facing, 1),
            "gripper_open": self.gripper_open,
            "commands_executed": self.command_count,
            "workspace": {
                "x_bounds": [self.MIN_X, self.MAX_X],
                "y_bounds": [self.MIN_Y, self.MAX_Y],
            }
        }

    def _status(self):
        """Legacy method for CLI output."""
        print(f"[Robot] {self._get_status_str()}\n")
