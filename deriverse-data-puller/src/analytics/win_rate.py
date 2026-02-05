import json
from pathlib import Path
from collections import defaultdict

EVENTS = Path("data/normalized/events.jsonl")

def win_rate():
    wins = defaultdict(int)
    total = defaultdict(int)

    for line in EVENTS.read_text().splitlines():
        e = json.loads(line)
        if e["event_type"] == "settle_pnl":
            total[e["trader_id"]] += 1
            if e["realized_pnl"] > 0:
                wins[e["trader_id"]] += 1

    return {
        t: wins[t] / total[t] if total[t] else 0
        for t in total
    }
