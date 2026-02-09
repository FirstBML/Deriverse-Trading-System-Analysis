import json
import random
import os
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

# -------------------------------
# CONFIG
# -------------------------------
OUTPUT_PATH = Path("data/normalized/events.jsonl")  # ✅ CORRECT: JSONL format
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

SEED = int(os.getenv("MOCK_SEED", "42"))
random.seed(SEED)

# Use timezone-aware datetime
now = datetime.now(timezone.utc)
events = []

def generate_event_id(event_data, index):
    """Generate deterministic event ID."""
    seed_parts = [
        str(event_data.get('event_type', '')),
        str(event_data.get('timestamp', '') if isinstance(event_data.get('timestamp'), str) else ''),
        str(event_data.get('trader_id', '')),
        str(event_data.get('market_id', '')),
        str(index)
    ]
    seed = "|".join(seed_parts)
    return hashlib.sha256(seed.encode()).hexdigest()

def emit(event):
    """Helper to add event with proper formatting and event_id."""
    # Ensure timestamp is ISO string
    if 'timestamp' in event and isinstance(event['timestamp'], datetime):
        event['timestamp'] = event['timestamp'].isoformat().replace("+00:00", "Z")
    
    # Generate event_id if not present
    if 'event_id' not in event:
        event['event_id'] = generate_event_id(event, len(events) + 1)
    
    events.append(event)

# --------------------------------------------------
# 1️⃣ CLEAN OPEN → CLOSE PAIRS (3 positions)
# --------------------------------------------------

# --- WINNING LONG ---
emit({
    "event_type": "open",
    "timestamp": now,
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
    "timestamp": now + timedelta(hours=1),
    "trader_id": "trader_A",
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 120,
    "size": 1,
    "fee": 0.5,
})

# --- WINNING SHORT ---
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=10),
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
    "timestamp": now + timedelta(hours=2),
    "trader_id": "trader_B",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "short",
    "price": 1900,
    "size": 1,
    "fee": 1.0,
})

# --- FORCED LOSING SPOT TRADE ---
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=20),
    "trader_id": "trader_C",
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "buy",
    "price": 100,
    "size": 2,
    "fee": 0.2,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=3),
    "trader_id": "trader_C",
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "buy",
    "price": 92,
    "size": 2,
    "fee": 0.2,
})

# --------------------------------------------------
# 2️⃣ DUPLICATE OPEN (intentional edge case)
# --------------------------------------------------
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=30),
    "trader_id": "trader_A",
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 105,
    "size": 1,
    "fee": 0.5,
})

# --------------------------------------------------
# 3️⃣ CLOSE WITHOUT OPEN (intentional edge case)
# --------------------------------------------------
emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=4),
    "trader_id": "ghost_trader",
    "market_id": "BTC-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 30000,
    "size": 1,
    "fee": 2.0,
})

# --------------------------------------------------
# 4️⃣ OVERSIZED CLOSE (intentional edge case)
# --------------------------------------------------
emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=5),
    "trader_id": "trader_B",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "short",
    "price": 1800,
    "size": 5,
    "fee": 1.5,
})

# --------------------------------------------------
# 5️⃣ TRADE / NOISE EVENTS
# --------------------------------------------------
emit({
    "event_type": "trade",
    "timestamp": now + timedelta(minutes=5),
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
    "timestamp": now + timedelta(minutes=15),
    "trader_id": "trader_Y",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "sell",
    "price": 1995,
    "size": 0.3,
    "fee": 0.1,
})

# --- LOSING LONG PERPETUAL TRADE ---
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=25),
    "trader_id": "trader_D",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 2100,
    "size": 1,
    "fee": 1.0,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=4),
    "trader_id": "trader_D",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "long",
    "price": 2050,
    "size": 1,
    "fee": 1.0,
})

# --------------------------------------------------
# 6️⃣ OPTIONS TRADES 
# --------------------------------------------------

# --- CALL OPTION: Winning trade ---
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=1),
    "trader_id": "trader_E",
    "market_id": "SOL-CALL-120-20241227",
    "product_type": "option",
    "option_type": "call",
    "strike": 120,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "buy",
    "price": 5.0,
    "size": 10,
    "fee": 2.5,
    "delta": 0.65,
    "implied_vol": 0.45,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=25),
    "trader_id": "trader_E",
    "market_id": "SOL-CALL-120-20241227",
    "product_type": "option",
    "option_type": "call",
    "strike": 120,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "sell",
    "price": 8.0,
    "size": 10,
    "fee": 2.5,
    "delta": 0.85,
    "implied_vol": 0.50,
})

# --- PUT OPTION: Losing trade ---
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=2),
    "trader_id": "trader_F",
    "market_id": "ETH-PUT-1900-20241227",
    "product_type": "option",
    "option_type": "put",
    "strike": 1900,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "buy",
    "price": 45.0,
    "size": 5,
    "fee": 5.0,
    "delta": -0.35,
    "implied_vol": 0.55,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=48),
    "trader_id": "trader_F",
    "market_id": "ETH-PUT-1900-20241227",
    "product_type": "option",
    "option_type": "put",
    "strike": 1900,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "sell",
    "price": 20.0,
    "size": 5,
    "fee": 5.0,
    "delta": -0.15,
    "implied_vol": 0.40,
})

# --- OPTION EXERCISE (rare but important) ---
emit({
    "event_type": "exercise",
    "timestamp": now + timedelta(days=30),
    "trader_id": "trader_G",
    "market_id": "BTC-CALL-35000-20241227",
    "product_type": "option",
    "option_type": "call",
    "strike": 35000,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "exercise",
    "price": 35000,
    "size": 2,
    "fee": 50.0,
    "underlying_price": 38000,
})

# --- OPTION EXPIRATION (worthless) ---
emit({
    "event_type": "expire",
    "timestamp": datetime(2024, 12, 27, 23, 59, 59, tzinfo=timezone.utc),
    "trader_id": "trader_H",
    "market_id": "SOL-PUT-80-20241227",
    "product_type": "option",
    "option_type": "put",
    "strike": 80,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "expire",
    "price": 0.0,
    "size": 3,
    "fee": 0.0,
    "underlying_price": 95,
})

# --- PARTIAL CLOSE of options position ---
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=3),
    "trader_id": "trader_I",
    "market_id": "SOL-CALL-110-20241227",
    "product_type": "option",
    "option_type": "call",
    "strike": 110,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "buy",
    "price": 8.0,
    "size": 20,
    "fee": 8.0,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=27),
    "trader_id": "trader_I",
    "market_id": "SOL-CALL-110-20241227",
    "product_type": "option",
    "option_type": "call",
    "strike": 110,
    "expiry": "2024-12-27T23:59:59Z",
    "side": "sell",
    "price": 12.0,
    "size": 10,
    "fee": 6.0,
})

# --------------------------------------------------
# WRITE OUTPUT AS JSONL (one event per line)
# --------------------------------------------------
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    for event in events:
        # Write each event as a separate JSON line
        f.write(json.dumps(event) + "\n")

print(f"✅ Generated {len(events)} mock events → {OUTPUT_PATH} (seed={SEED})")
print(f"   Includes: Perpetuals, Spot, and OPTIONS trades")
print(f"   Format: JSONL (one event per line)")