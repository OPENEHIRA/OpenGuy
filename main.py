"""
main.py — EchoArm entry point
Chat-loop that accepts natural language commands and dispatches them
to the simulator via the AI-powered parser.
"""

import json
from parser import parse


def simulate(command):
    """Placeholder simulator — replace with your real simulator.simulate() call."""
    action = command.get("action")
    direction = command.get("direction", "")
    distance = command.get("distance_cm")
    angle = command.get("angle_deg")

    if action == "move":
        dist_str = f"{distance} cm" if distance else "a short distance"
        print(f"[Simulator] Moving {direction} {dist_str}... ✓")
    elif action == "rotate":
        angle_str = f"{angle}°" if angle else "~15°"
        print(f"[Simulator] Rotating {direction} {angle_str}... ✓")
    elif action == "grab":
        print("[Simulator] Closing gripper... ✓")
    elif action == "release":
        print("[Simulator] Opening gripper... ✓")
    elif action == "stop":
        print("[Simulator] Halting all movement... ✓")
    else:
        print(f"[Simulator] Unknown action: {action}")


def run():
    print("=" * 45)
    print("  EchoArm — Natural Language Robot Control")
    print("=" * 45)
    print("Type a command in plain English, or 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[EchoArm] Shutting down.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("[EchoArm] Goodbye.")
            break

        command = parse(user_input)

        confidence = command.get("confidence", 0)
        print(f"[Parsed] {json.dumps(command)}")
        if confidence < 0.5:
            print("[EchoArm] Low confidence — I may have misunderstood.")

        if command["action"] in (None, "unknown"):
            print("[EchoArm] Sorry, I didn't understand that command.\n")
            continue

        simulate(command)
        print()


if __name__ == "__main__":
    run()
