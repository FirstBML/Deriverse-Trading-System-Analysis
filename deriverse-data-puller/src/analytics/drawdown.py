import json
from pathlib import Path
from collections import defaultdict

EVENTS = Path("data/normalized/events.jsonl")

def compute_drawdown():
    peak = defaultdict(float)
    drawdown = defaultdict(float)

    for line in EVENTS.read_text().splitlines():
        e = json.loads(line)
        if e["event_type"] == "settle_pnl":
            trader = e["trader_id"]
            cum = e["cumulative_pnl"]
            peak[trader] = max(peak[trader], cum)
            drawdown[trader] = min(drawdown[trader], cum - peak[trader])

    return drawdown
