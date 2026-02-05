import json
from pathlib import Path
from collections import defaultdict

EVENTS = Path("data/normalized/events.jsonl")

def long_short_ratio():
    exposure = defaultdict(lambda: {"long": 0, "short": 0})

    for line in EVENTS.read_text().splitlines():
        e = json.loads(line)
        if e["event_type"] == "trade":
            side = "long" if e["side"] == "buy" else "short"
            exposure[e["market_id"]][side] += e["size"]

    return exposure
