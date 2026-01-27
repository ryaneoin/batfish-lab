#!/usr/bin/env python3
"""
3D Network Topology Visualization
Generates interactive 3D topology from existing JSON files
"""

import json
import networkx as nx
import plotly.graph_objects as go
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / 'output'

# Add near the top of generate_3d_topology.py
from parsers.hostname_parser import HostnameParser

def create_layered_3d_layout(graph):
    """Create 3D layout with hierarchical layers using hostname parsing"""
    pos_3d = {}
    
    # Initialize hostname parser
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
    
    # Use 2D spring layout for X,Y coordinates per layer
    for layer, data in nodes_by_layer.items():
        nodes = data['nodes']
        z = data['z']
        
        if not nodes:
            continue
        
        # Create subgraph for this layer
        subgraph = graph.subgraph(nodes)
        
        # Get 2D positions
        if len(nodes) > 1:
            pos_2d = nx.spring_layout(subgraph, k=2, iterations=50, seed=42)
        else:
            pos_2d = {nodes[0]: (0, 0)}
        
        # Add Z coordinate
        for node in nodes:
            x, y = pos_2d[node]
            pos_3d[node] = (x, y, z)
    
    return pos_3d

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
    """Create 3D layout with hierarchical layers"""
    pos_3d = {}
    
    # Assign Z-levels based on device type
    z_levels = {
        'router': 3.0,      # Top layer - Edge routers
        'core': 2.0,        # Core layer
        'distribution': 1.0, # Distribution layer
        'access': 0.0       # Bottom layer
    }
    
    # Group nodes by type
    nodes_by_type = {}
    for node in graph.nodes():
        node_type = graph.nodes[node].get('node_type', 'unknown')
        if node_type not in nodes_by_type:
            nodes_by_type[node_type] = []
        nodes_by_type[node_type].append(node)
    
    # Use 2D spring layout for X,Y coordinates per layer
    for node_type, nodes in nodes_by_type.items():
        if not nodes:
            continue
        
        # Create subgraph for this layer
        subgraph = graph.subgraph(nodes)
        
        # Get 2D positions
        if len(nodes) > 1:
            pos_2d = nx.spring_layout(subgraph, k=2, iterations=50, seed=42)
        else:
            pos_2d = {nodes[0]: (0, 0)}
        
        # Add Z coordinate
        z = z_levels.get(node_type, 1.5)
        for node in nodes:
            x, y = pos_2d[node]
            pos_3d[node] = (x, y, z)
    
    return pos_3d


def visualize_3d_topology(graphs):
    """Create 3D interactive visualization"""
    combined_graph = graphs['combined']
    
    # Create 3D layout
    print("Creating 3D layout...")
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
    
    # Create nodes
    node_x, node_y, node_z = [], [], []
    node_text = []
    node_color = []
    
    color_map = {
        'router': '#FF6B6B',      # Red
        'core': '#4ECDC4',        # Teal
        'distribution': '#95E1D3', # Light teal
        'access': '#F38181',      # Pink
        'unknown': '#AAAAAA'      # Gray
    }
    
    for node in combined_graph.nodes():
        if node in pos_3d:
            x, y, z = pos_3d[node]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            node_text.append(node)
            
            node_type = combined_graph.nodes[node].get('node_type', 'unknown')
            node_color.append(color_map.get(node_type, '#AAAAAA'))
    
    # Node trace
    traces.append(go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text',
        text=node_text,
        textposition='top center',
        textfont=dict(size=10, color='black'),
        marker=dict(
            size=12,
            color=node_color,
            line=dict(color='white', width=2)
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
            text='3D Network Topology (Drag to Rotate)',
            font=dict(size=20)
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
                ticktext=['Access', 'Distribution', 'Core', 'Edge'],
                tickvals=[0, 1, 2, 3],
                showbackground=True,
                backgroundcolor='#F5F5F5'
            ),
            bgcolor='white',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=40),
        hovermode='closest'
    )
    
    # Save
    output_file = OUTPUT_DIR / 'combined_topology_3d.html'
    fig.write_html(output_file)
    print(f"✓ 3D topology visualization saved to {output_file}")
    
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
        print("   Run: python run_pipeline.py first")
        return
    
    print(f"  ✓ Loaded {len(graphs['combined'].nodes())} devices")
    print(f"  ✓ Loaded {len(graphs['combined'].edges())} connections")
    
    # Generate 3D visualization
    output_file = visualize_3d_topology(graphs)
    
    print("\n" + "="*60)
    print("  ✅ Complete!")
    print("="*60)
    print(f"\nOpen: {output_file}")
    print("\n💡 Tip: Click and drag to rotate the 3D topology")
    print()


if __name__ == '__main__':
    main()
