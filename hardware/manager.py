"""
hardware/manager.py — Picks and manages the active hardware backend.

This is the only file app.py talks to. It reads hardware.json, creates
the right backend (simulator / ROS / IoT), and exposes the same interface
that the old RobotSimulator did — so app.py barely changes.

Usage in app.py:
    from hardware import HardwareManager
    robot = HardwareManager()
    robot.execute(action="move", direction="forward", distance_cm=10)
    robot.get_status()
    robot.reset()
"""

from typing import Optional, Dict, Any
from hardware.config import load_config
from hardware.base import HardwareBackend


class HardwareManager:
    """
    Central manager that routes commands to the active hardware backend.

    Reads hardware.json on startup to decide which backend to use.
    Exposes the same interface as RobotSimulator so app.py barely changes.
    """

    def __init__(self):
        self._config = load_config()
        self._backend: HardwareBackend = self._load_backend()
        self._backend.connect()
        print(f"[Hardware] Active backend: {self._backend.name}")

    def _load_backend(self) -> HardwareBackend:
        """Instantiate the correct backend based on config."""
        backend_name = self._config.get("backend", "simulator").lower()

        if backend_name == "simulator":
            from simulator import RobotSimulator
            use_3d = self._config.get("use_3d", True)
            return RobotSimulator(use_3d=use_3d)

        elif backend_name == "ros":
            from hardware.backends.ros_backend import ROSBackend
            ros_cfg = self._config.get("ros", {})
            return ROSBackend(
                host=ros_cfg.get("host", "localhost"),
                port=ros_cfg.get("port", 9090),
            )

        elif backend_name == "iot":
            from hardware.backends.iot_backend import IoTBackend
            iot_cfg = self._config.get("iot", {})
            return IoTBackend(
                protocol=iot_cfg.get("protocol", "serial"),
                port=iot_cfg.get("port", "COM3"),
                baud=iot_cfg.get("baud", 115200),
                mqtt_host=iot_cfg.get("mqtt_host", "localhost"),
                mqtt_port=iot_cfg.get("mqtt_port", 1883),
                mqtt_topic=iot_cfg.get("mqtt_topic", "openguy/command"),
            )

        else:
            print(f"[Hardware] Unknown backend '{backend_name}' — falling back to simulator")
            from simulator import RobotSimulator
            use_3d = self._config.get("use_3d", True)
            return RobotSimulator(use_3d=use_3d)

    # ── Public interface (same as old RobotSimulator) ─────────────────────────

    def execute(
        self,
        action: str,
        direction: Optional[str] = None,
        distance_cm: Optional[float] = None,
        angle_deg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute a command on the active backend."""
        return self._backend.execute(
            action=action,
            direction=direction,
            distance_cm=distance_cm,
            angle_deg=angle_deg,
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current robot status from the active backend."""
        status = self._backend.get_status()
        # Always include backend info so /api/health can report it
        status["active_backend"] = self._backend.name
        status["backend_connected"] = self._backend.is_connected()
        return status

    def reset(self) -> None:
        """Reset the active backend to initial state."""
        self._backend.reset()

    def is_connected(self) -> bool:
        """Check if the active backend is connected to hardware."""
        return self._backend.is_connected()

    @property
    def backend_name(self) -> str:
        """Name of the currently active backend."""
        return self._backend.name
