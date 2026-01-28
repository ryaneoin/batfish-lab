#!/usr/bin/env python3
"""
Enhanced 3D Network Topology Visualization with Z-Layers and Lanes
Generates interactive 3D topology with:
- Multiple Z layers (configurable per POSITION)
- Lanes within each layer (-10 to +10)
- Icon-based device type visualization
- HA pair detection and visualization
- Multi-datacenter support
"""

import json
import networkx as nx
import plotly.graph_objects as go
from pathlib import Path
import sys
from collections import defaultdict

# Paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / 'output'

# Add parsers and config to path
sys.path.insert(0, str(SCRIPT_DIR / 'parsers'))
sys.path.insert(0, str(SCRIPT_DIR))

# Import configuration and parser
try:
    from config import (
        POSITION_TO_Z_LAYER,
        POSITION_TO_LANE,
        get_lane_x_position,
        HA_PAIR_DETECTION,
        HA_PAIR_OFFSET,
        HA_PAIR_LINK_COLOR,
        HA_PAIR_LINK_WIDTH,
        HA_PAIR_LINK_DASH,
        LINK_STYLES,
        SHOW_NODE_LABELS,
        NODE_LABEL_SIZE,
        SPRING_K,
        SPRING_ITERATIONS,
        SPRING_SEED,
        Y_AXIS_SPREAD,
        get_position_display_name
    )
    from enhanced_hostname_parser import EnhancedHostnameParser
    USE_ENHANCED = True
    print("✓ Using enhanced parser with lane-based positioning")
except ImportError as e:
    print(f"Warning: Enhanced parser not available ({e}), using basic mode")
    USE_ENHANCED = False
    from hostname_parser import HostnameParser
    SPRING_K = 3.0
    SPRING_ITERATIONS = 100
    SPRING_SEED = 42
    Y_AXIS_SPREAD = 3.0


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
                graphs['hsrp'].add_edge(edge['source'], edge['target'], 
                                       link_type='hsrp', group=edge.get('group'))
                graphs['combined'].add_edge(edge['source'], edge['target'], 
                                           link_type='hsrp', group=edge.get('group'))
    
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


def create_enhanced_3d_layout(graph, datacenter_filter=None):
    """
    Create 3D layout with Z-layers and lanes
    
    Args:
        graph: NetworkX graph
        datacenter_filter: Optional datacenter to filter by
        
    Returns:
        dict: {node: (x, y, z)} positions
    """
    pos_3d = {}
    
    if USE_ENHANCED:
        parser = EnhancedHostnameParser()
        
        # Group nodes by Z-layer and lane
        nodes_by_layer_lane = defaultdict(lambda: defaultdict(list))
        node_info = {}
        
        for node in graph.nodes():
            parsed = parser.parse(node)
            
            # If parsing failed, try to use node_type attribute from graph
            if not parsed['valid']:
                node_type = graph.nodes[node].get('node_type', 'unknown')
                # Map legacy node types to Z-layers
                legacy_z_map = {'router': 4.0, 'core': 3.5, 'distribution': 2.5, 'access': 1.5}
                z_level = legacy_z_map.get(node_type, 1.5)
                lane = 0
                lane_x = get_lane_x_position(lane)
                parsed = {
                    'hostname': node,
                    'datacenter': None,
                    'position': node_type,
                    'type': node_type,
                    'counter': None,
                    'z_level': z_level,
                    'lane': lane,
                    'lane_x': lane_x,
                    'icon_config': {'symbol': 'circle', 'size': 10, 'color': '#4ECDC4'},
                    'valid': True,
                    'parse_method': 'legacy'
                }
            
            # Filter by datacenter if specified
            if datacenter_filter and parsed['datacenter'] != datacenter_filter:
                continue
            
            z_level = parsed['z_level']
            lane = parsed['lane']
            lane_x = parsed['lane_x']
            
            nodes_by_layer_lane[z_level][lane].append(node)
            node_info[node] = {
                'z': z_level,
                'lane': lane,
                'lane_x': lane_x,
                'parsed': parsed
            }
            
            # Debug output
            if parsed['valid']:
                pos_str = f"{parsed['position'] or 'N/A':12}"
                method = parsed.get('parse_method', 'full')
                print(f"  {node:20} → DC:{parsed['datacenter'] or 'N/A':5} Pos:{pos_str} "
                      f"Lane:{lane:+3d} Z:{z_level:4.1f} [{method}]")
        
        # Position nodes using lanes and spring layout within lanes
        for z_level in sorted(nodes_by_layer_lane.keys(), reverse=True):
            lanes = nodes_by_layer_lane[z_level]
            
            for lane, nodes in lanes.items():
                if not nodes:
                    continue
                
                base_x = get_lane_x_position(lane)
                
                # For multiple nodes in same lane, spread them along Y axis
                if len(nodes) == 1:
                    # Single node - place at lane center
                    pos_3d[nodes[0]] = (base_x, 0.0, z_level)
                else:
                    # Multiple nodes - use spring layout for Y positioning
                    subgraph = graph.subgraph(nodes)
                    
                    # Use 2D spring layout and extract Y coordinates
                    pos_2d = nx.spring_layout(
                        subgraph,
                        dim=2,
                        k=Y_AXIS_SPREAD,
                        iterations=SPRING_ITERATIONS,
                        seed=SPRING_SEED
                    )
                    
                    # Apply positions - use Y coordinate from spring layout
                    for node in nodes:
                        y = pos_2d[node][1] * Y_AXIS_SPREAD
                        pos_3d[node] = (base_x, y, z_level)
        
        # Handle HA pairs - offset them slightly for visibility
        if HA_PAIR_DETECTION:
            ha_pairs = parser.find_ha_pairs(list(pos_3d.keys()))
            for h1, h2 in ha_pairs:
                if h1 in pos_3d and h2 in pos_3d:
                    x1, y1, z1 = pos_3d[h1]
                    x2, y2, z2 = pos_3d[h2]
                    
                    # Offset along Y axis
                    pos_3d[h1] = (x1, y1 - HA_PAIR_OFFSET, z1)
                    pos_3d[h2] = (x2, y2 + HA_PAIR_OFFSET, z2)
        
        print(f"\n✓ Positioned {len(pos_3d)} devices across {len(nodes_by_layer_lane)} Z-layers")
        
    else:
        # Fallback to basic layout
        parser = HostnameParser()
        nodes_by_layer = {}
        
        for node in graph.nodes():
            layer = parser.get_layer(node)
            z_level = parser.get_z_level(node)
            
            if layer not in nodes_by_layer:
                nodes_by_layer[layer] = {'nodes': [], 'z': z_level}
            nodes_by_layer[layer]['nodes'].append(node)
        
        # Position using spring layout per layer
        for layer, data in nodes_by_layer.items():
            nodes = data['nodes']
            z = data['z']
            
            if not nodes:
                continue
            
            subgraph = graph.subgraph(nodes)
            
            if len(nodes) > 1:
                pos_2d = nx.spring_layout(
                    subgraph,
                    k=SPRING_K,
                    iterations=SPRING_ITERATIONS,
                    seed=SPRING_SEED
                )
            else:
                pos_2d = {nodes[0]: (0, 0)}
            
            for node in nodes:
                x, y = pos_2d[node]
                pos_3d[node] = (x, y, z)
    
    return pos_3d


def visualize_3d_topology_enhanced(graphs, datacenter=None):
    """Create enhanced 3D interactive visualization"""
    combined_graph = graphs['combined']
    
    # Filter by datacenter if specified
    if USE_ENHANCED and datacenter:
        parser = EnhancedHostnameParser()
        nodes_in_dc = [n for n in combined_graph.nodes() 
                       if parser.get_datacenter(n) == datacenter]
        combined_graph = combined_graph.subgraph(nodes_in_dc)
        title_suffix = f" - {datacenter.upper()} Datacenter"
    else:
        title_suffix = ""
    
    # Create 3D layout
    print(f"\nCreating enhanced 3D layout{title_suffix}...")
    pos_3d = create_enhanced_3d_layout(combined_graph, datacenter)
    
    if not pos_3d:
        print("❌ No devices to visualize!")
        return None
    
    # Initialize parser for metadata
    if USE_ENHANCED:
        parser = EnhancedHostnameParser()
    else:
        parser = HostnameParser()
    
    # Separate edges by type
    physical_edges = []
    hsrp_edges = []
    bgp_edges = []
    ha_pair_edges = []
    
    for u, v, key, data in combined_graph.edges(data=True, keys=True):
        link_type = data.get('link_type', 'physical')
        if link_type == 'physical':
            physical_edges.append((u, v, data))
        elif link_type == 'hsrp':
            hsrp_edges.append((u, v, data))
        elif link_type == 'bgp':
            bgp_edges.append((u, v, data))
    
    # Detect HA pairs
    if USE_ENHANCED and HA_PAIR_DETECTION:
        ha_pairs = parser.find_ha_pairs(list(pos_3d.keys()))
        ha_pair_edges = [(h1, h2) for h1, h2 in ha_pairs 
                        if h1 in pos_3d and h2 in pos_3d]
    
    traces = []
    
    # HA pair links (red dashed, thin)
    if ha_pair_edges:
        edge_x, edge_y, edge_z = [], [], []
        for u, v in ha_pair_edges:
            x0, y0, z0 = pos_3d[u]
            x1, y1, z1 = pos_3d[v]
            edge_x += [x0, x1, None]
            edge_y += [y0, y1, None]
            edge_z += [z0, z1, None]
        
        traces.append(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(
                color=HA_PAIR_LINK_COLOR,
                width=HA_PAIR_LINK_WIDTH,
                dash=HA_PAIR_LINK_DASH
            ),
            hoverinfo='none',
            name='HA Pairs',
            showlegend=True
        ))
    
    # Physical links
    if physical_edges:
        edge_x, edge_y, edge_z = [], [], []
        for u, v, data in physical_edges:
            if u in pos_3d and v in pos_3d:
                x0, y0, z0 = pos_3d[u]
                x1, y1, z1 = pos_3d[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
                edge_z += [z0, z1, None]
        
        style = LINK_STYLES.get('physical', {})
        traces.append(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(
                color=style.get('color', '#CCCCCC'),
                width=style.get('width', 2),
                dash=style.get('dash', 'solid')
            ),
            hoverinfo='none',
            name='Physical Links',
            showlegend=True
        ))
    
    # HSRP links
    if hsrp_edges:
        edge_x, edge_y, edge_z = [], [], []
        for u, v, data in hsrp_edges:
            if u in pos_3d and v in pos_3d:
                x0, y0, z0 = pos_3d[u]
                x1, y1, z1 = pos_3d[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
                edge_z += [z0, z1, None]
        
        style = LINK_STYLES.get('hsrp', {})
        traces.append(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(
                color=style.get('color', '#FF6B6B'),
                width=style.get('width', 4),
                dash=style.get('dash', 'dash')
            ),
            hoverinfo='none',
            name='HSRP Redundancy',
            showlegend=True
        ))
    
    # BGP links
    if bgp_edges:
        edge_x, edge_y, edge_z = [], [], []
        for u, v, data in bgp_edges:
            if u in pos_3d and v in pos_3d:
                x0, y0, z0 = pos_3d[u]
                x1, y1, z1 = pos_3d[v]
                edge_x += [x0, x1, None]
                edge_y += [y0, y1, None]
                edge_z += [z0, z1, None]
        
        style = LINK_STYLES.get('bgp', {})
        traces.append(go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            mode='lines',
            line=dict(
                color=style.get('color', '#4ECDC4'),
                width=style.get('width', 3),
                dash=style.get('dash', 'solid')
            ),
            hoverinfo='none',
            name='BGP Peering',
            showlegend=True
        ))
    
    # Create nodes with icons and colors
    node_x, node_y, node_z = [], [], []
    node_text = []
    node_symbols = []
    node_sizes = []
    node_colors = []
    hover_texts = []
    
    for node in pos_3d.keys():
        x, y, z = pos_3d[node]
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        
        if USE_ENHANCED:
            parsed = parser.parse(node)
            icon_config = parsed['icon_config']
            
            node_text.append(node if SHOW_NODE_LABELS else '')
            node_symbols.append(icon_config.get('symbol', 'circle'))
            node_sizes.append(icon_config.get('size', 10))
            node_colors.append(icon_config.get('color', '#AAAAAA'))
            
            # Rich hover text
            hover_parts = [f"<b>{node}</b>"]
            if parsed['datacenter']:
                hover_parts.append(f"DC: {parsed['datacenter'].upper()}")
            if parsed['position']:
                hover_parts.append(f"Position: {get_position_display_name(parsed['position'])}")
            if parsed['type']:
                hover_parts.append(f"Type: {icon_config.get('description', parsed['type'].upper())}")
            hover_parts.append(f"Z-Layer: {z:.1f}")
            hover_parts.append(f"Lane: {parsed['lane']:+d}")
            
            hover_texts.append('<br>'.join(hover_parts))
        else:
            node_text.append(node if SHOW_NODE_LABELS else '')
            node_symbols.append('circle')
            node_sizes.append(10)
            node_colors.append('#4ECDC4')
            hover_texts.append(node)
    
    # Node trace
    traces.append(go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers+text' if SHOW_NODE_LABELS else 'markers',
        text=node_text,
        textposition='top center',
        textfont=dict(size=NODE_LABEL_SIZE, color='black'),
        marker=dict(
            size=node_sizes,
            color=node_colors,
            symbol=node_symbols,
            line=dict(color='white', width=1)
        ),
        hovertext=hover_texts,
        hoverinfo='text',
        name='Devices',
        showlegend=True
    ))
    
    # Create figure
    fig = go.Figure(data=traces)
    
    # Get Z-layer labels
    if USE_ENHANCED:
        z_levels = sorted(set(POSITION_TO_Z_LAYER.values()), reverse=True)
        z_labels = []
        for z in z_levels:
            positions = [p for p, zl in POSITION_TO_Z_LAYER.items() if zl == z]
            label = ', '.join([get_position_display_name(p) for p in positions[:2]])
            if len(positions) > 2:
                label += '...'
            z_labels.append(label)
    else:
        z_levels = [3, 2, 1, 0]
        z_labels = ['Edge', 'Core', 'Distribution', 'Access']
    
    fig.update_layout(
        title=dict(
            text=f'3D Network Topology - Enhanced Lane-Based Layout{title_suffix}<br>'
                 f'<sub>Drag to rotate | Scroll to zoom | Z-layers with lanes</sub>',
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
                gridcolor='#F0F0F0',
                zeroline=False,
                zerolinecolor='#888',
                zerolinewidth=2,
                showticklabels=True,
                title='',
                tickmode='linear',
                tick0=-20,
                dtick=5,
                showspikes=False,
                showbackground=False
            ),
            yaxis=dict(
                showgrid=False,
                gridcolor='#F0F0F0',
                zeroline=False,
                zerolinecolor='#888',
                showticklabels=False,
                title='',
                showbackground=False,
                showspikes=False
            ),
            zaxis=dict(
                showgrid=False,
                gridcolor='#E0E0E0',
                zeroline=False,
                showticklabels=False,
                title='',
                ticktext=z_labels,
                tickvals=z_levels,
                showbackground=False,
                showspikes=False
            ),
            bgcolor='rgba(0,0,0,0)',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        margin=dict(l=0, r=0, b=0, t=80),
        hovermode='closest'
    )
    
    # Save
    if datacenter:
        output_file = OUTPUT_DIR / f'topology_3d_enhanced_{datacenter}.html'
    else:
        output_file = OUTPUT_DIR / 'topology_3d_enhanced.html'
    
    fig.write_html(output_file)
    print(f"\n✓ Enhanced 3D visualization saved to {output_file}")
    
    return output_file


def main():
    """Main entry point"""
    print("\n" + "="*70)
    print("  Enhanced 3D Network Topology Visualization")
    print("  With Z-Layers and Lane-Based Positioning")
    print("="*70 + "\n")
    
    # Load data
    print("Loading topology data...")
    graphs = load_topology_data()
    
    if not graphs['combined'].nodes():
        print("❌ No topology data found!")
        print("   Run: python run_pipeline_nxos.py first")
        return
    
    print(f"  ✓ Loaded {len(graphs['combined'].nodes())} devices")
    print(f"  ✓ Loaded {len(graphs['combined'].edges())} connections\n")
    
    # Generate visualizations
    if USE_ENHANCED:
        parser = EnhancedHostnameParser()
        datacenters = parser.group_by_datacenter(list(graphs['combined'].nodes()))
        
        if len(datacenters) > 1:
            print(f"Found {len(datacenters)} datacenters")
            
            # Generate combined view
            print("\n--- Generating combined view ---")
            visualize_3d_topology_enhanced(graphs)
            
            # Generate per-datacenter views
            for dc in sorted(datacenters.keys()):
                if dc != 'unknown':
                    print(f"\n--- Generating {dc.upper()} datacenter view ---")
                    visualize_3d_topology_enhanced(graphs, datacenter=dc)
        else:
            # Single datacenter or no datacenter info
            visualize_3d_topology_enhanced(graphs)
    else:
        visualize_3d_topology_enhanced(graphs)
    
    print("\n" + "="*70)
    print("  ✅ Complete!")
    print("="*70)
    print("\n💡 Features:")
    print("   - Z-layers: Positions mapped to configurable heights")
    print("   - Lanes: -10 to +10 positioning within each layer")
    print("   - Icons: Device types shown with different symbols")
    print("   - HA Pairs: Automatically detected and highlighted")
    print()


if __name__ == '__main__':
    main()
