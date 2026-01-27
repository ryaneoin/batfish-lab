#!/usr/bin/env python3
"""
Comprehensive Batfish Network Analysis - 11 Security & Compliance Checks
"""
import pandas as pd
from pathlib import Path
from pybatfish.client.session import Session
from datetime import datetime
import json

# Paths
SCRIPT_DIR = Path(__file__).parent
LAB_DIR = SCRIPT_DIR.parent
SNAPSHOT_PATH = str(LAB_DIR / "snapshot")
OUTPUT_DIR = str(SCRIPT_DIR / "output")

# Initialize Batfish
bf = Session(host="localhost")


def save_csv(df, name):
    """Save DataFrame to timestamped CSV"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{OUTPUT_DIR}/{name}_{ts}.csv"
    df.to_csv(path, index=False)
    print(f"[+] Saved: {path}")
    return path


def extract_hostname(interface_obj):
    """Extract hostname from Batfish interface object"""
    interface_str = str(interface_obj)
    return interface_str.split("[")[0] if "[" in interface_str else interface_str


def extract_interface_name(interface_obj):
    """Extract interface name from Batfish interface object"""
    interface_str = str(interface_obj)
    if "[" in interface_str and "]" in interface_str:
        return interface_str.split("[")[1].split("]")[0]
    return ""


print("[+] Connecting to Batfish...")
print(f"[+] Snapshot: {SNAPSHOT_PATH}")
print(f"[+] Output: {OUTPUT_DIR}")

try:
    bf.set_network("network-analysis")
    bf.init_snapshot(SNAPSHOT_PATH, name="snapshot", overwrite=True)
    print("[+] ✓ Connected")
except Exception as e:
    print(f"[!] Error: {e}")
    exit(1)

# ============================================================================
# CHECK 1: FHRP COMPLIANCE
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 1: FHRP COMPLIANCE (HSRP/VRRP)")
print("=" * 80)

hsrp_sum = pd.DataFrame()
try:
    hsrp = bf.q.hsrpProperties().answer().frame()
    if len(hsrp) > 0:
        save_csv(hsrp, "hsrp_detailed")
        hsrp_sum = hsrp.copy()
        hsrp_sum["Protocol"] = "HSRP"
        hsrp_sum["Hostname"] = hsrp_sum["Interface"].apply(extract_hostname)
        print(f"✓ HSRP groups: {len(hsrp)}")
except Exception as e:
    print(f"✗ HSRP error: {e}")

vrrp_sum = pd.DataFrame()
try:
    vrrp = bf.q.vrrpProperties().answer().frame()
    if len(vrrp) > 0:
        save_csv(vrrp, "vrrp_detailed")
        vrrp_sum = vrrp.copy()
        vrrp_sum["Protocol"] = "VRRP"
        vrrp_sum["Hostname"] = vrrp_sum["Interface"].apply(extract_hostname)
        print(f"✓ VRRP groups: {len(vrrp)}")
except Exception as e:
    print(f"✗ VRRP error: {e}")

if len(hsrp_sum) > 0 or len(vrrp_sum) > 0:
    fhrp = pd.concat([hsrp_sum, vrrp_sum], ignore_index=True)
    save_csv(fhrp, "fhrp_unified")

# ============================================================================
# CHECK 2: INTERFACE SECURITY
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 2: INTERFACE SECURITY & DOCUMENTATION")
print("=" * 80)

interfaces = pd.DataFrame()
no_desc = pd.DataFrame()
try:
    interfaces = bf.q.interfaceProperties().answer().frame()
    if len(interfaces) > 0:
        save_csv(interfaces, "interfaces_all")

        # Check for descriptions
        if "Description" in interfaces.columns:
            no_desc = interfaces[
                interfaces["Description"].isna() | (interfaces["Description"] == "")
            ]
            if len(no_desc) > 0:
                print(f"⚠️  {len(no_desc)} interfaces without descriptions")
                save_csv(no_desc, "interfaces_no_description")
            else:
                print(f"✓ All interfaces documented")

        # Check active status - handle different column names
        active_count = 0
        if "Admin_Status" in interfaces.columns:
            active = interfaces[interfaces["Admin_Status"] == "ACTIVE"]
            active_count = len(active)
        elif "Active" in interfaces.columns:
            active = interfaces[interfaces["Active"] == True]
            active_count = len(active)
        else:
            active_count = len(interfaces)

        print(f"✓ Interfaces analyzed: {len(interfaces)}")
        print(f"  - Active: {active_count}")

except Exception as e:
    print(f"✗ Interface error: {e}")

# ============================================================================
# CHECK 3: BGP AUTHENTICATION
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 3: BGP AUTHENTICATION AUDIT")
print("=" * 80)

bgp_peers = pd.DataFrame()
no_auth = pd.DataFrame()
try:
    bgp_process = bf.q.bgpProcessConfiguration().answer().frame()
    if len(bgp_process) > 0:
        save_csv(bgp_process, "bgp_process_config")
        print(f"✓ BGP processes: {len(bgp_process)}")

        bgp_peers = bf.q.bgpPeerConfiguration().answer().frame()
        if len(bgp_peers) > 0:
            save_csv(bgp_peers, "bgp_peers")

            # Check for authentication - handle different column names
            if "Password_Set" in bgp_peers.columns:
                no_auth = bgp_peers[bgp_peers["Password_Set"] == False]
                if len(no_auth) > 0:
                    print(f"⚠️  {len(no_auth)} BGP peers without authentication")
                    save_csv(no_auth, "bgp_peers_no_auth")
                else:
                    print(f"✓ All BGP peers authenticated")
            elif "Auth_Type" in bgp_peers.columns:
                no_auth = bgp_peers[bgp_peers["Auth_Type"].isna()]
                if len(no_auth) > 0:
                    print(f"⚠️  {len(no_auth)} BGP peers without authentication")
                    save_csv(no_auth, "bgp_peers_no_auth")
            else:
                print(f"ℹ️  Cannot determine BGP authentication status")

            print(f"✓ Total BGP peers: {len(bgp_peers)}")
    else:
        print("ℹ️  No BGP configured")
except Exception as e:
    print(f"✗ BGP error: {e}")

# ============================================================================
# CHECK 4: ROUTING TABLE
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 4: ROUTING TABLE ANALYSIS")
print("=" * 80)

routes = pd.DataFrame()
try:
    routes = bf.q.routes().answer().frame()
    if len(routes) > 0:
        save_csv(routes, "routing_table")

        if "Protocol" in routes.columns:
            route_counts = routes["Protocol"].value_counts()
            print(f"✓ Total routes: {len(routes)}")
            for protocol, count in route_counts.head(10).items():
                print(f"  - {protocol}: {count}")
        else:
            print(f"✓ Total routes: {len(routes)}")
    else:
        print("ℹ️  No routes")
except Exception as e:
    print(f"✗ Routing error: {e}")

# ============================================================================
# CHECK 5: ACL DEAD RULES
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 5: ACL DEAD RULE DETECTION")
print("=" * 80)

acl_lines = pd.DataFrame()
unreachable = pd.DataFrame()
try:
    acl_lines = bf.q.filterLineReachability().answer().frame()
    if len(acl_lines) > 0:
        save_csv(acl_lines, "acl_reachability")

        if "Unreachable" in acl_lines.columns:
            unreachable = acl_lines[acl_lines["Unreachable"] == True]
            if len(unreachable) > 0:
                print(f"⚠️  {len(unreachable)} dead ACL rules")
                save_csv(unreachable, "acl_dead_rules")
            else:
                print(f"✓ No dead rules")

        print(f"✓ ACL lines analyzed: {len(acl_lines)}")
    else:
        print("ℹ️  No ACLs found")
except Exception as e:
    print(f"✗ ACL error: {e}")

# ============================================================================
# CHECK 6: UNUSED STRUCTURES
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 6: UNUSED STRUCTURES (Cleanup Candidates)")
print("=" * 80)

unused_structures = pd.DataFrame()
try:
    unused_structures = bf.q.unusedStructures().answer().frame()
    if len(unused_structures) > 0:
        save_csv(unused_structures, "unused_structures")

        if "Structure_Type" in unused_structures.columns:
            unused_acls = unused_structures[
                unused_structures["Structure_Type"].str.contains(
                    "acl", case=False, na=False
                )
            ]
            if len(unused_acls) > 0:
                print(f"ℹ️  {len(unused_acls)} unused ACLs")
                save_csv(unused_acls, "unused_acls")

        print(f"✓ Total unused: {len(unused_structures)}")
    else:
        print("✓ No unused structures")
except Exception as e:
    print(f"✗ Unused structures error: {e}")

# ============================================================================
# CHECK 7: OSPF CONFIGURATION
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 7: OSPF CONFIGURATION")
print("=" * 80)

ospf_process = pd.DataFrame()
try:
    ospf_process = bf.q.ospfProcessConfiguration().answer().frame()
    if len(ospf_process) > 0:
        save_csv(ospf_process, "ospf_process")
        print(f"✓ OSPF processes: {len(ospf_process)}")

        ospf_interfaces = bf.q.ospfInterfaceConfiguration().answer().frame()
        if len(ospf_interfaces) > 0:
            save_csv(ospf_interfaces, "ospf_interfaces")

            if "Passive" in ospf_interfaces.columns:
                passive = ospf_interfaces[ospf_interfaces["Passive"] == True]
                print(f"✓ OSPF interfaces: {len(ospf_interfaces)}")
                print(f"  - Passive: {len(passive)}")
                print(f"  - Active: {len(ospf_interfaces) - len(passive)}")
            else:
                print(f"✓ OSPF interfaces: {len(ospf_interfaces)}")
    else:
        print("ℹ️  No OSPF")
except Exception as e:
    print(f"✗ OSPF error: {e}")

# ============================================================================
# CHECK 8: LAYER 2 TOPOLOGY (Optional - may not be in all Batfish versions)
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 8: LAYER 2 TOPOLOGY")
print("=" * 80)

try:
    if hasattr(bf.q, "layer2"):
        layer2 = bf.q.layer2().answer().frame()
        if len(layer2) > 0:
            save_csv(layer2, "layer2_topology")
            print(f"✓ L2 edges: {len(layer2)}")
        else:
            print("ℹ️  No L2 topology")
    else:
        print("ℹ️  Layer 2 query not available in this Batfish version")
except Exception as e:
    print(f"ℹ️  L2 topology not available: {e}")

# ============================================================================
# CHECK 9: NTP CONFIGURATION (Optional - may not be in all Batfish versions)
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 9: NTP CONSISTENCY")
print("=" * 80)

try:
    if hasattr(bf.q, "ntpServers"):
        ntp = bf.q.ntpServers().answer().frame()
        if len(ntp) > 0:
            save_csv(ntp, "ntp_servers")
            if "Server" in ntp.columns:
                unique = ntp["Server"].nunique()
                print(f"✓ NTP servers: {unique}")
                if unique > 1:
                    print(f"⚠️  Multiple NTP servers (inconsistency)")
        else:
            print("⚠️  No NTP configured")
    else:
        print("ℹ️  NTP query not available in this Batfish version")
except Exception as e:
    print(f"ℹ️  NTP check not available: {e}")

# ============================================================================
# CHECK 10: CONFIGURATION INVENTORY
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 10: CONFIGURATION INVENTORY")
print("=" * 80)

defined = pd.DataFrame()
try:
    defined = bf.q.definedStructures().answer().frame()
    if len(defined) > 0:
        save_csv(defined, "defined_structures")

        if "Structure_Type" in defined.columns:
            counts = defined["Structure_Type"].value_counts()
            print(f"✓ Structures defined:")
            for struct, count in counts.head(15).items():
                print(f"  - {struct}: {count}")
        else:
            print(f"✓ Total structures: {len(defined)}")
    else:
        print("ℹ️  No structures")
except Exception as e:
    print(f"✗ Inventory error: {e}")

# ============================================================================
# CHECK 11: COMPLIANCE SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("CHECK 11: COMPLIANCE SUMMARY")
print("=" * 80)

try:
    devices = set()
    if len(interfaces) > 0 and "Interface" in interfaces.columns:
        for intf in interfaces["Interface"]:
            hostname = extract_hostname(intf)
            if hostname:
                devices.add(hostname)

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_devices": len(devices),
        "device_names": list(devices),
        "fhrp_groups": len(fhrp) if "fhrp" in locals() and len(fhrp) > 0 else 0,
        "interfaces_total": len(interfaces) if len(interfaces) > 0 else 0,
        "interfaces_no_description": len(no_desc) if len(no_desc) > 0 else 0,
        "bgp_peers_total": len(bgp_peers) if len(bgp_peers) > 0 else 0,
        "bgp_peers_no_auth": len(no_auth) if len(no_auth) > 0 else 0,
        "routes_total": len(routes) if len(routes) > 0 else 0,
        "acl_lines_total": len(acl_lines) if len(acl_lines) > 0 else 0,
        "acl_dead_rules": len(unreachable) if len(unreachable) > 0 else 0,
        "unused_structures": (
            len(unused_structures) if len(unused_structures) > 0 else 0
        ),
        "ospf_processes": len(ospf_process) if len(ospf_process) > 0 else 0,
        "defined_structures": len(defined) if len(defined) > 0 else 0,
    }

    summary_file = f"{OUTPUT_DIR}/compliance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[+] Saved: {summary_file}")

    print(f"\n📊 Summary:")
    print(f"   Devices: {summary['total_devices']}")
    print(f"   FHRP groups: {summary['fhrp_groups']}")
    print(f"   Interfaces: {summary['interfaces_total']}")
    print(f"   BGP peers: {summary['bgp_peers_total']}")
    print(f"   Routes: {summary['routes_total']}")
    print(f"   OSPF processes: {summary['ospf_processes']}")
    if summary["interfaces_no_description"] > 0:
        print(f"   ⚠️  No description: {summary['interfaces_no_description']}")
    if summary["bgp_peers_no_auth"] > 0:
        print(f"   ⚠️  BGP no auth: {summary['bgp_peers_no_auth']}")
    if summary["acl_dead_rules"] > 0:
        print(f"   ⚠️  ACL dead rules: {summary['acl_dead_rules']}")
    if summary["unused_structures"] > 0:
        print(f"   ℹ️  Unused structures: {summary['unused_structures']}")

except Exception as e:
    print(f"✗ Summary error: {e}")

print("\n" + "=" * 80)
print("✅ ANALYSIS COMPLETE!")
print(f"Output: {OUTPUT_DIR}")
print("=" * 80)
