def compute_pnl(events: list[dict]) -> float:
    """
    Simplified PnL calculation.
    """
    pnl = 0.0
    for e in events:
        pnl += e.get("pnl", 0.0)
    return pnl
