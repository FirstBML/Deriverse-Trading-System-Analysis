from typing import List, Dict

def build_pnl(trades: List[Dict]) -> List[Dict]:
    pnl = []

    for t in trades:
        direction = 1 if t["side"] == "buy" else -1

        pnl.append({
            "trade_id": t["trade_id"],
            "trader": t["trader"],
            "market": t["market"],
            "timestamp": t["timestamp"],
            "pnl": direction * t["price"] * t["size"] * 0.001
        })

    return pnl
