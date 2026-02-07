# scripts/build_trades_table.py

import json
import pandas as pd
from src.analytics.etl.trade_normalizer import normalize_trades

RAW_PATH = "data/raw/raw_events.json"
OUT_PATH = "data/processed/trades.csv"

def main():
    with open(RAW_PATH, "r") as f:
        raw_events = json.load(f)

    events_df = pd.DataFrame(raw_events)

    trades_df = normalize_trades(events_df)

    trades_df.to_csv(OUT_PATH, index=False)
    print(f"✅ {OUT_PATH} created ({len(trades_df)} trades)")

if __name__ == "__main__":
    main()
