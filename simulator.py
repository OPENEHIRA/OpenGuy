# simulator.py
# Mock robot simulator — prints robot state changes

class RobotSimulator:
    def __init__(self):
        # Robot starts at position (0, 0) facing "north"
        self.x = 0.0
        self.y = 0.0
        self.facing = 0  # degrees, 0 = north
        self.gripper_open = True
        print("[EchoArm] Robot initialized at position (0, 0)")

    def execute(self, command):
        action = command.get("action")

        if action == "move":
            direction = command["direction"]
            dist = command["distance_cm"]

            if direction == "forward":
                self.y += dist
            elif direction == "backward":
                self.y -= dist
            elif direction == "left":
                self.x -= dist
            elif direction == "right":
                self.x += dist

            print(f"[Robot] Moved {direction} {dist} cm → Position: ({self.x}, {self.y})")

        elif action == "rotate":
            direction = command["direction"]
            angle = command["angle_deg"]

            if direction == "left":
                self.facing = (self.facing - angle) % 360
            else:
                self.facing = (self.facing + angle) % 360

            print(f"[Robot] Rotated {direction} {angle}° → Facing: {self.facing}°")

        elif action == "stop":
            print("[Robot] Stopped. Holding position.")

        elif action == "grab":
            self.gripper_open = False
            print("[Robot] Gripper CLOSED — object grabbed.")

        elif action == "release":
            self.gripper_open = True
            print("[Robot] Gripper OPEN — object released.")

        elif action == "unknown":
            print(f"[Robot] Could not understand command: '{command.get('raw')}'")

        else:
            print("[Robot] No action taken.")

        self._status()

    def _status(self):
        gripper = "Open" if self.gripper_open else "Closed"
        print(f"         Status → Pos: ({self.x}, {self.y}) | Facing: {self.facing}° | Gripper: {gripper}\n")
