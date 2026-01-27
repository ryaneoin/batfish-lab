#!/usr/bin/env python3
"""
HSRP Parser for Cisco NX-OS - Extract HSRP/VRRP redundancy relationships
Handles NX-OS indentation and syntax
"""

import re
from pathlib import Path
from typing import Dict, List
import json
from ciscoconfparse import CiscoConfParse


class HSRPParserNXOS:
    """Parse NX-OS HSRP/VRRP configuration to identify redundancy relationships"""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.hsrp_groups = []
        self.edges = []
        
    def parse_config(self, config_file: Path) -> List[Dict]:
        """Parse NX-OS HSRP configuration from a single device"""
        parse = CiscoConfParse(str(config_file), syntax='nxos')
        device_name = config_file.stem
        
        hsrp_configs = []
        
        # Find all interfaces
        interface_objs = parse.find_objects(r'^interface')
        
        for intf_obj in interface_objs:
            interface_name = intf_obj.text.replace('interface ', '').strip()
            
            # Look for HSRP groups under this interface
            hsrp_group_objs = [child for child in intf_obj.children 
                              if re.match(r'\s+hsrp\s+\d+', child.text)]
            
            for hsrp_obj in hsrp_group_objs:
                group_match = re.search(r'hsrp\s+(\d+)', hsrp_obj.text)
                if not group_match:
                    continue
                
                group_id = group_match.group(1)
                
                hsrp_data = {
                    'device': device_name,
                    'interface': interface_name,
                    'group_id': group_id,
                    'vip': None,
                    'priority': 100,  # Default priority
                    'preempt': False,
                    'authentication': False
                }
                
                # Parse HSRP group configuration
                for child in hsrp_obj.children:
                    # Virtual IP
                    vip_match = re.search(r'ip\s+(\d+\.\d+\.\d+\.\d+)', child.text)
                    if vip_match:
                        hsrp_data['vip'] = vip_match.group(1)
                    
                    # Priority
                    priority_match = re.search(r'priority\s+(\d+)', child.text)
                    if priority_match:
                        hsrp_data['priority'] = int(priority_match.group(1))
                    
                    # Preempt
                    if 'preempt' in child.text.lower():
                        hsrp_data['preempt'] = True
                    
                    # Authentication
                    if 'authentication' in child.text.lower():
                        hsrp_data['authentication'] = True
                
                hsrp_configs.append(hsrp_data)
            
            # Also check for VRRP (NX-OS uses vrrp command)
            vrrp_group_objs = [child for child in intf_obj.children 
                              if re.match(r'\s+vrrp\s+\d+', child.text)]
            
            for vrrp_obj in vrrp_group_objs:
                group_match = re.search(r'vrrp\s+(\d+)', vrrp_obj.text)
                if not group_match:
                    continue
                
                group_id = group_match.group(1)
                
                vrrp_data = {
                    'device': device_name,
                    'interface': interface_name,
                    'group_id': group_id,
                    'vip': None,
                    'priority': 100,
                    'preempt': False,
                    'authentication': False,
                    'protocol': 'VRRP'
                }
                
                # Parse VRRP group configuration
                for child in vrrp_obj.children:
                    # Virtual IP (address in VRRP)
                    vip_match = re.search(r'address\s+(\d+\.\d+\.\d+\.\d+)', child.text)
                    if vip_match:
                        vrrp_data['vip'] = vip_match.group(1)
                    
                    # Priority
                    priority_match = re.search(r'priority\s+(\d+)', child.text)
                    if priority_match:
                        vrrp_data['priority'] = int(priority_match.group(1))
                    
                    # Preempt
                    if 'preempt' in child.text.lower():
                        vrrp_data['preempt'] = True
                    
                    # Authentication
                    if 'authentication' in child.text.lower():
                        vrrp_data['authentication'] = True
                
                hsrp_configs.append(vrrp_data)
        
        return hsrp_configs
    
    def parse_all(self) -> Dict:
        """Parse all config files and build HSRP/VRRP relationships"""
        config_files = list(self.config_dir.glob('*.cfg')) + list(self.config_dir.glob('*.txt'))
        
        if not config_files:
            print(f"Warning: No .cfg or .txt files found in {self.config_dir}")
            return {'groups': [], 'edges': []}
        
        all_hsrp = []
        for config_file in config_files:
            hsrp_configs = self.parse_config(config_file)
            all_hsrp.extend(hsrp_configs)
        
        self.hsrp_groups = all_hsrp
        
        # Build edges showing redundancy relationships
        # Group by interface + group_id + VIP
        groups_by_key = {}
        for group in all_hsrp:
            # Use interface name (without device) + group_id + VIP as key
            intf_short = group['interface'].split('/')[-1] if '/' in group['interface'] else group['interface']
            key = f"{intf_short}_group{group['group_id']}_vip{group['vip']}"
            
            if key not in groups_by_key:
                groups_by_key[key] = []
            groups_by_key[key].append(group)
        
        # Create edges between devices in same HSRP/VRRP group
        edges = []
        for key, group_members in groups_by_key.items():
            if len(group_members) < 2:
                continue  # Skip orphaned groups
            
            # Create edges between all pairs (redundancy relationships)
            for i in range(len(group_members)):
                for j in range(i + 1, len(group_members)):
                    edge = {
                        'source': group_members[i]['device'],
                        'target': group_members[j]['device'],
                        'link_type': 'hsrp',
                        'group_id': group_members[i]['group_id'],
                        'vip': group_members[i]['vip'],
                        'interface': group_members[i]['interface'],
                        'protocol': group_members[i].get('protocol', 'HSRP')
                    }
                    edges.append(edge)
        
        self.edges = edges
        
        return {
            'groups': all_hsrp,
            'edges': edges
        }
    
    def export_json(self, output_file: str):
        """Export HSRP/VRRP topology to JSON"""
        hsrp_data = self.parse_all()
        
        with open(output_file, 'w') as f:
            json.dump(hsrp_data, f, indent=2)
        
        print(f"✓ Exported NX-OS HSRP/VRRP topology to {output_file}")
        print(f"   HSRP/VRRP Groups: {len(hsrp_data['groups'])}")
        print(f"   Redundancy Links: {len(hsrp_data['edges'])}")
        
        return hsrp_data


if __name__ == '__main__':
    import sys
    config_dir = sys.argv[1] if len(sys.argv) > 1 else 'data/running_configs'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'output/hsrp_topology_nxos.json'
    
    parser = HSRPParserNXOS(config_dir)
    hsrp_data = parser.export_json(output_file)
    
    print("\n📊 HSRP/VRRP Groups:")
    for group in hsrp_data['groups'][:10]:  # Show first 10
        protocol = group.get('protocol', 'HSRP')
        auth_str = " (authenticated)" if group['authentication'] else ""
        preempt_str = " preempt" if group['preempt'] else ""
        print(f"   {group['device']} {group['interface']} - {protocol} Group {group['group_id']} "
              f"VIP: {group['vip']} Priority: {group['priority']}{preempt_str}{auth_str}")
