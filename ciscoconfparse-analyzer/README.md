# CiscoConfParse Network Analyzer

Docker-based network configuration auditor using CiscoConfParse to analyze Cisco device configurations for FHRP (HSRP/VRRP/GLBP) and BGP security compliance.

## Features

- **FHRP Audit**: Analyzes HSRP/VRRP/GLBP configurations for PCI-DSS compliance
  - Authentication checks
  - Preemption configuration
  - Interface tracking validation
  - Priority configuration
  - Virtual IP verification

- **BGP Security Audit**: Analyzes BGP configurations for security best practices
  - MD5 authentication verification
  - TTL security (GTSM) checks
  - Maximum-prefix limits
  - Route filtering (inbound/outbound)
  - Global BGP configuration validation

## Project Structure

```
ciscoconfparse-analyzer/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker Compose configuration
├── requirements.txt        # Python dependencies
├── analyzer/
│   ├── main.py            # Main analysis script
│   ├── fhrp_auditor.py    # FHRP audit module
│   └── bgp_auditor.py     # BGP audit module
└── output/                # Analysis results (JSON reports)
```

## Prerequisites

- Docker
- Docker Compose
- Cisco device configuration files in `../configs/` directory

## Quick Start

### 1. Build the container

```bash
cd /Users/eoin/projects/batfish-lab/ciscoconfparse-analyzer
docker-compose build
```

### 2. Run the analysis

```bash
docker-compose up
```

This will:
- Mount your `../configs/` directory (read-only)
- Analyze all `.cfg` files
- Generate JSON reports in `./output/`
- Display colored terminal output with findings

### 3. View results

Results are saved in the `output/` directory with timestamps:
- `fhrp_audit_YYYYMMDD_HHMMSS.json` - FHRP audit results
- `bgp_audit_YYYYMMDD_HHMMSS.json` - BGP audit results
- `combined_audit_YYYYMMDD_HHMMSS.json` - Combined report

## Sample Output

The analyzer provides:
- **Color-coded terminal output** showing issues by severity
- **PCI-DSS compliance mapping** where applicable
- **Remediation suggestions** for each finding
- **Risk scores** for each configuration element
- **Overall compliance percentages** per device and globally

### Severity Levels

- 🔴 **CRITICAL**: Major security/compliance issue requiring immediate attention
- 🔴 **HIGH**: Significant security concern
- 🟡 **MEDIUM**: Important configuration issue
- 🔵 **LOW**: Minor configuration improvement

## Configuration Analysis

### FHRP Checks (PCI-DSS Focused)

- ✅ Authentication configured (PCI-DSS 2.2.4)
- ✅ Preemption enabled for automatic recovery
- ✅ Interface tracking for upstream failure detection
- ✅ Explicit priority configuration
- ✅ Virtual IP properly configured

### BGP Security Checks

- ✅ MD5 authentication (PCI-DSS 4.1)
- ✅ TTL security (GTSM)
- ✅ Maximum-prefix limits (PCI-DSS 2.2.4)
- ✅ Inbound route filtering (PCI-DSS 1.3.6)
- ✅ Outbound route filtering
- ✅ Router-ID configuration
- ✅ Neighbor change logging (PCI-DSS 10.2)

## Development

### Running without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CONFIGS_DIR=/Users/eoin/projects/batfish-lab/configs
export OUTPUT_DIR=./output

# Run analysis
cd analyzer
python main.py
```

### Adding Custom Checks

1. Edit `analyzer/fhrp_auditor.py` or `analyzer/bgp_auditor.py`
2. Add new check methods following existing patterns
3. Update severity levels and PCI mappings as needed
4. Rebuild container: `docker-compose build`

## Integration with Batfish

This CiscoConfParse analyzer provides **configuration-level compliance** checks. For **network behavior analysis** (reachability, forwarding, etc.), combine with Batfish:

- CiscoConfParse: "Does this config line exist?"
- Batfish: "What does this config actually do?"
- Combined: Full compliance + behavioral validation

## Example Use Cases

### PCI-DSS Audit Preparation
```bash
# Run analysis before auditor arrives
docker-compose up

# Review output/combined_audit_*.json for issues
# Remediate HIGH/CRITICAL findings
# Generate evidence from JSON reports
```

### Configuration Drift Detection
```bash
# Run analysis after network changes
docker-compose up

# Compare new results with baseline
# Identify configuration deviations
```

### Security Hardening
```bash
# Run analysis to find security gaps
docker-compose up

# Focus on CRITICAL/HIGH severity issues
# Apply remediations from suggestions
```

## Notes

- Config files are mounted read-only for safety
- Output directory is writable for report generation
- All analysis runs in isolated container
- No network access required (offline analysis)

## Troubleshooting

### No config files found
```bash
# Verify configs directory exists and contains .cfg files
ls -la ../configs/

# Check docker-compose.yml volume mount paths
```

### Permission issues
```bash
# Ensure output directory is writable
chmod 755 output/
```

### Container build fails
```bash
# Clean and rebuild
docker-compose down
docker-compose build --no-cache
```

## Next Steps

1. **Add more protocol audits** (OSPF, ACLs, QoS)
2. **Integrate with Batfish** for behavioral analysis
3. **Generate PDF reports** using report templates
4. **Build MCP server** for AI agent integration
5. **Add topology visualization** with NetworkX

## Author

Built for network automation and PCI-DSS compliance auditing.
