#!/usr/bin/env python3
"""
BGP Parser for Cisco NX-OS - Extract BGP peering relationships
Handles NX-OS template-based configuration syntax
"""

import re
from pathlib import Path
from typing import Dict, List
import json
from ciscoconfparse import CiscoConfParse


class BGPParserNXOS:
    """Parse NX-OS BGP configuration to identify peering relationships"""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.peers = []
        self.edges = []
        
    def parse_loopback(self, config_file: Path) -> str:
        """Extract loopback0 IP from NX-OS config"""
        parse = CiscoConfParse(str(config_file), syntax='nxos')
        
        # Find Loopback0 interface
        loopback_objs = parse.find_objects(r'^interface loopback0')
        if not loopback_objs:
            return None
        
        # Find IP address under loopback
        for child in loopback_objs[0].children:
            ip_match = re.search(r'ip address\s+(\S+)', child.text)
            if ip_match:
                return ip_match.group(1).split('/')[0]  # Strip /32 if present
        
        return None
    
    def parse_config(self, config_file: Path) -> List[Dict]:
        """Parse NX-OS BGP configuration from a single device"""
        parse = CiscoConfParse(str(config_file), syntax='nxos')
        device_name = config_file.stem
        
        bgp_configs = []
        
        # Find BGP AS number
        bgp_objs = parse.find_objects(r'^router bgp')
        if not bgp_objs:
            return []
        
        bgp_obj = bgp_objs[0]
        as_match = re.search(r'router bgp\s+(\d+)', bgp_obj.text)
        if not as_match:
            return []
        
        local_as = as_match.group(1)
        
        # Parse peer templates first
        templates = {}
        template_objs = parse.find_objects(r'^\s+template peer')
        
        for template_obj in template_objs:
            template_match = re.search(r'template peer\s+(\S+)', template_obj.text)
            if not template_match:
                continue
            
            template_name = template_match.group(1)
            template_data = {'remote_as': None, 'description': None}
            
            # Get remote-as from template
            for child in template_obj.children:
                remote_as_match = re.search(r'remote-as\s+(\d+)', child.text)
                if remote_as_match:
                    template_data['remote_as'] = remote_as_match.group(1)
                
                desc_match = re.search(r'description\s+(.+)', child.text)
                if desc_match:
                    template_data['description'] = desc_match.group(1).strip()
            
            templates[template_name] = template_data
        
        # Find all BGP neighbors
        neighbor_objs = parse.find_objects(r'^\s+neighbor\s+\d+\.')
        
        for neighbor_obj in neighbor_objs:
            neighbor_match = re.search(r'neighbor\s+(\S+)', neighbor_obj.text)
            if not neighbor_match:
                continue
            
            neighbor_ip = neighbor_match.group(1)
            
            neighbor_data = {
                'device': device_name,
                'local_as': local_as,
                'neighbor_ip': neighbor_ip,
                'remote_as': None,
                'description': None,
                'template': None
            }
            
            # Check neighbor's child config lines
            for child in neighbor_obj.children:
                # Check for template inheritance
                inherit_match = re.search(r'inherit peer\s+(\S+)', child.text)
                if inherit_match:
                    template_name = inherit_match.group(1)
                    neighbor_data['template'] = template_name
                    
                    # Apply template data
                    if template_name in templates:
                        if templates[template_name]['remote_as']:
                            neighbor_data['remote_as'] = templates[template_name]['remote_as']
                        if templates[template_name]['description']:
                            neighbor_data['description'] = templates[template_name]['description']
                
                # Direct remote-as (overrides template)
                remote_as_match = re.search(r'remote-as\s+(\d+)', child.text)
                if remote_as_match:
                    neighbor_data['remote_as'] = remote_as_match.group(1)
                
                # Description
                desc_match = re.search(r'description\s+(.+)', child.text)
                if desc_match:
                    neighbor_data['description'] = desc_match.group(1).strip()
            
            if neighbor_data['remote_as']:  # Only add if we found remote-as
                bgp_configs.append(neighbor_data)
        
        return bgp_configs
    
    def parse_all(self) -> Dict:
        """Parse all config files and build BGP peering relationships"""
        config_files = list(self.config_dir.glob('*.cfg')) + list(self.config_dir.glob('*.txt'))
        
        if not config_files:
            print(f"Warning: No .cfg or .txt files found in {self.config_dir}")
            return {'peers': [], 'edges': []}
        
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
                'peering_type': 'eBGP' if peer['local_as'] != peer['remote_as'] else 'iBGP',
                'template': peer.get('template')
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
        
        print(f"✓ Exported NX-OS BGP topology to {output_file}")
        print(f"   BGP Peers: {len(bgp_data['peers'])}")
        print(f"   Peering Links: {len(bgp_data['edges'])}")
        
        # Count eBGP vs iBGP
        ebgp = sum(1 for e in bgp_data['edges'] if e.get('peering_type') == 'eBGP')
        ibgp = sum(1 for e in bgp_data['edges'] if e.get('peering_type') == 'iBGP')
        
        print(f"   eBGP: {ebgp}, iBGP: {ibgp}")
        
        return bgp_data


if __name__ == '__main__':
    import sys
    config_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/running_configs'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output/bgp_topology_nxos.json'
    
    parser = BGPParserNXOS(config_dir)
    bgp_data = parser.export_json(output_file)
    
    print("\n📊 BGP Peerings:")
    for peer in bgp_data['peers'][:10]:  # Show first 10
        peering_type = 'eBGP' if peer['local_as'] != peer['remote_as'] else 'iBGP'
        template_str = f" (template: {peer['template']})" if peer.get('template') else ""
        print(f"   {peer['device']} (AS{peer['local_as']}) → {peer['neighbor_ip']} "
              f"(AS{peer['remote_as']}) - {peering_type}{template_str}")
