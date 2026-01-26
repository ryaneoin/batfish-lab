# SOLUTION TO PROMTAIL LABEL PROBLEM

## The Problem
When trying to add a custom `fhrp` label to Promtail logs, it wasn't appearing even though the regex was working correctly.

## The Solution
Use `static_labels:` instead of `labels:`

### ❌ WRONG - This doesn't work:
```yaml
- labels:
    fhrp: "redundancy"  # Looks for a field called "fhrp" in the data
```

### ✅ CORRECT - This works:
```yaml
- static_labels:
    fhrp: "true"  # Creates a NEW label with this static value
```

## Key Differences

### `labels:` stage
- Takes field names that already exist in extracted data
- Promotes those fields to be queryable labels
- Example: After regex extracts `hostname`, use `labels: hostname:` to make it queryable

### `static_labels:` stage  
- Creates brand new labels that don't exist in the data
- Assigns them static values
- Perfect for tagging logs with categories like `fhrp: "true"`

## Complete Working Example

```yaml
pipeline_stages:
  # 1. Extract fields from CSV with regex
  - regex:
      expression: '^(?P<hostname>[^,]*),(?P<interface>[^,]*),(?P<protocol>VRRP|HSRP)'
  
  # 2. Promote extracted fields to labels
  - labels:
      hostname:      # Uses value from regex capture
      interface:     # Uses value from regex capture
      protocol:      # Uses value from regex capture
  
  # 3. Add custom marker label
  - static_labels:
      fhrp: "true"   # NEW label, not from data
```

## Why The Original Config Didn't Work

When using:
```yaml
- labels:
    fhrp:
```

Promtail looked for a field called `fhrp` in the parsed data, couldn't find it, and silently skipped it. There was no error because Promtail assumed it might appear in some logs.

## Testing in Grafana

After fixing the config:

```logql
# This will now work:
{fhrp="true"}

# Combined queries:
{fhrp="true", protocol="HSRP"}
{fhrp="true", hostname="R1"}
```

## Real-World Use Cases

### Mark all network device logs
```yaml
- static_labels:
    device_type: "network"
```

### Tag by data source
```yaml
- static_labels:
    source: "batfish"
    analysis_type: "fhrp_audit"
```

### Add environment markers
```yaml
- static_labels:
    environment: "production"
    region: "emea"
```

## Quick Test Command

After setup, verify labels are working:
```bash
curl -G http://localhost:3100/loki/api/v1/label
```

Should show:
- hostname
- interface_name  
- protocol
- fhrp  ← This proves static_labels works!

---

**Bottom Line**: 
- `labels:` = use existing fields
- `static_labels:` = create new fields

This distinction is not well documented in Promtail docs, which causes confusion!
