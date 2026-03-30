# 🦾 EchoArm

**Control a robot arm with plain English. No code required.**

EchoArm is an open-source project that translates natural language commands into robot arm actions using an AI-powered parser. Type what you want the robot to do — EchoArm understands the intent and executes it.

> **Status:** MVP (simulator) · AI parser live · Hardware integration coming soon

---

## ✨ Demo

```
You:     go a bit forward
EchoArm: [Parsed] {"action":"move","direction":"forward","distance_cm":5,"confidence":0.9}
         Moving forward 5 cm... ✓

You:     turn slightly right
EchoArm: [Parsed] {"action":"rotate","direction":"right","angle_deg":15,"confidence":0.85}
         Rotating right 15°... ✓

You:     pick up the object
EchoArm: [Parsed] {"action":"grab","confidence":0.95}
         Closing gripper... ✓
```

No robotics background needed. Speak naturally — EchoArm figures out the rest.

---

## 🚀 Quickstart

**Requirements:** Python 3.8+ · No external libraries needed

```bash
git clone https://github.com/NEHIRAAS/echoarm.git
cd echoarm
python main.py
```

That's it. You're running an AI-powered simulated robot arm in your terminal.

---

## 🧠 How It Works

EchoArm uses a two-stage parsing pipeline in `parser.py`:

**Stage 1 — AI parser:** Your input is sent to Claude (via the Anthropic API) with a structured prompt that instructs it to return a JSON command. This handles flexible, natural phrasing like "swing way to the left" or "drop it gently" that rigid pattern-matching cannot.

**Stage 2 — Regex fallback:** If the API is unreachable, the parser automatically falls back to the original regex logic. The system keeps working offline — it just becomes less flexible.

Every parsed command includes a `confidence` score. If confidence falls below 0.5, EchoArm warns you that it may have misunderstood, so you can rephrase rather than watch the robot do something unexpected.

---

## 🗂️ Project Structure

```
echoarm/
├── main.py        # Entry point — starts the chat loop
├── parser.py      # AI-powered NL → structured command converter
└── simulator.py   # Simulates robot arm movement
```

Three files. Intentionally minimal. Easy to read, easy to extend.

---

## ⚙️ What EchoArm Understands

The AI parser handles both precise and natural phrasing:

| What you say | What EchoArm does |
|---|---|
| `move forward 10 cm` | Moves arm forward exactly 10 cm |
| `go a bit forward` | Moves forward ~5 cm |
| `swing way to the left` | Moves left ~30 cm |
| `rotate left 90 degrees` | Rotates left 90° |
| `turn slightly right` | Rotates right ~15° |
| `grab` / `pick up the object` | Closes the gripper |
| `release` / `drop it gently` | Opens the gripper |
| `stop` | Halts all movement |

---

## 🗺️ Roadmap

- [x] Regex-based natural language parser (MVP)
- [x] Python simulator (MVP)
- [x] AI-powered parser with confidence scoring
- [x] Graceful offline fallback
- [ ] Web UI for command input
- [ ] PyBullet physics simulation
- [ ] Serial/USB connection to real hardware
- [ ] Multi-step instructions ("pick up the block and place it on the left")
- [ ] Voice input

Have an idea? [Open an issue](https://github.com/NEHIRAAS/echoarm/issues) — contributions are welcome.

---

## 🤝 Contributing

EchoArm is beginner-friendly. If you can write Python, you can contribute.

**Good first issues:**
- Add new command types to the regex fallback in `parser.py`
- Improve the AI system prompt for better edge-case handling
- Write tests for the `parse()` function
- Connect `simulator.py` to real serial hardware
- Improve this README

**How to contribute:**

1. Fork the repo
2. Create a branch: `git checkout -b my-feature`
3. Make your changes
4. Open a pull request with a short description

No contribution is too small. Found a typo? Send a PR.

---

## 💡 Why EchoArm?

Most robotics projects require specialised knowledge — ROS, motor drivers, inverse kinematics. EchoArm starts from a different premise: **what if anyone could control a robot by just talking to it?**

This project is early. The simulator is a proof of concept. The long-term goal is a lightweight, dependency-free layer that sits between a chat interface and real hardware — accessible to hobbyists, educators, and developers alike.

---

## 📄 License

MIT — free to use, modify, and distribute.

---

*Built by [@NEHIRAAS](https://github.com/NEHIRAAS) · Star ⭐ if this is useful*
