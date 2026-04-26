#!/bin/bash
# ============================================
#  OpenGuy Robotics — Smart Auto-Installer
#  Works on Windows (Git Bash), macOS, Linux
# ============================================

set -e

echo ""
echo "  ============================================"
echo "   OpenGuy Robotics — Smart Auto-Installer"
echo "  ============================================"
echo ""

# Detect OS
IS_WINDOWS=false
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "mingw"* ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
fi

# ── Step 1: Find a compatible Python (3.10-3.13) ──
PYTHON_CMD=""

check_python() {
    local cmd=$1
    if command -v "$cmd" &>/dev/null; then
        local ver_output
        ver_output=$($cmd --version 2>&1)
        # Only proceed if output starts with "Python"
        if [[ "$ver_output" == Python* ]]; then
            local ver=$(echo "$ver_output" | awk '{print $2}')
            local major=$(echo "$ver" | cut -d. -f1)
            local minor=$(echo "$ver" | cut -d. -f2)
            if [[ "$major" =~ ^[0-9]+$ ]] && [[ "$minor" =~ ^[0-9]+$ ]]; then
                if [ "$major" -eq 3 ] && [ "$minor" -ge 10 ] && [ "$minor" -le 13 ]; then
                    PYTHON_CMD="$cmd"
                    echo "[OK] Compatible Python found: $cmd ($ver)"
                    return 0
                fi
            fi
        fi
    fi
    return 1
}

# Try various Python commands
for cmd in python3.12 python3.13 python3.11 python3.10 python3 python; do
    if check_python "$cmd"; then
        break
    fi
done

# On Windows, also try the py launcher
if [ -z "$PYTHON_CMD" ] && [ "$IS_WINDOWS" = true ]; then
    if command -v py &>/dev/null; then
        for minor in 12 13 11 10; do
            if py -3.$minor --version &>/dev/null 2>&1; then
                PYTHON_CMD="py -3.$minor"
                echo "[OK] Compatible Python found via py launcher: 3.$minor"
                break
            fi
        done
    fi
fi

# No compatible Python found — install it
if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "[WARN] No compatible Python 3.10-3.13 found."
    echo ""

    if [ "$IS_WINDOWS" = true ]; then
        # Windows: use winget
        if command -v winget &>/dev/null; then
            echo "[INFO] Installing Python 3.12 via winget..."
            winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
            # After install, the py launcher should work
            PYTHON_CMD="py -3.12"
            echo "[OK] Python 3.12 installed. You may need to RESTART Git Bash."
            echo ""
            echo "  After restarting, run this command again:"
            echo "  curl -sL https://raw.githubusercontent.com/OPENEHIRA/OpenGuy/main/install.sh | bash"
            echo ""
            exit 0
        else
            echo "[INFO] winget not found. Downloading Python 3.12 installer..."
            curl -L -o python_installer.exe "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
            echo ""
            echo "[INFO] Running Python installer..."
            echo "  IMPORTANT: Check 'Add python.exe to PATH' in the installer!"
            echo ""
            ./python_installer.exe
            echo ""
            echo "[INFO] After installation completes, RESTART Git Bash and run:"
            echo "  curl -sL https://raw.githubusercontent.com/OPENEHIRA/OpenGuy/main/install.sh | bash"
            echo ""
            exit 0
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &>/dev/null; then
            echo "[INFO] Installing Python 3.12 via Homebrew..."
            brew install python@3.12
            PYTHON_CMD="python3.12"
        else
            echo "[ERROR] Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif command -v apt-get &>/dev/null; then
        echo "[INFO] Installing Python 3.12 via apt..."
        sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv python3-pip
        PYTHON_CMD="python3.12"
    elif command -v dnf &>/dev/null; then
        echo "[INFO] Installing Python 3.12 via dnf..."
        sudo dnf install -y python3.12
        PYTHON_CMD="python3.12"
    else
        echo "[ERROR] Could not auto-install Python."
        echo "  Please install Python 3.12 from: https://www.python.org/downloads/"
        exit 1
    fi
fi

echo ""

# ── Step 2: Check Git ──
if ! command -v git &>/dev/null; then
    echo "[WARN] Git not found. Installing..."
    if [ "$IS_WINDOWS" = true ]; then
        if command -v winget &>/dev/null; then
            winget install Git.Git --accept-package-agreements --accept-source-agreements
        else
            echo "[ERROR] Please install Git from https://git-scm.com/downloads"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
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
    echo "[INFO] OpenGuy directory exists. Pulling latest..."
    cd OpenGuy
    git pull
else
    echo "[INFO] Cloning OpenGuy..."
    git clone https://github.com/OPENEHIRA/OpenGuy.git
    cd OpenGuy
fi

echo ""

# ── Step 4: Install deps ──
echo "[INFO] Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip 2>/dev/null || true
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
