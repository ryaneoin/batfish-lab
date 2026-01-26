# Batfish Network Analysis Lab

Comprehensive network analysis toolkit combining multiple approaches:
- **Batfish FHRP Analyzer**: Behavioral analysis for HSRP/VRRP compliance
- **Topology Visualizer**: CDP/BGP/HSRP topology mapping and visualization  
- **CiscoConfParse**: Configuration syntax parsing and validation
- **Loki Stack**: Log aggregation and monitoring

## Project Components

```
batfish-lab/
├── batfish-analyzer/          # Batfish FHRP compliance analysis
├── topology-visualizer/       # Multi-layer topology visualization
├── ciscoconfparse-analyzer/   # Configuration parser (standalone)
├── loki-stack/               # Monitoring and observability
├── configs/                  # Network device configurations
├── docker/                   # Docker orchestration
├── tools/                    # Utility scripts
└── docs/                     # Documentation
```

## Quick Start

### Option 1: Topology Visualization (Recommended for first-time)

```bash
cd batfish-lab/topology-visualizer

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the pipeline
python run_pipeline.py

# View results
open output/combined_topology.html
```

### Option 2: Batfish FHRP Analysis

```bash
cd batfish-lab/batfish-analyzer

# Ensure Batfish is running
docker run -d -p 9997:9997 -p 9996:9996 --name batfish batfish/batfish

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run analysis
python analyze_network.py

# View CSV outputs
ls -lh output/*.csv
```

### Option 3: Full Stack with Loki/Grafana

```bash
# Start Batfish (if not already running)
docker run -d -p 9997:9997 -p 9996:9996 --name batfish batfish/batfish

# Run Batfish analysis
cd batfish-lab/batfish-analyzer
source .venv/bin/activate
python analyze_network.py

# Start Loki stack
cd ../loki-stack
docker-compose up -d

# Access Grafana at http://localhost:3000
# Username: admin, Password: admin
```

## What Each Component Does

### Batfish Analyzer
- Behavioral analysis of HSRP/VRRP configurations
- Compliance checking and audit trail generation
- CSV output for integration with monitoring systems
- Detects configuration issues before deployment

### Topology Visualizer  
- Parses CDP neighbor data for physical topology
- Extracts HSRP redundancy relationships
- Maps BGP peering connections
- Generates interactive HTML visualizations with Plotly
- Produces combined multi-layer topology views

### CiscoConfParse Analyzer
- Standalone configuration parsing and analysis
- Syntax validation and structure extraction
- Independent component with own Docker setup

### Loki Stack
- Ingests CSV outputs from Batfish via Promtail
- Stores time-series network state in Loki
- Visualizes compliance trends in Grafana
- Enables LogQL queries for network audit

## Use Cases

1. **Change Management**: Simulate configuration changes before deployment
2. **Compliance Auditing**: Generate PCI-DSS evidence for auditors
3. **Topology Documentation**: Auto-generate network diagrams from live data
4. **Dependency Analysis**: Map service dependencies across infrastructure
5. **Failure Simulation**: Test redundancy and identify single points of failure

## Documentation

See `docs/` for detailed guides:
- `QUICKSTART.md` - Get started in 5 minutes
- `SETUP.md` - Detailed installation and configuration
- `TROUBLESHOOTING.md` - Common issues and solutions

## Network Device Configurations

Place your network device configs in `configs/`:
- Cisco IOS configurations (`.cfg` or `.txt`)
- CDP neighbor data in `topology-visualizer/data/cdp_data/`

## Next Steps

1. Try the topology visualizer with sample data
2. Add your own network configs
3. Integrate with CI/CD for pre-deployment validation
4. Set up scheduled analysis with cron
5. Export Grafana dashboards for team use

---

**Note**: Test in lab environment before deploying to production network!
