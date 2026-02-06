import json
from pathlib import Path
from collections import defaultdict

EVENTS = Path("data/normalized/events.jsonl")

def build_exposure():
    """
    Compute long vs short exposure per market.
    """
    exposure = defaultdict(lambda: {"long": 0, "short": 0})

    for line in EVENTS.read_text().splitlines():
        e = json.loads(line)
        if e["event_type"] == "trade":
            side = "long" if e["side"] == "buy" else "short"
            exposure[e["market_id"]][side] += e["size"]

    return dict(exposure)
