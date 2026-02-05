import json
from pathlib import Path
from collections import defaultdict

EVENTS = Path("data/normalized/events.jsonl")

def compute_fees():
    trader = defaultdict(float)
    market = defaultdict(float)

    for line in EVENTS.read_text().splitlines():
        e = json.loads(line)
        if e["event_type"] == "trade":
            trader[e["trader_id"]] += e["fee"]
            market[e["market_id"]] += e["fee"]

    return trader, market
