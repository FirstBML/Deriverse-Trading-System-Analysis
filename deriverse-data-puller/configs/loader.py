import yaml
from pathlib import Path

def load_config(filename):
    path = Path(__file__).parent / filename
    with open(path) as f:
        return yaml.safe_load(f)
