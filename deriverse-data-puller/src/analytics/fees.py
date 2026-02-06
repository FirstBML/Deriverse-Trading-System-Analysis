from typing import List, Dict
from collections import defaultdict

def build_fees(trades: List[Dict], fee_rate=0.0005):
    trader_fees = defaultdict(float)
    market_fees = defaultdict(float)

    for t in trades:
        fee = abs(t["price"] * t["size"]) * fee_rate
        trader_fees[t["trader"]] += fee
        market_fees[t["market"]] += fee

    return dict(trader_fees), dict(market_fees)
