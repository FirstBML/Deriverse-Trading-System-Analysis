from collections import defaultdict
import json

def options_trader_pnl(events_path: str):
    pnl = defaultdict(float)

    with open(events_path) as f:
        for line in f:
            e = json.loads(line)

            if e["product_type"] != "option":
                continue

            trader = e["trader_id"]

            pnl[trader] -= e.get("premium", 0.0)
            pnl[trader] += e.get("exercise_pnl", 0.0)

    return pnl
