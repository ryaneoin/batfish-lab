#!/bin/bash
# Quick start script for Batfish Network Analysis Lab
# Starts all services and runs initial analysis

set -e

echo "=========================================="
echo "  Batfish Network Analysis Lab"
echo "  Quick Start"
echo "=========================================="
echo

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "[!] Error: Run this script from the batfish-lab directory"
    exit 1
fi

# Setup batfish-analyzer
echo "[1/4] Setting up Batfish analyzer..."
cd batfish-analyzer
./setup.sh
cd ..
echo

# Start all services
echo "[2/4] Starting Docker services..."
docker-compose up -d
echo

# Wait for services to be ready
echo "[3/4] Waiting for services to initialize..."
echo "    (This may take 30-60 seconds)"
sleep 5

# Wait for Batfish
RETRIES=30
while [ $RETRIES -gt 0 ]; do
    if curl -s http://localhost:9996/ > /dev/null 2>&1; then
        echo "    ✓ Batfish ready"
        break
    fi
    RETRIES=$((RETRIES - 1))
    if [ $RETRIES -eq 0 ]; then
        echo "    [!] Batfish did not start in time. Check logs: docker logs batfish"
        exit 1
    fi
    sleep 2
done

# Wait for Grafana
RETRIES=15
while [ $RETRIES -gt 0 ]; do
    if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
        echo "    ✓ Grafana ready"
        break
    fi
    RETRIES=$((RETRIES - 1))
    sleep 2
done

echo

# Run initial analysis
echo "[4/4] Running network analysis..."
cd batfish-analyzer
source .venv/bin/activate
python3 analyze_network.py
deactivate
cd ..

echo
echo "=========================================="
echo "  ✅ Setup Complete!"
echo "=========================================="
echo
echo "Services running:"
echo "  • Batfish:  http://localhost:9996"
echo "  • Loki:     http://localhost:3100"
echo "  • Grafana:  http://localhost:3000"
echo
echo "Access Grafana:"
echo "  URL:      http://localhost:3000"
echo "  Username: admin"
echo "  Password: admin"
echo
echo "Next steps:"
echo "  • View dashboards in Grafana"
echo "  • Add more configs to configs/"
echo "  • Run analysis: cd batfish-analyzer && ./run_analysis.sh"
echo
echo "To stop all services:"
echo "  docker-compose down"
echo
