"""
whatsapp_bot.py - WhatsApp bot interface for OpenGuy.
Control robots via WhatsApp chat with natural language commands.

Uses Twilio's WhatsApp Business API for message handling.
Includes: rate limiting, error handling, note management, safety checks.
"""

import os
import logging
from typing import Optional, Dict, Any
import requests
import json
from datetime import datetime, timedelta
import time

from parser import parse
from hybrid_sim import HybridExecutor
from notes_manager import NoteManager
from robot_learner import RobotLearner
from bot_exceptions import (
    BotException, HardwareException, CommandParseException,
    ValidationException, RateLimitException, SafetyException,
    ExecutorException, TwilioException
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenGuyWhatsAppBot:
    """WhatsApp bot interface for OpenGuy robot control via Twilio."""
    
    def __init__(self, account_sid: str, auth_token: str, twilio_phone: str, executor: Optional[HybridExecutor] = None):
        """
        Initialize WhatsApp bot using Twilio.
        
        Args:
            account_sid: Twilio Account SID
            auth_token: Twilio Auth Token
            twilio_phone: Twilio WhatsApp number (e.g., "whatsapp:+1234567890")
            executor: Optional HybridExecutor instance (creates own if not provided)
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.twilio_phone = twilio_phone
        self.executor = executor or HybridExecutor(try_hardware=True)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}  # Store per-user state
        
        # Note management for persistent storage
        self.notes = NoteManager()
        
        # Robot learning system for autonomous adaptation
        self.learner = RobotLearner("openguy_robot")
        
        # Rate limiting: max 10 commands per 60 seconds per user
        self.rate_limit = (10, 60)  # (max_commands, time_window_seconds)
        
        # Safety settings
        self.max_distance_cm = 200  # Maximum safe distance
        self.max_angle_deg = 360
        self.require_confirmation = False  # Safety confirmations enabled
        
        # Twilio messaging endpoint
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    def send_message(self, phone_number: str, text: str) -> bool:
        """
        Send WhatsApp message via Twilio with error handling.
        
        Args:
            phone_number: Recipient phone in E.164 format (e.g., "+1234567890")
            text: Message text to send
            
        Returns:
            True if successful
            
        Raises:
            TwilioException: If Twilio API fails
        """
        try:
            # Ensure phone has whatsapp: prefix
            recipient = f"whatsapp:{phone_number}" if not phone_number.startswith("whatsapp:") else phone_number
            
            # Validate phone number format
            if not self._validate_phone(recipient):
                raise ValidationException(f"Invalid phone format: {phone_number}")
            
            payload = {
                "From": self.twilio_phone,
                "To": recipient,
                "Body": text
            }
            
            response = requests.post(
                self.api_url,
                data=payload,
                auth=(self.account_sid, self.auth_token),
                timeout=10  # 10 second timeout
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Message sent: {phone_number}")
                return True
            else:
                error_msg = f"Twilio error ({response.status_code}): {response.text}"
                logger.error(error_msg)
                self.notes.log_error(phone_number, "TWILIO_SEND_FAILED", error_msg, {
                    "status_code": response.status_code
                })
                raise TwilioException(error_msg)
                
        except requests.Timeout:
            error_msg = "Request timeout - Twilio API not responding"
            logger.error(error_msg)
            self.notes.log_error(phone_number, "TWILIO_TIMEOUT", error_msg, {})
            raise TwilioException(error_msg)
        except Exception as e:
            if isinstance(e, BotException):
                raise
            logger.error(f"Error sending message: {e}")
            self.notes.log_error(phone_number, "SEND_MESSAGE_ERROR", str(e), {})
            raise TwilioException(str(e))
    
    def send_media(self, phone_number: str, media_url: str, caption: str = "") -> bool:
        """
        Send media (image/video) via WhatsApp.
        
        Args:
            phone_number: Recipient phone number
            media_url: URL to media file
            caption: Optional caption
            
        Returns:
            True if successful
        """
        try:
            recipient = f"whatsapp:{phone_number}" if not phone_number.startswith("whatsapp:") else phone_number
            
            payload = {
                "From": self.twilio_phone,
                "To": recipient,
                "MediaUrl": media_url
            }
            if caption:
                payload["Body"] = caption
            
            response = requests.post(
                self.api_url,
                data=payload,
                auth=(self.account_sid, self.auth_token)
            )
            
            return response.status_code in [200, 201]
        except Exception as e:
            logger.error(f"Error sending media: {e}")
            return False
    
    def handle_message(self, incoming_message: Dict[str, Any]) -> str:
        """
        Handle incoming WhatsApp message from Twilio webhook.
        Includes rate limiting, validation, and logging.
        
        Args:
            incoming_message: Message data from Twilio webhook
            
        Returns:
            Response text to send back
        """
        try:
            phone_number = incoming_message.get("From", "").replace("whatsapp:", "")
            text = incoming_message.get("Body", "").strip()
            message_sid = incoming_message.get("MessageSid", "unknown")
            
            # Validate inputs
            if not phone_number or not text:
                raise ValidationException("Missing phone number or message text")
            
            logger.info(f"Message from {phone_number}: {text[:50]}...")
            
            # Check rate limit
            if not self._check_rate_limit(phone_number):
                max_commands, window = self.rate_limit
                error = f"Rate limited: max {max_commands} commands per {window}s"
                self.notes.log_error(phone_number, "RATE_LIMIT_EXCEEDED", error, {})
                return f"⏳ Too many commands! Please wait before sending another."
            
            # Initialize user session if needed
            if phone_number not in self.user_sessions:
                self.user_sessions[phone_number] = {
                    "last_action": None,
                    "pending_chain": None,
                    "commands_executed": 0,
                    "command_times": []
                }
            
            # Track command time for rate limiting
            self.user_sessions[phone_number]["command_times"].append(datetime.now())
            
            # Handle special commands
            if text == "/start" or text.lower() in ["start", "hello", "hi"]:
                return self._handle_start(phone_number)
            elif text == "/help" or text.lower() == "help":
                return self._handle_help(phone_number)
            elif text == "/status" or text.lower() == "status":
                return self._handle_status(phone_number)
            elif text == "/mode" or text.lower() == "mode":
                return self._handle_mode(phone_number)
            elif text == "/notes" or text.lower() == "notes":
                return self._handle_notes(phone_number)
            elif text.startswith("/note "):
                parts = text[6:].split(":", 1)
                if len(parts) == 2:
                    return self._handle_save_note(phone_number, parts[0].strip(), parts[1].strip())
                return "❌ Format: /note title:content"
            elif text == "/history" or text.lower() == "history":
                return self._handle_history(phone_number)
            elif text == "/learn" or text.lower() == "learn":
                return self._handle_learn(phone_number)
            elif text == "/stop" or text.lower() == "stop":
                return self._handle_stop(phone_number)
            elif text.startswith("/"):
                return f"❓ Unknown command: {text}\nType /help for available commands."
            
            # Handle robot commands
            return self._handle_robot_command(phone_number, text)
            
        except BotException as e:
            logger.warning(f"Bot exception: {e}")
            self.notes.log_error(phone_number, type(e).__name__, str(e), {})
            return e.get_user_message()
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.notes.log_error(phone_number, "UNEXPECTED_ERROR", str(e), {})
            return "❌ An unexpected error occurred. Please try again."
    
    def _handle_start(self, phone_number: str) -> str:
        """Handle start command."""
        response = (
            "🤖 *Welcome to OpenGuy!*\n\n"
            "I can control robot arms using natural language.\n\n"
            "Try commands like:\n"
            "• move forward 10 cm\n"
            "• rotate right 45 degrees\n"
            "• grab the object\n"
            "• move forward, rotate right, and grab\n\n"
            "Type /help for more info."
        )
        return response
    
    def _handle_help(self, phone_number: str) -> str:
        """Handle help command."""
        response = (
            "*📖 Available Commands*\n\n"
            "*Special Commands:*\n"
            "/start - Welcome message\n"
            "/help - Show this help\n"
            "/status - Robot status\n"
            "/mode - Check simulator/hardware mode\n"
            "/history - View recent commands\n"
            "/learn - Show robot learning report\n"
            "/notes - View your notes\n"
            "/note title:content - Save a note\n"
            "/stop - Stop command chain\n\n"
            "*Robot Commands:*\n"
            "Say anything to control the robot:\n"
            "• move forward/backward/left/right\n"
            "• rotate left/right by angle\n"
            "• grab / release\n"
            "• multi-step: move forward, rotate right, grab\n\n"
            "*Examples:*\n"
            "go 10cm right\n"
            "spin 90 degrees\n"
            "pick up the block\n"
            "move forward 20cm and release\n\n"
            "*🤖 Robot Learning:*\n"
            "The robot learns from every command!\n"
            "• Tracks success/failure patterns\n"
            "• Automatically adjusts movement size\n"
            "• Recovers better from known failures\n"
            "Type /learn to see what it has learned."
        )
        return response
    
    def _handle_status(self, phone_number: str) -> str:
        """Handle status command."""
        status = self.executor.get_status()
        
        mode = "🟢 HARDWARE" if status['mode'] == 'hardware' else "🟡 SIMULATOR"
        hw_available = "✅ Yes" if status.get('hardware_available') else "❌ No"
        
        response = (
            "*🤖 Robot Status*\n\n"
            f"Mode: {mode}\n"
            f"Hardware Available: {hw_available}\n"
            f"Position: ({status.get('x', 0):.1f}, {status.get('y', 0):.1f})\n"
            f"Facing: {status.get('facing', 0):.0f}°\n"
            f"Gripper: {'Open' if status.get('gripper_open', True) else 'Closed'}\n"
            f"Commands Executed: {status.get('commands_executed', 0)}"
        )
        return response
    
    def _handle_mode(self, phone_number: str) -> str:
        """Handle mode command."""
        status = self.executor.get_status()
        
        if status['mode'] == 'hardware':
            return "🟢 *HARDWARE MODE*\nControlling real robot arm via USB/Serial"
        else:
            return "🟡 *SIMULATOR MODE*\nNo hardware detected. Using virtual simulator."
    
    def _handle_stop(self, phone_number: str) -> str:
        """Handle stop command."""
        if phone_number in self.user_sessions:
            self.user_sessions[phone_number]['pending_chain'] = None
            return "⏹️ Command chain stopped."
        return "No active command chain."
    
    def _handle_notes(self, phone_number: str) -> str:
        """Show all notes for user."""
        notes = self.notes.get_user_notes(phone_number)
        
        if not notes:
            return "📝 No notes saved yet.\n\nTo save a note, use:\n/note title:content"
        
        response = "📝 *Your Notes:*\n\n"
        for title, content in notes.items():
            response += f"• *{title}:* {content}\n"
        
        return response
    
    def _handle_save_note(self, phone_number: str, title: str, content: str) -> str:
        """Save a note for the user."""
        try:
            if not title or not content:
                return "❌ Format: /note title:content"
            
            if self.notes.save_user_note(phone_number, title, content):
                return f"✅ Note saved: {title}"
            else:
                return "❌ Failed to save note"
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            self.notes.log_error(phone_number, "SAVE_NOTE_ERROR", str(e), {})
            return "❌ Error saving note"
    
    def _handle_history(self, phone_number: str) -> str:
        """Show command history."""
        history = self.notes.get_command_history(phone_number, limit=5)
        
        if not history:
            return "📜 No command history yet."
        
        response = "📜 *Recent Commands:*\n\n"
        for cmd in history:
            action = cmd.get("parsed", {}).get("action", "unknown")
            success = "✅" if cmd.get("success") else "❌"
            response += f"{success} {action}: {cmd.get('command', '')}\n"
        
        return response
    
    def _handle_learn(self, phone_number: str) -> str:
        """Show what the robot has learned from all users' experiences."""
        report = self.learner.get_learning_report()
        
        if report['total_experiences'] == 0:
            return "📚 *No learning data yet.*\n\nTry executing some commands first!"
        
        response = "📚 *Robot Learning Report*\n\n"
        response += f"*Total Experiences:* {report['total_experiences']}\n"
        response += f"*Success Rate:* {report['overall_success_rate']}\n"
        response += f"*Learned Strategies:* {report['learned_strategies']}\n\n"
        
        response += "*Learned Commands:*\n"
        
        strategies = report.get('strategies', {})
        if strategies:
            for cmd_name, strategy in list(strategies.items())[:5]:  # Show top 5
                success_rate = strategy.get('success_rate', 'N/A')
                attempts = strategy.get('total_attempts', 0)
                status = strategy.get('adaptation_status', 'Learning')
                response += f"\n• *{cmd_name}*\n"
                response += f"  Success: {success_rate} ({attempts} attempts)\n"
                response += f"  Status: {status}\n"
                
                failures = strategy.get('common_failures', {})
                if failures:
                    top_failure = list(failures.items())[0]
                    response += f"  ⚠️ Most common issue: {top_failure[0]} ({top_failure[1]}x)\n"
        else:
            response += "No strategies learned yet."
        
        response += "\n\n💡 *How it works:*\n"
        response += "• Robot learns from every command\n"
        response += "• Automatically reduces risky moves after failures\n"
        response += "• Increases confidence after successes\n"
        response += "• Breaks large moves into steps if needed\n"
        response += "• Saves learned behavior to disk"
        
        return response
    
    # ── Safety and Validation ──────────────────────────────────────────
    
    def _check_rate_limit(self, phone_number: str) -> bool:
        """Check if user exceeds rate limit."""
        if phone_number not in self.user_sessions:
            return True
        
        command_times = self.user_sessions[phone_number].get("command_times", [])
        max_commands, window_seconds = self.rate_limit
        
        # Remove old commands outside window
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)
        recent_commands = [t for t in command_times if t > cutoff_time]
        
        # Update session
        self.user_sessions[phone_number]["command_times"] = recent_commands
        
        return len(recent_commands) < max_commands
    
    def _validate_command_safety(self, parsed: Dict[str, Any]) -> None:
        """
        Validate command for safety violations.
        
        Raises:
            SafetyException: If command violates safety rules
        """
        action = parsed.get('action', '')
        distance = parsed.get('distance_cm', 0)
        angle = parsed.get('angle_deg', 0)
        
        # Check distance limits
        if distance and abs(distance) > self.max_distance_cm:
            raise SafetyException(
                f"Distance {distance}cm exceeds max {self.max_distance_cm}cm. "
                f"For safety reasons, please use smaller movements."
            )
        
        # Check angle limits
        if angle and abs(angle) > self.max_angle_deg:
            raise SafetyException(
                f"Angle {angle}° exceeds max {self.max_angle_deg}°. "
                f"Use smaller rotations."
            )
        
        # No negative distances (always move forward in positive direction)
        if distance and distance < 0 and action == 'move':
            raise SafetyException("Use direction words (forward/backward) instead of negative values")
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Basic validation: should have whatsapp:+ prefix and digits
        if not phone.startswith("whatsapp:+"):
            return False
        
        digits = phone.replace("whatsapp:+", "")
        return digits.isdigit() and len(digits) >= 10
    
    # ── Help Command ──────────────────────────────────────────────────
    
    def _handle_help(self, phone_number: str) -> str:
        """Handle help command."""
        response = (
            "*📖 Available Commands*\n\n"
            "*Special Commands:*\n"
            "/start - Welcome message\n"
            "/help - Show this help\n"
            "/status - Robot status\n"
            "/mode - Check simulator/hardware mode\n"
            "/notes - Show your saved notes\n"
            "/note title:content - Save a note\n"
            "/history - See recent commands\n"
            "/stop - Stop command chain\n\n"
            "*Robot Commands:*\n"
            "Say anything to control the robot:\n"
            "• move forward/backward/left/right 5-200cm\n"
            "• rotate left/right by 1-360°\n"
            "• grab / release\n"
            "• multi-step: move forward, rotate right, grab\n\n"
            "*Examples:*\n"
            "go 10cm right\n"
            "spin 90 degrees\n"
            "pick up the block\n"
            "move forward 20cm and release\n\n"
            "⚠️ *Safety Limits:*\n"
            f"Max distance: {self.max_distance_cm}cm\n"
            f"Max angle: {self.max_angle_deg}°"
        )
        return response
    
    def _handle_robot_command(self, phone_number: str, text: str) -> str:
        """
        Handle robot commands with safety checks, error handling, and learning.
        Uses robot learner to adapt parameters based on past experiences.
        """
        try:
            start_time = time.time()
            
            # Parse the command
            parsed = parse(text, use_ai=True)
            
            if not parsed['action'] or parsed['action'] == 'unknown':
                raise CommandParseException("Could not parse command. Try: move forward, rotate right, grab")
            
            # Safety checks
            self._validate_command_safety(parsed)
            
            # Get adaptive parameters from learner
            adaptive_params = self.learner.get_adaptive_parameters(
                action=parsed['action'],
                direction=parsed['direction'],
                distance=parsed['distance_cm'],
                angle=parsed['angle_deg']
            )
            
            # Apply learning-based adjustments to parameters
            execution_distance = adaptive_params['distance']
            execution_angle = adaptive_params['angle']
            execution_time = 0.0
            
            # Execute the command (possibly in multiple steps if learner recommends it)
            if adaptive_params['break_into_steps'] and parsed['distance_cm']:
                # Break into smaller steps for better control
                num_steps = adaptive_params['recommended_steps']
                step_distance = execution_distance / num_steps if execution_distance else None
                result = None
                
                for step in range(num_steps):
                    step_result = self.executor.execute(
                        action=parsed['action'],
                        direction=parsed['direction'],
                        distance_cm=step_distance,
                        angle_deg=execution_angle if step == num_steps - 1 else 0
                    )
                    result = step_result
            else:
                # Execute in single step
                try:
                    result = self.executor.execute(
                        action=parsed['action'],
                        direction=parsed['direction'],
                        distance_cm=execution_distance,
                        angle_deg=execution_angle
                    )
                except Exception as e:
                    execution_time = time.time() - start_time
                    # Record failure for learning
                    error_type = "COLLISION" if "collision" in str(e).lower() else \
                                "TIMEOUT" if "timeout" in str(e).lower() else \
                                "HARDWARE_ERROR"
                    self.learner.record_experience(
                        action=parsed['action'],
                        direction=parsed['direction'],
                        distance=parsed['distance_cm'],
                        angle=parsed['angle_deg'],
                        success=False,
                        error=error_type,
                        execution_time=execution_time,
                        notes=f"User: {phone_number}"
                    )
                    raise ExecutorException(f"Robot execution failed: {str(e)}")
            
            execution_time = time.time() - start_time
            
            # Record success for learning
            self.learner.record_experience(
                action=parsed['action'],
                direction=parsed['direction'],
                distance=parsed['distance_cm'],
                angle=parsed['angle_deg'],
                success=True,
                execution_time=execution_time,
                notes=f"User: {phone_number}"
            )
            
            # Update session
            self.user_sessions[phone_number]['last_action'] = parsed['action']
            self.user_sessions[phone_number]['commands_executed'] += 1
            
            # Log successful command
            self.notes.log_command(
                phone_number, text, parsed, result, True
            )
            self.notes.log_robot_state(phone_number, self.executor.get_status())
            
            # Format response
            lines = result.get('output', [])
            if not lines and 'status' in result:
                lines = [result['status']]
            
            confidence = parsed.get('confidence', 0)
            conf_emoji = "🟢" if confidence >= 0.8 else "🟡" if confidence >= 0.5 else "🔴"
            
            response = (
                f"{conf_emoji} *Confidence: {confidence:.0%}*\n\n"
                f"*Action:* {parsed['action'].title()}\n"
            )
            
            if parsed['direction']:
                response += f"*Direction:* {parsed['direction']}\n"
            if parsed['distance_cm']:
                response += f"*Distance:* {parsed['distance_cm']}cm"
                if execution_distance != parsed['distance_cm']:
                    response += f" (adjusted to {execution_distance:.0f}cm)"
                response += "\n"
            if parsed['angle_deg']:
                response += f"*Angle:* {parsed['angle_deg']}°\n"
            
            response += f"\n*Result:*\n" + "\n".join(lines)
            
            # Add learning feedback
            attempts = adaptive_params.get('attempts', 0)
            if adaptive_params.get('confidence', 0.5) < 0.6 and attempts > 0:
                response += f"\n\n💡 *Learning Status:* {adaptive_params.get('success_rate', 'N/A')} success rate " \
                           f"over {attempts} attempts (being cautious)"
            elif attempts > 5:
                response += f"\n\n✅ *Learned:* {adaptive_params.get('success_rate', 'N/A')} success rate"
            
            return response
            
        except BotException as e:
            self.notes.log_command(phone_number, text, {}, {}, False, str(e))
            self.notes.log_error(phone_number, type(e).__name__, str(e), {"command": text})
            return f"❌ {e.get_user_message()}"
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            self.notes.log_command(phone_number, text, {}, {}, False, str(e))
            self.notes.log_error(phone_number, "COMMAND_ERROR", str(e), {"command": text})
            return f"⚠️ Error: Command failed. Please try again."
    
    def handle_webhook(self, message_data: Dict[str, Any]) -> str:
        """
        Handle incoming webhook from Twilio.
        
        Args:
            message_data: Message data from webhook
            
        Returns:
            Response to send
        """
        return self.handle_message(message_data)
    
    def close(self):
        """Close bot and cleanup."""
        self.executor.close()


def create_whatsapp_bot(
    account_sid: Optional[str] = None,
    auth_token: Optional[str] = None,
    twilio_phone: Optional[str] = None,
    executor: Optional[HybridExecutor] = None
) -> OpenGuyWhatsAppBot:
    """
    Create and configure WhatsApp bot using Twilio.
    
    Args:
        account_sid: Twilio Account SID (defaults to TWILIO_ACCOUNT_SID env var)
        auth_token: Twilio Auth Token (defaults to TWILIO_AUTH_TOKEN env var)
        twilio_phone: Twilio WhatsApp number (defaults to TWILIO_WHATSAPP_NUMBER env var)
        executor: Optional HybridExecutor instance
        
    Returns:
        Configured WhatsApp bot instance
        
    Raises:
        ValueError: If required credentials are missing
    """
    account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = twilio_phone or os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    if not all([account_sid, auth_token, twilio_phone]):
        raise ValueError(
            "Missing Twilio credentials. Set environment variables:\n"
            "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER"
        )
    
    return OpenGuyWhatsAppBot(account_sid, auth_token, twilio_phone, executor=executor)
