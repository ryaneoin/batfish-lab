#!/usr/bin/env python3
"""
Network Device Configuration and Show Output Collector
Connects to network devices via SSH using Netmiko and collects:
- Running configurations
- Show command outputs for topology analysis (CDP, LLDP, HSRP, VRRP, BGP)
- Compliance-relevant outputs (interfaces, ACLs, authentication)
"""

import os
import sys
import yaml
from datetime import datetime
from pathlib import Path
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DeviceCollector:
    """Collect configuration and show outputs from network devices"""
    
    def __init__(self, inventory_file='inventory.yaml', output_dir='configs'):
        self.inventory_file = inventory_file
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create output directories
        self.config_dir = self.output_dir / 'running-configs'
        self.show_dir = self.output_dir / 'show-outputs' / self.timestamp
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.show_dir.mkdir(parents=True, exist_ok=True)
        
        # Load inventory
        self.devices = self._load_inventory()
    
    def _load_inventory(self):
        """Load device inventory from YAML file"""
        try:
            with open(self.inventory_file, 'r') as f:
                inventory = yaml.safe_load(f)
            logger.info(f"Loaded {len(inventory.get('devices', []))} devices from inventory")
            return inventory.get('devices', [])
        except FileNotFoundError:
            logger.error(f"Inventory file {self.inventory_file} not found")
            sys.exit(1)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing inventory file: {e}")
            sys.exit(1)
    
    def _connect_to_device(self, device_params):
        """Establish SSH connection to device"""
        try:
            connection = ConnectHandler(**device_params)
            logger.info(f"Connected to {device_params['host']}")
            return connection
        except NetmikoTimeoutException:
            logger.error(f"Timeout connecting to {device_params['host']}")
            return None
        except NetmikoAuthenticationException:
            logger.error(f"Authentication failed for {device_params['host']}")
            return None
        except Exception as e:
            logger.error(f"Error connecting to {device_params['host']}: {str(e)}")
            return None
    
    def _save_output(self, hostname, output, filename, subdir=None):
        """Save command output to file"""
        if subdir:
            save_dir = self.show_dir / subdir
            save_dir.mkdir(exist_ok=True)
        else:
            save_dir = self.config_dir
        
        filepath = save_dir / f"{hostname}_{filename}"
        with open(filepath, 'w') as f:
            f.write(output)
        logger.info(f"Saved {filepath}")
    
    def collect_running_config(self, connection, hostname):
        """Collect running configuration"""
        try:
            logger.info(f"Collecting running-config from {hostname}")
            config = connection.send_command('show running-config')
            self._save_output(hostname, config, 'running-config.txt')
            return True
        except Exception as e:
            logger.error(f"Error collecting config from {hostname}: {str(e)}")
            return False
    
    def collect_show_outputs(self, connection, hostname, device_type):
        """Collect various show command outputs"""
        
        # Define show commands based on device type
        if 'cisco_ios' in device_type or 'cisco_xe' in device_type:
            show_commands = {
                'topology': [
                    'show cdp neighbors detail',
                    'show lldp neighbors detail',
                    'show standby brief',
                    'show vrrp brief',
                ],
                'routing': [
                    'show ip route',
                    'show ip bgp summary',
                    'show ip bgp neighbors',
                    'show ip ospf neighbor',
                    'show ip eigrp neighbors',
                ],
                'interfaces': [
                    'show ip interface brief',
                    'show interfaces description',
                    'show interfaces status',
                ],
                'security': [
                    'show ip access-lists',
                    'show running-config | include username',
                    'show running-config | section line vty',
                ],
                'inventory': [
                    'show version',
                    'show inventory',
                    'show module',
                ]
            }
        elif 'cisco_nxos' in device_type:
            show_commands = {
                'topology': [
                    'show cdp neighbors detail',
                    'show lldp neighbors detail',
                    'show hsrp brief',
                    'show vrrp brief',
                ],
                'routing': [
                    'show ip route',
                    'show ip bgp summary',
                    'show ip bgp neighbors',
                    'show ip ospf neighbors',
                ],
                'interfaces': [
                    'show ip interface brief',
                    'show interface description',
                    'show interface status',
                ],
                'security': [
                    'show ip access-lists',
                ],
                'inventory': [
                    'show version',
                    'show inventory',
                    'show module',
                ]
            }
        else:
            logger.warning(f"Unknown device type {device_type}, using minimal command set")
            show_commands = {
                'basic': [
                    'show version',
                    'show ip interface brief',
                ]
            }
        
        # Collect outputs
        results = {}
        for category, commands in show_commands.items():
            logger.info(f"Collecting {category} outputs from {hostname}")
            for command in commands:
                try:
                    output = connection.send_command(command, delay_factor=2)
                    # Create safe filename from command
                    filename = command.replace(' ', '_').replace('|', '_pipe_') + '.txt'
                    self._save_output(hostname, output, filename, subdir=category)
                    results[command] = 'success'
                except Exception as e:
                    logger.error(f"Error running '{command}' on {hostname}: {str(e)}")
                    results[command] = f'failed: {str(e)}'
        
        return results
    
    def process_device(self, device):
        """Process a single device - collect config and show outputs"""
        hostname = device.get('hostname', device.get('host', 'unknown'))
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing device: {hostname}")
        logger.info(f"{'='*60}")
        
        # Prepare connection parameters
        device_params = {
            'device_type': device.get('device_type', 'cisco_ios'),
            'host': device['host'],
            'username': device.get('username', os.environ.get('NET_USERNAME')),
            'password': device.get('password', os.environ.get('NET_PASSWORD')),
            'secret': device.get('secret', os.environ.get('NET_SECRET', '')),
            'port': device.get('port', 22),
            'timeout': device.get('timeout', 30),
            'session_log': f'netmiko_{hostname}.log',
        }
        
        # Handle key-based authentication if specified
        if device.get('use_keys'):
            device_params['use_keys'] = True
            device_params['key_file'] = device.get('key_file')
        
        # Connect to device
        connection = self._connect_to_device(device_params)
        if not connection:
            return {'hostname': hostname, 'status': 'failed', 'reason': 'connection_failed'}
        
        try:
            # Enter enable mode if needed
            if device_params.get('secret'):
                connection.enable()
            
            # Collect running config
            config_success = self.collect_running_config(connection, hostname)
            
            # Collect show outputs
            show_results = self.collect_show_outputs(
                connection, 
                hostname, 
                device_params['device_type']
            )
            
            return {
                'hostname': hostname,
                'status': 'success',
                'config_collected': config_success,
                'show_commands': show_results
            }
            
        except Exception as e:
            logger.error(f"Error processing {hostname}: {str(e)}")
            return {'hostname': hostname, 'status': 'failed', 'reason': str(e)}
        
        finally:
            connection.disconnect()
            logger.info(f"Disconnected from {hostname}")
    
    def run_collection(self):
        """Run collection for all devices in inventory"""
        logger.info(f"\nStarting collection run at {datetime.now()}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Processing {len(self.devices)} devices\n")
        
        results = []
        for device in self.devices:
            result = self.process_device(device)
            results.append(result)
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info("COLLECTION SUMMARY")
        logger.info(f"{'='*60}")
        
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = len(results) - successful
        
        logger.info(f"Total devices: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        
        if failed > 0:
            logger.info("\nFailed devices:")
            for result in results:
                if result['status'] == 'failed':
                    reason = result.get('reason', 'unknown')
                    logger.info(f"  - {result['hostname']}: {reason}")
        
        logger.info(f"\nConfigs saved to: {self.config_dir}")
        logger.info(f"Show outputs saved to: {self.show_dir}")
        
        return results


def create_sample_inventory():
    """Create a sample inventory.yaml file"""
    sample_inventory = {
        'devices': [
            {
                'hostname': 'core-sw-01',
                'host': '192.168.1.10',
                'device_type': 'cisco_ios',
                'username': 'admin',
                'password': 'password',
                'secret': 'enable_password',
            },
            {
                'hostname': 'core-sw-02',
                'host': '192.168.1.11',
                'device_type': 'cisco_ios',
                'username': 'admin',
                'password': 'password',
                'secret': 'enable_password',
            },
            {
                'hostname': 'edge-rtr-01',
                'host': '192.168.1.1',
                'device_type': 'cisco_ios',
                'username': 'admin',
                'use_keys': True,
                'key_file': '~/.ssh/id_rsa',
            }
        ]
    }
    
    with open('inventory.yaml', 'w') as f:
        yaml.dump(sample_inventory, f, default_flow_style=False)
    
    print("Sample inventory.yaml created")
    print("Edit this file with your device details before running collection")


def main():
    """Main execution"""
    if len(sys.argv) > 1 and sys.argv[1] == '--create-inventory':
        create_sample_inventory()
        sys.exit(0)
    
    # Check for inventory file
    if not os.path.exists('inventory.yaml'):
        logger.error("inventory.yaml not found!")
        logger.info("Run with --create-inventory to generate a sample file")
        sys.exit(1)
    
    # Run collection
    collector = DeviceCollector(
        inventory_file='inventory.yaml',
        output_dir='configs'
    )
    collector.run_collection()


if __name__ == '__main__':
    main()
