import pandas as pd
import numpy as np
import json

def build_funding(events_path: str) -> pd.DataFrame:
    rows = []

    with open(events_path) as f:
        for line in f:
            e = json.loads(line)
            if e["event_type"] != "funding":
                continue

            rows.append({
                "timestamp": e["ts"],
                "trader_id": e["trader_id"],
                "market": e["market"],
                "funding_payment": e["funding_payment"],
            })

    return pd.DataFrame(rows)
