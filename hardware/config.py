"""
hardware/config.py — Load hardware configuration from hardware.json.

Reads which backend to use and its connection settings.
If hardware.json doesn't exist, falls back to simulator (safe default).
"""

import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path("hardware.json")

DEFAULTS: Dict[str, Any] = {
    "backend": "simulator",
    "use_3d": False,
    "ros": {
        "host": "localhost",
        "port": 9090,
        "command_topic": "/openguy/command",
        "status_topic": "/openguy/status",
    },
    "iot": {
        "protocol": "serial",
        "port": "COM3",
        "baud": 115200,
        "mqtt_host": "localhost",
        "mqtt_port": 1883,
        "mqtt_topic": "openguy/command",
    },
}


def load_config() -> Dict[str, Any]:
    """
    Load hardware.json, falling back to defaults if missing or broken.

    Returns:
        Config dict with "backend" key and per-backend settings.
    """
    if not CONFIG_FILE.exists():
        print(f"[Hardware] {CONFIG_FILE} not found — using defaults (simulator)")
        return DEFAULTS.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        # Merge with defaults so missing keys don't crash anything
        merged = DEFAULTS.copy()
        merged.update(config)
        return merged
    except (json.JSONDecodeError, OSError) as e:
        print(f"[Hardware] Failed to read {CONFIG_FILE}: {e} — using defaults")
        return DEFAULTS.copy()


def get_backend_name() -> str:
    """Return the active backend name ('simulator', 'ros', 'iot')."""
    return load_config().get("backend", "simulator")
