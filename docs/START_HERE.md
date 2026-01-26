# ⚡ IMPORTANT: Use Virtual Environment

## Quick Setup (Recommended)

```bash
cd /Users/eoin/projects/batfish-lab/topology-visualizer

# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the pipeline
python run_pipeline.py

# 5. View visualizations
open output/combined_topology.html
```

## Why Virtual Environment?

✅ **Isolated dependencies** - Won't conflict with other Python projects  
✅ **Clean uninstall** - Just delete the `.venv/` folder  
✅ **Reproducible** - Same dependencies every time  
✅ **Best practice** - Industry standard for Python projects

## You'll Know It's Working

When the venv is active, your terminal will show:
```bash
(.venv) eoin@machine:~/projects/batfish-lab/topology-visualizer$
```

## Deactivate When Done

```bash
deactivate
```

## See Full Details

- `QUICKSTART.md` - All commands in one place
- `SETUP_COMPLETE.md` - Complete project documentation

---

**TL;DR:** Always run `source .venv/bin/activate` before running the pipeline!
