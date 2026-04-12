"""
robot_learner.py - Robot Learning and Adaptation System
Enables robots to learn from experience, adapt behavior, and improve over time.

The robot can:
1. Track what works and what fails
2. Learn optimal paths/strategies from history
3. Recover better when facing familiar failures
4. Adapt movement patterns based on success rates
5. Save learned models for future sessions
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class CommandExperience:
    """Represents one execution experience of a command."""
    
    def __init__(self, action: str, direction: Optional[str], distance: Optional[float],
                 angle: Optional[float], success: bool, error: Optional[str] = None,
                 execution_time: float = 0.0, notes: str = ""):
        self.action = action
        self.direction = direction
        self.distance = distance
        self.angle = angle
        self.success = success
        self.error = error
        self.execution_time = execution_time
        self.notes = notes
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "action": self.action,
            "direction": self.direction,
            "distance": self.distance,
            "angle": self.angle,
            "success": self.success,
            "error": self.error,
            "execution_time": self.execution_time,
            "notes": self.notes,
            "timestamp": self.timestamp
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'CommandExperience':
        """Create from dictionary."""
        exp = CommandExperience(
            action=data["action"],
            direction=data["direction"],
            distance=data["distance"],
            angle=data["angle"],
            success=data["success"],
            error=data.get("error"),
            execution_time=data.get("execution_time", 0.0),
            notes=data.get("notes", "")
        )
        exp.timestamp = data["timestamp"]
        return exp


class AdaptiveStrategy:
    """Learned strategy for executing a command."""
    
    def __init__(self, action: str, direction: Optional[str], 
                 base_distance: Optional[float], base_angle: Optional[float]):
        self.action = action
        self.direction = direction
        self.base_distance = base_distance
        self.base_angle = base_angle
        
        # Learning parameters
        self.total_attempts = 0
        self.successful_attempts = 0
        self.total_time = 0.0
        
        # Adaptive modifications
        self.recommended_distance_adjustment = 1.0  # Multiplier
        self.recommended_speed = 1.0  # Multiplier
        self.recommended_max_steps = 1  # Break into smaller steps
        
        # Failure history
        self.failure_reasons: Dict[str, int] = defaultdict(int)
        self.recovery_strategies: Dict[str, str] = {}
        
        # Last updated
        self.last_updated = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate (0.0 to 1.0)."""
        if self.total_attempts == 0:
            return 0.5  # Unknown, assume 50%
        return self.successful_attempts / self.total_attempts
    
    @property
    def average_time(self) -> float:
        """Calculate average execution time."""
        if self.successful_attempts == 0:
            return 0.0
        return self.total_time / self.successful_attempts
    
    def record_attempt(self, success: bool, time_taken: float, error: Optional[str] = None):
        """Record an attempt at this command."""
        self.total_attempts += 1
        if success:
            self.successful_attempts += 1
            self.total_time += time_taken
        else:
            if error:
                self.failure_reasons[error] += 1
        
        self.last_updated = datetime.now()
    
    def should_reduce_step_size(self) -> bool:
        """Check if we should execute in smaller steps."""
        # If many failures, break into smaller chunks
        return self.success_rate < 0.7 and self.total_attempts > 5
    
    def update_strategy(self):
        """Update recommendations based on learning."""
        if self.success_rate < 0.5 and self.total_attempts > 10:
            # Too many failures, reduce distance/angle
            self.recommended_distance_adjustment = 0.75
            self.recommended_speed = 0.8
            self.recommended_max_steps = 3
        elif self.success_rate > 0.95 and self.total_attempts > 15:
            # Doing great, can be more aggressive
            self.recommended_distance_adjustment = 1.1
            self.recommended_speed = 1.1
            self.recommended_max_steps = 1
        elif self.success_rate > 0.8:
            # Good success, normal parameters
            self.recommended_distance_adjustment = 1.0
            self.recommended_speed = 1.0
            self.recommended_max_steps = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "action": self.action,
            "direction": self.direction,
            "base_distance": self.base_distance,
            "base_angle": self.base_angle,
            "total_attempts": self.total_attempts,
            "successful_attempts": self.successful_attempts,
            "total_time": self.total_time,
            "recommended_distance_adjustment": self.recommended_distance_adjustment,
            "recommended_speed": self.recommended_speed,
            "recommended_max_steps": self.recommended_max_steps,
            "failure_reasons": dict(self.failure_reasons),
            "recovery_strategies": self.recovery_strategies,
            "success_rate": self.success_rate,
            "average_time": self.average_time
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AdaptiveStrategy':
        """Create from dictionary."""
        strategy = AdaptiveStrategy(
            action=data["action"],
            direction=data.get("direction"),
            base_distance=data.get("base_distance"),
            base_angle=data.get("base_angle")
        )
        strategy.total_attempts = data.get("total_attempts", 0)
        strategy.successful_attempts = data.get("successful_attempts", 0)
        strategy.total_time = data.get("total_time", 0.0)
        strategy.recommended_distance_adjustment = data.get("recommended_distance_adjustment", 1.0)
        strategy.recommended_speed = data.get("recommended_speed", 1.0)
        strategy.recommended_max_steps = data.get("recommended_max_steps", 1)
        strategy.failure_reasons = defaultdict(int, data.get("failure_reasons", {}))
        strategy.recovery_strategies = data.get("recovery_strategies", {})
        return strategy


class RobotLearner:
    """
    Main learning system for robots.
    
    Tracks command execution, learns from failures, and adapts behavior.
    """
    
    def __init__(self, robot_id: str, learn_dir: str = "robot_learning"):
        """
        Initialize learner.
        
        Args:
            robot_id: Unique robot identifier
            learn_dir: Directory to store learned models
        """
        self.robot_id = robot_id
        self.learn_dir = Path(learn_dir)
        self.learn_dir.mkdir(exist_ok=True)
        
        # Experience database
        self.experiences: List[CommandExperience] = []
        self.strategies: Dict[str, AdaptiveStrategy] = {}
        
        # Load persisted learning
        self._load_models()
        
        logger.info(f"RobotLearner initialized for robot: {robot_id}")
    
    def record_experience(self, action: str, direction: Optional[str],
                         distance: Optional[float], angle: Optional[float],
                         success: bool, error: Optional[str] = None,
                         execution_time: float = 0.0, notes: str = "") -> None:
        """
        Record an experience (successful or failed execution).
        
        Args:
            action: Action type (move, rotate, grab, etc.)
            direction: Direction (forward, backward, left, right)
            distance: Distance in cm
            angle: Angle in degrees
            success: Whether execution succeeded
            error: Error message if failed
            execution_time: How long it took
            notes: Additional notes
        """
        exp = CommandExperience(action, direction, distance, angle,
                               success, error, execution_time, notes)
        self.experiences.append(exp)
        
        # Update strategy
        strategy_key = self._make_strategy_key(action, direction)
        if strategy_key not in self.strategies:
            self.strategies[strategy_key] = AdaptiveStrategy(
                action, direction, distance, angle
            )
        
        self.strategies[strategy_key].record_attempt(success, execution_time, error)
        self.strategies[strategy_key].update_strategy()
        
        logger.info(f"Recorded experience: {action} {direction} - {'SUCCESS' if success else 'FAILED'}")
        
        # Periodically save
        if len(self.experiences) % 10 == 0:
            self._save_models()
    
    def get_adaptive_parameters(self, action: str, direction: Optional[str],
                               distance: Optional[float],
                               angle: Optional[float]) -> Dict[str, Any]:
        """
        Get recommended adaptive parameters for a command.
        
        Returns adjusted parameters based on learning history.
        """
        strategy_key = self._make_strategy_key(action, direction)
        
        if strategy_key not in self.strategies:
            # No experience yet, return defaults
            return {
                "distance": distance,
                "angle": angle,
                "step_size_multiplier": 1.0,
                "speed_multiplier": 1.0,
                "break_into_steps": False,
                "recommended_steps": 1,
                "confidence": 0.5
            }
        
        strategy = self.strategies[strategy_key]
        
        # Adjust parameters based on learning
        adjusted_distance = distance
        adjusted_angle = angle
        
        if distance:
            adjusted_distance = distance * strategy.recommended_distance_adjustment
        if angle:
            adjusted_angle = angle * strategy.recommended_speed
        
        return {
            "distance": adjusted_distance,
            "angle": adjusted_angle,
            "step_size_multiplier": strategy.recommended_distance_adjustment,
            "speed_multiplier": strategy.recommended_speed,
            "break_into_steps": strategy.should_reduce_step_size(),
            "recommended_steps": strategy.recommended_max_steps,
            "confidence": strategy.success_rate,
            "success_rate": f"{strategy.success_rate:.1%}",
            "attempts": strategy.total_attempts,
            "average_time": f"{strategy.average_time:.2f}s"
        }
    
    def get_recovery_strategy(self, action: str, direction: Optional[str],
                             error: str) -> Optional[str]:
        """
        Get learned recovery strategy for a specific error.
        
        Example: If robot falls, suggest how to recover (reduce speed, smaller steps, etc)
        """
        strategy_key = self._make_strategy_key(action, direction)
        
        if strategy_key not in self.strategies:
            return None
        
        strategy = self.strategies[strategy_key]
        return strategy.recovery_strategies.get(error)
    
    def register_recovery_strategy(self, action: str, direction: Optional[str],
                                  error: str, strategy: str) -> None:
        """
        Register a recovery strategy for an error type.
        
        Example:
            register_recovery_strategy("move", "forward", "FALL_DETECTED",
                                     "reduce_speed_and_break_into_steps")
        """
        strategy_key = self._make_strategy_key(action, direction)
        
        if strategy_key not in self.strategies:
            self.strategies[strategy_key] = AdaptiveStrategy(action, direction, None, None)
        
        self.strategies[strategy_key].recovery_strategies[error] = strategy
        logger.info(f"Registered recovery strategy for {strategy_key}: {error} → {strategy}")
    
    def get_best_command_variants(self, action: str, direction: Optional[str],
                                 limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get the most successful variants of a command from history.
        
        Useful for suggesting what works best.
        """
        # Filter experiences for this action
        relevant = [
            e for e in self.experiences
            if e.action == action and e.direction == direction and e.success
        ]
        
        if not relevant:
            return []
        
        # Group by distance/angle and count successes
        variants: Dict[Tuple, int] = defaultdict(int)
        for exp in relevant:
            key = (exp.distance, exp.angle)
            variants[key] += 1
        
        # Sort by frequency
        sorted_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)
        
        result = []
        for (distance, angle), count in sorted_variants[:limit]:
            result.append({
                "distance": distance,
                "angle": angle,
                "success_count": count,
                "recommendation": f"This variant succeeded {count} times"
            })
        
        return result
    
    def get_learning_report(self) -> Dict[str, Any]:
        """Get a report of what the robot has learned."""
        total_attempts = len(self.experiences)
        successful = sum(1 for e in self.experiences if e.success)
        
        strategies_report = {}
        for key, strategy in self.strategies.items():
            strategies_report[key] = {
                "success_rate": f"{strategy.success_rate:.1%}",
                "total_attempts": strategy.total_attempts,
                "common_failures": dict(
                    sorted(strategy.failure_reasons.items(),
                           key=lambda x: x[1], reverse=True)[:3]
                ),
                "adaptation_status": "Optimistic" if strategy.success_rate > 0.8
                                    else "Cautious" if strategy.success_rate > 0.5
                                    else "Learning"
            }
        
        return {
            "robot_id": self.robot_id,
            "total_experiences": total_attempts,
            "total_successes": successful,
            "overall_success_rate": f"{successful/total_attempts:.1%}" if total_attempts > 0 else "N/A",
            "learned_strategies": len(self.strategies),
            "strategies": strategies_report,
            "last_updated": datetime.now().isoformat()
        }
    
    def _make_strategy_key(self, action: str, direction: Optional[str]) -> str:
        """Create a unique key for a command."""
        if direction:
            return f"{action}_{direction}"
        return action
    
    def _save_models(self) -> None:
        """Save learned models to disk."""
        try:
            model_file = self.learn_dir / f"{self.robot_id}_model.json"
            
            data = {
                "robot_id": self.robot_id,
                "experiences": [e.to_dict() for e in self.experiences[-100:]],  # Keep last 100
                "strategies": {k: v.to_dict() for k, v in self.strategies.items()},
                "saved_at": datetime.now().isoformat()
            }
            
            with open(model_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved learning model to {model_file}")
        except Exception as e:
            logger.error(f"Error saving models: {e}")
    
    def _load_models(self) -> None:
        """Load previously learned models from disk."""
        try:
            model_file = self.learn_dir / f"{self.robot_id}_model.json"
            
            if not model_file.exists():
                logger.info(f"No previous learning model found for {self.robot_id}")
                return
            
            with open(model_file, 'r') as f:
                data = json.load(f)
            
            # Load experiences
            for exp_data in data.get("experiences", []):
                self.experiences.append(CommandExperience.from_dict(exp_data))
            
            # Load strategies
            for key, strategy_data in data.get("strategies", {}).items():
                self.strategies[key] = AdaptiveStrategy.from_dict(strategy_data)
            
            logger.info(f"Loaded {len(self.experiences)} experiences and "
                       f"{len(self.strategies)} strategies for {self.robot_id}")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def reset_learning(self) -> None:
        """Reset all learning (start fresh)."""
        self.experiences = []
        self.strategies = {}
        logger.warning(f"Learning reset for {self.robot_id}")
    
    def export_learned_code(self) -> str:
        """
        Export learned behavior as Python code.
        
        This generates a module that can be used to replicate learned behavior.
        """
        code = f'''"""
Auto-generated learning module for {self.robot_id}
Generated: {datetime.now().isoformat()}
"""

# Learned optimal parameters for each command
LEARNED_PARAMETERS = {{
'''
        
        for key, strategy in self.strategies.items():
            code += f'''    "{key}": {{
        "success_rate": {strategy.success_rate:.3f},
        "distance_adjustment": {strategy.recommended_distance_adjustment:.2f},
        "speed_adjustment": {strategy.recommended_speed:.2f},
        "break_into_steps": {strategy.should_reduce_step_size()},
        "recommended_steps": {strategy.recommended_max_steps},
        "total_attempts": {strategy.total_attempts},
        "last_updated": "{strategy.last_updated.isoformat()}",
    }},
'''
        
        code += '''}}

# Recovery strategies for common errors
RECOVERY_STRATEGIES = {
'''
        
        for key, strategy in self.strategies.items():
            if strategy.recovery_strategies:
                code += f'''    "{key}": {strategy.recovery_strategies},
'''
        
        code += '''}}

def get_parameters(action, direction):
    """Get learned parameters for a command."""
    key = f"{action}_{direction}" if direction else action
    return LEARNED_PARAMETERS.get(key, {})

def get_recovery(action, direction, error):
    """Get recovery strategy for an error."""
    key = f"{action}_{direction}" if direction else action
    strategies = RECOVERY_STRATEGIES.get(key, {})
    return strategies.get(error)
'''
        
        return code
