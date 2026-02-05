def compute_max_drawdown(pnl_series: list[float]) -> float:
    peak = 0.0
    max_dd = 0.0

    cumulative = 0.0
    for pnl in pnl_series:
        cumulative += pnl
        peak = max(peak, cumulative)
        max_dd = min(max_dd, cumulative - peak)

    return max_dd
