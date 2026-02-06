# scripts/run_analytics.py

from src.analytics.trades import build_trades
from src.analytics.pnl import build_pnl
from src.analytics.win_rate import build_win_rate
from src.analytics.drawdown import build_drawdowns
from src.analytics.exposure import build_exposure
from src.analytics.fees import build_fees
from src.analytics.time_based import build_time_metrics
from src.common.logging import get_logger
from configs.loader import load_config

logger = get_logger(__name__)


def main():
    config = load_config("analytics.yaml")

    logger.info("Starting analytics computation")

    build_trades(config)
    build_pnl(config)
    build_win_rate(config)
    build_drawdowns(config)
    build_exposure(config)
    build_fees(config)
    build_time_metrics(config)

    logger.info("Analytics tables successfully built")


if __name__ == "__main__":
    main()
import json
from pathlib import Path

from src.analytics.pnl import compute_pnl
from src.analytics.win_rate import compute_win_rate
from src.analytics.drawdown import compute_max_drawdown
from src.analytics.fees import compute_total_fees


RAW_DIR = Path("data/raw_events")
OUT_DIR = Path("data/analytics")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_events():
    events = []
    for f in RAW_DIR.glob("*.jsonl"):
        with open(f) as fh:
            for line in fh:
                events.append(json.loads(line))
    return events


def run():
    events = load_events()

    settles = [e for e in events if e["type"] == "SettlePnlRecord"]

    pnl_series = [s["pnl"] for s in settles]

    metrics = {
        "total_pnl": compute_pnl(settles),
        "win_rate": compute_win_rate(settles),
        "max_drawdown": compute_max_drawdown(pnl_series),
        "total_fees": compute_total_fees(events),
    }

    with open(OUT_DIR / "summary.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    run()
