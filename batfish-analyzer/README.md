# Batfish Network Analyzer

Automated FHRP (HSRP/VRRP) compliance analysis using Batfish behavioral modeling.

## What It Does

- **Analyzes HSRP/VRRP configurations** for compliance issues
- **Detects redundancy problems** (orphaned groups, priority conflicts)
- **Generates timestamped CSV outputs** for audit trails
- **Integrates with Loki/Grafana** for trend visualization

## Quick Start

### 1. Setup (First Time Only)

```bash
cd batfish-analyzer
./setup.sh
```

This will:
- Copy configs from `../configs/` to `../snapshot/configs/`
- Create Python virtual environment
- Install dependencies (pybatfish, pandas)

### 2. Start Batfish Service

From the project root:
```bash
docker-compose up -d batfish
```

Wait ~30 seconds for Batfish to initialize.

### 3. Run Analysis

```bash
cd batfish-analyzer
./run_analysis.sh
```

## Output Files

All outputs are saved to `output/` with timestamps:

- **`hsrp_detailed_YYYYMMDD_HHMMSS.csv`** - Raw HSRP data from Batfish
- **`vrrp_detailed_YYYYMMDD_HHMMSS.csv`** - Raw VRRP data from Batfish
- **`fhrp_unified_YYYYMMDD_HHMMSS.csv`** - Combined audit report with status

### CSV Schema

```
Interface,Group_ID,Priority,Preempt,Enabled,Hostname,Interface_Name,Protocol,Audit_Status
```

**Audit_Status values:**
- `OK` - Configuration is compliant
- `DISABLED` - FHRP group is disabled
- `NO_PREEMPT` - Preempt is not enabled
- `ORPHANED` - Group has only one member (no redundancy)

## Compliance Checks

The analyzer performs these checks:

1. **Redundancy Check** - Warns if FHRP groups have <2 members
2. **Priority Conflicts** - Detects duplicate priorities in same group
3. **Disabled Groups** - Identifies disabled FHRP instances
4. **Preempt Status** - Reports groups without preempt enabled

## Extending Analysis

To add new Batfish queries:

1. Review [Batfish Questions Reference](https://pybatfish.readthedocs.io/en/latest/questions.html)
2. Add new analysis function to `analyze_network.py`:

```python
print("\n=== Analyzing BGP ===")
bgp = bf.q.bgpProcessConfiguration().answer().frame()
save_csv(bgp, "bgp_config")
```

3. Run analysis to generate new CSV outputs

## Integration with Monitoring Stack

CSV outputs are automatically ingested by Promtail and sent to Loki for time-series storage. View trends in Grafana at http://localhost:3000.

## Troubleshooting

**"Batfish container is not running"**
```bash
cd ..
docker-compose up -d batfish
```

**"No .cfg files found"**
- Add device configs to `../configs/`
- Run `./setup.sh` to copy them to snapshot

**Connection errors**
- Ensure Batfish is fully started (check `docker logs batfish`)
- Verify port 9996 is accessible: `curl http://localhost:9996/`

## Requirements

- Docker and Docker Compose
- Python 3.9+
- Network device configurations in Cisco IOS format

## Architecture

```
batfish-analyzer/
├── analyze_network.py    # Main analysis script (pybatfish v2 API)
├── requirements.txt       # Python dependencies
├── setup.sh              # First-time setup
├── run_analysis.sh       # Execute analysis
├── output/               # Generated CSV files
└── .venv/                # Python virtual environment
```

Configs are read from `../snapshot/configs/` which is populated from `../configs/` by the setup script.
