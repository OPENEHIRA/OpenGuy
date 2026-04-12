"""
hardware.py - Hardware abstraction layer for real robot arms.
Supports USB/Serial connections to physical robots.
Auto-detects and manages hardware connections.
"""

import serial
import json
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class RobotType(Enum):
    """Supported robot hardware types."""
    UNKNOWN = "unknown"
    ARDUINO_ARM = "arduino_arm"  # DIY Arduino-based 5-DOF arm
    UR_ROBOT = "ur_robot"  # Universal Robots UR3/UR5/UR10
    ABB_ROBO = "abb_robo"  # ABB IRB robots
    DOBOT = "dobot"  # Dobot Magician
    PHANTOM_X = "phantom_x"  # PhantomX Pincher robot
    SIMULATOR = "simulator"  # Fallback to simulator


@dataclass
class HardwareInfo:
    """Information about detected hardware."""
    robot_type: RobotType
    port: str
    baudrate: int
    name: str
    description: str


class RobotHardware(ABC):
    """Abstract base class for hardware implementations."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the hardware. Returns True if successful."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the hardware."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if hardware is connected."""
        pass
    
    @abstractmethod
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a robot action. Returns result dict."""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get current hardware status."""
        pass


class ArduinoArmHardware(RobotHardware):
    """Handler for DIY Arduino-based robot arms."""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial: Optional[serial.Serial] = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to Arduino via USB/Serial."""
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            self.connected = True
            print(f"[Hardware] Connected to Arduino arm on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"[Hardware] Failed to connect: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Arduino."""
        if self.serial:
            self.serial.close()
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self.connected and self.serial is not None
    
    def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Send command to Arduino via JSON protocol.
        
        Arduino expects JSON like:
        {"action": "move", "direction": "forward", "distance": 10}
        
        Arduino responds with:
        {"success": true, "status": "moved 10cm forward"}
        """
        if not self.is_connected():
            return {"success": False, "error": "Hardware not connected"}
        
        try:
            # Build command JSON
            command = {"action": action, **kwargs}
            command_str = json.dumps(command) + "\n"
            
            # Send to Arduino
            self.serial.write(command_str.encode())
            
            # Read response with timeout
            response_line = self.serial.readline().decode().strip()
            if not response_line:
                return {"success": False, "error": "No response from hardware"}
            
            response = json.loads(response_line)
            return response
            
        except (serial.SerialException, json.JSONDecodeError) as e:
            return {"success": False, "error": f"Communication error: {e}"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get Arduino arm status."""
        if not self.is_connected():
            return {"connected": False, "error": "Not connected"}
        
        try:
            # Send status request
            status_cmd = json.dumps({"action": "status"}) + "\n"
            self.serial.write(status_cmd.encode())
            
            response_line = self.serial.readline().decode().strip()
            response = json.loads(response_line)
            response["connected"] = True
            return response
            
        except Exception as e:
            return {"connected": True, "error": f"Status error: {e}"}


class HardwareDetector:
    """Auto-detects connected robot hardware."""
    
    @staticmethod
    def scan_ports() -> List[HardwareInfo]:
        """
        Scan available serial ports and identify robot hardware.
        
        Returns list of detected hardware.
        """
        try:
            import serial.tools.list_ports
        except ImportError:
            print("[Hardware] pyserial not available, skipping hardware detection")
            return []
        
        detected = []
        
        # Scan all available ports
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            info = HardwareDetector._identify_port(port)
            if info:
                detected.append(info)
        
        return detected
    
    @staticmethod
    def _identify_port(port) -> Optional[HardwareInfo]:
        """Identify what's on a given port."""
        # Arduino boards typically show as "Arduino" or "CH340"
        if "Arduino" in port.description or "CH340" in port.description:
            return HardwareInfo(
                robot_type=RobotType.ARDUINO_ARM,
                port=port.device,
                baudrate=115200,
                name="Arduino Robot Arm",
                description=port.description
            )
        
        # Universal Robots connect via network, not serial
        # (would need separate TCP/IP handler)
        
        # Add more robot types as needed
        
        return None
    
    @staticmethod
    def connect_first_available() -> Optional[RobotHardware]:
        """
        Auto-detect and connect to first available hardware.
        
        Returns connected hardware object or None.
        """
        detected = HardwareDetector.scan_ports()
        
        if not detected:
            print("[Hardware] No compatible hardware detected")
            return None
        
        # Try to connect to first detected hardware
        hardware_info = detected[0]
        print(f"[Hardware] Detected: {hardware_info.name} on {hardware_info.port}")
        
        # Create appropriate handler based on type
        if hardware_info.robot_type == RobotType.ARDUINO_ARM:
            hardware = ArduinoArmHardware(hardware_info.port, hardware_info.baudrate)
            if hardware.connect():
                return hardware
        
        return None


# Global hardware instance
_hardware: Optional[RobotHardware] = None


def init_hardware(auto_detect: bool = True) -> Optional[RobotHardware]:
    """
    Initialize hardware connection.
    
    Args:
        auto_detect: If True, scan for hardware automatically
        
    Returns:
        Connected hardware object or None
    """
    global _hardware
    
    if auto_detect:
        _hardware = HardwareDetector.connect_first_available()
    
    return _hardware


def get_hardware() -> Optional[RobotHardware]:
    """Get current hardware connection."""
    return _hardware


def close_hardware() -> None:
    """Close hardware connection."""
    global _hardware
    if _hardware:
        _hardware.disconnect()
        _hardware = None


def is_hardware_available() -> bool:
    """Check if hardware is connected."""
    return _hardware is not None and _hardware.is_connected()
