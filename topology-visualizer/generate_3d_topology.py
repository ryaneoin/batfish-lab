#!/usr/bin/env python3
"""
3D Network Topology Visualization with Hostname-Based Layer Classification
Generates interactive 3D topology from existing JSON files
"""

import json
import networkx as nx
import plotly.graph_objects as go
from pathlib import Path
import sys
import re

# Paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / 'output'

# Add parsers to path
sys.path.insert(0, str(SCRIPT_DIR / 'parsers'))

# Try to import hostname parser, fall back to simple classification
try:
    from hostname_parser import HostnameParser
    USE_HOSTNAME_PARSER = True
except ImportError:
    USE_HOSTNAME_PARSER = False
    print("Warning: hostname_parser not found, using simple classification")


def classify_device_simple(node_name, node_type):
    """Simple fallback classification based on node_type from CDP"""
    z_levels = {
        'router': 3.0,
        'core': 2.0,
        'distribution': 1.0,
        'access': 0.0,
        'unknown': 1.5
    }
    return z_levels.get(node_type, 1.5)


def load_topology_data():
    """Load topology data from JSON files"""
    graphs = {
        'physical': nx.Graph(),
        'hsrp': nx.Graph(),
        'bgp': nx.DiGraph(),
        'combined': nx.MultiGraph()
    }
    
    # Load physical topology
    physical_file = OUTPUT_DIR / 'cdp_topology.json'
    if physical_file.exists():
        with open(physical_file, 'r') as f:
            data = json.load(f)
            for node in data['nodes']:
                for g in graphs.values():
                    g.add_node(node['name'], node_type=node['type'])
            for edge in data['edges']:
                graphs['physical'].add_edge(edge['source'], edge['target'], link_type='physical')
                graphs['combined'].add_edge(edge['source'], edge['target'], link_type='physical')
    
    # Load HSRP topology
    hsrp_file = OUTPUT_DIR / 'hsrp_topology.json'
    if hsrp_file.exists():
        with open(hsrp_file, 'r') as f:
            data = json.load(f)
            for edge in data['edges']:
                graphs['hsrp'].add_edge(edge['source'], edge['target'], link_type='hsrp', group=edge.get('group'))
                graphs['combined'].add_edge(edge['source'], edge['target'], link_type='hsrp', group=edge.get('group'))
    
    # Load BGP topology  
    bgp_file = OUTPUT_DIR / 'bgp_topology.json'
    if bgp_file.exists():
        with open(bgp_file, 'r') as f:
            data = json.load(f)
            for edge in data['edges']:
                graphs['bgp'].add_edge(edge['source'], edge['target'], 
                                      link_type='bgp', 
                                      peering_type=edge.get('type'))
                graphs['combined'].add_edge(edge['source'], edge['target'], 
                                           link_type='bgp',
                                           peering_type=edge.get('type'))
    
    return graphs


def create_layered_3d_layout(graph):
    """Create 3D layout with hierarchical layers using hostname parsing"""
    pos_3d = {}
    
    if USE_HOSTNAME_PARSER:
        print("Using hostname-based layer classification...")
        parser = HostnameParser()
        
        # Group nodes by parsed layer
        nodes_by_layer = {}
        for node in graph.nodes():
            # Parse hostname to get layer
            parsed = parser.parse(node)
            layer = parsed['layer']
            z_level = parsed['z_level']
            
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = {'nodes': [], 'z': z_level}
            nodes_by_layer[layer]['nodes'].append(node)
            
            # Debug output
            if parsed['valid']:
                print(f"  {node:20} → {parsed['location']:4}-{parsed['role']:3}-{parsed['type']:2} → Layer: {layer:12} (Z={z_level})")
            else:
                print(f"  {node:20} → UNPARSED → Layer: {layer:12} (Z={z_level})")
    else:
        print("Using simple node_type classification...")
        # Fallback: group by node_type from CDP
        nodes_by_layer = {}
        for node in graph.nodes():
            node_type = graph.nodes[node].get('node_type', 'unknown')
            z_level = classify_device_simple(node, node_type)
            layer = node_type
            
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = {'nodes': [], 'z': z_level}
            nodes_by_layer[layer]['nodes'].append(node)
    
    print(f"\nLayer distribution:")
    for layer, data in sorted(nodes_by_layer.items(), key=lambda x: x[1]['z'], reverse=True):
        print(f"  Z={data['z']}: {layer:12} - {len(data['nodes'])} devices")
    
    # Use 2D spring layout for X,Y coordinates per layer
    for layer, data in nodes_by_layer.items():
        nodes = data['nodes']
        z = data['z']
        
        if not nodes:
            continue
        
        # Create subgraph for this layer
        subgraph = graph.subgraph(nodes)
        
        # Get 2D positions with more spacing
        if len(nodes) > 1:
            pos_2d = nx.spring_layout(subgraph, k=3, iterations=100, seed=42)
        else:
            pos_2d = {nodes[0]: (0, 0)}
        
        # Add Z coordinate
        for node in nodes:
            x, y = pos_2d[node]
            pos_3d[node] = (x, y, z)
    
    return pos_3d


def visualize_3d_topology(graphs):
    """Create 3D interactive visualization"""
    combined_graph = graphs['combined']
    
    # Create 3D layout
    print("\nCreating 3D layout...")
    pos_3d = create_layered_3d_layout(combined_graph)
    
    # Separate edges by type
    physical_edges = []
    hsrp_edges = []
    bgp_edges = []
    
    for u, v, key, data in combined_graph.edges(data=True, keys=True):
        link_type = data.get('link_type', 'physical')
        if link_type == 'physical':
            physical_edges.append((u, v, data))
        elif link_type == 'hsrp':
            hsrp_edges.append((u, v, data))
        elif link_type == 'bgp':
            bgp_edges.append((u, v, data))
    
    traces = []
    
    # Physical links (gray solid lines)
    if physical_edges:
        edge_x, edge_y, edge_z = [], [], []
        for u, v, data in physical_edges:
            if u in pos_3d and v in pos_3d:
                x0, y0, z0 = pos_3d[u]
                x1, y1, z1 = pos_3d[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
                edge_z += [z0, z1, None]
        
        traces.append(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(color='#CCCCCC', width=2),
            hoverinfo='none',
            name='Physical Links',
            showlegend=True
        ))
    
    # HSRP links (red dashed lines)
    if hsrp_edges:
        edge_x, edge_y, edge_z = [], [], []
        for u, v, data in hsrp_edges:
            if u in pos_3d and v in pos_3d:
                x0, y0, z0 = pos_3d[u]
                x1, y1, z1 = pos_3d[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
                edge_z += [z0, z1, None]
        
        traces.append(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(color='#FF6B6B', width=4, dash='dash'),
            hoverinfo='none',
            name='HSRP Redundancy',
            showlegend=True
        ))
    
    # BGP links (blue lines)
    if bgp_edges:
        edge_x, edge_y, edge_z = [], [], []
        for u, v, data in bgp_edges:
            if u in pos_3d and v in pos_3d:
                x0, y0, z0 = pos_3d[u]
                x1, y1, z1 = pos_3d[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
                edge_z += [z0, z1, None]
        
        traces.append(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(color='#4ECDC4', width=3),
            hoverinfo='none',
            name='BGP Peering',
            showlegend=True
        ))
    
    # Create nodes with colors by layer
    node_x, node_y, node_z = [], [], []
    node_text = []
    node_color = []
    
    color_map = {
        'router': '#FF6B6B',      # Red - Edge/Internet
        'core': '#4ECDC4',        # Teal - Core
        'distribution': '#95E1D3', # Light teal - Distribution
        'access': '#F38181',      # Pink - Access
        'unknown': '#AAAAAA'      # Gray - Unknown
    }
    
    if USE_HOSTNAME_PARSER:
        parser = HostnameParser()
    
    for node in combined_graph.nodes():
        if node in pos_3d:
            x, y, z = pos_3d[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            node_text.append(node)
            
            # Get layer from hostname parser or fallback to node_type
            if USE_HOSTNAME_PARSER:
                layer = parser.get_layer(node)
            else:
                layer = combined_graph.nodes[node].get('node_type', 'unknown')
            
            node_color.append(color_map.get(layer, '#AAAAAA'))
    
    # Node trace
    traces.append(go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        textfont=dict(size=8, color='black'),
        marker=dict(
            size=10,
            color=node_color,
            line=dict(color='white', width=1)
        ),
        hovertext=node_text,
        hoverinfo='text',
        name='Devices',
        showlegend=True
    ))
    
    # Create figure
    fig = go.Figure(data=traces)
    
    fig.update_layout(
        title=dict(
            text='3D Network Topology - Layer-Based Layout<br><sub>Drag to rotate | Scroll to zoom</sub>',
            font=dict(size=18)
        ),
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#888',
            borderwidth=1
        ),
        scene=dict(
            xaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                title='',
                showbackground=False
            ),
            yaxis=dict(
                showgrid=False,
                zeroline=False,
                showticklabels=False,
                title='',
                showbackground=False
            ),
            zaxis=dict(
                showgrid=True,
                gridcolor='#E0E0E0',
                zeroline=False,
                showticklabels=True,
                title='Network Layer',
                ticktext=['Access/Private', 'Distribution', 'Core', 'Edge/Internet'],
                tickvals=[0, 1, 2, 3],
                showbackground=True,
                backgroundcolor='#F5F5F5'
            ),
            bgcolor='white',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=60),
        hovermode='closest'
    )
    
    # Save
    output_file = OUTPUT_DIR / 'combined_topology_3d.html'
    fig.write_html(output_file)
    print(f"\n✓ 3D topology visualization saved to {output_file}")
    
    return output_file


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("  3D Network Topology Visualization")
    print("="*60 + "\n")
    
    # Load data
    print("Loading topology data...")
    graphs = load_topology_data()
    
    if not graphs['combined'].nodes():
        print("❌ No topology data found!")
        print("   Run: python run_pipeline_nxos.py first")
        return
    
    print(f"  ✓ Loaded {len(graphs['combined'].nodes())} devices")
    print(f"  ✓ Loaded {len(graphs['combined'].edges())} connections\n")
    
    # Generate 3D visualization
    output_file = visualize_3d_topology(graphs)
    
    print("\n" + "="*60)
    print("  ✅ Complete!")
    print("="*60)
    print(f"\nOpen: {output_file}")
    print("\n💡 Tips:")
    print("   - Click and drag to rotate")
    print("   - Scroll to zoom")
    print("   - Layers: Z=3 (Edge), Z=2 (Core), Z=1 (Dist), Z=0 (Access)")
    print()


if __name__ == '__main__':
    main()
