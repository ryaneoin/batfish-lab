#!/usr/bin/env python3
"""
Batfish Network Analysis Script - FHRP Focus with Auth Detection
Compatible with pybatfish 2024.x API (v2)
"""
import pandas as pd
from pathlib import Path
from pybatfish.client.session import Session
from datetime import datetime

# Use paths relative to script location
SCRIPT_DIR = Path(__file__).parent
LAB_DIR = SCRIPT_DIR.parent
SNAPSHOT_PATH = str(LAB_DIR / "snapshot")
OUTPUT_DIR = str(SCRIPT_DIR / "output")

# Initialize Batfish session
bf = Session(host="localhost")

def save_csv(df, name):
    """Save DataFrame to timestamped CSV file"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{OUTPUT_DIR}/{name}_{ts}.csv"
    df.to_csv(path, index=False)
    print(f"[+] Saved: {path}")
    return path

def extract_hostname(interface_obj):
    """Extract hostname from Batfish interface object"""
    interface_str = str(interface_obj)
    if '[' in interface_str:
        return interface_str.split('[')[0]
    return interface_str

def extract_interface_name(interface_obj):
    """Extract interface name from Batfish interface object"""
    interface_str = str(interface_obj)
    if '[' in interface_str and ']' in interface_str:
        return interface_str.split('[')[1].split(']')[0]
    return ''

print("[+] Connecting to Batfish...")
print(f"[+] Snapshot path: {SNAPSHOT_PATH}")
print(f"[+] Output path: {OUTPUT_DIR}")

try:
    bf.set_network("fhrp-network")
    bf.init_snapshot(SNAPSHOT_PATH, name="snapshot", overwrite=True)
    print(f"[+] Connected to Batfish successfully")
    print("[+] Snapshot initialized")
except Exception as e:
    print(f"[!] Error connecting: {e}")
    exit(1)

print("\n=== Analyzing HSRP ===")
hsrp_sum = pd.DataFrame()
try:
    hsrp = bf.q.hsrpProperties().answer().frame()
    if len(hsrp) > 0:
        save_csv(hsrp, "hsrp_detailed")
        hsrp_sum = hsrp.copy()
        hsrp_sum = hsrp_sum.rename(columns={'Group_Id': 'Group_ID', 'Active': 'Enabled'})
        hsrp_sum['Protocol'] = 'HSRP'
        hsrp_sum['Hostname'] = hsrp_sum['Interface'].apply(extract_hostname)
        hsrp_sum['Interface_Name'] = hsrp_sum['Interface'].apply(extract_interface_name)
        hsrp_sum['Interface'] = hsrp_sum['Interface'].astype(str)
        hsrp_sum = hsrp_sum[['Interface', 'Group_ID', 'Priority', 'Preempt', 'Enabled',
                             'Hostname', 'Interface_Name', 'Protocol']]
        print(f"✓ HSRP groups found: {len(hsrp)}")
        print(f"\nHSRP Configuration:")
        print(hsrp_sum[['Hostname', 'Interface_Name', 'Group_ID', 'Priority', 'Preempt']].to_string(index=False))
except Exception as e:
    print(f"Error analyzing HSRP: {e}")

print("\n=== Analyzing VRRP ===")
vrrp_sum = pd.DataFrame()
try:
    vrrp = bf.q.vrrpProperties().answer().frame()
    if len(vrrp) > 0:
        save_csv(vrrp, "vrrp_detailed")
        vrrp_sum = vrrp.copy()
        vrrp_sum = vrrp_sum.rename(columns={'Group_Id': 'Group_ID', 'Active': 'Enabled'})
        vrrp_sum['Protocol'] = 'VRRP'
        vrrp_sum['Hostname'] = vrrp_sum['Interface'].apply(extract_hostname)
        vrrp_sum['Interface_Name'] = vrrp_sum['Interface'].apply(extract_interface_name)
        vrrp_sum['Interface'] = vrrp_sum['Interface'].astype(str)
        vrrp_sum = vrrp_sum[['Interface', 'Group_ID', 'Priority', 'Preempt', 'Enabled',
                             'Hostname', 'Interface_Name', 'Protocol']]
        print(f"✓ VRRP groups found: {len(vrrp)}")
        print(f"\nVRRP Configuration:")
        print(vrrp_sum[['Hostname', 'Interface_Name', 'Group_ID', 'Priority', 'Preempt']].to_string(index=False))
except Exception as e:
    print(f"Error analyzing VRRP: {e}")

print("\n=== FHRP Configuration Audit ===")

# Check for orphaned groups (single member)
if len(hsrp_sum) > 0 or len(vrrp_sum) > 0:
    fhrp = pd.concat([hsrp_sum, vrrp_sum], ignore_index=True)

    # Count members per group
    group_counts = fhrp.groupby(['Protocol', 'Group_ID']).size().reset_index(name='Member_Count')

    print("\n[!] Redundancy Check:")
    for _, row in group_counts.iterrows():
        if row['Member_Count'] < 2:
            print(f"  ⚠️  WARNING: {row['Protocol']} Group {row['Group_ID']} has only {row['Member_Count']} member (no redundancy)")
        else:
            print(f"  ✓ {row['Protocol']} Group {row['Group_ID']}: {row['Member_Count']} members")

    # Check for priority conflicts
    print("\n[!] Priority Conflict Check:")
    for protocol in fhrp['Protocol'].unique():
        for group_id in fhrp[fhrp['Protocol'] == protocol]['Group_ID'].unique():
            group_members = fhrp[(fhrp['Protocol'] == protocol) & (fhrp['Group_ID'] == group_id)]
            priorities = group_members['Priority'].value_counts()

            if len(priorities) == 1 and len(group_members) > 1:
                priority_val = priorities.index[0]
                hosts = ', '.join(group_members['Hostname'].tolist())
                print(f"  ⚠️  WARNING: {protocol} Group {group_id} has duplicate priority {priority_val} on: {hosts}")
            elif len(group_members) > 1:
                print(f"  ✓ {protocol} Group {group_id}: Priorities are differentiated")

    # Check for disabled groups
    print("\n[!] Disabled Groups Check:")
    disabled = fhrp[fhrp['Enabled'] == False]
    if len(disabled) > 0:
        print(f"  ⚠️  WARNING: {len(disabled)} groups are disabled:")
        for _, row in disabled.iterrows():
            print(f"     - {row['Hostname']} {row['Protocol']} Group {row['Group_ID']}")
    else:
        print("  ✓ All FHRP groups are enabled")

    # Check for non-preempt
    print("\n[!] Preempt Check:")
    non_preempt = fhrp[fhrp['Preempt'] == False]
    if len(non_preempt) > 0:
        print(f"  ℹ️  INFO: {len(non_preempt)} groups without preempt:")
        for _, row in non_preempt.iterrows():
            print(f"     - {row['Hostname']} {row['Protocol']} Group {row['Group_ID']}")
    else:
        print("  ✓ All FHRP groups have preempt enabled")

    # Add audit status column
    fhrp['Audit_Status'] = 'OK'
    fhrp.loc[fhrp['Enabled'] == False, 'Audit_Status'] = 'DISABLED'
    fhrp.loc[fhrp['Preempt'] == False, 'Audit_Status'] = 'NO_PREEMPT'

    # Check for groups with only 1 member
    for protocol in fhrp['Protocol'].unique():
        for group_id in fhrp[fhrp['Protocol'] == protocol]['Group_ID'].unique():
            group_members = fhrp[(fhrp['Protocol'] == protocol) & (fhrp['Group_ID'] == group_id)]
            if len(group_members) < 2:
                fhrp.loc[(fhrp['Protocol'] == protocol) & (fhrp['Group_ID'] == group_id), 'Audit_Status'] = 'ORPHANED'

    # Reorder columns for Promtail
    fhrp = fhrp[['Interface', 'Group_ID', 'Priority', 'Preempt', 'Enabled',
                 'Hostname', 'Interface_Name', 'Protocol', 'Audit_Status']]

    save_csv(fhrp, "fhrp_unified")

    print(f"\n✓ Total FHRP instances: {len(fhrp)}")
    print(f"  - HSRP: {len(hsrp_sum)}")
    print(f"  - VRRP: {len(vrrp_sum)}")

print("\n" + "="*60)
print("[+] Analysis complete!")
print(f"[+] CSV files saved to: {OUTPUT_DIR}")
print("="*60)
