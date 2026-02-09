# configs/loader.py

import yaml
from pathlib import Path
import logging  # ✅ ADD THIS

logger = logging.getLogger(__name__) 

def load_config(path: str) -> dict:
    with open(Path(path), "r") as f:
        return yaml.safe_load(f)