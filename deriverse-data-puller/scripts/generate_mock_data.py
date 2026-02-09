import json
from datetime import datetime, timedelta
from pathlib import Path

OUTPUT_PATH = Path("data/normalized/events.jsonl")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

now = datetime.utcnow()

events = []

def emit(event):
    events.append(event)

# --------------------------------------------------
# 1️⃣ CLEAN OPEN → CLOSE PAIRS (3 positions)
# --------------------------------------------------
emit({
    "event_type": "open",
    "timestamp": now.isoformat(),
    "trader_id": "trader_A",
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 100,
    "size": 1,
    "fee": 0.5,
})

emit({
    "event_type": "close",
    "timestamp": (now + timedelta(hours=1)).isoformat(),
    "trader_id": "trader_A",
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 120,
    "size": 1,
    "fee": 0.5,
})

emit({
    "event_type": "open",
    "timestamp": (now + timedelta(minutes=10)).isoformat(),
    "trader_id": "trader_B",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "short",
    "price": 2000,
    "size": 1,
    "fee": 1.0,
})

emit({
    "event_type": "close",
    "timestamp": (now + timedelta(hours=2)).isoformat(),
    "trader_id": "trader_B",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "short",
    "price": 1900,
    "size": 1,
    "fee": 1.0,
})

emit({
    "event_type": "open",
    "timestamp": (now + timedelta(minutes=20)).isoformat(),
    "trader_id": "trader_C",
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "buy",
    "price": 90,
    "size": 2,
    "fee": 0.2,
})

emit({
    "event_type": "close",
    "timestamp": (now + timedelta(hours=3)).isoformat(),
    "trader_id": "trader_C",
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "buy",
    "price": 95,
    "size": 2,
    "fee": 0.2,
})

# --------------------------------------------------
# 2️⃣ DUPLICATE OPEN (intentional)
# --------------------------------------------------
emit({
    "event_type": "open",
    "timestamp": (now + timedelta(minutes=30)).isoformat(),
    "trader_id": "trader_A",
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 105,
    "size": 1,
    "fee": 0.5,
})

# --------------------------------------------------
# 3️⃣ CLOSE WITHOUT OPEN (intentional)
# --------------------------------------------------
emit({
    "event_type": "close",
    "timestamp": (now + timedelta(hours=4)).isoformat(),
    "trader_id": "ghost_trader",
    "market_id": "BTC-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 30000,
    "size": 1,
    "fee": 2.0,
})

emit({
    "event_type": "close",
    "timestamp": (now + timedelta(hours=5)).isoformat(),
    "trader_id": "trader_B",
    "market_id": "DOGE-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 0.1,
    "size": 10,
    "fee": 0.1,
})

# --------------------------------------------------
# 4️⃣ TRADE / NOISE EVENTS
# --------------------------------------------------
emit({
    "event_type": "trade",
    "timestamp": (now + timedelta(minutes=5)).isoformat(),
    "trader_id": "trader_X",
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "buy",
    "price": 101,
    "size": 0.5,
    "fee": 0.1,
})

emit({
    "event_type": "trade",
    "timestamp": (now + timedelta(minutes=15)).isoformat(),
    "trader_id": "trader_Y",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "sell",
    "price": 1995,
    "size": 0.3,
    "fee": 0.1,
})

# --------------------------------------------------
# WRITE JSONL
# --------------------------------------------------
with open(OUTPUT_PATH, "w") as f:
    for e in events:
        f.write(json.dumps(e) + "\n")

print(f"Generated {len(events)} mock events → {OUTPUT_PATH}")
