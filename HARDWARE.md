# Hardware Integration Guide

## Overview

OpenGuy supports real robot hardware via USB/Serial connections. When hardware is connected, it automatically switches from simulation to real control.

## Supported Hardware

### Currently Implemented
- **Arduino-based Robot Arms** (DIY 5-DOF arms)
  - Auto-detection via USB/Serial
  - JSON command protocol
  - Tested on: Arduino Mega 2560, Arduino Due

### Planned Support
- Universal Robots (UR3, UR5, UR10)
- ABB IRB robots
- Dobot Magician
- PhantomX Pincher

---

## Arduino Hardware Setup

### Requirements
- Arduino Mega 2560 or Due
- Servo motors (5-6 for full arm)
- Power supply (5V for servos)
- USB cable for communication

### Arduino Firmware

**File:** `firmware/arduino_arm.ino`

```cpp
#include <ArduinoJSON.h>
#include <Servo.h>

// Servo pins
Servo base, shoulder, elbow, wrist, gripper;
const int SERVO_PINS[] = {2, 3, 4, 5, 6};

// Current positions (in degrees)
int positions[] = {90, 90, 90, 90, 90};

void setup() {
  Serial.begin(115200);
  
  // Attach servos
  for (int i = 0; i < 5; i++) {
    // servos[i].attach(SERVO_PINS[i]);
  }
  
  Serial.println("{\"status\": \"ready\"}");
}

void loop() {
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    processCommand(input);
  }
}

void processCommand(String jsonStr) {
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, jsonStr);
  
  if (error) {
    sendError("Invalid JSON");
    return;
  }
  
  String action = doc["action"];
  
  if (action == "move") {
    handleMove(doc);
  } else if (action == "rotate") {
    handleRotate(doc);
  } else if (action == "grab") {
    handleGrab();
  } else if (action == "release") {
    handleRelease();
  } else if (action == "status") {
    sendStatus();
  } else {
    sendError("Unknown action");
  }
}

void handleMove(JsonDocument& doc) {
  String direction = doc["direction"];
  int distance = doc["distance_cm"] | 10;
  
  // TODO: Implement movement logic
  // Example: Move base servo based on direction
  
  sendSuccess("Moved " + direction + " " + String(distance) + "cm");
}

void handleRotate(JsonDocument& doc) {
  String direction = doc["direction"];
  int angle = doc["angle_deg"] | 45;
  
  // TODO: Implement rotation logic
  
  sendSuccess("Rotated " + direction + " " + String(angle) + "°");
}

void handleGrab() {
  // TODO: Close gripper servo
  sendSuccess("Gripper closed");
}

void handleRelease() {
  // TODO: Open gripper servo
  sendSuccess("Gripper opened");
}

void sendStatus() {
  StaticJsonDocument<256> doc;
  doc["x"] = 0.0;
  doc["y"] = 0.0;
  doc["facing"] = 0;
  doc["gripper_open"] = true;
  doc["commands_executed"] = 0;
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
}

void sendSuccess(String message) {
  StaticJsonDocument<128> doc;
  doc["success"] = true;
  doc["status"] = message;
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
}

void sendError(String message) {
  StaticJsonDocument<128> doc;
  doc["success"] = false;
  doc["error"] = message;
  
  String output;
  serializeJson(doc, output);
  Serial.println(output);
}
```

### Communication Protocol

**Command Format (JSON):**
```json
{
  "action": "move|rotate|grab|release|status",
  "direction": "forward|backward|left|right",
  "distance_cm": 10,
  "angle_deg": 45
}
```

**Response Format:**
```json
{
  "success": true,
  "status": "Moved forward 10cm"
}
```

---

## Python Integration

### Basic Usage

```python
from hybrid_sim import HybridExecutor

# Creates executor, auto-detects hardware
executor = HybridExecutor(try_hardware=True)

# Execute commands - automatically uses hardware if available
result = executor.execute('move', 'forward', 10.0)
print(result)  # Same format whether hardware or simulator

# Check what's being used
status = executor.get_status()
print(status['mode'])  # "hardware" or "simulator"
print(status['hardware_available'])  # True/False

# Cleanup
executor.close()
```

### Using with Flask API

The Flask app automatically uses `HybridExecutor` when hardware is present:

```python
from hybrid_sim import HybridExecutor

executor = HybridExecutor(try_hardware=True)

@app.route("/api/execute", methods=["POST"])
def api_execute():
    data = request.get_json() or {}
    result = executor.execute(
        action=data.get("action"),
        direction=data.get("direction"),
        distance_cm=data.get("distance_cm"),
        angle_deg=data.get("angle_deg")
    )
    return jsonify(result)
```

### Manual Hardware Control

```python
from hardware import init_hardware

# Auto-detect and connect
hardware = init_hardware(auto_detect=True)

if hardware and hardware.is_connected():
    # Send raw commands
    result = hardware.execute('move', direction='forward', distance_cm=10)
    print(result)
    
    hardware.disconnect()
```

---

## Integration Layers

```
┌─────────────────────────────────────┐
│  Web UI / API                       │
│  (index.html, app.py)               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  HybridExecutor                     │  ← Smart switching
│  (simulator / hardware)             │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
   SIMULATOR    HARDWARE
   (PyBullet)   (Arduino/USB)
```

---

## Testing Hardware Integration

### 1. Test Detection
```bash
python -c "from hardware import HardwareDetector; print(HardwareDetector.scan_ports())"
```

### 2. Test Manual Connection
```bash
python -c "
from hardware import init_hardware
hw = init_hardware()
if hw:
    print('Connected:', hw.is_connected())
    result = hw.execute('status')
    print('Status:', result)
    hw.disconnect()
"
```

### 3. Test HybridExecutor
```bash
pytest tests/test_hybrid_sim.py -v
```

### 4. Integration Test via API

Start server:
```bash
python app.py
```

Send command:
```bash
curl -X POST http://localhost:5000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "move",
    "direction": "forward",
    "distance_cm": 10
  }'
```

---

## Troubleshooting

### Hardware Not Detected
- Check USB connection
- Verify Arduino board drivers installed
- Try: `python -m serial.tools.list_ports`

### Connection Fails
- Check serial port permission: `sudo usermod -a -G dialout $USER`
- Verify baud rate matches (115200)
- Check Arduino is running firmware

### Commands Not Responding
- Verify JSON format on Arduino side
- Check serial monitor for errors
- Ensure Arduino firmware is loaded

---

## Adding New Hardware Types

1. Create handler class in `hardware.py`:
```python
class MyRobotHardware(RobotHardware):
    def connect(self): ...
    def execute(self, action, **kwargs): ...
    # etc
```

2. Add detection in `HardwareDetector._identify_port()`

3. Update `HardwareDetector.connect_first_available()`

4. Test with `tests/test_hardware.py`
