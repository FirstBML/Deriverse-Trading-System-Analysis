import pandas as pd
from pathlib import Path
import io
import logging
from datetime import datetime, timedelta, UTC
from src.analytics.pnl_engine import compute_realized_pnl
from src.analytics.summary import compute_executive_summary

now = datetime.now(UTC)
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
    """Load events from JSONL file with flexible timestamp parsing."""
    events = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                events.append(pd.read_json(io.StringIO(line), typ="series"))
    
    if not events:
        logger.warning(f"No events found in {path}")
        return pd.DataFrame()
    
    df = pd.DataFrame(events)
    
    # FIX: Use format='ISO8601' to handle different timestamp formats
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"], format='ISO8601', utc=True)
    except Exception as e:
        logger.warning(f"ISO8601 parsing failed, trying mixed format: {e}")
        df["timestamp"] = pd.to_datetime(df["timestamp"], format='mixed', utc=True)
    
    return df


def run_analytics(events_df, auto_summary=True, submission_mode=True):
    if events_df.empty:
        logger.error("No events to analyze")
        return None, None
    
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
        logger.error(f"Normalized events not found at {NORMALIZED_EVENTS_PATH}")
        logger.error("Run 'python -m scripts.generate_mock_data' first")
        return

    events_df = load_events(NORMALIZED_EVENTS_PATH)
    run_analytics(events_df)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()