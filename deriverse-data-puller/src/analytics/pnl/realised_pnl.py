import json
import pandas as pd

def build_realised_pnl(events_path: str) -> pd.DataFrame:
    rows = []

    with open(events_path) as f:
        for line in f:
            e = json.loads(line)
            if e["event_type"] != "settle_pnl":
                continue

            rows.append({
                "timestamp": e["ts"],
                "trader_id": e["trader_id"],
                "market": e["market"],
                "realised_pnl": e["realised_pnl"],
            })

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp")
