import json
from pathlib import Path
from collections import defaultdict

EVENTS = Path("data/normalized/events.jsonl")

def compute_pnl():
    trader_pnl = defaultdict(float)
    market_pnl = defaultdict(float)

    for line in EVENTS.read_text().splitlines():
        e = json.loads(line)
        if e["event_type"] == "settle_pnl":
            trader_pnl[e["trader_id"]] += e["realized_pnl"]
            market_pnl[e["market_id"]] += e["realized_pnl"]

    return trader_pnl, market_pnl
