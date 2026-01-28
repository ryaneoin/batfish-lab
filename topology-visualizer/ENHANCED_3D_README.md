# Enhanced 3D Network Topology Visualization

## Overview

This enhanced 3D topology visualizer extends the original system with:

- **Configurable Z-Layers**: Map device POSITION codes to vertical layers (Z-axis)
- **Lane-Based Positioning**: Divide each Z-layer into lanes (-10 to +10) for organized horizontal placement
- **Icon-Based Device Types**: Different symbols and colors for device types (sr, sw, fw, lb)
- **HA Pair Detection**: Automatically identify and visualize high-availability pairs
- **Multi-Datacenter Support**: Generate separate visualizations per datacenter

## Hostname Format

The system parses hostnames in the format: `{DATACENTER}{POSITION}{TYPE}{COUNT}`

### Examples

```
npccosr01  = npc  + co  + sr + 01
             │      │     │    │
             │      │     │    └─ Counter (HA pairs differ here)
             │      │     └────── Type (icon/symbol)
             │      └──────────── Position (Z-layer & lane)
             └─────────────────── Datacenter (separate graphs)

wpcaccsw11 = wpc  + acc + sw + 11
ch2igwsr01 = ch2  + igw + sr + 01
```

### Component Values

**DATACENTER** (separate graph per datacenter):
- `npc` - North Production Cloud
- `wpc` - West Production Cloud
- `apc` - Asia Pacific Cloud
- `apd` - Asia Pacific DR
- `ukrc` - UK Regional Cloud
- `ukpc` - UK Production Cloud
- `ch2` - Chicago 2
- `va1` - Virginia 1
- `ma5` - Massachusetts 5
- `ld5` - London 5

**POSITION** (determines Z-layer and lane):
- `igw` - Internet Gateway (Z=5.0, Lane=0)
- `pub` - Public DMZ (Z=4.5, Lane=+2)
- `co` - Core (Z=3.5, Lane=0)
- `dc` - Data Center Core (Z=3.0, Lane=-2)
- `di` - Distribution (Z=2.5, Lane=0)
- `lb` - Load Balancer (Z=2.0, Lane=-3)
- `acc` - Access (Z=1.5, Lane=0)
- `wd` - Workstation Distribution (Z=1.0, Lane=-5)
- `prv` - Private (Z=0.5, Lane=+5)
- `csh` - Customer/Site Hub (Z=0.0, Lane=+8)

**TYPE** (determines icon/symbol):
- `sr` - Switch Router (red diamond)
- `sw` - Switch (teal square)
- `fw` - Firewall (yellow diamond-open) [optional]
- `lb` - Load Balancer (light teal circle) [optional]

**COUNT** (2 digits):
- Used for device numbering
- HA pairs share same datacenter+position+type but different counts
- Examples: 01, 02, 10, 11, etc.

## Architecture

### Files

```
topology-visualizer/
├── config.py                              # Configuration (Z-layers, lanes, icons)
├── generate_3d_topology_enhanced.py       # Enhanced 3D generator
├── parsers/
│   ├── enhanced_hostname_parser.py        # Enhanced hostname parser
│   └── hostname_parser.py                 # Original parser (backwards compat)
└── output/
    ├── topology_3d_enhanced.html          # Combined view
    └── topology_3d_enhanced_{dc}.html     # Per-datacenter views
```

### Configuration (`config.py`)

The configuration file defines:

1. **Z-Layer Mapping**: `POSITION_TO_Z_LAYER` dict
   ```python
   POSITION_TO_Z_LAYER = {
       'igw': 5.0,    # Highest layer
       'co': 3.5,     # Core layer
       'acc': 1.5,    # Access layer
       'csh': 0.0,    # Lowest layer
   }
   ```

2. **Lane Mapping**: `POSITION_TO_LANE` dict
   ```python
   POSITION_TO_LANE = {
       'igw': 0,      # Center lane
       'pub': 2,      # Right of center
       'dc': -2,      # Left of center
       'csh': 8,      # Far right
   }
   ```

3. **Icon Configuration**: `TYPE_TO_ICON` dict
   ```python
   TYPE_TO_ICON = {
       'sr': {
           'symbol': 'diamond',
           'size': 12,
           'color': '#FF6B6B',
           'description': 'Switch Router'
       }
   }
   ```

4. **HA Pair Settings**: Detection and visualization options
5. **Visualization Settings**: Colors, line styles, labels, etc.

## Usage

### Basic Usage

```bash
# Generate enhanced 3D visualization
python generate_3d_topology_enhanced.py

# Test the parser
python parsers/enhanced_hostname_parser.py

# Validate configuration
python config.py
```

### Output

The system generates:

1. **Combined View**: `output/topology_3d_enhanced.html`
   - All datacenters in one visualization
   
2. **Per-Datacenter Views**: `output/topology_3d_enhanced_{dc}.html`
   - Separate file for each datacenter (npc, wpc, etc.)

### Features in Visualization

- **Z-Layers**: Devices organized by vertical position based on POSITION code
- **Lanes**: Horizontal positioning (-10 to +10) within each layer
- **Icons**: Different shapes/colors for device types
- **HA Pairs**: 
  - Automatically detected (same DC+position+type, different count)
  - Connected with red dashed lines
  - Slightly offset for visibility
- **Link Types**:
  - Physical links: Gray solid lines
  - HSRP redundancy: Red dashed lines
  - BGP peering: Teal lines
  - HA pairs: Thin red dashed lines
- **Interactive**:
  - Drag to rotate
  - Scroll to zoom
  - Hover for device details

## Configuration Examples

### Adding a New Position

```python
# In config.py

# Add to Z-layer mapping
POSITION_TO_Z_LAYER['dmz'] = 4.0  # Between pub and co

# Add to lane mapping  
POSITION_TO_LANE['dmz'] = 3  # Right side

# Update position names (optional)
def get_position_display_name(position: str) -> str:
    position_names = {
        # ... existing ...
        'dmz': 'DMZ Zone',
    }
    return position_names.get(position, position.upper())
```

### Adding a New Device Type

```python
# In config.py

TYPE_TO_ICON['rtr'] = {
    'symbol': 'triangle-up',
    'size': 11,
    'color': '#9B59B6',
    'description': 'Router'
}
```

### Adjusting Lane Spacing

```python
# In config.py

LANE_WIDTH = 3.0  # Increase spacing between lanes (default: 2.0)
```

### Changing HA Pair Visualization

```python
# In config.py

HA_PAIR_DETECTION = False  # Disable HA pair detection
HA_PAIR_OFFSET = 0.5      # Increase offset distance (default: 0.3)
HA_PAIR_LINK_COLOR = '#00FF00'  # Change link color to green
```

## How It Works

### 1. Hostname Parsing

```python
parser = EnhancedHostnameParser()
parsed = parser.parse('npccosr01')

# Returns:
{
    'hostname': 'npccosr01',
    'datacenter': 'npc',
    'position': 'co',
    'type': 'sr',
    'counter': '01',
    'z_level': 3.5,
    'lane': 0,
    'lane_x': 0.0,
    'icon_config': {...},
    'valid': True
}
```

### 2. Layout Generation

1. **Group by Z-layer and lane**: Devices organized into (Z, lane) buckets
2. **Lane positioning**: X-axis = lane * LANE_WIDTH
3. **Y-axis spread**: Spring layout within each (Z, lane) group
4. **HA pair adjustment**: Pairs offset along Y-axis for visibility

### 3. Visualization

- **Nodes**: Positioned at (lane_x, y_spread, z_level)
- **Links**: Lines connecting nodes in 3D space
- **Symbols**: Plotly marker symbols based on device type
- **Colors**: From configuration

## Backwards Compatibility

The system maintains compatibility with the original `hostname_parser.py`:

```python
# Old parser still works
from hostname_parser import HostnameParser
parser = HostnameParser()
layer = parser.get_layer('npccosr01')  # Returns 'core'
```

The enhanced parser provides the `HostnameParser` alias:

```python
# Enhanced parser with HostnameParser alias
from enhanced_hostname_parser import HostnameParser
parser = HostnameParser()
parsed = parser.parse('npccosr01')  # Full enhanced parsing
```

## Testing

### Test Parser

```bash
python parsers/enhanced_hostname_parser.py
```

Output shows:
- Parsed hostname components
- Z-level and lane assignments
- HA pair detection
- Datacenter grouping

### Validate Configuration

```bash
python config.py
```

Checks for:
- Consistent Z-layer and lane mappings
- Valid lane ranges
- Configuration summary

## Troubleshooting

### Parser Not Recognizing Hostnames

1. Check datacenter code is in `DATACENTERS` list
2. Check position code is in `POSITION_TO_Z_LAYER` and `POSITION_TO_LANE`
3. Check type code is in `TYPE_TO_ICON` (or will use default)
4. Verify format: 2-4 char datacenter + 2-3 char position + 2 char type + 2 digit count

### Devices Not Positioning Correctly

1. Verify Z-layer values in `POSITION_TO_Z_LAYER`
2. Check lane assignments in `POSITION_TO_LANE`
3. Adjust `LANE_WIDTH` for spacing
4. Modify `Y_AXIS_SPREAD` for vertical distribution within lanes

### HA Pairs Not Detected

1. Ensure `HA_PAIR_DETECTION = True` in config
2. Verify devices have same datacenter+position+type but different counters
3. Check counters are 2-digit format (01, 02, not 1, 2)

### Visualization Issues

1. Check `output/` directory exists
2. Verify topology data files exist:
   - `cdp_topology.json`
   - `hsrp_topology.json` (optional)
   - `bgp_topology.json` (optional)
3. Run `python run_pipeline_nxos.py` to regenerate topology data

## Extending the System

### Add Custom Attributes

Extend the parser to extract additional hostname components:

```python
# In enhanced_hostname_parser.py

def parse(self, hostname: str) -> Dict:
    # ... existing parsing ...
    
    # Add custom attribute
    result['custom_attribute'] = extract_custom(hostname)
    
    return result
```

### Custom Layout Algorithms

Replace the lane-based layout with custom logic:

```python
# In generate_3d_topology_enhanced.py

def create_custom_layout(graph):
    pos_3d = {}
    
    for node in graph.nodes():
        # Your custom positioning logic
        x, y, z = calculate_position(node)
        pos_3d[node] = (x, y, z)
    
    return pos_3d
```

### Additional Visualizations

Create views with different filters or groupings:

```python
# Group by position instead of datacenter
positions = parser.group_by_attribute(nodes, 'position')
for pos, devices in positions.items():
    visualize_subset(devices, title=f"Position: {pos}")
```

## Performance Notes

- **Spring Layout**: Computationally expensive for large graphs
  - Adjust `SPRING_ITERATIONS` to balance quality vs. speed
  - Smaller `SPRING_K` = tighter clustering
  
- **Multiple Datacenters**: Separate visualizations reduce complexity
  - Consider generating only needed datacenter views
  
- **Large Networks**: 
  - Filter by datacenter or position
  - Reduce `Y_AXIS_SPREAD` to pack nodes tighter
  - Disable `SHOW_NODE_LABELS` for cleaner view

## Future Enhancements

Potential improvements:

1. **Dynamic Lane Width**: Auto-adjust based on device count per lane
2. **Subnet Grouping**: Visual containers for subnets within lanes
3. **Time-Based Views**: Animate topology changes over time
4. **Traffic Overlays**: Show bandwidth utilization on links
5. **Alert Integration**: Highlight devices with alerts/issues
6. **Export Formats**: SVG, PDF for documentation
7. **Web Interface**: Interactive configuration editor
8. **ServiceNow Integration**: Pull device metadata from CMDB

## License

Part of the batfish-lab project.
