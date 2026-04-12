# WhatsApp Bot Integration

Control your robot arm directly from WhatsApp using natural language commands. The WhatsApp bot provides instant access to your robot from the most popular messaging app.

## Features

- **Natural Language Control**: Send plain English commands to move and control your robot
- **Real-time Responses**: Get immediate feedback on robot status and actions
- **Hardware Auto-Detection**: Seamlessly switches between real hardware and simulator
- **Multi-step Chains**: Execute complex sequences: "move forward, rotate right, and grab"
- **Session Tracking**: Each user gets personalized command history and state
- **Media Support**: Receive status images and videos about robot operations

## Setup

### Prerequisites

1. **Twilio Account** (free trial available)
   - Visit [twilio.com](https://www.twilio.com/whatsapp)
   - Create a Twilio account
   - Get your Twilio phone number

2. **WhatsApp Business Account**
   - Registered with Twilio
   - Bot template approved (for high volume)

### 1. Install Twilio SDK

Already included in requirements.txt via `requests`. Twilio webhook uses form data, not SDK.

### 2. Get Twilio Credentials

1. Go to [Twilio Console](https://www.twilio.com/console)
2. Find your **Account SID** (starts with "AC")
3. Find your **Auth Token** (long string)
4. Navigate to **Messaging** → **Try it out** → **Send a WhatsApp Message**
5. Copy your **Twilio WhatsApp Number** (e.g., "+1415xxx1234")

### 3. Set Environment Variables

Create a `.env` file or export variables:

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_WHATSAPP_NUMBER="whatsapp:+1415xxx1234"
```

Or in `.env` file:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+1415xxx1234
```

### 4. Setup Webhook URL

Twilio needs to know where to send messages. Configure it in Twilio Console:

1. Go to **Messaging** → **Settings** → **WhatsApp Sandbox Settings**
2. Set **When a message comes in** to:
   ```
   https://yourdomain.com/whatsapp
   ```
3. Save configuration

### 5. Run Flask Server

```bash
python app.py
```

Server will report:
```
✓ WhatsApp bot enabled
```

### 6. Start Chatting

Add the Twilio WhatsApp number to your contacts and send a message:
```
hello
```

Bot will respond with welcome message.

---

## Commands

### Special Commands

| Command | Description |
|---------|-------------|
| `/start` or `hello` | Welcome message and quick start |
| `/help` | Show all available commands |
| `/status` | Check robot position, angle, gripper state |
| `/mode` | Check if using HARDWARE or SIMULATOR |
| `/stop` | Stop current command execution |

### Robot Commands

Just write what you want the robot to do:

```
move forward 10 cm
rotate right 45 degrees
grab the object
release
move forward, rotate left, grab
go backward 5 cm
spin 90 degrees
pick up the block
let it go
```

### Examples

**Single Commands:**
```
User: move forward 10 cm
Bot:  🟢 Confidence: 92%
      Action: Move
      Direction: forward
      Distance: 10cm
      Result: 🚀 Moved forward 10.0cm
              📍 New position: (10.0, 0.0)
```

**Status Check:**
```
User: /status
Bot:  🤖 Robot Status
      Mode: 🟢 HARDWARE
      Hardware Available: ✅ Yes
      Position: (10.0, 0.0)
      Facing: 0°
      Gripper: Open
      Commands Executed: 1
```

**Multi-Step Sequence:**
```
User: move forward 5cm, rotate right, grab
Bot:  Step 1/3: Moved forward 5.0cm ✓
      Step 2/3: Rotated right 45° ✓
      Step 3/3: Gripper CLOSED ✓
```

**Check Mode:**
```
User: /mode
Bot:  🟡 SIMULATOR MODE
      No hardware detected. Using virtual simulator.
```

---

## Deployment

### Local Testing (ngrok tunnel)

For testing on localhost without public domain:

```bash
# Terminal 1: Start ngrok tunnel
ngrok http 5000

# You'll see something like:
# Forwarding          https://abcd1234.ngrok.io -> localhost:5000

# Terminal 2: Set webhook URL in Twilio Console to:
# https://abcd1234.ngrok.io/whatsapp

# Terminal 3: Run Flask app
python app.py
```

### Production Deployment (Heroku example)

```bash
# Deploy to Heroku
git push heroku main

# Set environment variables
heroku config:set TWILIO_ACCOUNT_SID="ACxxxxxxx"
heroku config:set TWILIO_AUTH_TOKEN="xxxxxxx"
heroku config:set TWILIO_WHATSAPP_NUMBER="whatsapp:+1415xxx1234"

# Update Twilio webhook URL to your Heroku app
# In Twilio Console: https://your-app.herokuapp.com/whatsapp
```

### Production Deployment (AWS example)

```bash
# Deploy Lambda function with Flask app
# Or use Elastic Beanstalk

# Set environment variables in AWS
# Update Twilio console webhook URL
```

---

## How It Works

### Message Flow

```
User on WhatsApp
       ↓
Sends message
       ↓
Twilio API receives
       ↓
Sends webhook POST to /whatsapp
       ↓
Flask app processes
       ↓
WhatsAppBot.handle_message()
       ↓
Parses natural language
       ↓
HybridExecutor executes command
       ↓
Formats response
       ↓
Sends back via Twilio API
       ↓
User sees response on WhatsApp
```

### Architecture

```
┌─────────────┐
│   WhatsApp  │
│   User      │
└──────┬──────┘
       │
       ├─────→ Twilio WhatsApp Service
       │              ↓
       │         HTTP POST
       │              ↓
       │        Flask /whatsapp
       │              ↓
       │    WhatsAppWebhookServer
       │              ↓
       │    OpenGuyWhatsAppBot
       │              ↓
       │    HybridExecutor
       │         ↙      ↘
       │    Hardware  Simulator
       │              ↓
       │        HTTP POST Response
       │              ↓
       └─────← Twilio API ← Your Server
```

---

## Natural Language Understanding

The parser recognizes variations of commands:

### Movement Commands
- "move forward" / "go forward" / "advance"
- "move backward" / "go back" / "retreat"
- "move left" / "turn left"
- "move right" / "turn right"

### Rotation Commands
- "rotate right" / "turn right" / "spin right"
- "rotate left" / "turn left" / "spin left"
- "rotate 45 degrees" / "spin 90°"

### Gripper Commands
- "grab" / "pick up" / "grasp"
- "release" / "drop" / "open gripper"
- "squeeze" / "hold tight"

### Distances
- "10 cm" / "10cm" / "10 centimeters"
- "5 inches" / "5in"
- "a little" (2-5cm) / "a lot" (20-30cm)

### Angles
- "45 degrees" / "45°" / "45"
- "left" (45°) / "right" (45°)
- "half-turn" (180°) / "full turn" (360°)

---

## Error Handling

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `Couldn't understand command` | Unclear natural language | Use keywords: move, rotate, grab, release |
| `Hardware error` | Robot not connected | Check USB, bot falls back to simulator |
| `Confidence too low` | Ambiguous command | Be more specific: "move forward 10 cm" |
| `Webhook not receiving` | Twilio not configured | Check webhook URL in Twilio Console |

### Debug Mode

Enable logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check Flask logs for webhook errors.

---

## Response Format

### Success Response
```
🟢 Confidence: 92%

Action: Move
Direction: forward
Distance: 10cm

Result:
🚀 Moved forward 10.0cm
📍 New position: (10.0, 0.0)
```

### Error Response
```
🔴 Confidence: 32%

Sorry, I couldn't understand that. Try:
• move forward
• rotate right
• grab
```

### Status Response
```
🤖 Robot Status

Mode: 🟢 HARDWARE
Hardware Available: ✅ Yes
Position: (10.0, 0.0)
Facing: 45°
Gripper: Closed
Commands Executed: 5
```

---

## API Reference

### WhatsAppBot Class

```python
from whatsapp_bot import OpenGuyWhatsAppBot

bot = OpenGuyWhatsAppBot(
    account_sid="ACxxxxxxx",
    auth_token="token",
    twilio_phone="whatsapp:+1415xxx1234"
)

# Handle incoming message
response = bot.handle_message({
    "From": "whatsapp:+1234567890",
    "Body": "move forward 10 cm",
    "MessageSid": "SM123456"
})

# Send message
bot.send_message("+1234567890", "Message text")

# Send media
bot.send_media("+1234567890", "https://example.com/image.jpg", "Caption")
```

### Webhook Integration

```python
from whatsapp_webhook import setup_whatsapp_webhook

app = Flask(__name__)

# In main section
webhook = setup_whatsapp_webhook(app, executor=my_executor)
```

---

## Multi-User Support

Each user's session is stored separately:

```python
# Each phone number gets its own session
bot.user_sessions[phone_number] = {
    "last_action": "move",
    "pending_chain": None,
    "commands_executed": 5
}
```

Users can:
- Execute commands independently
- Track their own command history
- Have separate conversation context

---

## Twilio Pricing

**Free Trial:**
- $15 free Twilio credit for first 30 days
- Enough for ~100-200 messages during trial

**After Trial:**
- WhatsApp messages: $0.005-0.01 per message
- Two-way conversations: Varies by region
- Always cheaper for low-volume usage

Check [Twilio Pricing](https://www.twilio.com/sms/pricing) for current rates.

---

## Troubleshooting

### Webhook Not Receiving Messages

1. **Check Twilio Console:**
   ```
   Messaging → WhatsApp Sandbox Settings
   When a message comes in: https://yourdomain.com/whatsapp
   ```

2. **Check URL is HTTPS** (required by Twilio)

3. **Test webhook status:**
   ```
   GET http://localhost:5000/whatsapp/status
   ```
   Should return: `{"status": "active", "webhook": "/whatsapp", "platform": "whatsapp"}`

4. **Check Flask logs** for errors

### Bot Not Responding

1. Verify Twilio credentials in environment
2. Check internet connection
3. Run server with debug logging:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

### Commands Not Parsing

1. Use clearer natural language
2. Include measurement units: "move forward 10 cm"
3. Check parser with `/help` for accepted keywords

### Hardware Not Detecting

1. Check USB cable connection
2. Check `/status` - should show "SIMULATOR" if hardware unavailable
3. Bot will fall back to simulator automatically

---

## Examples

### Setup Session

```bash
# Set environment variables
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_WHATSAPP_NUMBER="whatsapp:+1415561234"

# Run server
python app.py

# In Twilio Console, set webhook to:
# https://yourdomain.com/whatsapp

# Add Twilio WhatsApp number to your contacts
# Send: hello
```

### Usage Session

```
You: hello
Bot: 🤖 Welcome to OpenGuy!
     I can control robot arms using natural language.
     Try commands like:
     • move forward 10 cm
     • rotate right 45 degrees
     • grab the object

You: move forward
Bot: 🟢 Confidence: 92%
     Action: Move
     Direction: forward
     Distance: 10cm
     Result: 🚀 Moved forward 10.0cm

You: rotate right 90
Bot: 🟢 Confidence: 88%
     ...

You: /status
Bot: 🤖 Robot Status
     Mode: 🟡 SIMULATOR
     Position: (10.0, 0.0)
     Facing: 90°
     Gripper: Open
```

---

## Support

For issues:

1. Check this documentation
2. Run test suite: `pytest tests/test_whatsapp_bot.py -v`
3. Check Twilio webhook logs
4. Enable debug logging in Flask

## License

Same as OpenGuy project. See LICENSE file.
