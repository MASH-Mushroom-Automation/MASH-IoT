#!/bin/bash
# M.A.S.H. IoT - Dependency Installation Script
# Run on Raspberry Pi to install all system dependencies

set -e  # Exit on error

echo "========================================="
echo " M.A.S.H. IoT - Dependency Installation"
echo "========================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "Do not run as root. Run as normal user."
    exit 1
fi

# Update package lists
echo "[1/6] Updating package lists..."
sudo apt-get update

# Install system dependencies
echo "[2/6] Installing system packages..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    network-manager \
    chromium-browser \
    sqlite3 \
    git \
    build-essential \
    libatlas-base-dev \
    libopenblas-dev \
    libjpeg-dev \
    zlib1g-dev

# Install PlatformIO for Arduino development (optional)
echo "[3/6] Installing PlatformIO CLI (for Arduino)..."
if ! command -v pio &> /dev/null; then
    pip3 install platformio
    echo "PlatformIO installed"
else
    echo "PlatformIO already installed"
fi

# Create Python virtual environment
echo "[4/6] Creating Python virtual environment..."
cd "$(dirname "$0")/.."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created"
else
    echo "Virtual environment exists"
fi

# Activate venv and install Python packages
echo "[5/6] Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
echo "[6/6] Creating data directories..."
mkdir -p data/models
mkdir -p data/logs
mkdir -p logs
mkdir -p ~/.mash

# Set execute permissions on all scripts
echo "[7/7] Setting execute permissions on scripts..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

echo ""
echo "========================================="
echo " Installation Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Find Arduino: python3 scripts/find_arduino.py"
echo "2. Test connection: python3 scripts/test_arduino.py"
echo "3. Configure Firebase: Place credentials in config/firebase_config.json"
echo "4. Start system: cd rpi_gateway && python3 -m app.main"
echo "5. Setup kiosk: bash scripts/setup_kiosk.sh"
echo ""

