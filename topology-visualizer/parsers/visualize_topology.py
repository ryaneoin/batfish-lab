#!/usr/bin/env python3
"""
Network Topology Visualizer - Combine CDP, HSRP, BGP data into NetworkX graphs
Generate interactive visualizations for audit documentation
"""

import json
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, List, Tuple
import pandas as pd
from pathlib import Path


class NetworkTopologyVisualizer:
    """Create comprehensive network topology visualizations"""
    
    def __init__(self):
        self.physical_graph = nx.Graph()
        self.hsrp_graph = nx.Graph()
        self.bgp_graph = nx.DiGraph()  # Directed for BGP
        self.combined_graph = nx.MultiGraph()
        
    def load_cdp_topology(self, cdp_file: str):
        """Load physical topology from CDP data"""
        with open(cdp_file, 'r') as f:
            data = json.load(f)
        
        # Add nodes with metadata
        for node in data['nodes']:
            self.physical_graph.add_node(
                node['name'],
                node_type=node['type']
            )
            self.combined_graph.add_node(
                node['name'],
                node_type=node['type']
            )
        
        # Add edges
        for edge in data['edges']:
            self.physical_graph.add_edge(
                edge['source'],
                edge['target'],
                link_type='physical',
                source_intf=edge.get('source_interface', ''),
                target_intf=edge.get('target_interface', '')
            )
            self.combined_graph.add_edge(
                edge['source'],
                edge['target'],
                link_type='physical',
                source_intf=edge.get('source_interface', ''),
                target_intf=edge.get('target_interface', ''),
                key='physical'
            )
        
        print(f"✓ Loaded CDP topology: {len(data['nodes'])} nodes, {len(data['edges'])} links")
    
    def load_hsrp_topology(self, hsrp_file: str):
        """Load HSRP redundancy relationships"""
        with open(hsrp_file, 'r') as f:
            data = json.load(f)
        
        # Add HSRP edges
        for edge in data['edges']:
            self.hsrp_graph.add_edge(
                edge['source'],
                edge['target'],
                link_type='hsrp',
                virtual_ip=edge.get('virtual_ip'),
                group=edge.get('group')
            )
            self.combined_graph.add_edge(
                edge['source'],
                edge['target'],
                link_type='hsrp',
                virtual_ip=edge.get('virtual_ip'),
                group=edge.get('group'),
                key='hsrp'
            )
        
        print(f"✓ Loaded HSRP topology: {len(data['edges'])} redundancy pairs")
    
    def load_bgp_topology(self, bgp_file: str):
        """Load BGP peering relationships"""
        with open(bgp_file, 'r') as f:
            data = json.load(f)
        
        # Add BGP edges
        for edge in data['edges']:
            self.bgp_graph.add_edge(
                edge['source'],
                edge['target'],
                link_type='bgp',
                peering_type=edge.get('peering_type'),
                local_as=edge.get('local_as'),
                remote_as=edge.get('remote_as')
            )
            self.combined_graph.add_edge(
                edge['source'],
                edge['target'],
                link_type='bgp',
                peering_type=edge.get('peering_type'),
                key='bgp'
            )
        
        print(f"✓ Loaded BGP topology: {len(data['edges'])} peerings")
    
    def create_physical_layout(self, graph: nx.Graph) -> Dict:
        """Create hierarchical layout for physical topology"""
        layers = {
            'router': 0,
            'core': 1,
            'distribution': 2,
            'access': 3,
            'unknown': 4
        }
        
        pos = {}
        layer_counts = {layer: 0 for layer in layers.values()}
        
        for node in graph.nodes():
            node_type = graph.nodes[node].get('node_type', 'unknown')
            layer = layers.get(node_type, 4)
            
            x = layer_counts[layer] * 2
            y = -layer * 2
            
            pos[node] = (x, y)
            layer_counts[layer] += 1
        
        return pos
    
    def visualize_physical_topology(self, output_file: str):
        """Create interactive physical topology visualization"""
        pos = self.create_physical_layout(self.physical_graph)
        
        edge_trace = []
        for edge in self.physical_graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_trace.append(
                go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=2, color='#888'),
                    hoverinfo='none',
                    showlegend=False
                )
            )
        
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        color_map = {
            'router': '#FF6B6B',
            'core': '#4ECDC4',
            'distribution': '#95E1D3',
            'access': '#F38181',
            'unknown': '#AAAAAA'
        }
        
        for node in self.physical_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            node_type = self.physical_graph.nodes[node].get('node_type', 'unknown')
            node_color.append(color_map.get(node_type, '#AAAAAA'))
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            marker=dict(
                size=20,
                color=node_color,
                line=dict(width=2, color='white')
            ),
            hoverinfo='text',
            showlegend=False
        )
        
        fig = go.Figure(data=edge_trace + [node_trace])
        
        fig.update_layout(
            title='Physical Network Topology (CDP)',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        fig.write_html(output_file)
        print(f"✓ Physical topology visualization saved to {output_file}")
    
    def visualize_hsrp_topology(self, output_file: str):
        """Create HSRP redundancy visualization"""
        pos = nx.spring_layout(self.hsrp_graph, k=2, iterations=50)
        
        edge_trace = []
        for edge in self.hsrp_graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_trace.append(
                go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=3, color='#FF6B6B', dash='dash'),
                    hoverinfo='text',
                    hovertext=f"HSRP Group {edge[2].get('group', 'N/A')}<br>VIP: {edge[2].get('virtual_ip', 'N/A')}",
                    showlegend=False
                )
            )
        
        node_x = []
        node_y = []
        node_text = []
        
        for node in self.hsrp_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            marker=dict(
                size=25,
                color='#4ECDC4',
                line=dict(width=2, color='white')
            ),
            hoverinfo='text',
            showlegend=False
        )
        
        fig = go.Figure(data=edge_trace + [node_trace])
        
        fig.update_layout(
            title='HSRP Redundancy Groups',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        fig.write_html(output_file)
        print(f"✓ HSRP topology visualization saved to {output_file}")
    
    def visualize_bgp_topology(self, output_file: str):
        """Create BGP peering visualization"""
        pos = nx.circular_layout(self.bgp_graph)
        
        ebgp_edges = [(u, v) for u, v, d in self.bgp_graph.edges(data=True) 
                      if d.get('peering_type') == 'eBGP']
        ibgp_edges = [(u, v) for u, v, d in self.bgp_graph.edges(data=True) 
                      if d.get('peering_type') == 'iBGP']
        
        edge_traces = []
        
        for edge in ebgp_edges:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_traces.append(
                go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=2, color='#FF6B6B'),
                    name='eBGP',
                    showlegend=False,
                    hoverinfo='text',
                    hovertext='eBGP Peering'
                )
            )
        
        for edge in ibgp_edges:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            
            edge_traces.append(
                go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    mode='lines',
                    line=dict(width=2, color='#4ECDC4'),
                    name='iBGP',
                    showlegend=False,
                    hoverinfo='text',
                    hovertext='iBGP Peering'
                )
            )
        
        node_x = []
        node_y = []
        node_text = []
        
        for node in self.bgp_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            marker=dict(
                size=25,
                color='#95E1D3',
                line=dict(width=2, color='white')
            ),
            hoverinfo='text',
            showlegend=False
        )
        
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title='BGP Peering Topology',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        fig.write_html(output_file)
        print(f"✓ BGP topology visualization saved to {output_file}")
    
    def visualize_combined_topology(self, output_file: str):
        """Create combined multi-layer topology visualization"""
        pos = nx.spring_layout(self.combined_graph, k=3, iterations=100)
        
        edge_traces = []
        
        for u, v, key, data in self.combined_graph.edges(data=True, keys=True):
            if data.get('link_type') == 'physical':
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                
                edge_traces.append(
                    go.Scatter(
                        x=[x0, x1, None],
                        y=[y0, y1, None],
                        mode='lines',
                        line=dict(width=1, color='#CCCCCC'),
                        showlegend=False,
                        hoverinfo='text',
                        hovertext=f"Physical: {data.get('source_intf', '')} ↔ {data.get('target_intf', '')}"
                    )
                )
        
        for u, v, key, data in self.combined_graph.edges(data=True, keys=True):
            if data.get('link_type') == 'hsrp':
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                
                edge_traces.append(
                    go.Scatter(
                        x=[x0, x1, None],
                        y=[y0, y1, None],
                        mode='lines',
                        line=dict(width=3, color='#FF6B6B', dash='dash'),
                        showlegend=False,
                        hoverinfo='text',
                        hovertext=f"HSRP: Group {data.get('group', 'N/A')}"
                    )
                )
        
        for u, v, key, data in self.combined_graph.edges(data=True, keys=True):
            if data.get('link_type') == 'bgp':
                x0, y0 = pos[u]
                x1, y1 = pos[v]
                
                edge_traces.append(
                    go.Scatter(
                        x=[x0, x1, None],
                        y=[y0, y1, None],
                        mode='lines',
                        line=dict(width=2, color='#4ECDC4'),
                        showlegend=False,
                        hoverinfo='text',
                        hovertext=f"BGP: {data.get('peering_type', 'N/A')}"
                    )
                )
        
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        color_map = {
            'router': '#FF6B6B',
            'core': '#4ECDC4',
            'distribution': '#95E1D3',
            'access': '#F38181',
            'unknown': '#AAAAAA'
        }
        
        for node in self.combined_graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
            node_type = self.combined_graph.nodes[node].get('node_type', 'unknown')
            node_color.append(color_map.get(node_type, '#AAAAAA'))
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            text=node_text,
            textposition='top center',
            marker=dict(
                size=25,
                color=node_color,
                line=dict(width=2, color='white')
            ),
            hoverinfo='text',
            showlegend=False
        )
        
        fig = go.Figure(data=edge_traces + [node_trace])
        
        fig.update_layout(
            title='Combined Network Topology (Physical + HSRP + BGP)',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=0, l=0, r=0, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        fig.write_html(output_file)
        print(f"✓ Combined topology visualization saved to {output_file}")
    
    def generate_topology_summary(self, output_file: str):
        """Generate summary statistics for auditors"""
        summary = {
            'Physical Topology': {
                'Devices': len(self.physical_graph.nodes()),
                'Physical Links': len(self.physical_graph.edges()),
                'Device Types': {}
            },
            'Redundancy (HSRP)': {
                'HSRP Pairs': len(self.hsrp_graph.edges()),
                'Devices with HSRP': len(self.hsrp_graph.nodes())
            },
            'BGP Routing': {
                'BGP Speakers': len(self.bgp_graph.nodes()),
                'BGP Peerings': len(self.bgp_graph.edges()),
                'eBGP Peerings': sum(1 for _, _, d in self.bgp_graph.edges(data=True) 
                                    if d.get('peering_type') == 'eBGP'),
                'iBGP Peerings': sum(1 for _, _, d in self.bgp_graph.edges(data=True) 
                                    if d.get('peering_type') == 'iBGP')
            }
        }
        
        for node in self.physical_graph.nodes():
            node_type = self.physical_graph.nodes[node].get('node_type', 'unknown')
            summary['Physical Topology']['Device Types'][node_type] = \
                summary['Physical Topology']['Device Types'].get(node_type, 0) + 1
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✓ Topology summary saved to {output_file}")
        
        print("\n📊 Network Topology Summary:")
        print(f"   Total Devices: {summary['Physical Topology']['Devices']}")
        print(f"   Physical Links: {summary['Physical Topology']['Physical Links']}")
        print(f"   HSRP Redundancy Pairs: {summary['Redundancy (HSRP)']['HSRP Pairs']}")
        print(f"   BGP Peerings: {summary['BGP Routing']['BGP Peerings']} "
              f"({summary['BGP Routing']['eBGP Peerings']} eBGP, "
              f"{summary['BGP Routing']['iBGP Peerings']} iBGP)")
