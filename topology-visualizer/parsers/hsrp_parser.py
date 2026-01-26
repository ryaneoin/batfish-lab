#!/usr/bin/env python3
"""
HSRP Parser - Extract HSRP redundancy relationships from configs
"""

import re
from pathlib import Path
from typing import Dict, List
import json
from ciscoconfparse import CiscoConfParse


class HSRPParser:
    """Parse HSRP configuration to identify redundancy groups"""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.hsrp_groups = {}
        self.edges = []
        
    def parse_config(self, config_file: Path) -> List[Dict]:
        """Parse HSRP configuration from a single device"""
        parse = CiscoConfParse(str(config_file))
        device_name = config_file.stem
        
        hsrp_configs = []
        
        # Find all interfaces with HSRP
        hsrp_intfs = parse.find_objects(r'^interface')
        
        for intf_obj in hsrp_intfs:
            intf_name = intf_obj.text.replace('interface ', '')
            
            # Look for standby commands under this interface
            standby_objs = intf_obj.re_search_children(r'^\s+standby\s+(\d+)')
            
            if not standby_objs:
                continue
            
            for standby_line in standby_objs:
                # Extract group number
                group_match = re.search(r'standby\s+(\d+)', standby_line.text)
                if not group_match:
                    continue
                    
                group_num = group_match.group(1)
                
                # Extract IP address if present
                ip_match = re.search(r'standby\s+\d+\s+ip\s+(\S+)', standby_line.text)
                virtual_ip = ip_match.group(1) if ip_match else None
                
                # Extract priority
                priority_match = re.search(r'standby\s+\d+\s+priority\s+(\d+)', standby_line.text)
                priority = int(priority_match.group(1)) if priority_match else 100
                
                # Extract preempt
                preempt = 'preempt' in standby_line.text
                
                hsrp_configs.append({
                    'device': device_name,
                    'interface': intf_name,
                    'group': group_num,
                    'virtual_ip': virtual_ip,
                    'priority': priority,
                    'preempt': preempt
                })
        
        return hsrp_configs
    
    def parse_all(self) -> Dict:
        """Parse all config files and build HSRP groups"""
        config_files = list(self.config_dir.glob('*.cfg'))
        
        all_hsrp = []
        for config_file in config_files:
            hsrp_configs = self.parse_config(config_file)
            all_hsrp.extend(hsrp_configs)
        
        # Group by virtual IP or group number
        groups = {}
        for hsrp in all_hsrp:
            # Use virtual IP as key if available, otherwise use interface+group
            if hsrp['virtual_ip']:
                key = hsrp['virtual_ip']
            else:
                key = f"{hsrp['interface']}_group{hsrp['group']}"
            
            if key not in groups:
                groups[key] = []
            groups[key].append(hsrp)
        
        self.hsrp_groups = groups
        
        # Build edges showing HSRP pairs
        edges = []
        for group_key, members in groups.items():
            if len(members) >= 2:
                # Sort by priority to identify active/standby
                sorted_members = sorted(members, key=lambda x: x['priority'], reverse=True)
                
                for i in range(len(sorted_members) - 1):
                    edges.append({
                        'source': sorted_members[i]['device'],
                        'target': sorted_members[i+1]['device'],
                        'link_type': 'hsrp',
                        'virtual_ip': group_key if '.' in group_key else None,
                        'group': sorted_members[i]['group'],
                        'active_priority': sorted_members[0]['priority'],
                        'standby_priority': sorted_members[1]['priority'] if len(sorted_members) > 1 else None
                    })
        
        self.edges = edges
        
        return {
            'groups': groups,
            'edges': edges
        }
    
    def export_json(self, output_file: str):
        """Export HSRP topology to JSON"""
        hsrp_data = self.parse_all()
        
        with open(output_file, 'w') as f:
            json.dump(hsrp_data, f, indent=2)
        
        print(f"✓ Exported HSRP topology to {output_file}")
        print(f"   HSRP Groups: {len(hsrp_data['groups'])}")
        print(f"   Redundancy Links: {len(hsrp_data['edges'])}")
        
        return hsrp_data


if __name__ == '__main__':
    parser = HSRPParser('/app/configs')
    hsrp_data = parser.export_json('/app/output/hsrp_topology.json')
    
    print("\n📊 HSRP Groups:")
    for group_id, members in hsrp_data['groups'].items():
        print(f"\n   Group: {group_id}")
        for member in sorted(members, key=lambda x: x['priority'], reverse=True):
            role = "Active" if member['priority'] > 100 else "Standby"
            print(f"     {member['device']} - {member['interface']} (Priority: {member['priority']}, {role})")
