#!/usr/bin/env python3
"""
CDP Parser - Extract physical topology from CDP neighbor data
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import json


class CDPParser:
    """Parse Cisco CDP neighbor output to build physical topology"""
    
    def __init__(self, cdp_dir: str):
        self.cdp_dir = Path(cdp_dir)
        self.neighbors = {}
        self.edges = []
        self.nodes = set()
        
    def parse_cdp_file(self, filepath: Path) -> List[Dict]:
        """Parse a single CDP neighbor file"""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract local device name from filename
        local_device = filepath.stem.replace('_cdp', '')
        
        # Split into individual neighbor entries
        neighbor_blocks = content.split('-------------------------')
        
        neighbors = []
        for block in neighbor_blocks:
            if not block.strip():
                continue
                
            neighbor = {}
            
            # Extract Device ID
            device_match = re.search(r'Device ID:\s*(\S+)', block)
            if device_match:
                neighbor['remote_device'] = device_match.group(1)
            
            # Extract IP address
            ip_match = re.search(r'IP address:\s*(\S+)', block)
            if ip_match:
                neighbor['remote_ip'] = ip_match.group(1)
            
            # Extract Platform
            platform_match = re.search(r'Platform:\s*cisco\s*([^,]+)', block)
            if platform_match:
                neighbor['platform'] = platform_match.group(1).strip()
            
            # Extract Capabilities
            cap_match = re.search(r'Capabilities:\s*(.+?)(?:\n|$)', block)
            if cap_match:
                neighbor['capabilities'] = cap_match.group(1).strip()
            
            # Extract Local Interface
            local_int_match = re.search(r'Interface:\s*(\S+),', block)
            if local_int_match:
                neighbor['local_interface'] = local_int_match.group(1)
            
            # Extract Remote Port
            remote_port_match = re.search(r'Port ID \(outgoing port\):\s*(\S+)', block)
            if remote_port_match:
                neighbor['remote_interface'] = remote_port_match.group(1)
            
            if neighbor.get('remote_device'):
                neighbor['local_device'] = local_device
                neighbors.append(neighbor)
        
        return neighbors
    
    def parse_all(self) -> Dict:
        """Parse all CDP files in directory"""
        cdp_files = list(self.cdp_dir.glob('*_cdp.txt'))
        
        all_neighbors = []
        for cdp_file in cdp_files:
            neighbors = self.parse_cdp_file(cdp_file)
            all_neighbors.extend(neighbors)
            
        # Build unique edges (bidirectional links)
        seen_edges = set()
        edges = []
        
        for neighbor in all_neighbors:
            local = neighbor['local_device']
            remote = neighbor['remote_device']
            local_int = neighbor.get('local_interface', '')
            remote_int = neighbor.get('remote_interface', '')
            
            # Create normalized edge identifier (alphabetically sorted)
            edge_key = tuple(sorted([
                f"{local}:{local_int}",
                f"{remote}:{remote_int}"
            ]))
            
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({
                    'source': local,
                    'target': remote,
                    'source_interface': local_int,
                    'target_interface': remote_int,
                    'link_type': 'physical'
                })
                
                self.nodes.add(local)
                self.nodes.add(remote)
        
        self.edges = edges
        
        # Build neighbor dictionary
        for neighbor in all_neighbors:
            local = neighbor['local_device']
            if local not in self.neighbors:
                self.neighbors[local] = []
            self.neighbors[local].append(neighbor)
        
        return {
            'nodes': list(self.nodes),
            'edges': edges,
            'neighbor_details': self.neighbors
        }
    
    def get_device_type(self, device_name: str) -> str:
        """Infer device type from name"""
        if 'CORE' in device_name:
            return 'core'
        elif 'DIST' in device_name:
            return 'distribution'
        elif 'ACC' in device_name:
            return 'access'
        elif 'EDGE' in device_name or 'RTR' in device_name:
            return 'router'
        else:
            return 'unknown'
    
    def export_json(self, output_file: str):
        """Export topology to JSON"""
        topology = self.parse_all()
        
        # Add device type metadata
        nodes_with_metadata = []
        for node in topology['nodes']:
            nodes_with_metadata.append({
                'name': node,
                'type': self.get_device_type(node)
            })
        
        topology['nodes'] = nodes_with_metadata
        
        with open(output_file, 'w') as f:
            json.dump(topology, f, indent=2)
        
        print(f"✓ Exported CDP topology to {output_file}")
        return topology


if __name__ == '__main__':
    parser = CDPParser('/app/cdp_data')
    topology = parser.export_json('/app/output/cdp_topology.json')
    
    print(f"\n📊 CDP Topology Summary:")
    print(f"   Devices: {len(topology['nodes'])}")
    print(f"   Links: {len(topology['edges'])}")
    print(f"\n   Devices by type:")
    
    type_counts = {}
    for node in topology['nodes']:
        node_type = node['type']
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
    
    for device_type, count in sorted(type_counts.items()):
        print(f"     {device_type}: {count}")
