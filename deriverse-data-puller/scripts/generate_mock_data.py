# deriverse-data-puller/scripts/generate_mock_data.py

import sys
from pathlib import Path

# -------------------------------
# Ensure repo root is in sys.path
# -------------------------------
ROOT = Path(__file__).resolve().parents[1]  # deriverse-data-puller
sys.path.append(str(ROOT))

# -------------------------------
# Standard imports
# -------------------------------
import random
import datetime
import logging

# -------------------------------
# Project imports
# -------------------------------
from src.mock.market_simulator import MarketSimulator
from src.mock.trader_simulator import TraderSimulator
from src.storage.writer import EventWriter
from src.common.logging import get_logger
from configs.loader import load_config

# -------------------------------
# Setup logger
# -------------------------------
logger = get_logger("generate_mock_data")

# -------------------------------
# Load configuration
# -------------------------------
config = load_config("mock_data.yaml")  # example YAML config in configs/

# -------------------------------
# Main function
# -------------------------------
def main():
    logger.info("Starting mock data generation...")

    # Initialize market simulator
    market = MarketSimulator(config["market"])
    # Initialize trader simulator
    trader = TraderSimulator(config["trader"])

    # Simulate 100 events
    events = []
    for i in range(100):
        price_update = market.simulate_price()
        trade_event = trader.simulate_trade(price_update)
        events.append(trade_event)

    # Write events to storage
    writer = EventWriter(config["storage"])
    writer.write(events)

    logger.info(f"Generated {len(events)} mock events successfully.")


# -------------------------------
# Entry point
# -------------------------------
if __name__ == "__main__":
    main()
