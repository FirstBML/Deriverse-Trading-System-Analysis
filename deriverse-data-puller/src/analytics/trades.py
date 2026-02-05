def compute_trade_count(events: list[dict]) -> int:
    return sum(1 for e in events if e["type"] == "OrderRecord")