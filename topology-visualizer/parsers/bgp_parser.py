#!/usr/bin/env python3
"""
BGP Parser - Extract BGP peering relationships from configs
"""

import re
from pathlib import Path
from typing import Dict, List
import json
from ciscoconfparse import CiscoConfParse


class BGPParser:
    """Parse BGP configuration to identify peering relationships"""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.peers = []
        self.edges = []
        
    def parse_loopback(self, config_file: Path) -> str:
        """Extract loopback0 IP from config"""
        parse = CiscoConfParse(str(config_file))
        
        # Find Loopback0 interface
        loopback_objs = parse.find_objects(r'^interface Loopback0')
        if not loopback_objs:
            return None
        
        # Find IP address under loopback
        for child in loopback_objs[0].children:
            ip_match = re.search(r'ip address\s+(\S+)\s+', child.text)
            if ip_match:
                return ip_match.group(1)
        
        return None
    
    def parse_config(self, config_file: Path) -> List[Dict]:
        """Parse BGP configuration from a single device"""
        parse = CiscoConfParse(str(config_file))
        device_name = config_file.stem
        
        bgp_configs = []
        
        # Find BGP AS number
        bgp_objs = parse.find_objects(r'^router bgp')
        if not bgp_objs:
            return []
        
        # Should only be one router bgp statement
        bgp_obj = bgp_objs[0]
        as_match = re.search(r'router bgp\s+(\d+)', bgp_obj.text)
        if not as_match:
            return []
        
        local_as = as_match.group(1)
        
        # Find all BGP neighbors
        neighbor_objs = bgp_obj.re_search_children(r'^\s+neighbor\s+(\S+)')
        
        neighbors = {}
        for neighbor_line in neighbor_objs:
            neighbor_match = re.search(r'neighbor\s+(\S+)\s+(.+)', neighbor_line.text)
            if not neighbor_match:
                continue
            
            neighbor_ip = neighbor_match.group(1)
            config_line = neighbor_match.group(2)
            
            if neighbor_ip not in neighbors:
                neighbors[neighbor_ip] = {
                    'device': device_name,
                    'local_as': local_as,
                    'neighbor_ip': neighbor_ip,
                    'remote_as': None,
                    'description': None
                }
            
            # Extract remote AS
            if 'remote-as' in config_line:
                remote_as_match = re.search(r'remote-as\s+(\d+)', config_line)
                if remote_as_match:
                    neighbors[neighbor_ip]['remote_as'] = remote_as_match.group(1)
            
            # Extract description
            if 'description' in config_line:
                desc_match = re.search(r'description\s+(.+)', config_line)
                if desc_match:
                    neighbors[neighbor_ip]['description'] = desc_match.group(1).strip()
        
        bgp_configs = list(neighbors.values())
        return bgp_configs
    
    def parse_all(self) -> Dict:
        """Parse all config files and build BGP peering relationships"""
        config_files = list(self.config_dir.glob('*.cfg'))
        
        # Build IP to device name mapping from loopback IPs
        ip_to_device = {}
        for config_file in config_files:
            device_name = config_file.stem
            loopback_ip = self.parse_loopback(config_file)
            if loopback_ip:
                ip_to_device[loopback_ip] = device_name
        
        all_bgp = []
        for config_file in config_files:
            bgp_configs = self.parse_config(config_file)
            all_bgp.extend(bgp_configs)
        
        self.peers = all_bgp
        
        # Build edges showing BGP peerings with proper device name resolution
        edges = []
        processed = set()
        
        for peer in all_bgp:
            peer_key = f"{peer['device']}_{peer['neighbor_ip']}"
            
            if peer_key in processed:
                continue
            
            # Resolve neighbor IP to device name using loopback mapping
            target_device = ip_to_device.get(peer['neighbor_ip'], peer['neighbor_ip'])
            
            edge = {
                'source': peer['device'],
                'target': target_device,
                'link_type': 'bgp',
                'local_as': peer['local_as'],
                'remote_as': peer['remote_as'],
                'neighbor_ip': peer['neighbor_ip'],
                'peering_type': 'eBGP' if peer['local_as'] != peer['remote_as'] else 'iBGP'
            }
            
            edges.append(edge)
            processed.add(peer_key)
        
        self.edges = edges
        
        return {
            'peers': all_bgp,
            'edges': edges
        }
    
    def export_json(self, output_file: str):
        """Export BGP topology to JSON"""
        bgp_data = self.parse_all()
        
        with open(output_file, 'w') as f:
            json.dump(bgp_data, f, indent=2)
        
        print(f"✓ Exported BGP topology to {output_file}")
        print(f"   BGP Peers: {len(bgp_data['peers'])}")
        print(f"   Peering Links: {len(bgp_data['edges'])}")
        
        # Count eBGP vs iBGP
        ebgp = sum(1 for e in bgp_data['edges'] if e.get('peering_type') == 'eBGP')
        ibgp = sum(1 for e in bgp_data['edges'] if e.get('peering_type') == 'iBGP')
        
        print(f"   eBGP: {ebgp}, iBGP: {ibgp}")
        
        return bgp_data


if __name__ == '__main__':
    parser = BGPParser('/app/configs')
    bgp_data = parser.export_json('/app/output/bgp_topology.json')
    
    print("\n📊 BGP Peerings:")
    for peer in bgp_data['peers']:
        peering_type = 'eBGP' if peer['local_as'] != peer['remote_as'] else 'iBGP'
        print(f"   {peer['device']} (AS{peer['local_as']}) → {peer['neighbor_ip']} "
              f"(AS{peer['remote_as']}) - {peering_type}")
