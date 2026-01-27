#!/usr/bin/env python3
"""
Network Topology Analysis Pipeline for Cisco NX-OS
Orchestrates CDP, HSRP, BGP parsing and visualization for NX-OS devices
"""

import sys
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / 'data'
CDP_DATA_DIR = str(DATA_DIR / 'cdp_data')
CONFIGS_DIR = str(DATA_DIR / 'running_configs')
OUTPUT_DIR = str(SCRIPT_DIR / 'output')

# Add parsers directory to path
sys.path.insert(0, str(SCRIPT_DIR / 'parsers'))

from cdp_parser import CDPParser
from hsrp_parser_nxos import HSRPParserNXOS
from bgp_parser_nxos import BGPParserNXOS
from visualize_topology import NetworkTopologyVisualizer


def main():
    """Execute complete NX-OS topology analysis pipeline"""
    
    print("=" * 70)
    print("  NETWORK TOPOLOGY ANALYSIS PIPELINE (NX-OS)")
    print("=" * 70)
    print()
    
    # Step 1: Parse CDP data
    print("📡 Step 1: Parsing CDP Neighbor Data")
    print("-" * 70)
    cdp_parser = CDPParser(CDP_DATA_DIR)
    cdp_parser.export_json(f'{OUTPUT_DIR}/cdp_topology.json')
    print()
    
    # Step 2: Parse HSRP configuration (NX-OS)
    print("🔄 Step 2: Parsing HSRP/VRRP Configuration (NX-OS)")
    print("-" * 70)
    hsrp_parser = HSRPParserNXOS(CONFIGS_DIR)
    hsrp_parser.export_json(f'{OUTPUT_DIR}/hsrp_topology.json')
    print()
    
    # Step 3: Parse BGP configuration (NX-OS)
    print("🌐 Step 3: Parsing BGP Configuration (NX-OS)")
    print("-" * 70)
    bgp_parser = BGPParserNXOS(CONFIGS_DIR)
    bgp_parser.export_json(f'{OUTPUT_DIR}/bgp_topology.json')
    print()
    
    # Step 4: Create visualizations
    print("🎨 Step 4: Generating Network Visualizations")
    print("-" * 70)
    
    viz = NetworkTopologyVisualizer()
    
    # Load all topology data
    viz.load_cdp_topology(f'{OUTPUT_DIR}/cdp_topology.json')
    viz.load_hsrp_topology(f'{OUTPUT_DIR}/hsrp_topology.json')
    viz.load_bgp_topology(f'{OUTPUT_DIR}/bgp_topology.json')
    
    print()
    
    # Create visualizations
    viz.visualize_physical_topology(f'{OUTPUT_DIR}/physical_topology.html')
    viz.visualize_hsrp_topology(f'{OUTPUT_DIR}/hsrp_topology.html')
    viz.visualize_bgp_topology(f'{OUTPUT_DIR}/bgp_topology.html')
    viz.visualize_combined_topology(f'{OUTPUT_DIR}/combined_topology.html')
    
    # Generate summary
    viz.generate_topology_summary(f'{OUTPUT_DIR}/topology_summary.json')
    
    print()
    print("=" * 70)
    print("  ✅ PIPELINE COMPLETE")
    print("=" * 70)
    print()
    print(f"📁 Output files generated in {OUTPUT_DIR}/:")
    print("   📊 Data Files:")
    print("      - cdp_topology.json")
    print("      - hsrp_topology.json")
    print("      - bgp_topology.json")
    print("      - topology_summary.json")
    print()
    print("   🗺️  Visualization Files:")
    print("      - physical_topology.html      (Physical layer - CDP)")
    print("      - hsrp_topology.html          (HSRP/VRRP redundancy)")
    print("      - bgp_topology.html           (BGP peerings)")
    print("      - combined_topology.html      (All layers combined)")
    print()
    print("💡 Open the HTML files in a browser to view interactive topology maps")
    print("💡 Run 'python generate_3d_topology.py' to create 3D visualization")
    print()


if __name__ == '__main__':
    main()
