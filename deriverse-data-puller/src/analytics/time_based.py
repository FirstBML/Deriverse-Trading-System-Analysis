from collections import defaultdict
from typing import List, Dict

def build_time_metrics(pnls: List[Dict]) -> Dict:
    out = defaultdict(float)

    for p in pnls:
        day = p["timestamp"][:10]  # YYYY-MM-DD
        out[day] += p["pnl"]

    return dict(out)
