"""
telegram_bot.py - Telegram bot interface for OpenGuy.
Control robots via Telegram chat with natural language commands.
"""

import os
import logging
from typing import Optional, Dict, Any
import requests
import json

from parser import parse
from hybrid_sim import HybridExecutor


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenGuyTelegramBot:
    """Telegram bot interface for OpenGuy robot control."""
    
    def __init__(self, token: str, executor: Optional[HybridExecutor] = None):
        """
        Initialize Telegram bot.
        
        Args:
            token: Telegram bot token from BotFather
            executor: Optional HybridExecutor instance (creates own if not provided)
        """
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.executor = executor or HybridExecutor(try_hardware=True)
        self.user_chains: Dict[int, Dict[str, Any]] = {}  # Store active command chains
    
    def send_message(self, chat_id: int, text: str, reply_markup: Optional[str] = None) -> bool:
        """Send message to Telegram user."""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(f"{self.api_url}/sendMessage", json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def send_animation(self, chat_id: int, animation_url: str, caption: str = "") -> bool:
        """Send animation/video to Telegram user."""
        try:
            payload = {
                "chat_id": chat_id,
                "animation": animation_url,
                "caption": caption
            }
            response = requests.post(f"{self.api_url}/sendAnimation", json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send animation: {e}")
            return False
    
    def send_photo(self, chat_id: int, photo_url: str, caption: str = "") -> bool:
        """Send photo to Telegram user."""
        try:
            payload = {
                "chat_id": chat_id,
                "photo": photo_url,
                "caption": caption
            }
            response = requests.post(f"{self.api_url}/sendPhoto", json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return False
    
    def handle_message(self, message: Dict[str, Any]) -> str:
        """
        Handle incoming Telegram message.
        
        Args:
            message: Telegram message object
            
        Returns:
            Response text to send back
        """
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        user_id = message["from"]["id"]
        first_name = message["from"].get("first_name", "User")
        
        logger.info(f"Message from {first_name}: {text}")
        
        # Handle special commands
        if text == "/start":
            return self._handle_start(chat_id, first_name)
        elif text == "/help":
            return self._handle_help(chat_id)
        elif text == "/status":
            return self._handle_status(chat_id)
        elif text == "/mode":
            return self._handle_mode(chat_id)
        elif text == "/stop":
            return self._handle_stop(chat_id, user_id)
        elif text.startswith("/"):
            return f"❓ Unknown command: {text}\nType /help for available commands."
        
        # Handle robot commands
        return self._handle_robot_command(chat_id, text, user_id)
    
    def _handle_start(self, chat_id: int, name: str) -> str:
        """Handle /start command."""
        response = (
            f"🤖 Welcome to OpenGuy, {name}!\n\n"
            "I can control robot arms using natural language.\n\n"
            "Try commands like:\n"
            "• move forward 10 cm\n"
            "• rotate right 45 degrees\n"
            "• grab the object\n"
            "• move forward AND rotate right AND grab\n\n"
            "Type /help for more info."
        )
        return response
    
    def _handle_help(self, chat_id: int) -> str:
        """Handle /help command."""
        response = (
            "📖 *Available Commands*\n\n"
            "*Special Commands:*\n"
            "/start - Welcome message\n"
            "/help - Show this help\n"
            "/status - Robot status\n"
            "/mode - Check simulator/hardware mode\n"
            "/stop - Stop executing chains\n\n"
            "*Robot Commands:*\n"
            "Say anything to control the robot:\n"
            "• move forward/backward/left/right [distance]\n"
            "• rotate left/right [angle]\n"
            "• grab / release\n"
            "• multi-step: move forward AND rotate right AND grab\n\n"
            "*Examples:*\n"
            "go 10cm right\n"
            "spin 90 degrees\n"
            "pick up the block\n"
            "move forward 20cm and grab"
        )
        return response
    
    def _handle_status(self, chat_id: int) -> str:
        """Handle /status command."""
        status = self.executor.get_status()
        
        mode = "🟢 HARDWARE" if status['mode'] == 'hardware' else "🟡 SIMULATOR"
        hw_available = "✅ Yes" if status.get('hardware_available') else "❌ No"
        
        response = (
            f"*Robot Status*\n\n"
            f"Mode: {mode}\n"
            f"Hardware Available: {hw_available}\n"
            f"Position: ({status.get('x', 0):.1f}, {status.get('y', 0):.1f})\n"
            f"Facing: {status.get('facing', 0):.0f}°\n"
            f"Gripper: {'Open' if status.get('gripper_open', True) else 'Closed'}\n"
            f"Commands Executed: {status.get('commands_executed', 0)}"
        )
        return response
    
    def _handle_mode(self, chat_id: int) -> str:
        """Handle /mode command."""
        status = self.executor.get_status()
        
        if status['mode'] == 'hardware':
            return "🟢 *HARDWARE MODE*\nControlling real robot arm via USB/Serial"
        else:
            return "🟡 *SIMULATOR MODE*\nNo hardware detected. Using virtual simulator."
    
    def _handle_stop(self, chat_id: int, user_id: int) -> str:
        """Handle /stop command."""
        if user_id in self.user_chains:
            del self.user_chains[user_id]
            return "⏹️ Command chain stopped."
        return "No active command chain."
    
    def _handle_robot_command(self, chat_id: int, text: str, user_id: int) -> str:
        """Handle robot commands."""
        try:
            # Parse the command
            parsed = parse(text, use_ai=True)
            
            if not parsed['action'] or parsed['action'] == 'unknown':
                return "❓ Sorry, I couldn't understand that command. Try:\n• move forward\n• rotate right\n• grab"
            
            # Execute the command
            result = self.executor.execute(
                action=parsed['action'],
                direction=parsed['direction'],
                distance_cm=parsed['distance_cm'],
                angle_deg=parsed['angle_deg']
            )
            
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
                response += f"*Distance:* {parsed['distance_cm']}cm\n"
            if parsed['angle_deg']:
                response += f"*Angle:* {parsed['angle_deg']}°\n"
            
            response += f"\n*Result:*\n" + "\n".join(lines)
            
            return response
            
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return f"⚠️ Error: {str(e)}"
    
    def handle_update(self, update: Dict[str, Any]) -> Optional[str]:
        """
        Handle Telegram update.
        
        Args:
            update: Telegram update object
            
        Returns:
            Response to send, or None
        """
        if "message" in update:
            return self.handle_message(update["message"])
        
        return None
    
    def close(self):
        """Close bot and cleanup."""
        self.executor.close()


def create_bot(token: Optional[str] = None, executor: Optional[HybridExecutor] = None) -> OpenGuyTelegramBot:
    """
    Create and configure Telegram bot.
    
    Args:
        token: Bot token (defaults to TELEGRAM_BOT_TOKEN env var)
        executor: Optional HybridExecutor instance to use
        
    Returns:
        Configured bot instance
    """
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("No Telegram bot token provided. Set TELEGRAM_BOT_TOKEN environment variable.")
    
    return OpenGuyTelegramBot(token, executor=executor)
