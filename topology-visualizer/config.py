#!/usr/bin/env python3
"""
Configuration for Enhanced 3D Network Topology Visualization
Defines Z-layers, lanes, icons, and datacenter mappings
"""

from typing import Dict, List, Tuple

# =============================================================================
# DATACENTER DEFINITIONS
# =============================================================================

# Valid datacenters - each will get its own 3D graph
DATACENTERS = [
    'npc',   # North Production Cloud
    'wpc',   # West Production Cloud  
    'apc',   # Asia Pacific Cloud
    'apd',   # Asia Pacific Disaster Recovery
    'ukrc',  # UK Regional Cloud
    'ukpc',  # UK Production Cloud
    'ch2',   # Chicago 2
    'va1',   # Virginia 1
    'ma5',   # Massachusetts 5
    'ld5'    # London 5
]


# =============================================================================
# POSITION TO Z-LAYER MAPPING
# =============================================================================

# Position codes that map to Z-layers in the 3D visualization
# Higher Z values appear higher in the 3D space

POSITION_TO_Z_LAYER: Dict[str, float] = {
    # Edge/Internet Layer (Z = 5.0)
    'igw': 5.0,    # Internet Gateway
    'pub': 4.5,    # Public DMZ
    
    # Core Layer (Z = 3.0-4.0)
    'co': 3.5,     # Core
    'dc': 3.0,     # Data Center Core
    
    # Distribution Layer (Z = 2.0-2.5)
    'di': 2.5,     # Distribution
    'lb': 2.0,     # Load Balancer
    
    # Access Layer (Z = 0.5-1.5)
    'acc': 1.5,    # Access
    'wd': 1.0,     # Workstation Distribution
    'prv': 0.5,    # Private/Access
    'csh': 0.0,    # Customer/Site Hub
}


# =============================================================================
# POSITION TO LANE MAPPING
# =============================================================================

# Lane assignment for X-axis positioning within each Z-layer
# Lanes range from -10 to +10, with 0 being center

POSITION_TO_LANE: Dict[str, int] = {
    # Internet/Edge devices spread across lanes
    'igw': 0,      # Internet Gateway - center
    'pub': 2,      # Public DMZ - right of center
    
    # Core devices
    'co': 0,       # Core - center
    'dc': -2,      # Data Center Core - left of center
    
    # Distribution layer
    'di': 0,       # Distribution - center
    'lb': -3,      # Load Balancer - left
    
    # Access layer
    'acc': 0,      # Access - center
    'wd': -5,      # Workstation Distribution - far left
    'prv': 5,      # Private - far right
    'csh': 8,      # Customer Hub - far right
}


# Lane spacing configuration
LANE_WIDTH = 2.0           # Units between lanes
LANE_MIN = -10             # Minimum lane number
LANE_MAX = 10              # Maximum lane number


# =============================================================================
# TYPE TO ICON/SYMBOL MAPPING
# =============================================================================

# Device type codes and their visual representation
TYPE_TO_ICON: Dict[str, Dict[str, any]] = {
    'sr': {
        'symbol': 'diamond',
        'size': 12,
        'color': '#FF6B6B',     # Red
        'description': 'Switch Router'
    },
    'sw': {
        'symbol': 'square',
        'size': 10,
        'color': '#4ECDC4',     # Teal
        'description': 'Switch'
    },
    'fw': {
        'symbol': 'diamond-open',
        'size': 14,
        'color': '#FFD93D',     # Yellow
        'description': 'Firewall'
    },
    'lb': {
        'symbol': 'circle',
        'size': 11,
        'color': '#95E1D3',     # Light teal
        'description': 'Load Balancer'
    }
}

# Default icon for unknown types
DEFAULT_ICON = {
    'symbol': 'circle',
    'size': 8,
    'color': '#AAAAAA',
    'description': 'Unknown Device'
}


# =============================================================================
# HIGH AVAILABILITY (HA) PAIR CONFIGURATION
# =============================================================================

# HA pairs are identified by matching datacenter+position+type with different counts
# e.g., npccosr01 and npccosr02 are an HA pair

HA_PAIR_DETECTION = True    # Enable HA pair detection
HA_PAIR_OFFSET = 0.3        # Offset distance for HA pair visualization
HA_PAIR_LINK_COLOR = '#FF6B6B'
HA_PAIR_LINK_WIDTH = 2
HA_PAIR_LINK_DASH = 'dash'


# =============================================================================
# VISUALIZATION SETTINGS
# =============================================================================

# Grid and layer settings
SHOW_Z_GRID = True          # Show horizontal grid lines at each Z layer
SHOW_LANE_GUIDES = True     # Show vertical lane guide lines
GRID_COLOR = '#E0E0E0'
LANE_GUIDE_COLOR = '#F0F0F0'

# Node label settings
SHOW_NODE_LABELS = True
NODE_LABEL_SIZE = 8

# Link type colors and styles
LINK_STYLES = {
    'physical': {
        'color': '#CCCCCC',
        'width': 2,
        'dash': 'solid'
    },
    'hsrp': {
        'color': '#FF6B6B',
        'width': 4,
        'dash': 'dash'
    },
    'bgp': {
        'color': '#4ECDC4',
        'width': 3,
        'dash': 'solid'
    }
}


# =============================================================================
# SPRING LAYOUT CONFIGURATION
# =============================================================================

# Spring layout parameters for positioning within each layer
SPRING_K = 2.0              # Optimal distance between nodes
SPRING_ITERATIONS = 100     # Number of iterations for layout algorithm
SPRING_SEED = 42            # Random seed for reproducibility

# Y-axis spread factor (how much to spread nodes along Y axis)
Y_AXIS_SPREAD = 3.0


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_z_layer(position: str) -> float:
    """Get Z-layer value for a position"""
    return POSITION_TO_Z_LAYER.get(position, 1.5)  # Default to middle


def get_lane(position: str) -> int:
    """Get lane number for a position"""
    lane = POSITION_TO_LANE.get(position, 0)  # Default to center
    return max(LANE_MIN, min(LANE_MAX, lane))  # Clamp to valid range


def get_icon_config(device_type: str) -> Dict:
    """Get icon configuration for a device type"""
    return TYPE_TO_ICON.get(device_type, DEFAULT_ICON)


def get_lane_x_position(lane: int) -> float:
    """Convert lane number to X-axis position"""
    return lane * LANE_WIDTH


def are_ha_pair(device1: Dict, device2: Dict) -> bool:
    """
    Determine if two devices form an HA pair
    
    Args:
        device1, device2: Parsed hostname dictionaries
        
    Returns:
        True if devices are an HA pair
    """
    if not (device1['valid'] and device2['valid']):
        return False
        
    return (device1['datacenter'] == device2['datacenter'] and
            device1['position'] == device2['position'] and
            device1['type'] == device2['type'] and
            device1['counter'] != device2['counter'])


def get_position_display_name(position: str) -> str:
    """Get human-readable name for position code"""
    position_names = {
        'igw': 'Internet Gateway',
        'pub': 'Public DMZ',
        'co': 'Core',
        'dc': 'Data Center Core',
        'di': 'Distribution',
        'lb': 'Load Balancer',
        'acc': 'Access',
        'wd': 'Workstation Distribution',
        'prv': 'Private',
        'csh': 'Customer Hub'
    }
    return position_names.get(position, position.upper())


# =============================================================================
# VALIDATION
# =============================================================================

def validate_config():
    """Validate configuration for consistency"""
    errors = []
    
    # Check that all positions have both Z-layer and lane assignments
    z_positions = set(POSITION_TO_Z_LAYER.keys())
    lane_positions = set(POSITION_TO_LANE.keys())
    
    if z_positions != lane_positions:
        missing_z = lane_positions - z_positions
        missing_lane = z_positions - lane_positions
        
        if missing_z:
            errors.append(f"Positions missing Z-layer: {missing_z}")
        if missing_lane:
            errors.append(f"Positions missing lane assignment: {missing_lane}")
    
    # Check lane ranges
    for pos, lane in POSITION_TO_LANE.items():
        if not (LANE_MIN <= lane <= LANE_MAX):
            errors.append(f"Position '{pos}' lane {lane} out of range [{LANE_MIN}, {LANE_MAX}]")
    
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  ❌ {error}")
        return False
    
    return True


if __name__ == '__main__':
    # Validate configuration when run directly
    print("Validating topology configuration...")
    if validate_config():
        print("✅ Configuration valid")
        print(f"\n📊 Configuration Summary:")
        print(f"  Datacenters: {len(DATACENTERS)}")
        print(f"  Positions: {len(POSITION_TO_Z_LAYER)}")
        print(f"  Z-layers: {len(set(POSITION_TO_Z_LAYER.values()))}")
        print(f"  Device types: {len(TYPE_TO_ICON)}")
        print(f"  Lane range: {LANE_MIN} to {LANE_MAX}")
    else:
        print("❌ Configuration has errors")
