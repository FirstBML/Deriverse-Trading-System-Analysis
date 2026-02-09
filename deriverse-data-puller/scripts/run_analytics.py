# scripts/run_analytics.py
import pandas as pd
from pathlib import Path
import io
import logging

from src.analytics.pnl_engine import compute_realized_pnl
from src.analytics.summary import compute_executive_summary

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

NORMALIZED_EVENTS_PATH = Path("data/normalized/events.jsonl")
ANALYTICS_DIR = Path("data/analytics")
POSITIONS_PATH = ANALYTICS_DIR / "positions.csv"
REALIZED_PNL_PATH = ANALYTICS_DIR / "realized_pnl.csv"


def load_events(path: Path) -> pd.DataFrame:
    events = []
    with open(path) as f:
        for line in f:
            events.append(pd.read_json(io.StringIO(line), typ="series"))
    df = pd.DataFrame(events)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def run_analytics(events_df, auto_summary=True, submission_mode=True):
    logger.info(f"Loaded {len(events_df)} events")

    if not submission_mode:
        logger.info(
            f"Event counts: {events_df['event_type'].value_counts().to_dict()}"
        )

    logger.info("Computing realized PnL (truth engine)")
    positions_df, pnl_df = compute_realized_pnl(events_df)

    if positions_df.empty:
        logger.warning("No closed positions found — analytics skipped")
        return None, None

    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    positions_df.to_csv(POSITIONS_PATH, index=False)
    pnl_df.to_csv(REALIZED_PNL_PATH, index=False)

    summary = compute_executive_summary(positions_df, pnl_df)

    if auto_summary:
        print("\n" + "=" * 50)
        print("EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"Total Realized PnL:  ${summary['total_pnl']:,.2f}")
        print(f"Total Fees Paid:     ${summary['total_fees']:,.2f}")
        print(f"Total Trades:        {summary['trade_count']}")
        print(f"Win Rate:            {summary['win_rate']:.1%}")
        print(f"Avg Win:             ${summary['avg_win']:,.2f}")
        print(f"Avg Loss:            ${summary['avg_loss']:,.2f}")
        print(f"Best Trade:          ${summary['best_trade']:,.2f}")
        print(f"Worst Trade:         ${summary['worst_trade']:,.2f}")
        print(f"Avg Duration:        {summary['avg_duration']}")
        print(f"Long Ratio:          {summary['long_ratio']:.1%}")
        print(f"Short Ratio:         {summary['short_ratio']:.1%}")
        print(f"Max Drawdown:        ${summary['max_drawdown']:,.2f}")
        print("=" * 50 + "\n")

    logger.info("Analytics run complete ✅")
    return positions_df, pnl_df


def main():
    logger.info("=" * 60)
    logger.info("Starting Deriverse Analytics Pipeline")
    logger.info("=" * 60)

    if not NORMALIZED_EVENTS_PATH.exists():
        logger.error("Normalized events not found. Run ingestion first.")
        return

    events_df = load_events(NORMALIZED_EVENTS_PATH)
    run_analytics(events_df)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
