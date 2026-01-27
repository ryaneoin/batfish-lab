# Network Device Configuration Collector

Python script using Netmiko to collect running configurations and show command outputs from network devices.

## Features

- Connects to multiple devices from YAML inventory
- Collects running configurations
- Gathers topology information (CDP, LLDP, HSRP, VRRP)
- Collects routing protocol data (BGP, OSPF, EIGRP)
- Captures interface and security information
- Supports multiple Cisco platforms (IOS, IOS-XE, NX-OS)
- Organized output directory structure
- Comprehensive logging

## Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements-collector.txt
```

## Configuration

1. Create your inventory file:
```bash
cp inventory.yaml.example inventory.yaml
```

2. Edit `inventory.yaml` with your device details:
```yaml
devices:
  - hostname: core-sw-01
    host: 192.168.1.10
    device_type: cisco_ios
    username: admin
    password: ${NET_PASSWORD}
    secret: ${NET_SECRET}
```

3. Set credentials via environment variables (recommended):
```bash
export NET_USERNAME=admin
export NET_PASSWORD=your_password
export NET_SECRET=your_enable_password
```

Alternatively, use SSH keys:
```yaml
  - hostname: device-01
    host: 192.168.1.10
    device_type: cisco_ios
    username: admin
    use_keys: true
    key_file: ~/.ssh/id_rsa
```

## Usage

Run the collection:
```bash
python collect_device_outputs.py
```

Generate sample inventory (first time):
```bash
python collect_device_outputs.py --create-inventory
```

## Output Structure

```
configs/
├── running-configs/
│   ├── core-sw-01_running-config.txt
│   ├── core-sw-02_running-config.txt
│   └── ...
└── show-outputs/
    └── 20260126_143022/
        ├── topology/
        │   ├── core-sw-01_show_cdp_neighbors_detail.txt
        │   └── ...
        ├── routing/
        │   ├── core-sw-01_show_ip_bgp_summary.txt
        │   └── ...
        ├── interfaces/
        ├── security/
        └── inventory/
```

## Show Commands Collected

### Topology
- CDP/LLDP neighbors
- HSRP/VRRP status

### Routing
- Routing tables
- BGP summary and neighbors
- OSPF/EIGRP neighbors

### Interfaces
- Interface brief
- Interface descriptions
- Interface status

### Security
- Access lists
- User accounts
- VTY line configuration

### Inventory
- Version information
- Hardware inventory
- Module information

## Integration with Batfish

The collected configurations can be used directly with your Batfish analysis:

```bash
# Copy configs to Batfish snapshot
cp configs/running-configs/*.txt snapshot/configs/

# Run Batfish analysis
cd batfish-analyzer
python analyze_network.py
```

## Logging

- Console output: Real-time progress
- File logging: `collection.log`
- Per-device session logs: `netmiko_<hostname>.log`

## Supported Device Types

- cisco_ios
- cisco_xe  
- cisco_nxos
- cisco_xr
- cisco_asa
- arista_eos
- juniper_junos
- Many others (see Netmiko documentation)

## Troubleshooting

### Connection Timeout
- Verify device IP/hostname is reachable
- Check firewall rules
- Increase timeout in inventory.yaml

### Authentication Failed
- Verify username/password
- Check enable secret
- Ensure SSH is enabled on devices

### Command Failures
- Some commands may not be available on all platforms
- Check device logs for specific errors
- Review per-device session logs

## PCI-DSS Compliance

This collector gathers information useful for PCI-DSS compliance audits:
- Running configurations for baseline comparison
- Access control lists
- Authentication configuration
- Interface security settings

Outputs are timestamped for audit trail purposes.
