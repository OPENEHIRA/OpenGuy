"""
simulator.py - Robot arm simulator with state tracking and validation.
Tracks position, orientation, and gripper state.
"""

import math
from typing import Optional, Dict, Any
from hardware.base import HardwareBackend

try:
    import pybullet as p
    PYBULLET_AVAILABLE = True
except ImportError:
    PYBULLET_AVAILABLE = False
    p = None


class RobotSimulator(HardwareBackend):
    """Simulates a 2D robot arm with position, rotation, and gripper control."""
    
    # Workspace boundaries (in cm)
    MIN_X = -100.0
    MAX_X = 100.0
    MIN_Y = -100.0
    MAX_Y = 100.0
    
    def __init__(self, use_3d: bool = True):
        """Initialize robot at origin (0, 0) facing north."""
        self.use_3d = use_3d  # Enable 3D physics simulation
        self.x: float = 0.0
        self.y: float = 0.0
        self.facing: float = 0  # degrees, 0 = north
        self.gripper_open: bool = True
        self.command_count: int = 0
        
        if self.use_3d and PYBULLET_AVAILABLE:
            self._init_pybullet()
            print("[Simulator] 3D PyBullet simulation initialized")
        else:
            self.use_3d = False
            print("[Simulator] 2D simulation initialized")

    def _init_pybullet(self):
        """Initialize PyBullet physics simulation."""
        self.physics_client = p.connect(p.DIRECT)  # Headless mode
        if self.physics_client == -1:
            self.use_3d = False
            print("[Simulator] PyBullet connection failed, using 2D fallback")
            return
        p.setGravity(0, 0, 0)  # Disable gravity for top-down simulation
        # p.setAdditionalSearchPath(pybullet_data.getDataPath())
        
        # Load ground plane
        # self.plane_id = p.loadURDF("plane.urdf")
        
        # Create simple robot: base box
        base_collision = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.05, 0.05, 0.025])
        base_visual = -1  # No visual for now
        
        self.robot_id = p.createMultiBody(
            baseMass=1.0,
            baseCollisionShapeIndex=base_collision,
            baseVisualShapeIndex=base_visual,
            basePosition=[0, 0, 0.025],
            baseOrientation=p.getQuaternionFromEuler([0, 0, 0])
        )
        
        if self.robot_id == -1:
            self.use_3d = False
            print("[Simulator] PyBullet createMultiBody failed, using 2D fallback")
            p.disconnect(self.physics_client)
            return
        
        # Create gripper as separate body
        gripper_collision = p.createCollisionShape(p.GEOM_BOX, halfExtents=[0.01, 0.01, 0.02])
        gripper_visual = p.createVisualShape(p.GEOM_BOX, halfExtents=[0.01, 0.01, 0.02], 
                                           rgbaColor=[0.2, 0.2, 0.2, 1])
        
        self.gripper_id = p.createMultiBody(
            baseMass=0.1,
            baseCollisionShapeIndex=gripper_collision,
            baseVisualShapeIndex=gripper_visual,
            basePosition=[0, 0, 0.07],  # Above base
            baseOrientation=[0, 0, 0, 1]
        )
        
        # Attach gripper to robot base with fixed joint
        p.createConstraint(self.robot_id, -1, self.gripper_id, -1, p.JOINT_FIXED, 
                         [0, 0, 0], [0, 0, 0], [0, 0, 0.045])
        
        # Step simulation to settle
        for _ in range(10):
            p.stepSimulation()

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

        if self.use_3d:
            return self._execute_3d(action, direction, distance_cm, angle_deg)
        else:
            return self._execute_2d(action, direction, distance_cm, angle_deg)

    def _execute_3d(self, action, direction, distance_cm, angle_deg):
        """Execute command in 3D PyBullet simulation."""
        result = {"success": True}
        
        if action == "move":
            result["movement"] = self._execute_move_3d(direction, distance_cm)
        elif action == "rotate":
            result["rotation"] = self._execute_rotate_3d(direction, angle_deg)
        elif action == "grab":
            result["gripper"] = self._execute_grab_3d()
        elif action == "release":
            result["gripper"] = self._execute_release_3d()
        elif action == "stop":
            result["status"] = "Robot stopped. Holding position."
        else:
            raise ValueError(f"Invalid action: {action}")
        
        # Update internal state from PyBullet
        self._sync_state_from_pybullet()
        
        # Always include current status
        result["status"] = self._get_status_str()
        return result

    def _execute_move_3d(self, direction, distance):
        """Execute movement in 3D space."""
        if not direction or distance is None:
            raise ValueError("Move requires direction and distance")
        
        distance_m = distance / 100.0  # Convert cm to meters
        
        # Get current position and orientation
        pos, orn = p.getBasePositionAndOrientation(self.robot_id)
        euler = p.getEulerFromQuaternion(orn)
        current_angle = euler[2]  # Z rotation
        
        # Calculate target position
        if direction == "forward":
            dx = distance_m * math.sin(current_angle)
            dy = distance_m * math.cos(current_angle)
        elif direction == "backward":
            dx = -distance_m * math.sin(current_angle)
            dy = -distance_m * math.cos(current_angle)
        elif direction == "left":
            dx = -distance_m * math.cos(current_angle)
            dy = distance_m * math.sin(current_angle)
        elif direction == "right":
            dx = distance_m * math.cos(current_angle)
            dy = -distance_m * math.sin(current_angle)
        else:
            raise ValueError(f"Invalid direction: {direction}")
        
        target_x = pos[0] + dx
        target_y = pos[1] + dy
        
        # Enforce boundaries
        target_x = max(self.MIN_X, min(self.MAX_X, target_x))
        target_y = max(self.MIN_Y, min(self.MAX_Y, target_y))
        
        # Move robot to new position
        p.resetBasePositionAndOrientation(self.robot_id, [target_x, target_y, pos[2]], [0, 0, 0, 1])
        
        # Step simulation to update
        # p.stepSimulation()
        
        moved_str = f"{distance} cm" if distance != int(distance) else f"{int(distance)} cm"
        return f"Moved {direction} {moved_str} → Position: ({target_x:.2f}, {target_y:.2f})"

    def _execute_rotate_3d(self, direction, angle):
        """Execute rotation in 3D space."""
        if not direction or angle is None:
            raise ValueError("Rotate requires direction and angle")
        
        pos, orn = p.getBasePositionAndOrientation(self.robot_id)
        euler = p.getEulerFromQuaternion(orn)
        
        if direction == "left":
            new_angle = euler[2] + math.radians(angle)
        elif direction == "right":
            new_angle = euler[2] - math.radians(angle)
        else:
            raise ValueError(f"Invalid rotation direction: {direction}")
        
        new_orn = p.getQuaternionFromEuler([euler[0], euler[1], new_angle])
        p.resetBasePositionAndOrientation(self.robot_id, pos, new_orn)
        
        angle_str = f"{int(angle)}°" if angle == int(angle) else f"{angle:.1f}°"
        return f"Rotated {direction} {angle_str} → Facing: {math.degrees(new_angle):.0f}°"

    def _execute_grab_3d(self):
        """Execute grab command."""
        # Move gripper down (close)
        p.resetBasePositionAndOrientation(self.gripper_id, [0, 0, 0.045], [0, 0, 0, 1])
        self.gripper_open = False
        return "Gripper CLOSED — object grabbed ✓"

    def _execute_release_3d(self):
        """Execute release command."""
        # Move gripper up (open)
        p.resetBasePositionAndOrientation(self.gripper_id, [0, 0, 0.07], [0, 0, 0, 1])
        self.gripper_open = True
        return "Gripper OPEN — object released ✓"

    def _sync_state_from_pybullet(self):
        """Sync internal state from PyBullet simulation."""
        pos, orn = p.getBasePositionAndOrientation(self.robot_id)
        euler = p.getEulerFromQuaternion(orn)
        
        self.x = pos[0] * 100  # Convert to cm
        self.y = pos[1] * 100
        self.facing = math.degrees(euler[2])

    def _execute_2d(self, action, direction, distance_cm, angle_deg):
        """Fallback 2D execution (original logic)."""
        result: Dict[str, Any] = {"success": True}

        if action == "move":
            if not direction or distance_cm is None:
                raise ValueError("Move requires direction and distance_cm")
            result["movement"] = self._execute_move_2d(direction, distance_cm)

        elif action == "rotate":
            if not direction or angle_deg is None:
                raise ValueError("Rotate requires direction and angle_deg")
            result["rotation"] = self._execute_rotate_2d(direction, angle_deg)

        elif action == "grab":
            result["gripper"] = self._execute_grab_2d()

        elif action == "release":
            result["gripper"] = self._execute_release_2d()

        elif action == "stop":
            result["status"] = "Robot stopped. Holding position."

        else:
            raise ValueError(f"Invalid action: {action}")

        # Always include current status
        result["status"] = self._get_status_str()
        return result

    def _execute_move_2d(self, direction: str, distance: float) -> str:
        """Execute a movement command and return status message."""
        print(f"DEBUG: direction={direction}, distance={distance}, self.y before={self.y}")
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
        print(f"DEBUG: self.y after={self.y}")
        return f"Moved {direction} {moved_str} → Position: ({self.x:.1f}, {self.y:.1f})"

    def _execute_rotate_2d(self, direction: str, angle: float) -> str:
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

    def _execute_grab_2d(self) -> str:
        """Execute a grab/grasp command."""
        self.gripper_open = False
        return "Gripper CLOSED — object grabbed ✓"

    def _execute_release_2d(self) -> str:
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
                "x_bounds": [self.MIN_X * 100, self.MAX_X * 100],
                "y_bounds": [self.MIN_Y * 100, self.MAX_Y * 100],
            },
            "simulation_mode": "3d" if self.use_3d else "2d"
        }

    def __del__(self):
        """Cleanup PyBullet on destruction."""
        if self.use_3d and hasattr(self, 'physics_client'):
            p.disconnect(self.physics_client)

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

    # ── HardwareBackend contract ──────────────────────────────────────────────

    def connect(self) -> bool:
        """Simulator needs no connection — always ready."""
        print("[Simulator] Ready (in-memory simulation)")
        return True

    def disconnect(self) -> None:
        """Nothing to close."""
        pass

    def is_connected(self) -> bool:
        return True

    def reset(self) -> None:
        """Reset to initial state."""
        self.x = 0.0
        self.y = 0.0
        self.facing = 0.0
        self.gripper_open = True
        self.command_count = 0
        print("[Simulator] Reset to initial state")

    @property
    def name(self) -> str:
        return "simulator"
