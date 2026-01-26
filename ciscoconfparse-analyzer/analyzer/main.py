"""
Main analysis script for CiscoConfParse network audit
Analyzes FHRP and BGP configurations from Cisco device configs
"""

import os
import json
import glob
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from fhrp_auditor import FHRPAuditor
from bgp_auditor import BGPAuditor

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")


def print_subheader(text: str):
    """Print formatted subheader"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKBLUE}{'-'*len(text)}{Colors.ENDC}")


def print_issue(issue: Dict[str, Any]):
    """Print formatted issue"""
    severity_colors = {
        'CRITICAL': Colors.FAIL,
        'HIGH': Colors.FAIL,
        'MEDIUM': Colors.WARNING,
        'LOW': Colors.OKCYAN
    }
    
    color = severity_colors.get(issue['severity'], Colors.ENDC)
    print(f"  {color}[{issue['severity']}]{Colors.ENDC} {issue['issue']}")
    if 'pci_requirement' in issue:
        print(f"    📋 PCI: {issue['pci_requirement']}")
    print(f"    🔧 Remediation: {issue['remediation']}")


def analyze_fhrp(config_files: List[str]) -> Dict[str, Any]:
    """Analyze FHRP configurations across all devices"""
    print_header("FHRP (HSRP/VRRP/GLBP) AUDIT")
    
    all_results = []
    
    for config_file in config_files:
        print_subheader(f"Analyzing: {os.path.basename(config_file)}")
        
        try:
            auditor = FHRPAuditor(config_file)
            result = auditor.audit_all_interfaces()
            all_results.append(result)
            
            # Print summary for this device
            device = result['device']
            total = result['total_fhrp_interfaces']
            compliant = result['compliant_interfaces']
            compliance_pct = result['overall_compliance_pct']
            
            if total == 0:
                print(f"  ℹ️  No FHRP interfaces found on {device}")
                continue
            
            compliance_color = Colors.OKGREEN if compliance_pct == 100 else Colors.WARNING if compliance_pct >= 50 else Colors.FAIL
            
            print(f"  Device: {Colors.BOLD}{device}{Colors.ENDC}")
            print(f"  Total FHRP Interfaces: {total}")
            print(f"  Compliant: {compliant}/{total}")
            print(f"  Compliance: {compliance_color}{compliance_pct}%{Colors.ENDC}")
            
            # Print issues for each interface
            for intf in result['interfaces']:
                if not intf['compliant']:
                    print(f"\n  {Colors.WARNING}⚠️  {intf['interface']} ({intf['protocol']}){Colors.ENDC}")
                    print(f"    Risk Score: {intf['risk_score']}/100")
                    for issue in intf['issues']:
                        print_issue(issue)
                else:
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} {intf['interface']} ({intf['protocol']})")
            
        except Exception as e:
            print(f"  {Colors.FAIL}Error analyzing {config_file}: {e}{Colors.ENDC}")
    
    return {
        'analysis_type': 'FHRP',
        'timestamp': datetime.now().isoformat(),
        'devices': all_results,
        'summary': _calculate_fhrp_summary(all_results)
    }


def analyze_bgp(config_files: List[str]) -> Dict[str, Any]:
    """Analyze BGP configurations across all devices"""
    print_header("BGP SECURITY AUDIT")
    
    all_results = []
    
    for config_file in config_files:
        print_subheader(f"Analyzing: {os.path.basename(config_file)}")
        
        try:
            auditor = BGPAuditor(config_file)
            result = auditor.audit_bgp_config()
            all_results.append(result)
            
            if not result['bgp_configured']:
                print(f"  ℹ️  {result['message']}")
                continue
            
            # Print summary for this device
            device = result['device']
            asn = result['asn']
            total = result['total_neighbors']
            compliant = result['compliant_neighbors']
            compliance_pct = result['overall_compliance_pct']
            
            compliance_color = Colors.OKGREEN if compliance_pct == 100 else Colors.WARNING if compliance_pct >= 50 else Colors.FAIL
            
            print(f"  Device: {Colors.BOLD}{device}{Colors.ENDC}")
            print(f"  ASN: {asn}")
            print(f"  Total Neighbors: {total}")
            print(f"  Compliant: {compliant}/{total}")
            print(f"  Compliance: {compliance_color}{compliance_pct}%{Colors.ENDC}")
            
            # Print global issues
            if result['global_config']['issues']:
                print(f"\n  {Colors.WARNING}⚠️  Global BGP Configuration Issues{Colors.ENDC}")
                for issue in result['global_config']['issues']:
                    print_issue(issue)
            
            # Print neighbor issues
            for neighbor in result['neighbors']:
                if not neighbor['compliant']:
                    print(f"\n  {Colors.WARNING}⚠️  Neighbor {neighbor['neighbor']} (AS {neighbor['remote_as']}){Colors.ENDC}")
                    print(f"    Risk Score: {neighbor['risk_score']}/100")
                    for issue in neighbor['issues']:
                        print_issue(issue)
                else:
                    print(f"  {Colors.OKGREEN}✓{Colors.ENDC} Neighbor {neighbor['neighbor']} (AS {neighbor['remote_as']})")
            
        except Exception as e:
            print(f"  {Colors.FAIL}Error analyzing {config_file}: {e}{Colors.ENDC}")
    
    return {
        'analysis_type': 'BGP',
        'timestamp': datetime.now().isoformat(),
        'devices': all_results,
        'summary': _calculate_bgp_summary(all_results)
    }


def _calculate_fhrp_summary(results: List[Dict]) -> Dict[str, Any]:
    """Calculate summary statistics for FHRP audit"""
    total_devices = len([r for r in results if r['total_fhrp_interfaces'] > 0])
    total_interfaces = sum(r['total_fhrp_interfaces'] for r in results)
    compliant_interfaces = sum(r['compliant_interfaces'] for r in results)
    
    # Collect all issues
    all_issues = []
    for result in results:
        for intf in result.get('interfaces', []):
            all_issues.extend(intf['issues'])
    
    # Count by severity
    severity_counts = {
        'CRITICAL': len([i for i in all_issues if i['severity'] == 'CRITICAL']),
        'HIGH': len([i for i in all_issues if i['severity'] == 'HIGH']),
        'MEDIUM': len([i for i in all_issues if i['severity'] == 'MEDIUM']),
        'LOW': len([i for i in all_issues if i['severity'] == 'LOW'])
    }
    
    return {
        'total_devices_with_fhrp': total_devices,
        'total_fhrp_interfaces': total_interfaces,
        'compliant_interfaces': compliant_interfaces,
        'overall_compliance_pct': round((compliant_interfaces / total_interfaces * 100), 2) if total_interfaces > 0 else 0,
        'issues_by_severity': severity_counts,
        'total_issues': len(all_issues)
    }


def _calculate_bgp_summary(results: List[Dict]) -> Dict[str, Any]:
    """Calculate summary statistics for BGP audit"""
    total_devices = len([r for r in results if r.get('bgp_configured', False)])
    total_neighbors = sum(r.get('total_neighbors', 0) for r in results if r.get('bgp_configured', False))
    compliant_neighbors = sum(r.get('compliant_neighbors', 0) for r in results if r.get('bgp_configured', False))
    
    # Collect all issues
    all_issues = []
    for result in results:
        if not result.get('bgp_configured', False):
            continue
        for neighbor in result.get('neighbors', []):
            all_issues.extend(neighbor['issues'])
        # Add global issues
        all_issues.extend(result.get('global_config', {}).get('issues', []))
    
    # Count by severity
    severity_counts = {
        'CRITICAL': len([i for i in all_issues if i['severity'] == 'CRITICAL']),
        'HIGH': len([i for i in all_issues if i['severity'] == 'HIGH']),
        'MEDIUM': len([i for i in all_issues if i['severity'] == 'MEDIUM']),
        'LOW': len([i for i in all_issues if i['severity'] == 'LOW'])
    }
    
    return {
        'total_devices_with_bgp': total_devices,
        'total_bgp_neighbors': total_neighbors,
        'compliant_neighbors': compliant_neighbors,
        'overall_compliance_pct': round((compliant_neighbors / total_neighbors * 100), 2) if total_neighbors > 0 else 0,
        'issues_by_severity': severity_counts,
        'total_issues': len(all_issues)
    }


def print_final_summary(fhrp_results: Dict, bgp_results: Dict):
    """Print final summary of all audits"""
    print_header("OVERALL AUDIT SUMMARY")
    
    # FHRP Summary
    fhrp_summary = fhrp_results['summary']
    print_subheader("FHRP Summary")
    print(f"  Devices with FHRP: {fhrp_summary['total_devices_with_fhrp']}")
    print(f"  Total FHRP Interfaces: {fhrp_summary['total_fhrp_interfaces']}")
    print(f"  Compliant Interfaces: {fhrp_summary['compliant_interfaces']}/{fhrp_summary['total_fhrp_interfaces']}")
    print(f"  Overall Compliance: {fhrp_summary['overall_compliance_pct']}%")
    print(f"  Total Issues: {fhrp_summary['total_issues']}")
    print(f"    - Critical: {fhrp_summary['issues_by_severity']['CRITICAL']}")
    print(f"    - High: {fhrp_summary['issues_by_severity']['HIGH']}")
    print(f"    - Medium: {fhrp_summary['issues_by_severity']['MEDIUM']}")
    print(f"    - Low: {fhrp_summary['issues_by_severity']['LOW']}")
    
    # BGP Summary
    bgp_summary = bgp_results['summary']
    print_subheader("BGP Summary")
    print(f"  Devices with BGP: {bgp_summary['total_devices_with_bgp']}")
    print(f"  Total BGP Neighbors: {bgp_summary['total_bgp_neighbors']}")
    print(f"  Compliant Neighbors: {bgp_summary['compliant_neighbors']}/{bgp_summary['total_bgp_neighbors']}")
    print(f"  Overall Compliance: {bgp_summary['overall_compliance_pct']}%")
    print(f"  Total Issues: {bgp_summary['total_issues']}")
    print(f"    - Critical: {bgp_summary['issues_by_severity']['CRITICAL']}")
    print(f"    - High: {bgp_summary['issues_by_severity']['HIGH']}")
    print(f"    - Medium: {bgp_summary['issues_by_severity']['MEDIUM']}")
    print(f"    - Low: {bgp_summary['issues_by_severity']['LOW']}")
    
    print()


def main():
    """Main entry point"""
    # Get config directory from environment or use default
    configs_dir = os.environ.get('CONFIGS_DIR', '/configs')
    output_dir = os.environ.get('OUTPUT_DIR', '/app/output')
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Find all .cfg files
    config_files = glob.glob(os.path.join(configs_dir, '*.cfg'))
    
    if not config_files:
        print(f"{Colors.FAIL}No .cfg files found in {configs_dir}{Colors.ENDC}")
        return
    
    print(f"{Colors.OKGREEN}Found {len(config_files)} config files{Colors.ENDC}")
    for cf in config_files:
        print(f"  - {os.path.basename(cf)}")
    
    # Run FHRP audit
    fhrp_results = analyze_fhrp(config_files)
    
    # Run BGP audit
    bgp_results = analyze_bgp(config_files)
    
    # Print final summary
    print_final_summary(fhrp_results, bgp_results)
    
    # Save results to JSON files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    fhrp_output = os.path.join(output_dir, f'fhrp_audit_{timestamp}.json')
    with open(fhrp_output, 'w') as f:
        json.dump(fhrp_results, f, indent=2)
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} FHRP audit saved to: {fhrp_output}")
    
    bgp_output = os.path.join(output_dir, f'bgp_audit_{timestamp}.json')
    with open(bgp_output, 'w') as f:
        json.dump(bgp_results, f, indent=2)
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} BGP audit saved to: {bgp_output}")
    
    # Save combined report
    combined_report = {
        'timestamp': datetime.now().isoformat(),
        'fhrp_audit': fhrp_results,
        'bgp_audit': bgp_results
    }
    
    combined_output = os.path.join(output_dir, f'combined_audit_{timestamp}.json')
    with open(combined_output, 'w') as f:
        json.dump(combined_report, f, indent=2)
    print(f"{Colors.OKGREEN}✓{Colors.ENDC} Combined audit saved to: {combined_output}")


if __name__ == '__main__':
    main()
