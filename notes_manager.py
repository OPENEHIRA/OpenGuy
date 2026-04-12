"""
notes_manager.py - Persistent notes and command logging for robot operations.
Safely stores robot state, commands, and user notes for auditing and recovery.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class NoteManager:
    """Manages persistent notes, command history, and robot state logs."""
    
    def __init__(self, notes_dir: str = "robot_notes"):
        """
        Initialize note manager.
        
        Args:
            notes_dir: Directory to store notes and logs
        """
        self.notes_dir = Path(notes_dir)
        self.notes_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()  # Thread-safe file access
        
        # Separate files for different types of data
        self.command_log_file = self.notes_dir / "command_history.json"
        self.robot_state_file = self.notes_dir / "robot_states.json"
        self.user_notes_file = self.notes_dir / "user_notes.json"
        self.error_log_file = self.notes_dir / "error_log.json"
    
    def log_command(self, phone_number: str, command: str, parsed: Dict[str, Any], 
                    result: Dict[str, Any], success: bool, error: Optional[str] = None) -> None:
        """
        Log a robot command for auditing and recovery.
        
        Args:
            phone_number: User's phone number
            command: Original natural language command
            parsed: Parsed command structure
            result: Execution result
            success: Whether command succeeded
            error: Error message if failed
        """
        with self.lock:
            try:
                history = self._load_json(self.command_log_file, [])
                
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user": phone_number,
                    "command": command,
                    "parsed": parsed,
                    "result": result,
                    "success": success,
                    "error": error,
                    "id": len(history) + 1
                }
                
                history.append(entry)
                # Keep last 1000 commands per file rotation
                if len(history) > 1000:
                    history = history[-1000:]
                
                self._save_json(self.command_log_file, history)
                logger.info(f"Command logged: {entry['id']}")
            except Exception as e:
                logger.error(f"Failed to log command: {e}")
    
    def log_robot_state(self, phone_number: str, state: Dict[str, Any]) -> None:
        """
        Log robot state snapshot for recovery and debugging.
        
        Args:
            phone_number: User who triggered the state
            state: Robot state snapshot
        """
        with self.lock:
            try:
                states = self._load_json(self.robot_state_file, [])
                
                snapshot = {
                    "timestamp": datetime.now().isoformat(),
                    "user": phone_number,
                    "state": state,
                    "id": len(states) + 1
                }
                
                states.append(snapshot)
                # Keep last 500 state snapshots
                if len(states) > 500:
                    states = states[-500:]
                
                self._save_json(self.robot_state_file, states)
            except Exception as e:
                logger.error(f"Failed to log robot state: {e}")
    
    def log_error(self, phone_number: str, error_type: str, error_message: str, 
                  context: Dict[str, Any]) -> None:
        """
        Log error with context for debugging.
        
        Args:
            phone_number: User affected
            error_type: Type of error (e.g., "hardware_fail", "parse_error")
            error_message: Error message
            context: Additional context
        """
        with self.lock:
            try:
                errors = self._load_json(self.error_log_file, [])
                
                entry = {
                    "timestamp": datetime.now().isoformat(),
                    "user": phone_number,
                    "type": error_type,
                    "message": error_message,
                    "context": context,
                    "id": len(errors) + 1
                }
                
                errors.append(entry)
                # Keep last 500 errors
                if len(errors) > 500:
                    errors = errors[-500:]
                
                self._save_json(self.error_log_file, errors)
                logger.warning(f"Error logged: {error_type} - {error_message}")
            except Exception as e:
                logger.error(f"Failed to log error: {e}")
    
    def save_user_note(self, phone_number: str, note_title: str, note_content: str) -> bool:
        """
        Save user note (e.g., "safe_height", "calibration_data").
        
        Args:
            phone_number: User's phone number
            note_title: Note identifier
            note_content: Note content
            
        Returns:
            True if successful
        """
        with self.lock:
            try:
                notes = self._load_json(self.user_notes_file, {})
                
                if phone_number not in notes:
                    notes[phone_number] = {}
                
                notes[phone_number][note_title] = {
                    "content": note_content,
                    "saved_at": datetime.now().isoformat()
                }
                
                self._save_json(self.user_notes_file, notes)
                logger.info(f"Note saved: {phone_number}/{note_title}")
                return True
            except Exception as e:
                logger.error(f"Failed to save note: {e}")
                return False
    
    def get_user_note(self, phone_number: str, note_title: str) -> Optional[str]:
        """
        Retrieve user note.
        
        Args:
            phone_number: User's phone number
            note_title: Note identifier
            
        Returns:
            Note content or None
        """
        with self.lock:
            try:
                notes = self._load_json(self.user_notes_file, {})
                
                if phone_number in notes and note_title in notes[phone_number]:
                    return notes[phone_number][note_title].get("content")
                return None
            except Exception as e:
                logger.error(f"Failed to get note: {e}")
                return None
    
    def get_user_notes(self, phone_number: str) -> Dict[str, str]:
        """
        Get all notes for a user.
        
        Args:
            phone_number: User's phone number
            
        Returns:
            Dictionary of note_title -> content
        """
        with self.lock:
            try:
                notes = self._load_json(self.user_notes_file, {})
                
                if phone_number in notes:
                    return {
                        title: data.get("content", "")
                        for title, data in notes[phone_number].items()
                    }
                return {}
            except Exception as e:
                logger.error(f"Failed to get user notes: {e}")
                return {}
    
    def get_command_history(self, phone_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get command history for a user.
        
        Args:
            phone_number: User's phone number
            limit: Number of recent commands to return
            
        Returns:
            List of command entries
        """
        with self.lock:
            try:
                history = self._load_json(self.command_log_file, [])
                
                user_history = [h for h in history if h.get("user") == phone_number]
                return user_history[-limit:]
            except Exception as e:
                logger.error(f"Failed to get command history: {e}")
                return []
    
    def get_recent_errors(self, phone_number: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent errors for a user.
        
        Args:
            phone_number: User's phone number
            limit: Number of recent errors
            
        Returns:
            List of error entries
        """
        with self.lock:
            try:
                errors = self._load_json(self.error_log_file, [])
                
                user_errors = [e for e in errors if e.get("user") == phone_number]
                return user_errors[-limit:]
            except Exception as e:
                logger.error(f"Failed to get recent errors: {e}")
                return []
    
    def _load_json(self, file_path: Path, default: Any = None) -> Any:
        """Load JSON file with error handling."""
        try:
            if file_path.exists():
                with open(file_path, 'r') as f:
                    return json.load(f)
            return default
        except json.JSONDecodeError:
            logger.warning(f"Corrupted JSON file: {file_path}, using default")
            return default
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return default
    
    def _save_json(self, file_path: Path, data: Any) -> None:
        """Save JSON file with error handling."""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving {file_path}: {e}")
