from typing import List, Dict

def build_trades(events: List[Dict]) -> List[Dict]:
    """
    Convert raw protocol events into normalized trade records.
    """
    trades = []

    for e in events:
        if e["event_type"] != "trade":
            continue

        trades.append({
            "trade_id": e["event_id"],
            "timestamp": e["timestamp"],
            "trader": e["trader"],
            "market": e["market"],
            "side": e["side"],
            "price": e["price"],
            "size": e["size"],
        })

    return trades
