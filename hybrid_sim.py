"""
hybrid_sim.py - Hybrid simulation/hardware executor.
Uses real hardware if available, falls back to simulator.
"""

from typing import Optional, Dict, Any
from simulator import RobotSimulator
from hardware import (
    get_hardware, 
    is_hardware_available, 
    init_hardware,
    RobotHardware
)


class HybridExecutor:
    """
    Executes commands on either real hardware or simulator.
    Seamlessly switches between modes.
    """
    
    def __init__(self, try_hardware: bool = True):
        """
        Initialize executor.
        
        Args:
            try_hardware: If True, attempt to connect to real hardware
        """
        self.simulator = RobotSimulator(use_3d=True)  # Use 3D physics simulation
        self.hardware: Optional[RobotHardware] = None
        self.mode: str = "simulator"
        
        if try_hardware:
            self.hardware = init_hardware(auto_detect=True)
            if self.hardware and self.hardware.is_connected():
                self.mode = "hardware"
                print("[HybridExecutor] Using REAL HARDWARE")
            else:
                print("[HybridExecutor] Using SIMULATOR (hardware not available)")
    
    def execute(
        self,
        action: str,
        direction: Optional[str] = None,
        distance_cm: Optional[float] = None,
        angle_deg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute command on hardware or simulator.
        
        Returns result dict with same format either way.
        """
        if self.mode == "hardware" and self.hardware:
            return self._execute_hardware(action, direction, distance_cm, angle_deg)
        else:
            return self._execute_simulator(action, direction, distance_cm, angle_deg)
    
    def _execute_hardware(
        self,
        action: str,
        direction: Optional[str] = None,
        distance_cm: Optional[float] = None,
        angle_deg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute on real hardware."""
        try:
            result = self.hardware.execute(
                action=action,
                direction=direction,
                distance_cm=distance_cm,
                angle_deg=angle_deg
            )
            
            # Ensure response has required fields
            if "success" not in result:
                result["success"] = False
            
            return result
            
        except Exception as e:
            print(f"[HybridExecutor] Hardware execution error: {e}")
            # Fall back to simulator
            print("[HybridExecutor] Falling back to simulator")
            self.mode = "simulator"
            return self._execute_simulator(action, direction, distance_cm, angle_deg)
    
    def _execute_simulator(
        self,
        action: str,
        direction: Optional[str] = None,
        distance_cm: Optional[float] = None,
        angle_deg: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute on simulator."""
        return self.simulator.execute(
            action=action,
            direction=direction,
            distance_cm=distance_cm,
            angle_deg=angle_deg
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current robot status."""
        status = {
            "mode": self.mode,
            "hardware_available": self.hardware is not None and self.hardware.is_connected()
        }
        
        if self.mode == "hardware" and self.hardware:
            hw_status = self.hardware.get_status()
            status.update(hw_status)
        else:
            status.update(self.simulator.get_status())
        
        return status
    
    def close(self) -> None:
        """Close hardware connection if open."""
        if self.hardware:
            self.hardware.disconnect()
        self.mode = "simulator"
