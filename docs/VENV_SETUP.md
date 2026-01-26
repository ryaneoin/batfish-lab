# Python Virtual Environment Setup

## Recommended: Use a Virtual Environment

### Setup (First Time Only)

```bash
cd /Users/eoin/projects/batfish-lab/topology-visualizer

# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Pipeline

```bash
cd /Users/eoin/projects/batfish-lab/topology-visualizer

# Activate venv (if not already active)
source .venv/bin/activate

# Run the pipeline
python run_pipeline.py

# View visualizations
open output/combined_topology.html

# Deactivate when done (optional)
deactivate
```

## Dependencies Required

From `requirements.txt`:
- networkx==3.2.1
- plotly==5.18.0
- pandas==2.1.4
- ciscoconfparse==1.9.41
- kaleido==0.2.1

## Visual Environment Indicator

When your venv is active, you'll see `(.venv)` in your terminal prompt:
```bash
(.venv) eoin@machine:~/projects/batfish-lab/topology-visualizer$
```

## Troubleshooting

### If you get "command not found: python3"
```bash
# Try just 'python'
python -m venv .venv
```

### If pip install fails
```bash
# Upgrade pip first
pip install --upgrade pip
pip install -r requirements.txt
```

### If you need to recreate the venv
```bash
# Remove old venv
rm -rf .venv

# Create fresh venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Alternative: System-Wide Install (Not Recommended)

If you really don't want to use a venv:
```bash
cd /Users/eoin/projects/batfish-lab/topology-visualizer
pip3 install --user -r requirements.txt
python3 run_pipeline.py
```

**But venv is strongly recommended!** It keeps your project dependencies isolated and prevents conflicts with other Python projects.
