"""
whatsapp_webhook.py - Flask integration for WhatsApp bot webhooks via Twilio.
Handles incoming WhatsApp messages through Twilio webhook.
"""

from flask import Flask, request, jsonify
from whatsapp_bot import create_whatsapp_bot, OpenGuyWhatsAppBot
import logging
import os

logger = logging.getLogger(__name__)


class WhatsAppWebhookServer:
    """Flask integration for WhatsApp webhook handling via Twilio."""
    
    def __init__(self, app: Flask, bot: OpenGuyWhatsAppBot, webhook_path: str = "/whatsapp"):
        """
        Initialize WhatsApp webhook integration.
        
        Args:
            app: Flask app
            bot: WhatsApp bot instance
            webhook_path: URL path for webhook (e.g., /whatsapp)
        """
        self.app = app
        self.bot = bot
        self.webhook_path = webhook_path
        self._register_routes()
    
    def _register_routes(self):
        """Register WhatsApp webhook routes."""
        
        @self.app.route(self.webhook_path, methods=["POST"])
        def whatsapp_webhook():
            """Handle incoming WhatsApp messages from Twilio."""
            try:
                # Get incoming message data from Twilio webhook
                incoming_data = request.form.to_dict()
                
                if not incoming_data:
                    logger.warning("Empty WhatsApp webhook data")
                    return jsonify({"status": "ok"}), 200
                
                message_sid = incoming_data.get("MessageSid", "unknown")
                logger.info(f"Received WhatsApp message: {message_sid}")
                
                # Handle the message
                response_text = self.bot.handle_webhook(incoming_data)
                
                # Send response if there is one
                if response_text and "From" in incoming_data:
                    phone_number = incoming_data["From"]
                    self.bot.send_message(phone_number, response_text)
                
                return jsonify({"status": "ok"}), 200
                
            except Exception as e:
                logger.error(f"WhatsApp webhook error: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route(self.webhook_path + "/status", methods=["GET"])
        def whatsapp_status():
            """Check WhatsApp webhook status."""
            return jsonify({
                "status": "active",
                "webhook": self.webhook_path,
                "platform": "whatsapp"
            }), 200


def setup_whatsapp_webhook(app: Flask, executor=None) -> WhatsAppWebhookServer:
    """
    Setup WhatsApp webhook integration with Flask app.
    
    Should be called during app initialization.
    
    Args:
        app: Flask app instance
        executor: Optional HybridExecutor to pass to bot
        
    Returns:
        WhatsAppWebhookServer instance, or None if credentials missing
    """
    # Check if Twilio credentials exist
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_phone = os.getenv("TWILIO_WHATSAPP_NUMBER")
    
    if not all([account_sid, auth_token, twilio_phone]):
        logger.info("Twilio credentials not set, WhatsApp bot disabled")
        return None
    
    try:
        bot = create_whatsapp_bot(
            account_sid=account_sid,
            auth_token=auth_token,
            twilio_phone=twilio_phone,
            executor=executor
        )
        webhook = WhatsAppWebhookServer(app, bot)
        logger.info("WhatsApp webhook initialized")
        return webhook
    except Exception as e:
        logger.error(f"Failed to initialize WhatsApp bot: {e}")
        return None
