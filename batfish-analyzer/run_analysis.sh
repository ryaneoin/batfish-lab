#!/bin/bash
# Run Batfish network analysis
# Prerequisites: Batfish container must be running

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================"
echo "  Batfish Network Analysis"
echo "======================================"
echo

# Check if Batfish is running
if ! docker ps | grep -q batfish; then
    echo "[!] Batfish container is not running!"
    echo "[!] Start it with: docker-compose up -d batfish"
    exit 1
fi

echo "[+] Batfish is running ✓"
echo

# Wait for Batfish to be ready
echo "[+] Waiting for Batfish to be ready..."
RETRIES=30
while [ $RETRIES -gt 0 ]; do
    if curl -s http://localhost:9996/ > /dev/null 2>&1; then
        echo "    ✓ Batfish is ready"
        break
    fi
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        echo "[!] Batfish did not become ready in time"
        exit 1
    fi
    echo "    Waiting... ($RETRIES attempts remaining)"
    sleep 2
done

echo

# Activate virtual environment and run analysis
echo "[+] Running network analysis..."
echo
source "$SCRIPT_DIR/.venv/bin/activate"
python3 "$SCRIPT_DIR/analyze_network.py"

echo
echo "======================================"
echo "  ✅ Analysis Complete!"
echo "======================================"
echo
echo "CSV files are in: $SCRIPT_DIR/output/"
echo "View in Grafana: http://localhost:3000"
echo
