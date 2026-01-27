#!/usr/bin/env python3
"""
Hostname Parser for Network Device Classification
Parses format: {location}{role}{type}{counter}
Example: npccosr01 = npc + co + sr + 01
"""

import re
from typing import Dict, Tuple


class HostnameParser:
    """Parse structured hostnames into location, role, type, and counter"""
    
    # Valid codes
    LOCATIONS = ['npc', 'wpc', 'ukrc', 'ukpc', 'apc', 'apd', 'ma5', 'ld5', 'ch2', 'va1']
    ROLES = ['co', 'id', 'di', 'pub', 'prv']
    TYPES = ['sr', 'sw']
    
    # Role to layer mapping for 3D visualization
    ROLE_TO_LAYER = {
        'co': 'core',           # Core
        'id': 'router',         # Internet Distribution (edge)
        'di': 'distribution',   # Distribution
        'pub': 'router',        # Internet/Public zone (edge)
        'prv': 'access'         # Private zone (access)
    }
    
    # Z-axis levels for 3D visualization
    LAYER_Z_LEVELS = {
        'router': 3.0,      # Edge/Internet
        'core': 2.0,        # Core
        'distribution': 1.0, # Distribution
        'access': 0.0       # Access
    }
    
    def __init__(self):
        # Build regex pattern dynamically from valid codes
        location_pattern = '|'.join(self.LOCATIONS)
        role_pattern = '|'.join(self.ROLES)
        type_pattern = '|'.join(self.TYPES)
        
        # Pattern: location(3-4) + role(2-3) + type(2-3) + counter(2)
        self.pattern = re.compile(
            rf'^({location_pattern})({role_pattern})({type_pattern})(\d{{2}})$',
            re.IGNORECASE
        )
    
    def parse(self, hostname: str) -> Dict:
        """
        Parse hostname into components
        
        Returns dict with:
        - location: str
        - role: str
        - type: str
        - counter: str
        - layer: str (for visualization)
        - z_level: float (for 3D positioning)
        - valid: bool
        """
        hostname_clean = hostname.strip().lower()
        
        match = self.pattern.match(hostname_clean)
        
        if not match:
            return {
                'hostname': hostname,
                'location': None,
                'role': None,
                'type': None,
                'counter': None,
                'layer': 'unknown',
                'z_level': 1.5,
                'valid': False
            }
        
        location, role, dev_type, counter = match.groups()
        layer = self.ROLE_TO_LAYER.get(role, 'unknown')
        z_level = self.LAYER_Z_LEVELS.get(layer, 1.5)
        
        return {
            'hostname': hostname,
            'location': location,
            'role': role,
            'type': dev_type,
            'counter': counter,
            'layer': layer,
            'z_level': z_level,
            'valid': True
        }
    
    def get_layer(self, hostname: str) -> str:
        """Quick method to just get the layer"""
        return self.parse(hostname)['layer']
    
    def get_z_level(self, hostname: str) -> float:
        """Quick method to just get Z-level for 3D positioning"""
        return self.parse(hostname)['z_level']


def test_parser():
    """Test the parser with example hostnames"""
    parser = HostnameParser()
    
    test_hostnames = [
        'npccosr01',  # Core switch router
        'npcdisr02',  # Distribution switch router
        'wpcidsw01',  # Internet distribution switch
        'ukrcpubsw03', # Public zone switch
        'apdprvsw05',  # Private zone switch
        'NPCCOSR01',   # Test case insensitive
        'invalid-name' # Should fail gracefully
    ]
    
    print("Hostname Parser Test Results:")
    print("=" * 80)
    
    for hostname in test_hostnames:
        result = parser.parse(hostname)
        if result['valid']:
            print(f"{hostname:15} → {result['location']:4} | {result['role']:3} | "
                  f"{result['type']:2} | #{result['counter']} | "
                  f"Layer: {result['layer']:12} (Z={result['z_level']})")
        else:
            print(f"{hostname:15} → INVALID (no match)")
    
    print("\n" + "=" * 80)
    print("Layer Summary:")
    print("  Z=3.0: Edge/Internet (id, pub)")
    print("  Z=2.0: Core (co)")
    print("  Z=1.0: Distribution (di)")
    print("  Z=0.0: Access (prv)")


if __name__ == '__main__':
    test_parser()
