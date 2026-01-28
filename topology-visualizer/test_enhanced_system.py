#!/usr/bin/env python3
"""
Quick test script for enhanced 3D topology visualization
Tests parser and generates sample visualizations
"""

import sys
from pathlib import Path

# Add paths
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPT_DIR / 'parsers'))

def test_config():
    """Test configuration validation"""
    print("\n" + "="*70)
    print("  Testing Configuration")
    print("="*70 + "\n")
    
    try:
        from config import validate_config, DATACENTERS, POSITION_TO_Z_LAYER, POSITION_TO_LANE
        
        if validate_config():
            print("✅ Configuration is valid\n")
            print(f"Configured datacenters: {len(DATACENTERS)}")
            print(f"Configured positions: {len(POSITION_TO_Z_LAYER)}")
            print(f"Lane range: {min(POSITION_TO_LANE.values())} to {max(POSITION_TO_LANE.values())}")
            return True
        else:
            print("❌ Configuration validation failed")
            return False
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return False


def test_parser():
    """Test enhanced hostname parser"""
    print("\n" + "="*70)
    print("  Testing Enhanced Hostname Parser")
    print("="*70 + "\n")
    
    try:
        from enhanced_hostname_parser import EnhancedHostnameParser
        
        parser = EnhancedHostnameParser()
        
        # Test cases
        test_hostnames = [
            'npccosr01',      # Core router in NPC
            'npccosr02',      # HA pair with above
            'wpcaccsw11',     # Access switch in WPC
            'ch2igwsr01',     # Internet gateway in CH2
            'ukrcpubsw03',    # Public DMZ switch in UKRC
        ]
        
        print("Parsing test hostnames:\n")
        print(f"{'Hostname':<16} {'DC':<6} {'Pos':<5} {'Type':<4} {'#':<3} {'Z':<5} {'Lane':<6} {'Valid':<6}")
        print("-" * 70)
        
        all_valid = True
        parsed_results = []
        
        for hostname in test_hostnames:
            parsed = parser.parse(hostname)
            parsed_results.append(parsed)
            
            if parsed['valid']:
                dc = parsed['datacenter'] or '-'
                pos = parsed['position'] or '-'
                typ = parsed['type'] or '-'
                cnt = parsed['counter'] or '-'
                z = f"{parsed['z_level']:.1f}"
                lane = f"{parsed['lane']:+d}"
                valid = '✓'
            else:
                dc = pos = typ = cnt = z = lane = '-'
                valid = '✗'
                all_valid = False
            
            print(f"{hostname:<16} {dc:<6} {pos:<5} {typ:<4} {cnt:<3} {z:<5} {lane:<6} {valid:<6}")
        
        # Test HA pair detection
        print("\n" + "-" * 70)
        print("HA Pair Detection:\n")
        
        ha_pairs = parser.find_ha_pairs(test_hostnames)
        if ha_pairs:
            for h1, h2 in ha_pairs:
                print(f"  ✓ {h1} <-> {h2}")
        else:
            print("  (No HA pairs in test set)")
        
        # Test datacenter grouping
        print("\n" + "-" * 70)
        print("Datacenter Grouping:\n")
        
        grouped = parser.group_by_datacenter(test_hostnames)
        for dc, devices in sorted(grouped.items()):
            print(f"  {dc.upper():8}: {', '.join(devices)}")
        
        if all_valid:
            print("\n✅ All test hostnames parsed successfully")
            return True
        else:
            print("\n⚠️  Some hostnames failed to parse")
            return False
            
    except Exception as e:
        print(f"❌ Error testing parser: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_topology_data():
    """Check if topology data files exist"""
    print("\n" + "="*70)
    print("  Checking Topology Data Files")
    print("="*70 + "\n")
    
    output_dir = SCRIPT_DIR / 'output'
    required_files = ['cdp_topology.json']
    optional_files = ['hsrp_topology.json', 'bgp_topology.json']
    
    all_good = True
    
    print("Required files:")
    for filename in required_files:
        filepath = output_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✓ {filename} ({size:,} bytes)")
        else:
            print(f"  ✗ {filename} (missing)")
            all_good = False
    
    print("\nOptional files:")
    for filename in optional_files:
        filepath = output_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✓ {filename} ({size:,} bytes)")
        else:
            print(f"  - {filename} (not present)")
    
    if all_good:
        print("\n✅ Required topology data files found")
        return True
    else:
        print("\n⚠️  Missing required topology data")
        print("   Run: python run_pipeline_nxos.py")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("  Enhanced 3D Topology Visualization - Test Suite")
    print("="*70)
    
    results = {
        'config': test_config(),
        'parser': test_parser(),
        'data': check_topology_data()
    }
    
    print("\n" + "="*70)
    print("  Test Summary")
    print("="*70 + "\n")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name.capitalize():.<20} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    
    if all_passed:
        print("  ✅ All tests passed!")
        print("="*70 + "\n")
        print("Ready to generate enhanced 3D visualization:")
        print("  python generate_3d_topology_enhanced.py")
    else:
        print("  ⚠️  Some tests failed")
        print("="*70 + "\n")
        print("Please fix issues before running visualization generator.")
    
    print()


if __name__ == '__main__':
    main()
