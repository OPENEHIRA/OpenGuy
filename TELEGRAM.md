# Telegram Bot Integration

OpenGuy includes a Telegram bot interface for controlling robot arms via chat. Send natural language commands from anywhere to control your robot seamlessly.

## Features

- **Natural Language Commands**: Control robots with conversational language
- **Real-time Status**: Check robot position, facing angle, and gripper status
- **Hardware/Simulator Mode**: Automatic detection and switching between real hardware and simulator
- **Multi-step Chains**: Execute complex sequences like "move forward AND rotate right AND grab"
- **Error Handling**: Graceful error messages and fallback to simulator if hardware unavailable

## Setup

### 1. Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the prompts
3. Choose a bot name (e.g., "OpenGuy Robot")
4. Choose a username (e.g., "openguy_robot_bot")
5. Copy the **API Token** provided (e.g., `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 2. Set Environment Variables

Create a `.env` file or export the token:

```bash
export TELEGRAM_BOT_TOKEN="your-token-here"
```

### 3. Run Flask Server with Webhook

The Telegram bot uses webhooks to receive updates in real-time:

```bash
# Set webhook URL (replace with your actual domain/IP)
export TELEGRAM_WEBHOOK_URL="https://yourdomain.com/telegram"

# Start server
python app.py
```

The webhook is automatically registered with Telegram when the server starts.

### 4. (Optional) For Local Testing

For development on localhost, you can use a tunneling service like `ngrok`:

```bash
# In another terminal, create public URL
ngrok http 5000

# Then set
export TELEGRAM_WEBHOOK_URL="https://abcd1234.ngrok.io/telegram"
```

## Commands

### Special Commands

- **`/start`** - Welcome message and quick start guide
- **`/help`** - Show available commands and examples
- **`/status`** - Check current robot position, angle, and gripper status
- **`/mode`** - Check if running in HARDWARE or SIMULATOR mode
- **`/stop`** - Stop current command chain execution

### Robot Commands

Say anything to control the robot. Examples:

```
move forward 10 cm
rotate right 45 degrees
grab the object
release
move forward AND rotate left AND grab
go backward 5cm
spin 90 degrees
pick up
let it go
```

The natural language parser understands variations like:
- `move forward` / `go forward` / `advance`
- `rotate right` / `turn right` / `spin right`
- `grab` / `pick up` / `grasp`
- `release` / `drop` / `open gripper`

## Robot Status Response Format

When you request `/status`, you'll get:

```
🤖 Robot Status

Mode: 🟢 HARDWARE (or 🟡 SIMULATOR)
Hardware Available: ✅ Yes (or ❌ No)
Position: (x, y) in cm
Facing: angle in degrees
Gripper: Open or Closed
Commands Executed: count
```

## Command Response Format

For each robot command, you'll receive:

```
🟢 Confidence: 85%

Action: Move
Direction: forward
Distance: 10cm

Result:
🚀 Moved forward 10.0cm
📍 New position: (10.0, 0.0)
```

Confidence indicators:
- 🟢 Green: High confidence (≥80%)
- 🟡 Yellow: Medium confidence (≥50%)
- 🔴 Red: Low confidence (<50%)

## Integration with Hardware

The Telegram bot automatically detects and connects to:

- **Arduino-based robot arms** - Auto-detected via USB serial
- **Simulator** - Used when hardware is unavailable

No additional configuration needed - the bot handles hardware detection internally.

## Webhook Security

### URL Registration

Webhooks are registered via the `/telegram/set_webhook` endpoint:

```bash
POST /telegram/set_webhook
Content-Type: application/json

{
  "webhook_url": "https://yourdomain.com/telegram"
}
```

### Webhook Status

Check webhook status:

```bash
GET /telegram/status
```

Response:
```json
{
  "status": "active",
  "webhook": "/telegram"
}
```

### Webhook Cleanup

Delete webhook when stopping the bot:

```bash
POST /telegram/delete_webhook
```

## Deployment

### Production Deployment

For production deployment:

1. **Use HTTPS**: Telegram requires valid SSL certificates
2. **Firebase/Heroku/AWS Lambda**: Serverless platforms with HTTPS
3. **Fixed Webhook URL**: Update `TELEGRAM_WEBHOOK_URL` before deploying

Example deployment to cloud platform:

```bash
# On cloud platform
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_WEBHOOK_URL="https://your-app.herokuapp.com/telegram"
python app.py
```

### Testing Without Public URL

For local testing without exposing server:

1. Use `ngrok` for local tunneling
2. Set webhook URL to ngrok URL
3. Stop `ngrok` when done to clean up

## Multi-Step Command Chains

Execute complex sequences of actions joined with "AND", "then", or "also":

```
move forward 10 cm AND rotate right 90 degrees AND grab
go forward then spin left then release
move backward, rotate right, and grab
```

The bot parses each step and executes them sequentially, displaying results for each step.

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Unknown command` | Unrecognized natural language | Use keywords: move, rotate, grab, release |
| `I couldn't understand that` | Unclear command | Be more specific: "move forward 10 cm" |
| `Hardware error` | Real hardware not available | Check USB connection, bot falls back to simulator |
| `Confidence too low` | Parser uncertain about command | Rephrase with clearer language |

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Architecture

```
User → Telegram Chat → Telegram API → Webhook → Flask App → Telegram Bot
                                         ↓
                                    HybridExecutor
                                         ↓
                        ┌────────────────┴────────────────┐
                     Hardware                          Simulator
                   (USB/Serial)                    (PyBullet 3D)
                   (Arduino Arm)                   (2D Fallback)
```

## API Reference

### Telegram Bot Class

```python
from telegram_bot import OpenGuyTelegramBot

bot = OpenGuyTelegramBot(token="your-token")

# Handle message
response = bot.handle_message({
    "chat": {"id": 123},
    "from": {"id": 456, "first_name": "User"},
    "text": "move forward 10 cm"
})

# Send message
bot.send_message(chat_id=123, text="Message text")

# Send photo
bot.send_photo(chat_id=123, photo_url="https://...", caption="Photo")

# Send animation
bot.send_animation(chat_id=123, animation_url="https://...", caption="Animation")
```

### Webhook Setup

```python
from telegram_webhook import setup_telegram_webhook

app = Flask(__name__)
webhook = setup_telegram_webhook(app, executor=my_executor)
```

### Set Webhook Method

```python
from telegram_webhook import TelegramWebhookServer

TelegramWebhookServer.set_webhook(
    bot_token="your-token",
    webhook_url="https://yourdomain.com/telegram"
)
```

## Troubleshooting

### Webhook Not Receiving Messages

1. **Check webhook URL**: Must be HTTPS with valid SSL
2. **Check firewall**: Telegram IPs (149.154.160.0/20) must be allowed
3. **Verify Flask app**: Test `/telegram/status` endpoint

### Bot Not Responding

1. **Check token**: Verify token is correct
2. **Check logs**: `python -c "import logging; logging.basicConfig(level=logging.DEBUG)"`
3. **Test locally**: Run with `python app.py` and check console

### Commands Not Parsing

1. **Use natural language**: Parser understands conversational text
2. **Be clear**: "move forward 10 cm" works better than "go 10"
3. **Check parser**: Test with `/help` to see accepted keywords

## Examples

### Session Example

```
User: /start
Bot: 🤖 Welcome! I can control robot arms using natural language...

User: move forward 10 cm
Bot: 🟢 Confidence: 92%
     Action: Move
     Direction: forward
     Distance: 10cm
     Result: 🚀 Moved forward 10.0cm

User: rotate right 45 degrees
Bot: 🟢 Confidence: 88%
     Action: Rotate
     ...

User: grab the object
Bot: 🟢 Confidence: 95%
     ...

User: /status
Bot: 🤖 Robot Status
     Mode: 🟢 HARDWARE
     Position: (10.0, 0.0)
     Gripper: Closed
```

### Multi-Step Command

```
User: advance 20cm, turn left, and pick up the block
Bot: 🟢 Confidence: 85%
     Step 1: Move forward 20cm ✅
     Step 2: Rotate left 45° ✅
     Step 3: Grab ✅
     All steps completed successfully!
```

## Support

For issues or questions:

1. Check this documentation
2. Run test suite: `pytest tests/test_telegram_bot.py -v`
3. Enable debug logging
4. Check Flask logs for webhook errors

## License

Same as OpenGuy project. See LICENSE file.
