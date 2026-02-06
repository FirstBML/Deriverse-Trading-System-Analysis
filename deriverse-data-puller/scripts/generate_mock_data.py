import random
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path("data/raw")
OUT.mkdir(exist_ok=True)

MARKETS = [
    {"market_id": "SOL-PERP", "base": "SOL"},
    {"market_id": "BTC-PERP", "base": "BTC"},
]

TRADERS = [f"trader_{i:03d}" for i in range(1, 21)]

START = datetime(2026, 2, 1)
EVENTS = []

prices = {
    "SOL-PERP": 100.0,
    "BTC-PERP": 42000.0,
}

positions = {}

def ts(i):
    return (START + timedelta(minutes=i)).isoformat() + "Z"

for i in range(500):
    market = random.choice(MARKETS)
    trader = random.choice(TRADERS)
    side = random.choice(["buy", "sell"])

    price_move = random.uniform(-0.5, 0.5)
    prices[market["market_id"]] += price_move

    size = round(random.uniform(0.1, 2.0), 3)
    fee = abs(size * prices[market["market_id"]] * 0.0005)

    trade = {
        "event_type": "trade",
        "ts": ts(i),
        "market_id": market["market_id"],
        "trader_id": trader,
        "side": side,
        "price": round(prices[market["market_id"]], 2),
        "size": size,
        "fee": round(fee, 4),
        "trade_id": str(uuid.uuid4())
    }

    EVENTS.append(trade)

    # occasionally settle pnl
    if i % 20 == 0:
        pnl = random.uniform(-20, 30)
        EVENTS.append({
            "event_type": "settle_pnl",
            "ts": ts(i),
            "market_id": market["market_id"],
            "trader_id": trader,
            "realized_pnl": round(pnl, 2),
            "cumulative_pnl": round(random.uniform(-200, 500), 2)
        })

    # funding
    if i % 50 == 0:
        EVENTS.append({
            "event_type": "funding",
            "ts": ts(i),
            "market_id": market["market_id"],
            "trader_id": trader,
            "funding_rate": 0.0001,
            "payment": round(random.uniform(-5, 5), 2)
        })

    # rare liquidation
    if random.random() < 0.01:
        victim = random.choice(TRADERS)
        EVENTS.append({
            "event_type": "liquidation",
            "ts": ts(i),
            "market_id": market["market_id"],
            "liquidated_trader": victim,
            "liquidator": trader,
            "price": round(prices[market["market_id"]], 2),
            "position_size": round(random.uniform(1, 5), 2),
            "penalty": round(random.uniform(5, 20), 2)
        })

with open(OUT / "raw_events.json", "w") as f:
    json.dump(EVENTS, f, indent=2)

print(f"Generated {len(EVENTS)} protocol events")
