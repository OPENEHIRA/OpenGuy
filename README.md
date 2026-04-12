# OpenGuy

**Control a robot with plain English.**

OpenGuy converts natural language commands into structured robot actions — no robotics experience required. Type what you want the arm to do, and OpenGuy handles the rest.

> **Status:** Production Ready — Flask backend · AI parser · Web UI · Multi-step chains · 2D visualization · voice input

---

## What's New (Latest Update)

✨ **Major Enhancements:**
- **Flask Backend**: Full REST API for robot control
- **Multi-Step Command Chains**: "pick up AND move forward AND release"
- **2D Workspace Visualization**: Real-time robot position tracking
- **Voice Input**: Browser-native voice commands via Web Speech API
- **Real Hardware Integration**: USB/Serial with auto-detection
- **Telegram Bot**: Chat interface for robot control
- **WhatsApp Bot**: Twilio-powered WhatsApp integration for robot control
- **Type-Safe Code**: Full type hints across all modules
- **Better Error Handling**: Comprehensive input validation

---

## Demo

### Single Commands
```
Input   →  "go a bit forward"
Parsed  →  { "action": "move", "direction": "forward", "distance_cm": 5, "confidence": 0.92 }
Output  →  Moving forward 5 cm... ✓

Input   →  "turn slightly right"
Parsed  →  { "action": "rotate", "direction": "right", "angle_deg": 15, "confidence": 0.88 }
Output  →  Rotating right 15°... ✓
```

### Command Chains
```
Input   →  "move forward AND rotate right AND grab"
Parsed  →  [
              { "action": "move", "direction": "forward", "distance_cm": 5 },
              { "action": "rotate", "direction": "right", "angle_deg": 45 },
              { "action": "grab", "confidence": 0.95 }
            ]
Output  →  Step 1/3 ✓ Step 2/3 ✓ Step 3/3 ✓
```

---

## Features

### Core Capabilities
- ✅ Natural language command parsing (AI + regex fallback)
- ✅ Confidence scoring (0.0-1.0) for ambiguous commands
- ✅ Multi-step command chains with "AND", "THEN", "&", or commas
- ✅ 2D workspace visualization showing robot position & orientation
- ✅ Real-time thinking state during processing
- ✅ Context-aware smart suggestions
- ✅ Persistent command history with replay
- ✅ Offline operation (regex parser works without API)
- ✅ **Real hardware integration** (USB/Serial with auto-detection)
- ✅ **Hybrid simulator/hardware mode** (seamless switching)

### API Endpoints
- `GET /` — Web UI
- `POST /api/parse` — Parse single command
- `POST /api/execute` — Execute command
- `GET /api/status` — Get robot state
- `POST /api/chain/parse` — Parse multi-step chain
- `POST /api/chain/execute` — Execute chain step
- `GET /api/chain/status` — Get chain progress
- `GET /api/visualize` — Get workspace SVG
- `GET /api/health` — Health check
- `GET /api/history` — Get command history

---

## How It Works

**1. Multi-Step Chain Parsing**
Commands separated by AND, THEN, &, or commas are parsed as chains:
```
"move forward 10cm AND rotate right 45° AND grab"
                  ↓
        [command1, command2, command3]
```

**2. 2D Workspace Visualization**
Real-time SVG showing:
- Robot position (green circle)
- Orientation (cyan direction line)
- Gripper state (open/closed indicator)
- Gridlines and coordinate labels

**3. Sequential Chain Execution**
Each step executes in order with progress tracking:
```
Step 1/3: Moved forward 10cm → Pos: (0.0, 10.0)
Step 2/3: Rotated right 45° → Facing: 45°
Step 3/3: Gripper CLOSED
```

**4. Flask Backend**
Production-ready REST API with:
- Type hints throughout
- Comprehensive error handling
- State management
- History persistence (JSON)
- Command validation

---

## Hardware Integration

OpenGuy automatically detects and uses connected robot hardware. When no hardware is available, it falls back to simulation seamlessly.

### Supported Hardware
- **Arduino-based Robot Arms** (DIY 5-DOF, auto-detected)
- **Simulator Fallback** (PyBullet 3D + 2D modes)

### Quick Start with Hardware

```python
from hybrid_sim import HybridExecutor

# Auto-detects hardware on startup
executor = HybridExecutor(try_hardware=True)

# Commands automatically use hardware if available
executor.execute('move', 'forward', 10)

# Check mode
print(executor.get_status()['mode'])  # "hardware" or "simulator"
```

For detailed hardware setup, see [HARDWARE.md](HARDWARE.md)

---

## Telegram Bot Interface

Control your robot from Telegram chat. Send natural language commands from anywhere to move your robot arm, check status, and execute complex multi-step sequences.

### Quick Start
```bash
# Set your Telegram bot token
export TELEGRAM_BOT_TOKEN="your-bot-token-from-BotFather"

# Start Flask server with webhook
python app.py

# Chat with your bot on Telegram!
```

### Features
- 💬 Natural language commands in chat
- 🤖 Auto-detection of hardware vs simulator
- 📊 Real-time robot status updates
- 🔗 Multi-step command chains
- 🎯 Confidence scoring for command clarity

### Example Commands
```
User: move forward 10 cm
Bot: 🚀 Moved forward 10.0cm
    📍 New position: (10.0, 0.0)

User: rotate right AND grab
Bot: Step 1/2 ✓ Rotated right 45°
    Step 2/2 ✓ Gripper CLOSED

User: /status
Bot: 🤖 Robot Status
    Mode: 🟢 HARDWARE
    Position: (10.0, 0.0)
    Gripper: Closed
```

For detailed Telegram setup and commands, see [TELEGRAM.md](TELEGRAM.md)

---

## WhatsApp Bot Interface

Control your robot directly from WhatsApp using Twilio integration. Reach your robot from the most popular messaging app with natural language commands.

### Quick Start
```bash
# Set your Twilio credentials
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token_here"
export TWILIO_WHATSAPP_NUMBER="whatsapp:+1415xxx1234"

# Start Flask server with webhook
python app.py

# Chat with your bot on WhatsApp!
```

### Features
- 💬 WhatsApp chat interface via Twilio
- 🤖 Hardware auto-detection
- 📊 Real-time status and feedback
- 🔗 Multi-step command chains
- 👥 Multi-user session support

### Example Session
```
User: hello
Bot: 🤖 Welcome to OpenGuy!
     I can control robot arms using natural language.

User: move forward, rotate right, grab
Bot: 🟢 Confidence: 88%
     Step 1/3 ✓ Moved forward 10cm
     Step 2/3 ✓ Rotated right 45°
     Step 3/3 ✓ Gripper CLOSED

User: /status
Bot: 🤖 Robot Status
     Mode: 🟡 SIMULATOR
     Position: (10.0, 0.0)
     Gripper: Closed
```

For detailed WhatsApp setup and commands, see [WHATSAPP.md](WHATSAPP.md)

---
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py

# Open http://localhost:5000 in your browser
```

### Docker (Coming Soon)
```bash
docker build -t openguy .
docker run -p 5000:5000 openguy
```

### API Usage
```bash
# Parse a command
curl -X POST http://localhost:5000/api/parse \
  -H "Content-Type: application/json" \
  -d '{"command": "move forward 10 cm"}'

# Parse a chain
curl -X POST http://localhost:5000/api/chain/parse \
  -H "Content-Type: application/json" \
  -d '{"command": "move forward AND rotate right AND grab"}'

# Get visualization
curl http://localhost:5000/api/visualize > workspace.svg
```

---

## Project Structure

```
OpenGuy/
├── app.py                  # Flask backend (REST API)
├── parser.py              # AI parser + regex fallback
├── simulator.py           # Robot state simulator
├── chain_executor.py      # Multi-step chain handler
├── visualizer.py          # 2D workspace visualization
├── index.html             # Web UI
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## Roadmap

### ✅ Completed
- [x] AI-based natural language parser (Claude Haiku)
- [x] Regex fallback with confidence scoring
- [x] Web UI with real-time thinking state
- [x] Command history with persistent replay
- [x] Smart context-aware suggestions
- [x] **Flask backend with REST API**
- [x] **Multi-step command chains**
- [x] **2D workspace visualization**
- [x] Type hints and validation

### 🚧 In Progress / Planned
- [x] PyBullet 3D physics simulation
- [x] Real hardware integration (USB/Serial)
- [x] Telegram bot interface
- [x] WhatsApp bot integration
- [x] **Robot learning & autonomous adaptation**
- [x] **Mobile app (React Native)** ✨ NEW
- [x] **Cloud deployment (Heroku/AWS)** ✨ NEW
- [ ] Advanced analytics dashboard

---

## Configuration

### Environment Variables
```bash
# Anthropic API key (optional, falls back to regex parser)
export ANTHROPIC_API_KEY=sk-ant-...

# Server configuration
export FLASK_ENV=development  # or production
export FLASK_PORT=5000
```

### Configuration File
Create `.env` file:
```
ANTHROPIC_API_KEY=sk-ant-...
FLASK_ENV=production
FLASK_PORT=5000
```

---

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Type checking
mypy *.py

# Linting
pylint *.py

# Format code
black *.py
```

---

## API Documentation

### Parse Command
```
POST /api/parse
Content-Type: application/json

Request:
{
  "command": "move forward 10 cm",
  "api_key": "sk-ant-..." (optional)
}

Response:
{
  "action": "move",
  "direction": "forward",
  "distance_cm": 10.0,
  "angle_deg": null,
  "confidence": 0.5,
  "raw": "move forward 10 cm"
}
```

### Parse Chain
```
POST /api/chain/parse
Content-Type: application/json

Request:
{
  "command": "move forward AND rotate right AND grab"
}

Response:
{
  "is_chain": true,
  "total_steps": 3,
  "commands": [
    { "action": "move", "direction": "forward", ... },
    { "action": "rotate", "direction": "right", ... },
    { "action": "grab", ... }
  ],
  "progress": { ... }
}
```

---

## 📱 Mobile App (React Native)

Control your robot from anywhere with the OpenGuy mobile app.

### Features
- 🎤 Voice control for natural language commands
- 📊 Real-time robot status and position tracking
- 🧠 View robot's learned strategies and success rates
- 📜 Command history with replay
- 🔄 Switch between WhatsApp, Telegram, or direct API
- 💫 Beautiful native interface for iOS and Android

### Quick Start
```bash
cd mobile
npm install                    # Install dependencies
npm run ios                   # Run on iOS simulator
# or
npm run android              # Run on Android emulator
```

### Build for Production
```bash
# iOS (macOS required)
npm run build:ios
# or
# Android
npm run build:android
```

For detailed setup, see [MOBILE_SETUP.md](MOBILE_SETUP.md)

---

## 🚀 Cloud Deployment

Deploy OpenGuy to production with Heroku or AWS.

### Quick Deploy to Heroku (⚡ Fastest)
```bash
heroku create openguy-robot
heroku config:set ROBOT_MODE=simulator
git push heroku main
heroku open
```

Your app is live! Visit: `https://openguy-robot.herokuapp.com`

### AWS Deployment
```bash
# Option 1: Elastic Beanstalk (easiest)
eb create openguy-env
eb open

# Option 2: ECS with Docker (most scalable)
aws ecr create-repository --repository-name openguy
docker build -t openguy .
docker tag openguy:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/openguy:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/openguy:latest
```

### Features
- ✅ Auto-scaling based on demand
- ✅ SSL/HTTPS included
- ✅ Health checks and monitoring
- ✅ Docker containerization
- ✅ CI/CD ready
- ✅ Persistent storage for learning data

For detailed deployment guides, see [DEPLOYMENT.md](DEPLOYMENT.md)

---

## 🧠 Robot Learning System

OpenGuy includes an intelligent learning system that enables robots to improve over time.

### How It Works
```
Command 1: "move forward 50cm" → SUCCESS ✓
Command 2: "move forward 50cm" → SUCCESS ✓
Command 3: "move forward 50cm" → COLLISION ✗

Robot learns: "50cm is risky, use smaller steps"

Command 4: "move forward 50cm" → AUTO-ADJUSTED to 2x25cm steps → SUCCESS ✓
```

### Features
- 📊 Tracks success/failure patterns
- 🔄 Auto-adjusts movement parameters
- 💾 Persists learned models to disk
- 📈 Generates learning reports
- 🎯 Predicts optimal execution strategies

### Access Learning Data
```bash
# Via Mobile App
User: /learn
Bot: 📚 Robot Learning Report
     Success Rate: 85%
     Learned Strategies: 7
```

For details, see [ROBOT_LEARNING.md](ROBOT_LEARNING.md)

---

## Contributing

OpenGuy is beginner-friendly. Pick any roadmap item and submit a PR!

**Good starting points:**
- Add new robot actions to `parser.py`
- Improve the AI system prompt
- Create tests in `tests/`
- Add hardware drivers
- Enhance the mobile app
- Improve cloud deployment

**How to contribute:**
1. Fork the repo
2. Create a branch: `git checkout -b your-feature`
3. Make your changes & test locally
4. Push & open a pull request

---

## License

MIT — free to use, modify, and distribute.

---

## Support

- 💬 [GitHub Discussions](https://github.com/OPENEHIRA/OpenGuy/discussions)
- 🐛 [Report Issues](https://github.com/OPENEHIRA/OpenGuy/issues)
- ⭐ [Star on GitHub](https://github.com/OPENEHIRA/OpenGuy)

---

*OpenGuy makes robot control conversational. Built with ❤️ by the community.*
