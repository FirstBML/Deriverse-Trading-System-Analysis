# scripts/run_analytics.py

from pathlib import Path
import pandas as pd

from configs.loader import load_config
from src.analytics.pnl.realised_pnl import build_realised_pnl
from src.analytics.pnl.funding import build_funding
from src.analytics.pnl.equity_curve import build_equity_curve
from src.analytics.trades.activity import build_trade_activity
from src.analytics.metrics.win_rate import build_win_rate
from src.analytics.metrics.drawdown import build_drawdowns
from src.analytics.metrics.exposure import build_exposure
from src.analytics.metrics.fees import build_fees

def main():
    config = load_config("analytics.yaml")

    events_path = config["events_path"]
    out = Path(config["output_path"])
    out.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # Trade activity (diagnostic)
    # -----------------------------
    trades = build_trade_activity(events_path)
    trades.to_csv(out / "trade_activity.csv", index=False)

    # -----------------------------
    # Protocol-truth realised PnL
    # -----------------------------
    realised = build_realised_pnl(events_path)
    realised.to_csv(out / "realised_pnl.csv", index=False)

    # -----------------------------
    # Funding
    # -----------------------------
    funding = build_funding(events_path)
    funding.to_csv(out / "funding.csv", index=False)

    # -----------------------------
    # Equity curve
    # -----------------------------
    equity = build_equity_curve(realised, funding)
    equity.to_csv(out / "equity_curve.csv", index=False)

    # -----------------------------
    # Risk & performance metrics
    # -----------------------------
    win_rate = build_win_rate(realised)
    win_rate.to_csv(out / "win_rate.csv", index=False)

    drawdowns = build_drawdowns(equity)
    drawdowns.to_csv(out / "drawdowns.csv", index=False)

    exposure = build_exposure(events_path)
    pd.DataFrame.from_dict(exposure, orient="index").to_csv(
        out / "exposure.csv"
    )

    fees = build_fees(trades)
    fees.to_csv(out / "fees.csv", index=False)

    print("✅ Analytics pipeline completed successfully")

if __name__ == "__main__":
    main()
