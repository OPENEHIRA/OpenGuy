#!/bin/bash
# ============================================
#  OpenGuy Robotics — Smart Auto-Installer
#  Works on macOS and Linux
# ============================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "  ============================================"
echo "   OpenGuy Robotics — Smart Auto-Installer"
echo "  ============================================"
echo ""

# ── Step 1: Check Python ──
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$($cmd --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 10 ] && [ "$MINOR" -le 13 ]; then
            PYTHON_CMD="$cmd"
            echo -e "${GREEN}[OK]${NC} Compatible Python found: $cmd ($VER)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${YELLOW}[WARN]${NC} No compatible Python 3.10-3.13 found."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            echo -e "${YELLOW}[INFO]${NC} Installing Python 3.12 via Homebrew..."
            brew install python@3.12
            PYTHON_CMD="python3.12"
        else
            echo -e "${RED}[ERROR]${NC} Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif command -v apt-get &>/dev/null; then
        echo -e "${YELLOW}[INFO]${NC} Installing Python 3.12 via apt..."
        sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv python3-pip
        PYTHON_CMD="python3.12"
    elif command -v dnf &>/dev/null; then
        echo -e "${YELLOW}[INFO]${NC} Installing Python 3.12 via dnf..."
        sudo dnf install -y python3.12
        PYTHON_CMD="python3.12"
    else
        echo -e "${RED}[ERROR]${NC} Please install Python 3.12 manually: https://www.python.org/downloads/"
        exit 1
    fi
fi

echo ""

# ── Step 2: Check Git ──
if ! command -v git &>/dev/null; then
    echo -e "${YELLOW}[WARN]${NC} Git not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        xcode-select --install 2>/dev/null || brew install git
    elif command -v apt-get &>/dev/null; then
        sudo apt-get install -y git
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y git
    fi
fi

echo ""

# ── Step 3: Clone ──
if [ -d "OpenGuy" ]; then
    echo -e "${GREEN}[INFO]${NC} OpenGuy directory exists. Pulling latest..."
    cd OpenGuy
    git pull
else
    echo -e "${GREEN}[INFO]${NC} Cloning OpenGuy..."
    git clone https://github.com/OPENEHIRA/OpenGuy.git
    cd OpenGuy
fi

echo ""

# ── Step 4: Install deps ──
echo -e "${GREEN}[INFO]${NC} Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install -r requirements.txt

echo ""
echo "  ============================================"
echo "   All dependencies installed successfully!"
echo "  ============================================"
echo ""
echo "  Starting OpenGuy server on http://localhost:5000"
echo "  Press Ctrl+C to stop the server."
echo ""

# ── Step 5: Start ──
$PYTHON_CMD server.py
