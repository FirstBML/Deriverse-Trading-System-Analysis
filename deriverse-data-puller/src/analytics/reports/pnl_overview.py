import os
import json
import pandas as pd
import matplotlib.pyplot as plt

from src.analytics.pnl.pnl_timeseries import build_pnl_timeseries
from src.analytics.pnl.drawdown import compute_drawdown


DATA_PATH = "data/processed/trades.csv"
REPORT_DIR = "data/reports"


def main():
    os.makedirs(REPORT_DIR, exist_ok=True)

    # Load trades
    trades_df = pd.read_csv(DATA_PATH, parse_dates=["trade_date"])

    # Build PnL series
    pnl_df = build_pnl_timeseries(trades_df)
    pnl_df["drawdown"] = compute_drawdown(pnl_df["cumulative_pnl"])

    # Save outputs
    pnl_df.to_csv(f"{REPORT_DIR}/pnl_timeseries.csv", index=False)
    pnl_df.to_json(f"{REPORT_DIR}/pnl_timeseries.json", orient="records")

    summary = {
        "total_pnl": round(pnl_df["pnl"].sum(), 2),
        "max_drawdown": round(pnl_df["drawdown"].min(), 2),
        "trading_days": int(pnl_df.shape[0])
    }

    with open(f"{REPORT_DIR}/pnl_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Plot (saved, no blocking)
    plt.figure(figsize=(10, 5))
    plt.plot(pnl_df["trade_date"], pnl_df["cumulative_pnl"], label="Cumulative PnL")
    plt.fill_between(
        pnl_df["trade_date"],
        pnl_df["drawdown"],
        0,
        alpha=0.3,
        label="Drawdown"
    )
    plt.title("Protocol PnL Performance")
    plt.xlabel("Date")
    plt.ylabel("PnL")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{REPORT_DIR}/pnl_curve.png")
    plt.close()

    print("✅ PnL analytics generated successfully")
    print(summary)


if __name__ == "__main__":
    main()
