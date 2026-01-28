#!/usr/bin/env python3
"""
Enhanced Hostname Parser for Network Device Classification
Parses format: {DATACENTER}{POSITION}{TYPE}{COUNT}
Examples: 
  - npccosr01 = npc + co + sr + 01
  - wpcaccsw11 = wpc + acc + sw + 11
"""

import re
from typing import Dict, Optional
import sys
from pathlib import Path

# Add parent directory to path to import config
SCRIPT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from config import (
        DATACENTERS,
        POSITION_TO_Z_LAYER,
        POSITION_TO_LANE,
        TYPE_TO_ICON,
        get_z_layer,
        get_lane,
        get_lane_x_position,
        get_icon_config
    )
except ImportError:
    print("Warning: config.py not found, using defaults")
    DATACENTERS = ['npc', 'wpc']
    POSITION_TO_Z_LAYER = {'co': 3.5, 'acc': 1.5}
    POSITION_TO_LANE = {'co': 0, 'acc': 0}
    TYPE_TO_ICON = {}
    get_z_layer = lambda p: 1.5
    get_lane = lambda p: 0
    get_lane_x_position = lambda l: l * 2.0
    get_icon_config = lambda t: {}


class EnhancedHostnameParser:
    """Parse structured hostnames into datacenter, position, type, and counter"""
    
    def __init__(self):
        """Initialize parser with configuration"""
        self.datacenters = DATACENTERS
        self.positions = list(POSITION_TO_Z_LAYER.keys())
        self.types = list(TYPE_TO_ICON.keys()) if TYPE_TO_ICON else ['sr', 'sw']
        
        # Build regex pattern dynamically
        dc_pattern = '|'.join(self.datacenters)
        pos_pattern = '|'.join(self.positions)
        type_pattern = '|'.join(self.types) if self.types else r'[a-z]{2}'
        
        # Pattern: datacenter(2-4) + position(2-3) + type(2) + counter(2)
        self.pattern = re.compile(
            rf'^({dc_pattern})({pos_pattern})({type_pattern})(\d{{2}})$',
            re.IGNORECASE
        )
        
        # Also support TYPE+COUNT format for flexibility (e.g., sr01, sw11)
        self.type_count_pattern = re.compile(
            rf'^({type_pattern})(\d{{2}})$',
            re.IGNORECASE
        )
    
    def parse(self, hostname: str) -> Dict:
        """
        Parse hostname into components
        
        Returns dict with:
        - hostname: str (original)
        - datacenter: str or None
        - position: str or None
        - type: str or None
        - counter: str or None
        - z_level: float
        - lane: int
        - lane_x: float (X-axis position based on lane)
        - icon_config: dict
        - valid: bool
        """
        hostname_clean = hostname.strip().lower()
        
        # Try full pattern first
        match = self.pattern.match(hostname_clean)
        
        if match:
            datacenter, position, dev_type, counter = match.groups()
            
            z_level = get_z_layer(position)
            lane = get_lane(position)
            lane_x = get_lane_x_position(lane)
            icon_config = get_icon_config(dev_type)
            
            return {
                'hostname': hostname,
                'datacenter': datacenter,
                'position': position,
                'type': dev_type,
                'counter': counter,
                'z_level': z_level,
                'lane': lane,
                'lane_x': lane_x,
                'icon_config': icon_config,
                'valid': True,
                'parse_method': 'full'
            }
        
        # Try type+count pattern (fallback for simple hostnames)
        match = self.type_count_pattern.match(hostname_clean)
        if match:
            dev_type, counter = match.groups()
            
            return {
                'hostname': hostname,
                'datacenter': None,
                'position': None,
                'type': dev_type,
                'counter': counter,
                'z_level': 1.5,  # Default middle layer
                'lane': 0,       # Default center lane
                'lane_x': 0.0,
                'icon_config': get_icon_config(dev_type),
                'valid': True,
                'parse_method': 'type_count'
            }
        
        # No match - return invalid
        return {
            'hostname': hostname,
            'datacenter': None,
            'position': None,
            'type': None,
            'counter': None,
            'z_level': 1.5,
            'lane': 0,
            'lane_x': 0.0,
            'icon_config': get_icon_config(None),
            'valid': False,
            'parse_method': 'none'
        }
    
    def get_datacenter(self, hostname: str) -> Optional[str]:
        """Quick method to get just the datacenter"""
        return self.parse(hostname)['datacenter']
    
    def get_z_level(self, hostname: str) -> float:
        """Quick method to get Z-level for 3D positioning"""
        return self.parse(hostname)['z_level']
    
    def get_lane(self, hostname: str) -> int:
        """Quick method to get lane number"""
        return self.parse(hostname)['lane']
    
    def get_lane_x(self, hostname: str) -> float:
        """Quick method to get X-axis position based on lane"""
        return self.parse(hostname)['lane_x']
    
    def are_ha_pair(self, hostname1: str, hostname2: str) -> bool:
        """
        Determine if two hostnames form an HA pair
        
        HA pairs have same datacenter+position+type but different counters
        """
        parsed1 = self.parse(hostname1)
        parsed2 = self.parse(hostname2)
        
        if not (parsed1['valid'] and parsed2['valid']):
            return False
        
        return (parsed1['datacenter'] == parsed2['datacenter'] and
                parsed1['position'] == parsed2['position'] and
                parsed1['type'] == parsed2['type'] and
                parsed1['counter'] != parsed2['counter'])
    
    def group_by_datacenter(self, hostnames: list) -> Dict[str, list]:
        """
        Group hostnames by datacenter
        
        Args:
            hostnames: List of hostname strings
            
        Returns:
            Dict mapping datacenter -> list of hostnames
        """
        grouped = {}
        
        for hostname in hostnames:
            parsed = self.parse(hostname)
            dc = parsed['datacenter'] or 'unknown'
            
            if dc not in grouped:
                grouped[dc] = []
            grouped[dc].append(hostname)
        
        return grouped
    
    def find_ha_pairs(self, hostnames: list) -> list:
        """
        Find all HA pairs in a list of hostnames
        
        Returns:
            List of tuples (hostname1, hostname2) representing HA pairs
        """
        pairs = []
        hostnames_sorted = sorted(hostnames)
        
        for i, h1 in enumerate(hostnames_sorted):
            for h2 in hostnames_sorted[i+1:]:
                if self.are_ha_pair(h1, h2):
                    pairs.append((h1, h2))
        
        return pairs


# =============================================================================
# BACKWARDS COMPATIBILITY with old HostnameParser
# =============================================================================

class HostnameParser(EnhancedHostnameParser):
    """Alias for backwards compatibility"""
    
    def get_layer(self, hostname: str) -> str:
        """Legacy method - returns position as layer name"""
        parsed = self.parse(hostname)
        return parsed['position'] or 'unknown'


# =============================================================================
# TESTING
# =============================================================================

def test_parser():
    """Test the parser with example hostnames"""
    parser = EnhancedHostnameParser()
    
    test_hostnames = [
        # Full format hostnames
        'npccosr01',      # NPC Core Switch Router 01
        'npccosr02',      # NPC Core Switch Router 02 (HA pair with above)
        'wpcaccsw11',     # WPC Access Switch 11
        'ukrcpubsw03',    # UKRC Public Switch 03
        'apdprvsw05',     # APD Private Switch 05
        'ch2igwsr01',     # CH2 Internet Gateway Switch Router 01
        'va1disw10',      # VA1 Distribution Switch 10
        'ld5lbsw20',      # LD5 Load Balancer Switch 20
        
        # Simple format (type+count only)
        'sr01',           # Switch Router 01
        'sw11',           # Switch 11
        
        # Invalid formats
        'CORE-SW-01',     # Old dash-separated format
        'invalid-name',   # No match
    ]
    
    print("\n" + "="*90)
    print("  Enhanced Hostname Parser Test Results")
    print("="*90 + "\n")
    
    print(f"{'Hostname':<16} {'DC':<6} {'Pos':<5} {'Type':<4} {'#':<3} {'Z':<5} {'Lane':<5} {'X':<7} {'Method':<12}")
    print("-" * 90)
    
    for hostname in test_hostnames:
        result = parser.parse(hostname)
        
        if result['valid']:
            dc = result['datacenter'] or '-'
            pos = result['position'] or '-'
            typ = result['type'] or '-'
            cnt = result['counter'] or '-'
            z = f"{result['z_level']:.1f}"
            lane = f"{result['lane']:+d}"
            lane_x = f"{result['lane_x']:+.1f}"
            method = result['parse_method']
            
            print(f"{hostname:<16} {dc:<6} {pos:<5} {typ:<4} {cnt:<3} {z:<5} {lane:<5} {lane_x:<7} {method:<12}")
        else:
            print(f"{hostname:<16} {'INVALID':<6} {'-':<5} {'-':<4} {'-':<3} {'-':<5} {'-':<5} {'-':<7} {'none':<12}")
    
    # Test HA pair detection
    print("\n" + "="*90)
    print("  HA Pair Detection")
    print("="*90 + "\n")
    
    ha_pairs = parser.find_ha_pairs(test_hostnames)
    if ha_pairs:
        for h1, h2 in ha_pairs:
            print(f"  ✓ HA Pair: {h1} <-> {h2}")
    else:
        print("  No HA pairs detected in test set")
    
    # Test grouping by datacenter
    print("\n" + "="*90)
    print("  Datacenter Grouping")
    print("="*90 + "\n")
    
    grouped = parser.group_by_datacenter(test_hostnames)
    for dc, devices in sorted(grouped.items()):
        print(f"  {dc.upper():8} ({len(devices):2} devices): {', '.join(devices[:5])}")
        if len(devices) > 5:
            print(f"           {' '*12}  ... and {len(devices)-5} more")
    
    print("\n" + "="*90)
    print("  Configuration Summary")
    print("="*90 + "\n")
    
    print(f"  Supported Datacenters: {', '.join(parser.datacenters)}")
    print(f"  Supported Positions:   {', '.join(parser.positions)}")
    print(f"  Supported Types:       {', '.join(parser.types)}")
    print(f"  Z-layer range:         {min(POSITION_TO_Z_LAYER.values()):.1f} to {max(POSITION_TO_Z_LAYER.values()):.1f}")
    print(f"  Lane range:            {min(POSITION_TO_LANE.values()):+d} to {max(POSITION_TO_LANE.values()):+d}")
    
    print()


if __name__ == '__main__':
    test_parser()
