# Quick Start Guide

## First Time Setup

```bash
cd /Users/eoin/projects/batfish-lab/topology-visualizer

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Run the Pipeline

```bash
cd /Users/eoin/projects/batfish-lab/topology-visualizer

# Activate venv (if not already active)
source .venv/bin/activate

# Run the topology analysis
python run_pipeline.py

# View the interactive visualization
open output/combined_topology.html
```

## View Individual Visualizations

```bash
open output/physical_topology.html    # Physical layer (CDP)
open output/hsrp_topology.html        # HSRP redundancy
open output/bgp_topology.html         # BGP peerings
open output/combined_topology.html    # All layers combined
```

## Project Structure

```
batfish-lab/
├── topology-visualizer/
│   ├── .venv/             # Virtual environment (you'll create this)
│   ├── data/
│   │   └── cdp_data/      # CDP neighbor data (8 devices)
│   ├── parsers/           # Python parsers + visualizer
│   ├── output/            # Generated visualizations ✅
│   ├── requirements.txt   # Python dependencies
│   └── run_pipeline.py    # Main pipeline script
├── configs/               # Device configs (shared)
├── ciscoconfparse-analyzer/  # Configuration parser
├── loki-stack/            # Monitoring stack
└── docs/                  # Documentation
```

## Using Your Own Network Data

1. **Collect CDP neighbor data:**
   ```bash
   show cdp neighbors detail > HOSTNAME_cdp.txt
   ```

2. **Collect device configs:**
   ```bash
   show running-config > HOSTNAME.cfg
   ```

3. **Copy to project:**
   ```bash
   cp *_cdp.txt /Users/eoin/projects/batfish-lab/topology-visualizer/data/cdp_data/
   cp *.cfg /Users/eoin/projects/batfish-lab/configs/
   ```

4. **Re-run pipeline:**
   ```bash
   cd /Users/eoin/projects/batfish-lab/topology-visualizer
   source .venv/bin/activate
   python run_pipeline.py
   ```

## Deactivate venv When Done

```bash
deactivate
```

Your terminal prompt will return to normal (no `(.venv)` prefix).

---

**See other docs for detailed setup instructions.**
