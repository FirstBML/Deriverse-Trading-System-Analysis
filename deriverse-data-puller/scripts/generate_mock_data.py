# scripts/generate_mock_data.py
import json
import random
import os
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ✅ Output to configs/mock_data.json (JSON array format)
OUTPUT_PATH = Path("configs/mock_data.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

SEED = int(os.getenv("MOCK_SEED", "42"))
random.seed(SEED)

now = datetime.now(timezone.utc)
events = []

# ✅ REALISTIC SOLANA WALLET ADDRESSES (base58-like)
WALLETS = {
    "alice": "7KNXqvHu2QWvDq8cGPGvKZhFvYnz3kQ5mL8xRt2Bp9uV",
    "bob": "5FxM2nQwP4vYkL9mT3xRd8eJbWp7sN6gH2cKt9uVfXyZ",
    "charlie": "9DpT3vHx5kN2qL8mR7wYfJ6bP4sE1cG9nZ5tK3uVwXyA",
    "diana": "4MqL8vYx2kP9nT7wR5fH3bJ6sE1cG4nZ8tK2uVwXyBpQ",
    "evan": "6NrK9wZx3mQ8pU7vS4gI2dL5tF1eH7oA9yM3xVbCwRtE",
    "fiona": "8QtN2xWy5lR7mV9uT6hK3eM4pG1fJ8nB7zL4wVcDxSeF",
    "george": "3HsJ7yVz4nQ6oW8tS5gL2fN9rH1eK6mC8xM5vBdEwRuG",
    "hannah": "2PrM8xUz6oT5nY7vR4jL3gP1sH9eN4mD6zK8wCfGxQuH",
    "ivan": "5TpQ9yXz7mS6oV8uR3kM2hN4rJ1fL5nE7xP6wDgHySvI",
    "julia": "4WqP8zYx5nT7mU9tS2lN6jM3rK1gH4oC8yL5vEfJxRwK",
}

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
    if 'timestamp' in event and isinstance(event['timestamp'], datetime):
        event['timestamp'] = event['timestamp'].isoformat().replace("+00:00", "Z")
    
    if 'event_id' not in event:
        event['event_id'] = generate_event_id(event, len(events) + 1)
    
    # ✅ ADD THIS: Assign order type
    if event['event_type'] in ['open', 'close']:
        # Randomly assign order types for diversity
        event['order_type'] = random.choice(['market', 'limit', 'stop'])
    
    events.append(event)
    
# --------------------------------------------------
# 1️⃣ SPOT TRADES (buy → sell) - 1 WIN, 1 LOSS
# --------------------------------------------------

# WINNING SPOT TRADE
emit({
    "event_type": "open",
    "timestamp": now,
    "trader_id": WALLETS["alice"],
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 100,
    "size": 10,
    "fee": 0.5,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=2),
    "trader_id": WALLETS["alice"],
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "sell",  # ✅ FIXED: Changed from "long" to "sell"
    "price": 110,
    "size": 10,
    "fee": 0.5,
})

# LOSING SPOT TRADE
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=10),
    "trader_id": WALLETS["bob"],
    "market_id": "ETH/USDC",
    "product_type": "spot",
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 2000,
    "size": 5,
    "fee": 1.0,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=3),
    "trader_id": WALLETS["bob"],
    "market_id": "ETH/USDC",
    "product_type": "spot",
    "side": "sell",  # ✅ FIXED: Changed from "long" to "sell"
    "price": 1950,
    "size": 5,
    "fee": 1.0,
})

# --------------------------------------------------
# 2️⃣ PERPETUAL TRADES (long/short) - 2 WINS, 1 LOSS
# --------------------------------------------------

# WINNING LONG PERP
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=20),
    "trader_id": WALLETS["charlie"],
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "long",  # ✅ CORRECT: Perps use long/short
    "price": 100,
    "size": 10,
    "fee": 0.5,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=4),
    "trader_id": WALLETS["charlie"],
    "market_id": "SOL-PERP",
    "product_type": "perp",
    "side": "long",  # ✅ CORRECT: Same side for perp close
    "price": 120,
    "size": 10,
    "fee": 0.5,
})

# WINNING SHORT PERP
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=30),
    "trader_id": WALLETS["diana"],
    "market_id": "BTC-PERP",
    "product_type": "perp",
    "side": "short",  # ✅ CORRECT: Perps use long/short
    "price": 50000,
    "size": 1,
    "fee": 5.0,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=5),
    "trader_id": WALLETS["diana"],
    "market_id": "BTC-PERP",
    "product_type": "perp",
    "side": "short",  # ✅ CORRECT: Same side for perp close
    "price": 48000,
    "size": 1,
    "fee": 5.0,
})

# LOSING LONG PERP
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=40),
    "trader_id": WALLETS["evan"],
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "long",  # ✅ CORRECT: Perps use long/short
    "price": 2100,
    "size": 5,
    "fee": 2.0,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=6),
    "trader_id": WALLETS["evan"],
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "long",  # ✅ CORRECT: Same side for perp close
    "price": 2050,
    "size": 5,
    "fee": 2.0,
})

# --------------------------------------------------
# 3️⃣ OPTION TRADES - COMPLETE LIFECYCLE
# --------------------------------------------------

# === LONG CALL OPTION: Buy call, sell it back (Winning) ===
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=1),
    "trader_id": WALLETS["fiona"],
    "market_id": "SOL-CALL-120-FEB28",
    "product_type": "option",
    "option_type": "call",
    "strike": 120,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 5.0,
    "size": 10,
    "fee": 0.5,
    "delta": 0.65,
    "implied_vol": 0.45,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=24),
    "trader_id": WALLETS["fiona"],
    "market_id": "SOL-CALL-120-FEB28",
    "product_type": "option",
    "option_type": "call",
    "strike": 120,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "sell",  # ✅ FIXED: Changed from "long" to "sell"
    "price": 8.0,
    "size": 10,
    "fee": 0.5,
    "delta": 0.85,
    "implied_vol": 0.50,
})

# === SHORT PUT OPTION: Sell put, buy it back (Winning) ===
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=1, minutes=30),
    "trader_id": WALLETS["george"],
    "market_id": "SOL-PUT-90-FEB28",
    "product_type": "option",
    "option_type": "put",
    "strike": 90,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "sell",  # ✅ CORRECT: Selling to open short position
    "price": 4.0,
    "size": 15,
    "fee": 0.7,
    "delta": -0.25,
    "implied_vol": 0.40,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=36),
    "trader_id": WALLETS["george"],
    "market_id": "SOL-PUT-90-FEB28",
    "product_type": "option",
    "option_type": "put",
    "strike": 90,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "buy",  # ✅ CORRECT: Buying to close short position
    "price": 1.5,
    "size": 15,
    "fee": 0.7,
    "delta": -0.10,
    "implied_vol": 0.30,
})

# === LONG PUT OPTION: Buy put, sell it back (Losing) ===
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=2),
    "trader_id": WALLETS["hannah"],
    "market_id": "ETH-PUT-1900-FEB28",
    "product_type": "option",
    "option_type": "put",
    "strike": 1900,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 45.0,
    "size": 5,
    "fee": 1.0,
    "delta": -0.35,
    "implied_vol": 0.55,
})

emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=48),
    "trader_id": WALLETS["hannah"],
    "market_id": "ETH-PUT-1900-FEB28",
    "product_type": "option",
    "option_type": "put",
    "strike": 1900,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "sell",  # ✅ FIXED: Changed from "long" to "sell"
    "price": 20.0,
    "size": 5,
    "fee": 1.0,
    "delta": -0.15,
    "implied_vol": 0.40,
})

# === LONG CALL: Buy and EXERCISE (ITM) - Winning ===
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=3),
    "trader_id": WALLETS["ivan"],
    "market_id": "BTC-CALL-50000-FEB28",
    "product_type": "option",
    "option_type": "call",
    "strike": 50000,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 2000.0,
    "size": 1,
    "fee": 10.0,
})

emit({
    "event_type": "exercise",
    "timestamp": now + timedelta(days=17),
    "trader_id": WALLETS["ivan"],
    "market_id": "BTC-CALL-50000-FEB28",
    "product_type": "option",
    "option_type": "call",
    "strike": 50000,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "exercise",  # ✅ CORRECT: Exercise is its own side
    "size": 1,
    "fee": 10.0,
    "underlying_price": 55000,
})

# === LONG PUT: Buy and let EXPIRE worthless (Losing) ===
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=4),
    "trader_id": WALLETS["julia"],
    "market_id": "SOL-PUT-80-FEB28",
    "product_type": "option",
    "option_type": "put",
    "strike": 80,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 3.0,
    "size": 20,
    "fee": 0.2,
})

emit({
    "event_type": "expire",
    "timestamp": now + timedelta(days=18),
    "trader_id": WALLETS["julia"],
    "market_id": "SOL-PUT-80-FEB28",
    "product_type": "option",
    "option_type": "put",
    "strike": 80,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "expire",  # ✅ CORRECT: Expire is its own side
    "price": 0.0,
    "size": 20,
    "fee": 0.0,
    "underlying_price": 95,
})

# === PARTIAL CLOSE: Long call, close in 2 tranches ===
emit({
    "event_type": "open",
    "timestamp": now + timedelta(hours=5),
    "trader_id": WALLETS["alice"],
    "market_id": "SOL-CALL-110-FEB28",
    "product_type": "option",
    "option_type": "call",
    "strike": 110,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 8.0,
    "size": 20,
    "fee": 1.0,
})

# First partial close
emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=26),
    "trader_id": WALLETS["alice"],
    "market_id": "SOL-CALL-110-FEB28",
    "product_type": "option",
    "option_type": "call",
    "strike": 110,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "sell",  # ✅ FIXED: Changed from "long" to "sell"
    "price": 12.0,
    "size": 10,
    "fee": 0.5,
})

# Second partial close
emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=50),
    "trader_id": WALLETS["alice"],
    "market_id": "SOL-CALL-110-FEB28",
    "product_type": "option",
    "option_type": "call",
    "strike": 110,
    "expiry": (now + timedelta(days=18)).isoformat().replace("+00:00", "Z"),
    "side": "sell",  # ✅ FIXED: Changed from "long" to "sell"
    "price": 15.0,
    "size": 10,
    "fee": 0.5,
})

# --------------------------------------------------
# 4️⃣ EDGE CASES (for robustness testing)
# --------------------------------------------------

# Duplicate open (should be ignored)
emit({
    "event_type": "open",
    "timestamp": now + timedelta(minutes=60),
    "trader_id": WALLETS["alice"],
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "buy",  # ✅ FIXED: Changed from "long" to "buy"
    "price": 105,
    "size": 5,
    "fee": 0.3,
})

# Close without open (should be rejected)
emit({
    "event_type": "close",
    "timestamp": now + timedelta(hours=10),
    "trader_id": "GhostWallet1111111111111111111111111111",
    "market_id": "GHOST-PERP",
    "product_type": "perp",
    "side": "long",  # ✅ CORRECT: Perps use long/short
    "price": 999,
    "size": 1,
    "fee": 0.1,
})

# Trade events (informational only)
emit({
    "event_type": "trade",
    "timestamp": now + timedelta(minutes=15),
    "trader_id": "MarketMaker1111111111111111111111111",
    "market_id": "SOL/USDC",
    "product_type": "spot",
    "side": "buy",  # ✅ CORRECT: Trades can use buy/sell
    "price": 101,
    "size": 100,
    "fee": 1.0,
})

emit({
    "event_type": "trade",
    "timestamp": now + timedelta(minutes=45),
    "trader_id": "MarketMaker1111111111111111111111111",
    "market_id": "ETH-PERP",
    "product_type": "perp",
    "side": "sell",  # ✅ CORRECT: Trades can use buy/sell
    "price": 2105,
    "size": 50,
    "fee": 5.0,
})

# --------------------------------------------------
# ✅ WRITE OUTPUT AS JSON ARRAY
# --------------------------------------------------
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)

print(f"✅ Generated {len(events)} mock events → {OUTPUT_PATH} (seed={SEED})")
print(f"   Wallets: {len(WALLETS)} realistic Solana addresses")
print(f"   Includes: Spot (buy/sell), Perps (long/short), Options (buy/sell/exercise/expire)")
print(f"   Format: JSON array - ready for ingestion")