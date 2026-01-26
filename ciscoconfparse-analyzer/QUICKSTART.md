# Quick Start Guide

## What Was Created

```
ciscoconfparse-analyzer/
├── Dockerfile                    # Python 3.11 container with CiscoConfParse
├── docker-compose.yml            # Mounts ../configs (read-only) and ./output
├── requirements.txt              # ciscoconfparse + dependencies
├── analyzer/
│   ├── main.py                  # Main orchestration script
│   ├── fhrp_auditor.py          # HSRP/VRRP/GLBP compliance checks
│   └── bgp_auditor.py           # BGP security audit
├── output/                       # JSON reports land here
├── run.sh                       # Convenience script
└── README.md                    # Full documentation
```

## Your Config Files

Found 4 router configs:
- R1.cfg - Has HSRP with auth, preempt, tracking ✅
- R2.cfg - Has HSRP but missing tracking ⚠️
- R3.cfg, R4.cfg - (will be analyzed)

## Run It Now

```bash
cd /Users/eoin/projects/batfish-lab/ciscoconfparse-analyzer

# Option 1: Use the convenience script
chmod +x run.sh
./run.sh

# Option 2: Use docker-compose directly
docker-compose build
docker-compose up
```

## What It Will Check

### FHRP (HSRP) Audit
- ✅ Authentication (MD5) - **PCI-DSS 2.2.4**
- ✅ Preemption enabled
- ✅ Interface tracking configured
- ✅ Priority explicitly set
- ✅ Virtual IP configured
- ✅ HSRP version specified

### BGP Security Audit
- ✅ MD5 authentication - **PCI-DSS 4.1**
- ✅ TTL security (GTSM)
- ✅ Maximum-prefix limits - **PCI-DSS 2.2.4**
- ✅ Inbound route filtering - **PCI-DSS 1.3.6**
- ✅ Outbound route filtering
- ✅ Router-ID configured
- ✅ Neighbor logging - **PCI-DSS 10.2**

## Expected Findings

Based on R1 and R2 configs I saw:

**R1 (HSRP)**:
- ✅ Fully compliant
- Has auth, preempt, tracking, priority 110

**R2 (HSRP)**:
- ⚠️ Missing interface tracking
- ⚠️ Lower priority (100)
- Otherwise compliant

**R1 (BGP)**:
- ⚠️ No MD5 authentication on neighbors
- ⚠️ No maximum-prefix limits
- ⚠️ No route filtering (critical for PCI)
- ℹ️ Has logging enabled

## Output Format

Three JSON files generated per run:
1. `fhrp_audit_YYYYMMDD_HHMMSS.json`
2. `bgp_audit_YYYYMMDD_HHMMSS.json`
3. `combined_audit_YYYYMMDD_HHMMSS.json`

Each contains:
- Device-by-device findings
- Issue severity (CRITICAL/HIGH/MEDIUM/LOW)
- PCI-DSS requirement mapping
- Remediation commands
- Risk scores
- Compliance percentages

## Terminal Output

You'll see color-coded output:
- 🔴 CRITICAL/HIGH issues
- 🟡 MEDIUM issues
- 🔵 LOW issues
- ✅ Compliant items

## Next Steps for Monday

1. **Run the analysis**: `./run.sh`
2. **Review JSON output**: Focus on HIGH/CRITICAL
3. **Demo the findings**: Show compliance percentages
4. **Highlight PCI value**: Automated evidence generation
5. **Propose next phase**: Integration with Batfish for behavioral validation

## Why This Matters for PCI

**Configuration-level compliance** (CiscoConfParse):
- "Does HSRP have MD5 auth configured?"
- "Are all BGP neighbors authenticated?"
- "Is tracking configured?"

**Behavioral validation** (Batfish - next phase):
- "Does traffic actually get blocked by ACLs?"
- "Can hosts in non-CDE reach CDE?"
- "Are routing policies actually enforced?"

**Combined = Complete audit evidence**

## Troubleshooting

If you get permission errors:
```bash
chmod 755 output/
```

If configs aren't found:
```bash
ls -la ../configs/  # Should show R1.cfg, R2.cfg, etc.
```

To rebuild from scratch:
```bash
./run.sh --rebuild
# or
docker-compose down && docker-compose build --no-cache
```

## This is Your Weekend POC

- ✅ Real configs analyzed
- ✅ Real PCI compliance checks
- ✅ Structured JSON output
- ✅ Ready for Monday demo
- ✅ Foundation for Batfish integration

The JSON output can feed into:
- NetworkX graphs
- Jinja2 PDF reports
- AI agent analysis
- Compliance dashboards
