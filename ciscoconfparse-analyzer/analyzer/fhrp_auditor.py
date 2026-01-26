"""
FHRP (HSRP/VRRP/GLBP) Configuration Auditor
Analyzes First Hop Redundancy Protocol configurations for security and compliance
"""

from ciscoconfparse import CiscoConfParse
from typing import Dict, List, Any
import re


class FHRPAuditor:
    """Auditor for FHRP configurations (HSRP, VRRP, GLBP)"""
    
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
    
    def audit_all_interfaces(self) -> Dict[str, Any]:
        """Audit all interfaces with FHRP configured"""
        results = {
            'device': self.device_name,
            'config_file': self.config_file,
            'interfaces': [],
            'total_fhrp_interfaces': 0,
            'compliant_interfaces': 0,
            'overall_compliance_pct': 0.0
        }
        
        # Find all interfaces with FHRP
        hsrp_intfs = self._find_hsrp_interfaces()
        vrrp_intfs = self._find_vrrp_interfaces()
        glbp_intfs = self._find_glbp_interfaces()
        
        # Audit each protocol
        for intf_obj in hsrp_intfs:
            audit_result = self._audit_hsrp_interface(intf_obj)
            results['interfaces'].append(audit_result)
        
        for intf_obj in vrrp_intfs:
            audit_result = self._audit_vrrp_interface(intf_obj)
            results['interfaces'].append(audit_result)
        
        for intf_obj in glbp_intfs:
            audit_result = self._audit_glbp_interface(intf_obj)
            results['interfaces'].append(audit_result)
        
        # Calculate statistics
        results['total_fhrp_interfaces'] = len(results['interfaces'])
        results['compliant_interfaces'] = sum(1 for i in results['interfaces'] if i['compliant'])
        
        if results['total_fhrp_interfaces'] > 0:
            results['overall_compliance_pct'] = round(
                (results['compliant_interfaces'] / results['total_fhrp_interfaces']) * 100, 2
            )
        
        return results
    
    def _find_hsrp_interfaces(self) -> List:
        """Find all interfaces with HSRP configured"""
        return self.parse.find_objects_w_child(
            parentspec=r'^interface',
            childspec=r'^\s+standby\s+\d+'
        )
    
    def _find_vrrp_interfaces(self) -> List:
        """Find all interfaces with VRRP configured"""
        return self.parse.find_objects_w_child(
            parentspec=r'^interface',
            childspec=r'^\s+vrrp\s+\d+'
        )
    
    def _find_glbp_interfaces(self) -> List:
        """Find all interfaces with GLBP configured"""
        return self.parse.find_objects_w_child(
            parentspec=r'^interface',
            childspec=r'^\s+glbp\s+\d+'
        )
    
    def _audit_hsrp_interface(self, intf_obj) -> Dict[str, Any]:
        """Audit HSRP configuration on an interface"""
        interface_name = intf_obj.text.split()[1]
        
        result = {
            'interface': interface_name,
            'protocol': 'HSRP',
            'compliant': True,
            'issues': [],
            'risk_score': 0
        }
        
        # Get all HSRP groups on this interface
        hsrp_groups = []
        for child in intf_obj.children:
            match = re.match(r'^\s+standby\s+(\d+)', child.text)
            if match:
                group_id = match.group(1)
                if group_id not in hsrp_groups:
                    hsrp_groups.append(group_id)
        
        for group_id in hsrp_groups:
            # Check for authentication
            auth_found = False
            for child in intf_obj.children:
                if f'standby {group_id} authentication' in child.text:
                    auth_found = True
                    break
            
            if not auth_found:
                result['compliant'] = False
                result['risk_score'] += 30
                result['issues'].append({
                    'severity': 'HIGH',
                    'issue': f'HSRP group {group_id} missing authentication',
                    'pci_requirement': 'PCI-DSS 2.2.4 - Configure system security parameters',
                    'remediation': f'Add: standby {group_id} authentication md5 key-string <password>'
                })
            
            # Check for preempt
            preempt_found = False
            for child in intf_obj.children:
                if f'standby {group_id} preempt' in child.text:
                    preempt_found = True
                    break
            
            if not preempt_found:
                result['compliant'] = False
                result['risk_score'] += 15
                result['issues'].append({
                    'severity': 'MEDIUM',
                    'issue': f'HSRP group {group_id} missing preempt',
                    'remediation': f'Add: standby {group_id} preempt'
                })
            
            # Check for custom timers (optional but recommended)
            timers_found = False
            for child in intf_obj.children:
                if f'standby {group_id} timers' in child.text:
                    timers_found = True
                    break
            
            if not timers_found:
                result['risk_score'] += 5
                result['issues'].append({
                    'severity': 'LOW',
                    'issue': f'HSRP group {group_id} using default timers',
                    'remediation': f'Consider: standby {group_id} timers msec 250 msec 750'
                })
        
        result['risk_score'] = min(result['risk_score'], 100)
        return result
    
    def _audit_vrrp_interface(self, intf_obj) -> Dict[str, Any]:
        """Audit VRRP configuration on an interface"""
        interface_name = intf_obj.text.split()[1]
        
        result = {
            'interface': interface_name,
            'protocol': 'VRRP',
            'compliant': True,
            'issues': [],
            'risk_score': 0
        }
        
        # Get all VRRP groups on this interface
        vrrp_groups = []
        for child in intf_obj.children:
            match = re.match(r'^\s+vrrp\s+(\d+)', child.text)
            if match:
                group_id = match.group(1)
                if group_id not in vrrp_groups:
                    vrrp_groups.append(group_id)
        
        for group_id in vrrp_groups:
            # Check for authentication
            auth_found = False
            for child in intf_obj.children:
                if f'vrrp {group_id} authentication' in child.text:
                    auth_found = True
                    break
            
            if not auth_found:
                result['compliant'] = False
                result['risk_score'] += 30
                result['issues'].append({
                    'severity': 'HIGH',
                    'issue': f'VRRP group {group_id} missing authentication',
                    'pci_requirement': 'PCI-DSS 2.2.4 - Configure system security parameters',
                    'remediation': f'Add: vrrp {group_id} authentication md5 key-string <password>'
                })
            
            # Check for preempt
            preempt_found = False
            for child in intf_obj.children:
                if f'vrrp {group_id} preempt' in child.text:
                    preempt_found = True
                    break
            
            if not preempt_found:
                result['compliant'] = False
                result['risk_score'] += 15
                result['issues'].append({
                    'severity': 'MEDIUM',
                    'issue': f'VRRP group {group_id} missing preempt',
                    'remediation': f'Add: vrrp {group_id} preempt'
                })
            
            # Check for timers
            timers_found = False
            for child in intf_obj.children:
                if f'vrrp {group_id} timers' in child.text:
                    timers_found = True
                    break
            
            if not timers_found:
                result['risk_score'] += 5
                result['issues'].append({
                    'severity': 'LOW',
                    'issue': f'VRRP group {group_id} using default timers',
                    'remediation': f'Consider: vrrp {group_id} timers advertise msec 250'
                })
        
        result['risk_score'] = min(result['risk_score'], 100)
        return result
    
    def _audit_glbp_interface(self, intf_obj) -> Dict[str, Any]:
        """Audit GLBP configuration on an interface"""
        interface_name = intf_obj.text.split()[1]
        
        result = {
            'interface': interface_name,
            'protocol': 'GLBP',
            'compliant': True,
            'issues': [],
            'risk_score': 0
        }
        
        # Get all GLBP groups on this interface
        glbp_groups = []
        for child in intf_obj.children:
            match = re.match(r'^\s+glbp\s+(\d+)', child.text)
            if match:
                group_id = match.group(1)
                if group_id not in glbp_groups:
                    glbp_groups.append(group_id)
        
        for group_id in glbp_groups:
            # Check for authentication
            auth_found = False
            for child in intf_obj.children:
                if f'glbp {group_id} authentication' in child.text:
                    auth_found = True
                    break
            
            if not auth_found:
                result['compliant'] = False
                result['risk_score'] += 30
                result['issues'].append({
                    'severity': 'HIGH',
                    'issue': f'GLBP group {group_id} missing authentication',
                    'pci_requirement': 'PCI-DSS 2.2.4 - Configure system security parameters',
                    'remediation': f'Add: glbp {group_id} authentication md5 key-string <password>'
                })
            
            # Check for preempt
            preempt_found = False
            for child in intf_obj.children:
                if f'glbp {group_id} preempt' in child.text:
                    preempt_found = True
                    break
            
            if not preempt_found:
                result['compliant'] = False
                result['risk_score'] += 15
                result['issues'].append({
                    'severity': 'MEDIUM',
                    'issue': f'GLBP group {group_id} missing preempt',
                    'remediation': f'Add: glbp {group_id} preempt'
                })
            
            # Check for timers
            timers_found = False
            for child in intf_obj.children:
                if f'glbp {group_id} timers' in child.text:
                    timers_found = True
                    break
            
            if not timers_found:
                result['risk_score'] += 5
                result['issues'].append({
                    'severity': 'LOW',
                    'issue': f'GLBP group {group_id} using default timers',
                    'remediation': f'Consider: glbp {group_id} timers msec 250 msec 750'
                })
        
        result['risk_score'] = min(result['risk_score'], 100)
        return result
