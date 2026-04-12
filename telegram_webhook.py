"""
telegram_webhook.py - Flask integration for Telegram bot webhooks.
Handles incoming Telegram updates via webhook.
"""

from flask import Flask, request, jsonify
from telegram_bot import create_bot, OpenGuyTelegramBot
import logging
import os

logger = logging.getLogger(__name__)


class TelegramWebhookServer:
    """Flask blueprint for Telegram webhook integration."""
    
    def __init__(self, app: Flask, bot: OpenGuyTelegramBot, webhook_path: str = "/telegram"):
        """
        Initialize Telegram webhook integration.
        
        Args:
            app: Flask app
            bot: Telegram bot instance
            webhook_path: URL path for webhook (e.g., /telegram)
        """
        self.app = app
        self.bot = bot
        self.webhook_path = webhook_path
        self._register_routes()
    
    def _register_routes(self):
        """Register Telegram webhook routes."""
        
        @self.app.route(self.webhook_path, methods=["POST"])
        def telegram_webhook():
            """Handle incoming Telegram updates."""
            try:
                update = request.json
                
                if not update:
                    return jsonify({"error": "Empty update"}), 400
                
                logger.info(f"Received update: {update.get('update_id')}")
                
                # Handle the update
                response_text = self.bot.handle_update(update)
                
                # Send response if there is one
                if response_text and "message" in update:
                    chat_id = update["message"]["chat"]["id"]
                    self.bot.send_message(chat_id, response_text)
                
                return jsonify({"status": "ok"}), 200
                
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route(self.webhook_path + "/status", methods=["GET"])
        def telegram_status():
            """Check webhook status."""
            return jsonify({"status": "active", "webhook": self.webhook_path}), 200
    
    @staticmethod
    def set_webhook(bot_token: str, webhook_url: str) -> bool:
        """
        Set Telegram webhook URL.
        
        Must be called once to register the webhook with Telegram.
        
        Args:
            bot_token: Telegram bot token
            webhook_url: Full webhook URL (e.g., https://myserver.com/telegram)
            
        Returns:
            True if successful
        """
        import requests
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
            payload = {"url": webhook_url}
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                logger.info(f"Webhook set to {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False
    
    @staticmethod
    def delete_webhook(bot_token: str) -> bool:
        """
        Delete Telegram webhook.
        
        Args:
            bot_token: Telegram bot token
            
        Returns:
            True if successful
        """
        import requests
        
        try:
            url = f"https://api.telegram.org/bot{bot_token}/deleteWebhook"
            response = requests.post(url)
            
            if response.status_code == 200:
                logger.info("Webhook deleted")
                return True
            else:
                logger.error(f"Failed to delete webhook: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False


def setup_telegram_webhook(app: Flask, executor=None) -> TelegramWebhookServer:
    """
    Setup Telegram webhook integration with Flask app.
    
    Should be called during app initialization.
    
    Args:
        app: Flask app instance
        executor: Optional HybridExecutor to pass to bot (creates own if not provided)
        
    Returns:
        TelegramWebhookServer instance
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, Telegram bot disabled")
        return None
    
    try:
        bot = create_bot(bot_token, executor=executor)
        webhook = TelegramWebhookServer(app, bot)
        logger.info("Telegram webhook initialized")
        return webhook
    except Exception as e:
        logger.error(f"Failed to initialize Telegram bot: {e}")
        return None
