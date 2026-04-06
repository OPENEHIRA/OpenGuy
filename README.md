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

## Installation & Usage

### Web UI (Recommended)
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
- [ ] Real hardware integration (USB/Serial)
- [ ] Telegram bot interface
- [ ] WhatsApp bot integration
- [ ] Mobile app (React Native)
- [ ] Cloud deployment
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

## Contributing

OpenGuy is beginner-friendly. Pick any roadmap item and submit a PR!

**Good starting points:**
- Add new robot actions to `parser.py`
- Improve the AI system prompt
- Create tests in `tests/`
- Add hardware drivers
- Build the mobile app
- Deploy to cloud

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
