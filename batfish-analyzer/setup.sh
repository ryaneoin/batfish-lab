#!/bin/bash
# Setup script for Batfish analyzer
# Copies configs from shared directory to Batfish snapshot directory

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(dirname "$SCRIPT_DIR")"

echo "======================================"
echo "  Batfish Analyzer Setup"
echo "======================================"
echo

# Create output directory
echo "[+] Creating output directory..."
mkdir -p "$SCRIPT_DIR/output"

# Copy configs to snapshot
echo "[+] Copying configs to snapshot directory..."
mkdir -p "$LAB_DIR/snapshot/configs"
cp "$LAB_DIR/configs"/*.cfg "$LAB_DIR/snapshot/configs/" 2>/dev/null || {
    echo "[!] No .cfg files found in configs directory"
    echo "[!] Please add network device configs to: $LAB_DIR/configs/"
    exit 1
}

CONFIG_COUNT=$(ls -1 "$LAB_DIR/snapshot/configs"/*.cfg 2>/dev/null | wc -l)
echo "    ✓ Copied $CONFIG_COUNT config files"

# Create Python virtual environment if it doesn't exist
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "[+] Creating Python virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
    echo "    ✓ Virtual environment created"
fi

# Install dependencies
echo "[+] Installing Python dependencies..."
source "$SCRIPT_DIR/.venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "    ✓ Dependencies installed"

echo
echo "======================================"
echo "  ✅ Setup Complete!"
echo "======================================"
echo
echo "Next steps:"
echo "  1. Start Batfish: docker-compose up -d batfish"
echo "  2. Run analysis: ./run_analysis.sh"
echo
