"""
tests/test_telegram_bot.py - Tests for Telegram bot functionality.
"""

import pytest
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram_bot import OpenGuyTelegramBot


class MockTelegramBot(OpenGuyTelegramBot):
    """Mock Telegram bot for testing without actual API calls."""
    
    def __init__(self):
        """Initialize mock bot without token."""
        self.token = "test_token"
        self.api_url = "https://api.telegram.org/bot_test"
        self.executor = None
        self.user_chains = {}
        
        # Import executor here to avoid circular imports
        from hybrid_sim import HybridExecutor
        self.executor = HybridExecutor(try_hardware=False)
        
        self.sent_messages = []
    
    def send_message(self, chat_id: int, text: str, reply_markup=None) -> bool:
        """Mock send_message that records calls."""
        self.sent_messages.append({
            "chat_id": chat_id,
            "text": text,
            "reply_markup": reply_markup
        })
        return True


class TestTelegramBot:
    """Test suite for Telegram bot."""
    
    @pytest.fixture
    def bot(self):
        """Create mock bot for testing."""
        return MockTelegramBot()
    
    def test_bot_initialization(self, bot):
        """Bot should initialize correctly."""
        assert bot is not None
        assert bot.executor is not None
    
    def test_handle_start_command(self, bot):
        """Should handle /start command."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "/start"
        }
        response = bot.handle_message(message)
        assert "Welcome" in response
        assert "Test" in response
    
    def test_handle_help_command(self, bot):
        """Should handle /help command."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "/help"
        }
        response = bot.handle_message(message)
        assert "Commands" in response
        assert "move" in response.lower()
    
    def test_handle_status_command(self, bot):
        """Should handle /status command."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "/status"
        }
        response = bot.handle_message(message)
        assert "Status" in response
        assert "Position" in response
    
    def test_handle_mode_command(self, bot):
        """Should handle /mode command."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "/mode"
        }
        response = bot.handle_message(message)
        assert "MODE" in response
        assert "SIMULATOR" in response or "HARDWARE" in response
    
    def test_handle_unknown_command(self, bot):
        """Should handle unknown commands gracefully."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "/unknown"
        }
        response = bot.handle_message(message)
        assert "Unknown command" in response or "help" in response.lower()
    
    def test_handle_move_command(self, bot):
        """Should handle move commands."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "move forward 10 cm"
        }
        response = bot.handle_message(message)
        assert response is not None
        # Response should contain robot action result
        assert "move" in response.lower() or "action" in response.lower()
    
    def test_handle_rotate_command(self, bot):
        """Should handle rotate commands."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "rotate right 45 degrees"
        }
        response = bot.handle_message(message)
        assert response is not None
        assert "rotate" in response.lower() or "action" in response.lower()
    
    def test_handle_grab_command(self, bot):
        """Should handle grab commands."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "grab the object"
        }
        response = bot.handle_message(message)
        assert response is not None
        assert "grab" in response.lower() or "gripper" in response.lower()
    
    def test_handle_release_command(self, bot):
        """Should handle release commands."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "release the object"
        }
        response = bot.handle_message(message)
        assert response is not None
    
    def test_handle_update_with_message(self, bot):
        """Should handle Telegram update with message."""
        update = {
            "update_id": 123,
            "message": {
                "chat": {"id": 456},
                "from": {"id": 789, "first_name": "Test"},
                "text": "move forward"
            }
        }
        response = bot.handle_update(update)
        assert response is not None
    
    def test_confidence_scoring(self, bot):
        """Response should include confidence scoring."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "move forward 10 cm"
        }
        response = bot.handle_message(message)
        assert "Confidence" in response
    
    def test_multi_command_chain(self, bot):
        """Should handle multi-step commands."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "move forward and rotate right and grab"
        }
        response = bot.handle_message(message)
        assert response is not None
    
    def test_invalid_command(self, bot):
        """Should handle invalid/unclear commands."""
        message = {
            "chat": {"id": 123},
            "from": {"id": 456, "first_name": "Test"},
            "text": "xyzabc nonsense gibberish"
        }
        response = bot.handle_message(message)
        assert "couldn't understand" in response.lower() or "try" in response.lower()
    
    def test_send_message_recorded(self, bot):
        """Mock bot should record sent messages."""
        bot.send_message(123, "test message")
        assert len(bot.sent_messages) == 1
        assert bot.sent_messages[0]["text"] == "test message"
        assert bot.sent_messages[0]["chat_id"] == 123
