
import pandas as pd
import json

def build_trade_activity(events_path: str):
    rows = []

    with open(events_path) as f:
        for line in f:
            e = json.loads(line)
            if e["event_type"] != "trade":
                continue

            rows.append({
                "timestamp": e["ts"],
                "trader_id": e["trader_id"],
                "market": e["market"],
                "side": e["side"],
                "price": e["price"],
                "size": e["size"],
                "fee": e["fee"],
            })

    return pd.DataFrame(rows)
