"""
Flask web application for OpenGuy robot control interface.
Serves the HTML UI and provides REST API endpoints for parsing and simulation.
"""

import os
import json
import urllib.request
import urllib.error
from typing import Any, Dict
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template_string, request, jsonify
from parser import parse
from hardware import HardwareManager
from chain_executor import parse_command_chain, execute_chain_step, get_chain_status, reset_chain
from visualizer import get_workspace_visualization
from speech import get_transcription_service_status

# ── Flask Setup ──────────────────────────────────────────────────────────────

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

# Global hardware manager — routes commands to simulator / ROS / IoT
# Change "backend" in hardware.json to switch targets (no code change needed)
robot = HardwareManager()

# Command history file
HISTORY_FILE = Path("command_history.json")


def load_history() -> list[Dict[str, Any]]:
    """Load command history from disk."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_history(history: list[Dict[str, Any]]) -> None:
    """Save command history to disk, keeping last 50."""
    # Keep last 50 commands
    history = history[-50:]
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except OSError as e:
        print(f"[EchoArm] Failed to save history: {e}")


def format_sim_result(result: Dict[str, str]) -> list[str]:
    """Convert simulator result to display-friendly lines."""
    lines = []
    if "movement" in result:
        lines.append(f"[MOVE] {result['movement']}")
    if "rotation" in result:
        lines.append(f"[ROTATE] {result['rotation']}")
    if "gripper" in result:
        lines.append(f"[GRIP] {result['gripper']}")
    if "status" in result:
        lines.append(f"[STATUS] {result['status']}")
    return lines


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main HTML UI."""
    with open("index.html", "r") as f:
        return render_template_string(f.read())


@app.route("/api/parse", methods=["POST"])
def api_parse():
    """Parse a natural language command."""
    data = request.get_json() or {}
    command_text = data.get("command", "").strip()
    api_key = data.get("api_key", os.getenv("ANTHROPIC_API_KEY"))

    if not command_text:
        return jsonify({"error": "Empty command"}), 400

    try:
        parsed = parse(command_text, api_key=api_key, use_ai=True)
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": f"Parse error: {str(e)}"}), 500


@app.route("/api/execute", methods=["POST"])
def api_execute():
    """Execute a parsed command on the simulator."""
    data = request.get_json() or {}

    # Validate required fields
    action = data.get("action")
    if not action:
        return jsonify({"error": "No action specified"}), 400

    try:
        result = robot.execute(
            action=action,
            direction=data.get("direction"),
            distance_cm=data.get("distance_cm"),
            angle_deg=data.get("angle_deg"),
        )

        # Add to history
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "command": data.get("raw", "unknown"),
            "parsed": data,
            "result": result,
        })
        save_history(history)

        return jsonify({
            "success": True,
            "result": result,
            "output": format_sim_result(result),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Execution error: {str(e)}"}), 500


@app.route("/api/status", methods=["GET"])
def api_status():
    """Get current robot status."""
    return jsonify(robot.get_status())


@app.route("/api/reset", methods=["POST"])
def api_reset():
    """Reset the robot to initial state."""
    robot.reset()
    return jsonify({"success": True, "message": "Robot reset to initial state"})


@app.route("/api/history", methods=["GET"])
def api_history():
    """Get command history."""
    history = load_history()
    return jsonify({"history": history[-20:]})  # Return last 20


@app.route("/api/history/clear", methods=["POST"])
def api_history_clear():
    """Clear all command history."""
    try:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        return jsonify({"success": True, "message": "History cleared"})
    except OSError as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def api_health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "robot_status": robot.get_status(),
        "timestamp": datetime.now().isoformat(),
    })


# ── Chain Execution Routes ───────────────────────────────────────────────────

@app.route("/api/chain/parse", methods=["POST"])
def api_chain_parse():
    """Parse a multi-step command chain."""
    data = request.get_json() or {}
    command_text = data.get("command", "").strip()
    api_key = data.get("api_key", os.getenv("ANTHROPIC_API_KEY"))

    if not command_text:
        return jsonify({"error": "Empty command"}), 400

    try:
        result = parse_command_chain(command_text, api_key=api_key)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Chain parse error: {str(e)}"}), 500


@app.route("/api/chain/status", methods=["GET"])
def api_chain_status():
    """Get current chain execution status."""
    return jsonify(get_chain_status())


@app.route("/api/chain/execute", methods=["POST"])
def api_chain_execute():
    """Execute a single step in the command chain."""
    data = request.get_json() or {}
    
    action = data.get("action")
    if not action:
        return jsonify({"error": "No action specified"}), 400

    try:
        # Execute the command
        result = robot.execute(
            action=action,
            direction=data.get("direction"),
            distance_cm=data.get("distance_cm"),
            angle_deg=data.get("angle_deg"),
        )

        # Record result and get next step
        chain_result = execute_chain_step(result)
        
        # Add to history
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "command": data.get("raw", "unknown"),
            "parsed": data,
            "result": result,
            "is_chain_step": True,
        })
        save_history(history)

        return jsonify({
            "success": True,
            "result": result,
            "output": format_sim_result(result),
            "chain_progress": chain_result["progress"],
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Execution error: {str(e)}"}), 500


@app.route("/api/chain/reset", methods=["POST"])
def api_chain_reset():
    """Reset the command chain executor."""
    reset_chain()
    return jsonify({"success": True, "message": "Chain reset"})


@app.route("/api/visualize", methods=["GET"])
def api_visualize():
    """Get 2D workspace visualization as SVG."""
    svg = get_workspace_visualization(robot.get_status())
    return svg, 200, {"Content-Type": "image/svg+xml"}


@app.route("/api/speech/status", methods=["GET"])
def api_speech_status():
    """Check available speech-to-text services."""
    return jsonify(get_transcription_service_status())


# ── Error Handlers ───────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({"error": "Internal server error"}), 500


@app.route("/api/groq-parse", methods=["POST"])
def groq_parse():
    """Proxy Groq API call to avoid CORS issues."""
    data = request.get_json() or {}
    command_text = data.get("command", "").strip()
    api_key = data.get("api_key", "")

    if not command_text:
        return jsonify({"error": "Empty command"}), 400

    if not api_key:
        return jsonify({"action": "move", "direction": "forward", "distance_cm": 10, "confidence": 0.5, "raw": command_text})

    try:
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a robot arm command parser. Extract action, direction, and distance from commands. Respond ONLY with JSON like: {\"action\":\"move\",\"direction\":\"forward\",\"distance_cm\":10,\"confidence\":0.95}"
                },
                {
                    "role": "user",
                    "content": command_text
                }
            ],
            "max_tokens": 100,
            "temperature": 0.1
        }

        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            raw = result["choices"][0]["message"]["content"].strip()
            parsed = json.loads(raw)
            parsed["raw"] = command_text
            return jsonify(parsed)

    except Exception as e:
        return jsonify({"action": "move", "direction": "forward", "distance_cm": 10, "confidence": 0.5, "raw": command_text, "error": str(e)})


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  OpenGuy - Robot Control Interface")
    print("=" * 50)
    print("\n[OK] Starting Flask server...")
    print("[OK] Open http://localhost:5000 in your browser")
    print("[OK] API docs: http://localhost:5000/api/health\n")

    # Setup Telegram bot webhook if token is provided
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if telegram_token:
        try:
            from telegram_webhook import setup_telegram_webhook
            setup_telegram_webhook(app, robot)
            print("[OK] Telegram bot enabled")
        except Exception as e:
            print(f"[WARN] Telegram bot setup failed: {e}")
    else:
        print("[INFO] Set TELEGRAM_BOT_TOKEN env var to enable Telegram bot")
    
    # Setup WhatsApp bot webhook if Twilio credentials provided
    twilio_creds = [
        os.getenv("TWILIO_ACCOUNT_SID"),
        os.getenv("TWILIO_AUTH_TOKEN"),
        os.getenv("TWILIO_WHATSAPP_NUMBER")
    ]
    if all(twilio_creds):
        try:
            from whatsapp_webhook import setup_whatsapp_webhook
            setup_whatsapp_webhook(app, robot)
            print("[OK] WhatsApp bot enabled")
        except Exception as e:
            print(f"[WARN] WhatsApp bot setup failed: {e}")
    else:
        print("[INFO] Set TWILIO_* env vars to enable WhatsApp bot")

    app.run(debug=True, host="0.0.0.0", port=5000)
	


@app.route("/api/arm/visualize", methods=["GET"])
def api_arm_visualize():
    from kinematics_visualizer import generate_arm_svg
    x = float(request.args.get("x", 100))
    y = float(request.args.get("y", 50))
    svg = generate_arm_svg(x, y)
    return svg, 200, {"Content-Type": "image/svg+xml"}
