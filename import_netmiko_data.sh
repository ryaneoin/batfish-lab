#!/bin/bash
# Import netmiko outputs into batfish-lab structure
# Expects files in format:
#   hostname_running-config.cfg
#   hostname_show_cdp_neighbors_detail.txt

set -e

# Update this path to where your netmiko outputs are stored
NETMIKO_DIR="${1:-/path/to/your/netmiko/outputs}"
LAB_DIR="/Users/eoin/projects/batfish-lab"

echo "=========================================="
echo "  Importing Netmiko Data"
echo "=========================================="
echo

if [ ! -d "$NETMIKO_DIR" ]; then
    echo "[!] Error: Directory not found: $NETMIKO_DIR"
    echo
    echo "Usage: ./import_netmiko_data.sh /path/to/netmiko/outputs"
    exit 1
fi

# Count files
running_configs=$(ls "$NETMIKO_DIR"/*_running-config.cfg 2>/dev/null | wc -l)
cdp_outputs=$(ls "$NETMIKO_DIR"/*_show_cdp_neighbors_detail.txt 2>/dev/null | wc -l)

echo "Found:"
echo "  - $running_configs running-config files"
echo "  - $cdp_outputs CDP neighbor detail files"
echo

if [ "$running_configs" -eq 0 ] && [ "$cdp_outputs" -eq 0 ]; then
    echo "[!] No files found with expected naming pattern"
    echo "    Expected: hostname_running-config.cfg"
    echo "    Expected: hostname_show_cdp_neighbors_detail.txt"
    exit 1
fi

# Import running configs
if [ "$running_configs" -gt 0 ]; then
    echo "[1/2] Importing running configs..."
    for file in "$NETMIKO_DIR"/*_running-config.cfg; do
        if [ -f "$file" ]; then
            # Extract hostname from filename
            basename=$(basename "$file")
            hostname=${basename%%_running-config.cfg}
            
            # Copy to configs directory
            cp "$file" "$LAB_DIR/configs/${hostname}.cfg"
            echo "  ✓ ${hostname}.cfg"
        fi
    done
else
    echo "[1/2] No running-config files found"
fi

echo

# Import CDP data
if [ "$cdp_outputs" -gt 0 ]; then
    echo "[2/2] Importing CDP neighbor data..."
    for file in "$NETMIKO_DIR"/*_show_cdp_neighbors_detail.txt; do
        if [ -f "$file" ]; then
            # Extract hostname from filename
            basename=$(basename "$file")
            hostname=${basename%%_show_cdp_neighbors_detail.txt}
            
            # Copy to CDP data directory
            cp "$file" "$LAB_DIR/topology-visualizer/data/cdp_data/${hostname}_cdp.txt"
            echo "  ✓ ${hostname}_cdp.txt"
        fi
    done
else
    echo "[2/2] No CDP neighbor detail files found"
fi

echo
echo "=========================================="
echo "  ✅ Import Complete!"
echo "=========================================="
echo
echo "Next steps:"
echo
echo "1. Run topology visualization:"
echo "   cd $LAB_DIR/topology-visualizer"
echo "   source .venv/bin/activate"
echo "   python run_pipeline.py"
echo "   open output/combined_topology.html"
echo
echo "2. Run Batfish analysis:"
echo "   cd $LAB_DIR/batfish-analyzer"
echo "   ./setup.sh"
echo "   ./run_analysis.sh"
echo
echo "3. Run CiscoConfParse analysis:"
echo "   cd $LAB_DIR/ciscoconfparse-analyzer"
echo "   python analyzer/main.py"
echo
