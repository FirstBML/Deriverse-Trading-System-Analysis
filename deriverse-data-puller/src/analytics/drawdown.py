from collections import defaultdict

def build_drawdowns(pnl_records: list[dict]) -> dict:
    """
    Compute max drawdown per trader from a list of pnl records.
    """
    equity = defaultdict(float)
    peak = defaultdict(float)
    drawdown = defaultdict(float)

    for r in pnl_records:
        trader = r["trader"]
        equity[trader] += r["pnl"]

        if equity[trader] > peak[trader]:
            peak[trader] = equity[trader]

        dd = peak[trader] - equity[trader]
        drawdown[trader] = max(drawdown[trader], dd)

    return dict(drawdown)
