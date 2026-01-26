#!/bin/bash

# CiscoConfParse Analyzer Runner
# Convenience script to build and run the analyzer

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== CiscoConfParse Network Analyzer ===${NC}\n"

# Check if configs directory exists
if [ ! -d "../configs" ]; then
    echo -e "${RED}Error: Configs directory not found at ../configs/${NC}"
    echo "Please ensure your config files are in the configs directory"
    exit 1
fi

# Count config files
CONFIG_COUNT=$(ls -1 ../configs/*.cfg 2>/dev/null | wc -l)
if [ "$CONFIG_COUNT" -eq 0 ]; then
    echo -e "${RED}Error: No .cfg files found in ../configs/${NC}"
    exit 1
fi

echo -e "${GREEN}Found $CONFIG_COUNT config file(s) to analyze${NC}\n"

# Check for rebuild flag
if [ "$1" == "--rebuild" ] || [ "$1" == "-r" ]; then
    echo -e "${YELLOW}Rebuilding container...${NC}"
    docker-compose build --no-cache
    echo ""
fi

# Run the analyzer
echo -e "${GREEN}Running analysis...${NC}\n"
docker-compose up

# Check if analysis completed successfully
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=== Analysis Complete ===${NC}"
    echo ""
    echo "Results saved in: $SCRIPT_DIR/output/"
    echo ""
    ls -lth output/*.json 2>/dev/null | head -5
else
    echo ""
    echo -e "${RED}=== Analysis Failed ===${NC}"
    exit 1
fi
