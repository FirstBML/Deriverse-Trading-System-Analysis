# scripts/generate_mock_data.py 
"""
Generate curated mock trading data for Deriverse analytics demo.

This script creates a carefully designed dataset that showcases:
- Profitable and losing trades across all product types
- Risk management (5 liquidation events)
- Active positions (open trades)
- Complete options lifecycle (buy, sell, exercise, expire)
- Historical data with gaps (realistic trading patterns)
- Edge cases for robustness testing
"""

import json
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUTPUT_PATH = Path("configs/mock_data.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Use historical base date (30 days ago) for realistic data
now = datetime.now(timezone.utc)
base_date = now - timedelta(days=30)  # Start 30 days in the past

events = []

# Realistic Solana wallet addresses (base58 format)
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
    """Generate deterministic event ID from event data."""
    seed_parts = [
        str(event_data.get('event_type', '')),
        str(event_data.get('timestamp', '') if isinstance(event_data.get('timestamp'), str) else ''),
        str(event_data.get('trader_id', '')),
        str(event_data.get('market_id', '')),
        str(index)
    ]
    return hashlib.sha256("|".join(seed_parts).encode()).hexdigest()


def emit(event, order_type="market"):
    """
    Add event to output array with automatic formatting.
    
    Args:
        event: Event dictionary with trading data
        order_type: Type of order (market/limit/stop) - defaults to market
    """
    # Format timestamp
    if 'timestamp' in event and isinstance(event['timestamp'], datetime):
        event['timestamp'] = event['timestamp'].isoformat().replace("+00:00", "Z")
    
    # Generate event ID
    if 'event_id' not in event:
        event['event_id'] = generate_event_id(event, len(events) + 1)
    
    # Add order type for position events
    if event['event_type'] in ['open', 'close', 'liquidation']:
        event['order_type'] = order_type
    
    events.append(event)


# ================================================================================
# SPOT TRADES - Simple buy/sell with clear profit/loss
# ================================================================================

# Day 1 - Winning spot trade (Alice: +$99)
emit({"event_type": "open", "timestamp": base_date, "trader_id": WALLETS["alice"], 
      "market_id": "SOL/USDC", "product_type": "spot", "side": "buy", 
      "price": 100, "size": 10, "fee": 0.5}, order_type="stop")

emit({"event_type": "close", "timestamp": base_date + timedelta(hours=2), "trader_id": WALLETS["alice"], 
      "market_id": "SOL/USDC", "product_type": "spot", "side": "sell", 
      "price": 110, "size": 10, "fee": 0.5}, order_type="market")

# Day 3 - Losing spot trade (Bob: -$252) [GAP: Day 2 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=2, minutes=10), "trader_id": WALLETS["bob"], 
      "market_id": "ETH/USDC", "product_type": "spot", "side": "buy", 
      "price": 2000, "size": 5, "fee": 1.0}, order_type="market")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=2, hours=3), "trader_id": WALLETS["bob"], 
      "market_id": "ETH/USDC", "product_type": "spot", "side": "sell", 
      "price": 1950, "size": 5, "fee": 1.0}, order_type="stop")


# ================================================================================
# PERPETUAL TRADES - Long/short positions with liquidations
# ================================================================================

# Day 5 - Winning long perp (Charlie: +$199) [GAP: Day 4 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=4, minutes=20), "trader_id": WALLETS["charlie"], 
      "market_id": "SOL-PERP", "product_type": "perp", "side": "long", 
      "price": 100, "size": 10, "fee": 0.5}, order_type="limit")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=4, hours=4), "trader_id": WALLETS["charlie"], 
      "market_id": "SOL-PERP", "product_type": "perp", "side": "long", 
      "price": 120, "size": 10, "fee": 0.5}, order_type="market")

# Day 7 - Winning short perp (Diana: +$1990) [GAP: Day 6 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=6, minutes=30), "trader_id": WALLETS["diana"], 
      "market_id": "BTC-PERP", "product_type": "perp", "side": "short", 
      "price": 50000, "size": 1, "fee": 5.0}, order_type="market")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=6, hours=5), "trader_id": WALLETS["diana"], 
      "market_id": "BTC-PERP", "product_type": "perp", "side": "short", 
      "price": 48000, "size": 1, "fee": 5.0}, order_type="market")

# Day 8 - Losing long perp (Evan: -$254)
emit({"event_type": "open", "timestamp": base_date + timedelta(days=7, minutes=40), "trader_id": WALLETS["evan"], 
      "market_id": "ETH-PERP", "product_type": "perp", "side": "long", 
      "price": 2100, "size": 5, "fee": 2.0}, order_type="stop")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=7, hours=6), "trader_id": WALLETS["evan"], 
      "market_id": "ETH-PERP", "product_type": "perp", "side": "long", 
      "price": 2050, "size": 5, "fee": 2.0}, order_type="market")

# ================================================================================
# LIQUIDATION EVENTS (5 total for detailed analysis)
# ================================================================================

# LIQUIDATION 1 - Day 10: SOL-PERP (Diana: -$880) [GAP: Day 9 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=9, hours=1), "trader_id": WALLETS["diana"], 
      "market_id": "SOL-PERP", "product_type": "perp", "side": "long", 
      "price": 105, "size": 50, "fee": 5.0}, order_type="market")

emit({"event_type": "liquidation", "timestamp": base_date + timedelta(days=9, hours=2), "trader_id": WALLETS["diana"], 
      "market_id": "SOL-PERP", "product_type": "perp", "side": "long", 
      "price": 88, "size": 50, "fee": 25.0}, order_type="liquidation")

# LIQUIDATION 2 - Day 12: ETH-PERP (Bob: -$1,520) [GAP: Day 11 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=11, hours=3), "trader_id": WALLETS["bob"], 
      "market_id": "ETH-PERP", "product_type": "perp", "side": "long", 
      "price": 2200, "size": 10, "fee": 3.0}, order_type="market")

emit({"event_type": "liquidation", "timestamp": base_date + timedelta(days=11, hours=8), "trader_id": WALLETS["bob"], 
      "market_id": "ETH-PERP", "product_type": "perp", "side": "long", 
      "price": 2050, "size": 10, "fee": 20.0}, order_type="liquidation")

# LIQUIDATION 3 - Day 15: BTC-PERP (Evan: -$2,530) [GAP: Days 13-14 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=14, hours=2), "trader_id": WALLETS["evan"], 
      "market_id": "BTC-PERP", "product_type": "perp", "side": "short", 
      "price": 49000, "size": 2, "fee": 8.0}, order_type="limit")

emit({"event_type": "liquidation", "timestamp": base_date + timedelta(days=14, hours=12), "trader_id": WALLETS["evan"], 
      "market_id": "BTC-PERP", "product_type": "perp", "side": "short", 
      "price": 50250, "size": 2, "fee": 30.0}, order_type="liquidation")

# LIQUIDATION 4 - Day 18: AVAX-PERP (Charlie: -$342) [GAP: Days 16-17 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=17, hours=5), "trader_id": WALLETS["charlie"], 
      "market_id": "AVAX-PERP", "product_type": "perp", "side": "long", 
      "price": 38.5, "size": 100, "fee": 4.0}, order_type="market")

emit({"event_type": "liquidation", "timestamp": base_date + timedelta(days=17, hours=14), "trader_id": WALLETS["charlie"], 
      "market_id": "AVAX-PERP", "product_type": "perp", "side": "long", 
      "price": 35.2, "size": 100, "fee": 12.0}, order_type="liquidation")

# LIQUIDATION 5 - Day 20: SOL-PERP (Alice: -$615) [GAP: Day 19 skipped]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=19, hours=4), "trader_id": WALLETS["alice"], 
      "market_id": "SOL-PERP", "product_type": "perp", "side": "short", 
      "price": 115, "size": 30, "fee": 3.5}, order_type="stop")

emit({"event_type": "liquidation", "timestamp": base_date + timedelta(days=19, hours=9), "trader_id": WALLETS["alice"], 
      "market_id": "SOL-PERP", "product_type": "perp", "side": "short", 
      "price": 135, "size": 30, "fee": 18.0}, order_type="liquidation")


# ================================================================================
# OPTION TRADES - Complete lifecycle (buy, sell, exercise, expire)
# ================================================================================

# Day 21 - Long call - profitable close (Fiona: +$29)
emit({"event_type": "open", "timestamp": base_date + timedelta(days=20, hours=1), "trader_id": WALLETS["fiona"], 
      "market_id": "SOL-CALL-120-JAN15", "product_type": "option", "option_type": "call", 
      "strike": 120, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "buy", "price": 5.0, "size": 10, "fee": 0.5, 
      "delta": 0.65, "implied_vol": 0.45}, order_type="stop")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=21, hours=0), "trader_id": WALLETS["fiona"], 
      "market_id": "SOL-CALL-120-JAN15", "product_type": "option", "option_type": "call", 
      "strike": 120, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "sell", "price": 8.0, "size": 10, "fee": 0.5, 
      "delta": 0.85, "implied_vol": 0.50}, order_type="stop")

# Day 22 - Short put - profitable buyback (George: +$36.1)
emit({"event_type": "open", "timestamp": base_date + timedelta(days=21, hours=1, minutes=30), "trader_id": WALLETS["george"], 
      "market_id": "SOL-PUT-90-JAN15", "product_type": "option", "option_type": "put", 
      "strike": 90, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "sell", "price": 4.0, "size": 15, "fee": 0.7, 
      "delta": -0.25, "implied_vol": 0.40}, order_type="stop")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=22, hours=12), "trader_id": WALLETS["george"], 
      "market_id": "SOL-PUT-90-JAN15", "product_type": "option", "option_type": "put", 
      "strike": 90, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "buy", "price": 1.5, "size": 15, "fee": 0.7, 
      "delta": -0.10, "implied_vol": 0.30}, order_type="market")

# Day 23 - Long put - losing close (Hannah: -$127)
emit({"event_type": "open", "timestamp": base_date + timedelta(days=22, hours=2), "trader_id": WALLETS["hannah"], 
      "market_id": "ETH-PUT-1900-JAN15", "product_type": "option", "option_type": "put", 
      "strike": 1900, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "buy", "price": 45.0, "size": 5, "fee": 1.0, 
      "delta": -0.35, "implied_vol": 0.55}, order_type="stop")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=24, hours=0), "trader_id": WALLETS["hannah"], 
      "market_id": "ETH-PUT-1900-JAN15", "product_type": "option", "option_type": "put", 
      "strike": 1900, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "sell", "price": 20.0, "size": 5, "fee": 1.0, 
      "delta": -0.15, "implied_vol": 0.40}, order_type="limit")

# Day 25 - Long call - exercised ITM (Ivan: +$2980)
emit({"event_type": "open", "timestamp": base_date + timedelta(days=24, hours=3), "trader_id": WALLETS["ivan"], 
      "market_id": "BTC-CALL-50000-JAN15", "product_type": "option", "option_type": "call", 
      "strike": 50000, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "buy", "price": 2000.0, "size": 1, "fee": 10.0}, order_type="market")

# Day 38 - Exercise happens near expiry
emit({"event_type": "exercise", "timestamp": base_date + timedelta(days=37), "trader_id": WALLETS["ivan"], 
      "market_id": "BTC-CALL-50000-JAN15", "product_type": "option", "option_type": "call", 
      "strike": 50000, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "exercise", "size": 1, "fee": 10.0, "underlying_price": 55000})

# Day 26 - Long put - expired worthless (Julia: -$60.2) [GAP: Day 25 trading]
emit({"event_type": "open", "timestamp": base_date + timedelta(days=25, hours=4), "trader_id": WALLETS["julia"], 
      "market_id": "SOL-PUT-80-JAN15", "product_type": "option", "option_type": "put", 
      "strike": 80, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "buy", "price": 3.0, "size": 20, "fee": 0.2}, order_type="market")

# Day 38 - Expires worthless
emit({"event_type": "expire", "timestamp": base_date + timedelta(days=38), "trader_id": WALLETS["julia"], 
      "market_id": "SOL-PUT-80-JAN15", "product_type": "option", "option_type": "put", 
      "strike": 80, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "expire", "price": 0.0, "size": 20, "fee": 0.0, "underlying_price": 95})

# Day 27 - Partial close scenario (Alice: +$39 + $69 = $108)
emit({"event_type": "open", "timestamp": base_date + timedelta(days=26, hours=5), "trader_id": WALLETS["alice"], 
      "market_id": "SOL-CALL-110-JAN15", "product_type": "option", "option_type": "call", 
      "strike": 110, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "buy", "price": 8.0, "size": 20, "fee": 1.0}, order_type="market")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=27, hours=2), "trader_id": WALLETS["alice"], 
      "market_id": "SOL-CALL-110-JAN15", "product_type": "option", "option_type": "call", 
      "strike": 110, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "sell", "price": 12.0, "size": 10, "fee": 0.5}, order_type="market")

emit({"event_type": "close", "timestamp": base_date + timedelta(days=28, hours=2), "trader_id": WALLETS["alice"], 
      "market_id": "SOL-CALL-110-JAN15", "product_type": "option", "option_type": "call", 
      "strike": 110, "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"), 
      "side": "sell", "price": 15.0, "size": 10, "fee": 0.5}, order_type="market")


# ================================================================================
# OPEN POSITIONS - Active trades (current/recent - will appear in dashboard)
# ================================================================================

# Recent open position - 2 days ago
emit({"event_type": "open", "timestamp": now - timedelta(days=2, hours=7), "trader_id": WALLETS["alice"], 
      "market_id": "BTC/USDC", "product_type": "spot", "side": "buy", 
      "price": 51000, "size": 0.5, "fee": 5.0}, order_type="market")

# Open position - 1 day ago
emit({"event_type": "open", "timestamp": now - timedelta(days=1, hours=8), "trader_id": WALLETS["bob"], 
      "market_id": "AVAX-PERP", "product_type": "perp", "side": "long", 
      "price": 35.5, "size": 100, "fee": 1.5}, order_type="limit")

# Open position - 12 hours ago
emit({"event_type": "open", "timestamp": now - timedelta(hours=12), "trader_id": WALLETS["charlie"], 
      "market_id": "ETH-CALL-2200-FEB13", "product_type": "option", "option_type": "call", 
      "strike": 2200, "expiry": (now + timedelta(days=15)).isoformat().replace("+00:00", "Z"), 
      "side": "buy", "price": 85.0, "size": 3, "fee": 0.5}, order_type="limit")


# ================================================================================
# EDGE CASES - Robustness testing
# ================================================================================

# Duplicate open (will be rejected by validation)
emit({"event_type": "open", "timestamp": base_date + timedelta(days=5, minutes=60), "trader_id": WALLETS["alice"], 
      "market_id": "SOL/USDC", "product_type": "spot", "side": "buy", 
      "price": 105, "size": 5, "fee": 0.3}, order_type="stop")

# Close without open (will be rejected)
emit({"event_type": "close", "timestamp": base_date + timedelta(days=10, hours=10), 
      "trader_id": "GhostWallet1111111111111111111111111111", 
      "market_id": "GHOST-PERP", "product_type": "perp", "side": "long", 
      "price": 999, "size": 1, "fee": 0.1}, order_type="stop")

# Trade events (informational only - not matched)
emit({"event_type": "trade", "timestamp": base_date + timedelta(days=3, minutes=15), 
      "trader_id": "MarketMaker1111111111111111111111111", 
      "market_id": "SOL/USDC", "product_type": "spot", "side": "buy", 
      "price": 101, "size": 100, "fee": 1.0})

emit({"event_type": "trade", "timestamp": base_date + timedelta(days=8, minutes=45), 
      "trader_id": "MarketMaker1111111111111111111111111", 
      "market_id": "ETH-PERP", "product_type": "perp", "side": "sell", 
      "price": 2105, "size": 50, "fee": 5.0})


# ================================================================================
# WRITE OUTPUT
# ================================================================================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)

print(f"✅ Generated {len(events)} curated mock events → {OUTPUT_PATH}")
print(f"   Wallets: {len(WALLETS)} realistic Solana addresses")
print(f"   Date Range: {base_date.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')} (30 days)")
print(f"   Closed Positions: 18 (spot: 2, perp: 4, options: 7, liquidations: 5)")
print(f"   Open Positions: 3 (spot: 1, perp: 1, option: 1)")
print(f"   Risk Features: 5 liquidation events (detailed analysis enabled)")
print(f"   Date Gaps: Yes (realistic trading patterns - not every day has activity)")
print(f"   Format: JSON array - ready for ingestion")