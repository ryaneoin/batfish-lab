"""
BGP Configuration Auditor
Analyzes BGP configurations for security and compliance
"""

from ciscoconfparse import CiscoConfParse
from typing import Dict, List, Any
import re


class BGPAuditor:
    """Auditor for BGP configurations"""
    
    def __init__(self, config_file: str):
        """Initialize with a Cisco configuration file"""
        self.config_file = config_file
        self.parse = CiscoConfParse(config_file, syntax='ios')
        self.device_name = self._extract_hostname()
    
    def _extract_hostname(self) -> str:
        """Extract hostname from configuration"""
        hostname_objs = self.parse.find_objects(r'^hostname\s+')
        if hostname_objs:
            return hostname_objs[0].text.split()[1]
        return "unknown"
    
    def audit_bgp_config(self) -> Dict[str, Any]:
        """Audit BGP configuration"""
        result = {
            'device': self.device_name,
            'config_file': self.config_file,
            'bgp_configured': False,
            'asn': None,
            'neighbors': [],
            'global_config': {
                'compliant': True,
                'issues': []
            },
            'total_neighbors': 0,
            'compliant_neighbors': 0,
            'overall_compliance_pct': 0.0
        }
        
        # Find BGP router configuration
        bgp_objs = self.parse.find_objects(r'^router\s+bgp\s+')
        
        if not bgp_objs:
            result['message'] = f"No BGP configured on {self.device_name}"
            return result
        
        result['bgp_configured'] = True
        
        # Extract ASN
        bgp_obj = bgp_objs[0]
        match = re.match(r'^router\s+bgp\s+(\d+)', bgp_obj.text)
        if match:
            result['asn'] = int(match.group(1))
        
        # Audit global BGP configuration
        self._audit_global_bgp_config(bgp_obj, result['global_config'])
        
        # Find all BGP neighbors
        neighbor_objs = self.parse.find_children_w_parents(
            parentspec=r'^router\s+bgp',
            childspec=r'^\s+neighbor\s+\S+\s+remote-as'
        )
        
        # Group neighbor configurations
        neighbors = {}
        for neighbor_line in neighbor_objs:
            match = re.match(r'^\s+neighbor\s+(\S+)\s+remote-as\s+(\d+)', neighbor_line.text)
            if match:
                neighbor_ip = match.group(1)
                remote_as = match.group(2)
                neighbors[neighbor_ip] = {
                    'neighbor': neighbor_ip,
                    'remote_as': remote_as,
                    'compliant': True,
                    'issues': [],
                    'risk_score': 0
                }
        
        # Audit each neighbor
        for neighbor_ip in neighbors:
            neighbor_result = self._audit_bgp_neighbor(bgp_obj, neighbor_ip, neighbors[neighbor_ip])
            result['neighbors'].append(neighbor_result)
        
        # Calculate statistics
        result['total_neighbors'] = len(result['neighbors'])
        result['compliant_neighbors'] = sum(1 for n in result['neighbors'] if n['compliant'])
        
        if result['total_neighbors'] > 0:
            result['overall_compliance_pct'] = round(
                (result['compliant_neighbors'] / result['total_neighbors']) * 100, 2
            )
        
        return result
    
    def _audit_global_bgp_config(self, bgp_obj, global_config: Dict):
        """Audit global BGP configuration"""
        
        # Check for BGP router-id
        router_id_found = False
        for child in bgp_obj.children:
            if re.match(r'^\s+bgp\s+router-id', child.text):
                router_id_found = True
                break
        
        if not router_id_found:
            global_config['compliant'] = False
            global_config['issues'].append({
                'severity': 'MEDIUM',
                'issue': 'BGP router-id not explicitly configured',
                'remediation': 'Add: bgp router-id <IP-address>'
            })
        
        # Check for BGP log-neighbor-changes
        log_changes_found = False
        for child in bgp_obj.children:
            if 'bgp log-neighbor-changes' in child.text:
                log_changes_found = True
                break
        
        if not log_changes_found:
            global_config['compliant'] = False
            global_config['issues'].append({
                'severity': 'LOW',
                'issue': 'BGP neighbor changes logging not enabled',
                'remediation': 'Add: bgp log-neighbor-changes'
            })
    
    def _audit_bgp_neighbor(self, bgp_obj, neighbor_ip: str, neighbor_data: Dict) -> Dict:
        """Audit a specific BGP neighbor configuration"""
        
        result = neighbor_data.copy()
        
        # Check for MD5 authentication
        password_found = False
        for child in bgp_obj.children:
            if f'neighbor {neighbor_ip} password' in child.text:
                password_found = True
                break
        
        if not password_found:
            result['compliant'] = False
            result['risk_score'] += 40
            result['issues'].append({
                'severity': 'CRITICAL',
                'issue': f'BGP neighbor {neighbor_ip} missing MD5 authentication',
                'pci_requirement': 'PCI-DSS 4.1 - Use strong cryptography for transmission',
                'remediation': f'Add: neighbor {neighbor_ip} password <md5-password>'
            })
        
        # Check for update-source (for iBGP)
        update_source_found = False
        for child in bgp_obj.children:
            if f'neighbor {neighbor_ip} update-source' in child.text:
                update_source_found = True
                break
        
        # Check for TTL security
        ttl_security_found = False
        for child in bgp_obj.children:
            if f'neighbor {neighbor_ip} ttl-security' in child.text:
                ttl_security_found = True
                break
        
        if not ttl_security_found:
            result['risk_score'] += 20
            result['issues'].append({
                'severity': 'HIGH',
                'issue': f'BGP neighbor {neighbor_ip} missing TTL security',
                'remediation': f'Add: neighbor {neighbor_ip} ttl-security hops 1 (for eBGP)'
            })
        
        # Check for prefix-list or filter-list
        filtering_found = False
        for child in bgp_obj.children:
            if f'neighbor {neighbor_ip} prefix-list' in child.text or \
               f'neighbor {neighbor_ip} filter-list' in child.text or \
               f'neighbor {neighbor_ip} route-map' in child.text:
                filtering_found = True
                break
        
        if not filtering_found:
            result['risk_score'] += 25
            result['issues'].append({
                'severity': 'HIGH',
                'issue': f'BGP neighbor {neighbor_ip} has no inbound/outbound filtering',
                'pci_requirement': 'PCI-DSS 1.3.6 - Filter traffic between network segments',
                'remediation': f'Add: neighbor {neighbor_ip} prefix-list <name> in/out'
            })
        
        # Check for maximum-prefix limit
        max_prefix_found = False
        for child in bgp_obj.children:
            if f'neighbor {neighbor_ip} maximum-prefix' in child.text:
                max_prefix_found = True
                break
        
        if not max_prefix_found:
            result['risk_score'] += 15
            result['issues'].append({
                'severity': 'MEDIUM',
                'issue': f'BGP neighbor {neighbor_ip} has no maximum-prefix limit',
                'remediation': f'Add: neighbor {neighbor_ip} maximum-prefix <limit> 85'
            })
        
        result['risk_score'] = min(result['risk_score'], 100)
        return result
