# Enhanced 3D Topology - Quick Start Guide

## What's New

Your 3D topology visualizer now supports:

### 🎯 Key Features

1. **Z-Layers (Vertical Positioning)**
   - Configurable mapping: POSITION → Z-level
   - Example: `igw` devices at Z=5.0 (top), `csh` devices at Z=0.0 (bottom)

2. **Lanes (Horizontal Positioning)**  
   - Range: -10 (far left) to +10 (far right)
   - Configurable mapping: POSITION → lane number
   - Example: `co` (core) at lane 0 (center), `prv` at lane +5 (right side)

3. **Icon-Based Device Types**
   - Different symbols per type: sr=diamond, sw=square
   - Custom colors per type
   - Configurable size and style

4. **HA Pair Detection**
   - Automatic detection: same DC+position+type, different count
   - Visual highlighting with red dashed lines
   - Slight Y-axis offset for visibility

5. **Multi-Datacenter Support**
   - Separate graph per datacenter
   - Combined view + individual datacenter views

## File Structure

```
topology-visualizer/
├── config.py                              # ⚙️  Edit this for Z-layers, lanes, icons
├── generate_3d_topology_enhanced.py       # 🚀 Run this to generate visualizations
├── test_enhanced_system.py                # 🧪 Run this to test everything
├── ENHANCED_3D_README.md                  # 📖 Full documentation
└── parsers/
    └── enhanced_hostname_parser.py        # 🔍 Hostname parsing logic
```

## Quick Start

### 1. Test the System

```bash
cd /Users/eoin/projects/batfish-lab/topology-visualizer
python test_enhanced_system.py
```

This will:
- ✓ Validate configuration
- ✓ Test hostname parsing  
- ✓ Check for topology data files
- ✓ Show what's configured

### 2. Generate Visualizations

```bash
python generate_3d_topology_enhanced.py
```

This will create:
- `output/topology_3d_enhanced.html` - Combined view (all datacenters)
- `output/topology_3d_enhanced_npc.html` - NPC datacenter only
- `output/topology_3d_enhanced_wpc.html` - WPC datacenter only
- etc. (one per datacenter found)

### 3. View in Browser

```bash
open output/topology_3d_enhanced.html
# or
open output/topology_3d_enhanced_npc.html
```

## Configuration Examples

### Change Z-Layer for a Position

Edit `config.py`:

```python
POSITION_TO_Z_LAYER = {
    # ...
    'co': 4.0,    # Move core layer higher (was 3.5)
    # ...
}
```

### Change Lane Assignment

Edit `config.py`:

```python
POSITION_TO_LANE = {
    # ...
    'acc': -3,    # Move access layer to left (was 0)
    # ...
}
```

### Add New Position Type

Edit `config.py`:

```python
# Add to Z-layer mapping
POSITION_TO_Z_LAYER['dmz'] = 4.25  # Between pub and co

# Add to lane mapping
POSITION_TO_LANE['dmz'] = 3  # Right side

# Add display name (in get_position_display_name function)
position_names = {
    # ... existing ...
    'dmz': 'DMZ Zone',
}
```

### Add New Device Type

Edit `config.py`:

```python
TYPE_TO_ICON['rtr'] = {
    'symbol': 'triangle-up',   # Plotly symbol name
    'size': 11,
    'color': '#9B59B6',        # Purple
    'description': 'Router'
}
```

## Hostname Format

Your hostnames must match: `{DATACENTER}{POSITION}{TYPE}{COUNT}`

Examples:
```
npccosr01  → npc (DC) + co (pos) + sr (type) + 01 (count)
wpcaccsw11 → wpc (DC) + acc (pos) + sw (type) + 11 (count)
ch2igwsr01 → ch2 (DC) + igw (pos) + sr (type) + 01 (count)
```

Configured values (edit `config.py` to modify):

**Datacenters**: npc, wpc, apc, apd, ukrc, ukpc, ch2, va1, ma5, ld5

**Positions** (with default Z-layers and lanes):
- igw: Z=5.0, Lane=0 (Internet Gateway)
- pub: Z=4.5, Lane=+2 (Public DMZ)
- co: Z=3.5, Lane=0 (Core)
- dc: Z=3.0, Lane=-2 (DC Core)
- di: Z=2.5, Lane=0 (Distribution)
- lb: Z=2.0, Lane=-3 (Load Balancer)
- acc: Z=1.5, Lane=0 (Access)
- wd: Z=1.0, Lane=-5 (Workstation Distribution)
- prv: Z=0.5, Lane=+5 (Private)
- csh: Z=0.0, Lane=+8 (Customer Hub)

**Types**: sr, sw (expand in config.py)

## Testing Individual Components

### Test Parser Only

```bash
cd parsers
python enhanced_hostname_parser.py
```

Shows how each test hostname is parsed.

### Test Configuration Only

```bash
python config.py
```

Validates configuration for errors and shows summary.

## Visualization Features

When you open the HTML file:

- **Drag**: Rotate the 3D view
- **Scroll**: Zoom in/out
- **Hover**: See device details (DC, position, type, Z-layer, lane)
- **Legend**: Toggle link types on/off

Visual elements:
- **Devices**: Positioned by (lane_x, y_spread, z_level)
- **Physical Links**: Gray solid lines
- **HSRP Links**: Red dashed thick lines
- **BGP Links**: Teal solid lines
- **HA Pairs**: Thin red dashed lines

## Common Adjustments

### Make Lanes Wider Apart

```python
# In config.py
LANE_WIDTH = 3.0  # Default: 2.0
```

### Change HA Pair Offset

```python
# In config.py
HA_PAIR_OFFSET = 0.5  # Default: 0.3
```

### Disable HA Pair Detection

```python
# In config.py
HA_PAIR_DETECTION = False
```

### Change Link Colors

```python
# In config.py
LINK_STYLES = {
    'physical': {
        'color': '#0000FF',  # Blue instead of gray
        'width': 3,
        'dash': 'solid'
    },
    # ...
}
```

### Hide Node Labels

```python
# In config.py
SHOW_NODE_LABELS = False
```

## Backwards Compatibility

The original `generate_3d_topology.py` and `hostname_parser.py` are unchanged and still work.

The new enhanced system adds:
- `generate_3d_topology_enhanced.py` - New generator
- `enhanced_hostname_parser.py` - New parser
- `config.py` - Centralized configuration

Both systems can coexist.

## Troubleshooting

### "No topology data found"

Run the pipeline first:
```bash
python run_pipeline_nxos.py
```

### Hostname not parsing

1. Check it matches format: `{DC}{POSITION}{TYPE}{COUNT}`
2. Verify DC is in `DATACENTERS` list
3. Verify POSITION is in `POSITION_TO_Z_LAYER` dict
4. Verify TYPE is in `TYPE_TO_ICON` dict (or will use default)

### Devices bunched together

Increase lane width:
```python
LANE_WIDTH = 4.0  # In config.py
```

Or increase Y-axis spread:
```python
Y_AXIS_SPREAD = 5.0  # In config.py
```

### HA pairs not detected

1. Check `HA_PAIR_DETECTION = True`
2. Verify pairs have same DC+position+type but different count
3. Ensure count is 2 digits (01, 02 not 1, 2)

## Next Steps

1. **Run test suite**: `python test_enhanced_system.py`
2. **Generate viz**: `python generate_3d_topology_enhanced.py`
3. **View in browser**: Open the HTML files
4. **Customize**: Edit `config.py` as needed
5. **Read full docs**: See `ENHANCED_3D_README.md`

## Summary of Changes

| Aspect | Before | After |
|--------|--------|-------|
| Z-layers | Fixed (4 levels) | Configurable (10 positions) |
| X-positioning | Spring layout | Lane-based (-10 to +10) |
| Icons | All circles | Type-specific symbols |
| HA pairs | Manual | Auto-detected |
| Datacenters | Single view | Per-DC + combined views |
| Configuration | Hardcoded | Centralized in config.py |

## Questions?

- Full docs: `ENHANCED_3D_README.md`
- Test all: `python test_enhanced_system.py`
- Parser test: `python parsers/enhanced_hostname_parser.py`
- Config test: `python config.py`
