# scripts/generate_mock_data.py 
"""
Generate curated mock trading data for Deriverse analytics demo.

Spot trades: 10 closed positions across 3 batches
  Batch 1 (original): 1 win, 1 loss
  Batch 2:            3 wins, 1 loss
  Batch 3 (NEW):      3 wins, 1 loss
"""

import json
import hashlib
import base58
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUTPUT_PATH = Path("configs/mock_data.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

now = datetime.now(timezone.utc)
base_date = now - timedelta(days=30)

events = []

WALLETS = {
    "alice":   "7KNXqvHu2QWvDq8cGPGvKZhFvYnz3kQ5mL8xRt2Bp9uV",
    "bob":     "5FxM2nQwP4vYkL9mT3xRd8eJbWp7sN6gH2cKt9uVfXyZ",
    "charlie": "9DpT3vHx5kN2qL8mR7wYfJ6bP4sE1cG9nZ5tK3uVwXyA",
    "diana":   "4MqL8vYx2kP9nT7wR5fH3bJ6sE1cG4nZ8tK2uVwXyBpQ",
    "evan":    "6NrK9wZx3mQ8pU7vS4gI2dL5tF1eH7oA9yM3xVbCwRtE",
    "fiona":   "8QtN2xWy5lR7mV9uT6hK3eM4pG1fJ8nB7zL4wVcDxSeF",
    "george":  "3HsJ7yVz4nQ6oW8tS5gL2fN9rH1eK6mC8xM5vBdEwRuG",
    "hannah":  "2PrM8xUz6oT5nY7vR4jL3gP1sH9eN4mD6zK8wCfGxQuH",
    "ivan":    "5TpQ9yXz7mS6oV8uR3kM2hN4rJ1fL5nE7xP6wDgHySvI",
    "julia":   "4WqP8zYx5nT7mU9tS2lN6jM3rK1gH4oC8yL5vEfJxRwK",
}

position_counter = {}


def generate_event_id(event_data, index):
    seed_parts = [
        str(event_data.get('event_type', '')),
        str(event_data.get('timestamp', '') if isinstance(event_data.get('timestamp'), str) else ''),
        str(event_data.get('trader_id', '')),
        str(event_data.get('market_id', '')),
        str(index)
    ]
    return hashlib.sha256("|".join(seed_parts).encode()).hexdigest()


def generate_tx_signature(event_data, index):
    seed_parts = [
        str(event_data.get('event_type', '')),
        str(event_data.get('timestamp', '')),
        str(event_data.get('trader_id', '')),
        str(event_data.get('market_id', '')),
        str(event_data.get('price', '')),
        str(index)
    ]
    seed = "|".join(seed_parts)
    hash_bytes = hashlib.sha256(seed.encode()).digest()
    padded = hash_bytes + bytes(32)
    return base58.b58encode(padded).decode()[:88]


def generate_position_id(trader_id, market_id, timestamp):
    trader_prefix = trader_id[:8]
    timestamp_ms = int(timestamp.timestamp() * 1000)
    return f"{trader_prefix}_{market_id}_{timestamp_ms}"


def emit(event, order_type="market", position_id=None):
    if 'timestamp' in event and isinstance(event['timestamp'], datetime):
        event['timestamp'] = event['timestamp'].isoformat().replace("+00:00", "Z")

    if 'event_id' not in event:
        event['event_id'] = generate_event_id(event, len(events) + 1)

    event['tx_hash'] = generate_tx_signature(event, len(events) + 1)

    if event['event_type'] == 'open':
        timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        new_position_id = generate_position_id(event['trader_id'], event['market_id'], timestamp)
        event['position_id'] = new_position_id
        key = f"{event['trader_id']}:{event['market_id']}"
        if key not in position_counter:
            position_counter[key] = []
        position_counter[key].append({
            'position_id': new_position_id,
            'entry_price': event['price'],
            'timestamp': event['timestamp']
        })

    elif event['event_type'] in ['close', 'liquidation', 'exercise', 'expire']:
        if position_id:
            event['position_id'] = position_id
        else:
            key = f"{event['trader_id']}:{event['market_id']}"
            if key in position_counter and position_counter[key]:
                position_info = position_counter[key][-1]
                event['position_id'] = position_info['position_id']
                if 'entry_price' not in event:
                    event['entry_price'] = position_info['entry_price']
                if event['event_type'] in ['close', 'liquidation', 'expire']:
                    position_counter[key].pop()

    if event['event_type'] in ['open', 'close', 'liquidation']:
        event['order_type'] = order_type

    events.append(event)


# ================================================================================
# SPOT TRADES — Batch 1 (original 2)
# ================================================================================

# WIN — Alice: SOL/USDC buy@$100 -> sell@$110  (+$99)
emit({
    "event_type": "open", "timestamp": base_date,
    "trader_id": WALLETS["alice"], "market_id": "SOL/USDC",
    "product_type": "spot", "side": "buy", "price": 100, "size": 10, "fee_usd": 0.5
}, order_type="stop")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(hours=2),
    "trader_id": WALLETS["alice"], "market_id": "SOL/USDC",
    "product_type": "spot", "side": "sell", "price": 110, "size": 10, "fee_usd": 0.5
}, order_type="market")

# LOSS — Bob: ETH/USDC buy@$2000 -> sell@$1950  (-$252)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=2, minutes=10),
    "trader_id": WALLETS["bob"], "market_id": "ETH/USDC",
    "product_type": "spot", "side": "buy", "price": 2000, "size": 5, "fee_usd": 1.0
}, order_type="market")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=2, hours=3),
    "trader_id": WALLETS["bob"], "market_id": "ETH/USDC",
    "product_type": "spot", "side": "sell", "price": 1950, "size": 5, "fee_usd": 1.0
}, order_type="stop")


# ================================================================================
# SPOT TRADES — Batch 2 (3 wins, 1 loss)
# ================================================================================

# WIN — George: AVAX/USDC buy@$36 -> sell@$40.20  (+$168)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=3, hours=9),
    "trader_id": WALLETS["george"], "market_id": "AVAX/USDC",
    "product_type": "spot", "side": "buy", "price": 36.0, "size": 40, "fee_usd": 0.72
}, order_type="limit")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=3, hours=14),
    "trader_id": WALLETS["george"], "market_id": "AVAX/USDC",
    "product_type": "spot", "side": "sell", "price": 40.2, "size": 40, "fee_usd": 0.80
}, order_type="market")

# WIN — Hannah: BTC/USDC buy@$48500 -> sell@$49125  (+$312.50)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=5, hours=10),
    "trader_id": WALLETS["hannah"], "market_id": "BTC/USDC",
    "product_type": "spot", "side": "buy", "price": 48500, "size": 0.5, "fee_usd": 4.85
}, order_type="market")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=5, hours=13),
    "trader_id": WALLETS["hannah"], "market_id": "BTC/USDC",
    "product_type": "spot", "side": "sell", "price": 49125, "size": 0.5, "fee_usd": 4.91
}, order_type="limit")

# LOSS — Fiona: SOL/USDC buy@$108 -> stop@$101  (-$108)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=8, hours=8),
    "trader_id": WALLETS["fiona"], "market_id": "SOL/USDC",
    "product_type": "spot", "side": "buy", "price": 108.0, "size": 15, "fee_usd": 1.08
}, order_type="market")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=8, hours=14),
    "trader_id": WALLETS["fiona"], "market_id": "SOL/USDC",
    "product_type": "spot", "side": "sell", "price": 101.0, "size": 15, "fee_usd": 1.01
}, order_type="stop")

# WIN — Ivan: ETH/USDC buy@$2050 -> sell@$2125 (overnight)  (+$225)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=12, hours=18),
    "trader_id": WALLETS["ivan"], "market_id": "ETH/USDC",
    "product_type": "spot", "side": "buy", "price": 2050.0, "size": 3, "fee_usd": 1.54
}, order_type="limit")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=13, hours=9),
    "trader_id": WALLETS["ivan"], "market_id": "ETH/USDC",
    "product_type": "spot", "side": "sell", "price": 2125.0, "size": 3, "fee_usd": 1.59
}, order_type="market")


# ================================================================================
# SPOT TRADES — Batch 3 (NEW: 3 wins, 1 loss)
# ================================================================================

# WIN — Julia: LINK/USDC buy@$14.20 -> sell@$15.80 (quick scalp)  (+$160)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=15, hours=11),
    "trader_id": WALLETS["julia"], "market_id": "LINK/USDC",
    "product_type": "spot", "side": "buy", "price": 14.20, "size": 100, "fee_usd": 1.42
}, order_type="limit")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=15, hours=15),
    "trader_id": WALLETS["julia"], "market_id": "LINK/USDC",
    "product_type": "spot", "side": "sell", "price": 15.80, "size": 100, "fee_usd": 1.58
}, order_type="market")

# LOSS — Diana: MATIC/USDC buy@$0.92 -> stop@$0.81 (gap down)  (-$110)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=17, hours=13),
    "trader_id": WALLETS["diana"], "market_id": "MATIC/USDC",
    "product_type": "spot", "side": "buy", "price": 0.92, "size": 1000, "fee_usd": 0.92
}, order_type="market")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=17, hours=20),
    "trader_id": WALLETS["diana"], "market_id": "MATIC/USDC",
    "product_type": "spot", "side": "sell", "price": 0.81, "size": 1000, "fee_usd": 0.81
}, order_type="stop")

# WIN — Charlie: DOT/USDC buy@$7.30 -> sell@$8.10 (news rally)  (+$160)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=20, hours=7),
    "trader_id": WALLETS["charlie"], "market_id": "DOT/USDC",
    "product_type": "spot", "side": "buy", "price": 7.30, "size": 200, "fee_usd": 1.46
}, order_type="limit")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=20, hours=16),
    "trader_id": WALLETS["charlie"], "market_id": "DOT/USDC",
    "product_type": "spot", "side": "sell", "price": 8.10, "size": 200, "fee_usd": 1.62
}, order_type="market")

# WIN — Bob: SOL/USDC buy@$118 -> sell@$127 (swing trade)  (+$225)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=24, hours=9),
    "trader_id": WALLETS["bob"], "market_id": "SOL/USDC",
    "product_type": "spot", "side": "buy", "price": 118.0, "size": 25, "fee_usd": 2.95
}, order_type="limit")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=25, hours=14),
    "trader_id": WALLETS["bob"], "market_id": "SOL/USDC",
    "product_type": "spot", "side": "sell", "price": 127.0, "size": 25, "fee_usd": 3.18
}, order_type="market")


# ================================================================================
# PERPETUAL TRADES
# ================================================================================

# WIN — Charlie: SOL-PERP long@$100 -> close@$120  (+$199)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=4, minutes=20),
    "trader_id": WALLETS["charlie"], "market_id": "SOL-PERP",
    "product_type": "perp", "side": "long", "price": 100, "size": 10, "fee_usd": 0.5
}, order_type="limit")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=4, hours=4),
    "trader_id": WALLETS["charlie"], "market_id": "SOL-PERP",
    "product_type": "perp", "side": "long", "price": 120, "size": 10, "fee_usd": 0.5
}, order_type="market")

# WIN — Diana: BTC-PERP short@$50000 -> cover@$48000  (+$1990)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=6, minutes=30),
    "trader_id": WALLETS["diana"], "market_id": "BTC-PERP",
    "product_type": "perp", "side": "short", "price": 50000, "size": 1, "fee_usd": 5.0
}, order_type="market")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=6, hours=5),
    "trader_id": WALLETS["diana"], "market_id": "BTC-PERP",
    "product_type": "perp", "side": "short", "price": 48000, "size": 1, "fee_usd": 5.0
}, order_type="market")

# LOSS — Evan: ETH-PERP long@$2100 -> close@$2050  (-$254)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=7, minutes=40),
    "trader_id": WALLETS["evan"], "market_id": "ETH-PERP",
    "product_type": "perp", "side": "long", "price": 2100, "size": 5, "fee_usd": 2.0
}, order_type="stop")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=7, hours=6),
    "trader_id": WALLETS["evan"], "market_id": "ETH-PERP",
    "product_type": "perp", "side": "long", "price": 2050, "size": 5, "fee_usd": 2.0
}, order_type="market")


# ================================================================================
# LIQUIDATION EVENTS (5 total)
# ================================================================================

# LIQ 1 — Diana: SOL-PERP long@$105 -> liq@$88  (-$880)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=9, hours=1),
    "trader_id": WALLETS["diana"], "market_id": "SOL-PERP",
    "product_type": "perp", "side": "long", "price": 105, "size": 50, "fee_usd": 5.0
}, order_type="market")
emit({
    "event_type": "liquidation", "timestamp": base_date + timedelta(days=9, hours=2),
    "trader_id": WALLETS["diana"], "market_id": "SOL-PERP",
    "product_type": "perp", "side": "long", "price": 88, "size": 50, "fee_usd": 25.0
}, order_type="liquidation")

# LIQ 2 — Bob: ETH-PERP long@$2200 -> liq@$2050  (-$1520)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=11, hours=3),
    "trader_id": WALLETS["bob"], "market_id": "ETH-PERP",
    "product_type": "perp", "side": "long", "price": 2200, "size": 10, "fee_usd": 3.0
}, order_type="market")
emit({
    "event_type": "liquidation", "timestamp": base_date + timedelta(days=11, hours=8),
    "trader_id": WALLETS["bob"], "market_id": "ETH-PERP",
    "product_type": "perp", "side": "long", "price": 2050, "size": 10, "fee_usd": 20.0
}, order_type="liquidation")

# LIQ 3 — Evan: BTC-PERP short@$49000 -> liq@$50250  (-$2530)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=14, hours=2),
    "trader_id": WALLETS["evan"], "market_id": "BTC-PERP",
    "product_type": "perp", "side": "short", "price": 49000, "size": 2, "fee_usd": 8.0
}, order_type="limit")
emit({
    "event_type": "liquidation", "timestamp": base_date + timedelta(days=14, hours=12),
    "trader_id": WALLETS["evan"], "market_id": "BTC-PERP",
    "product_type": "perp", "side": "short", "price": 50250, "size": 2, "fee_usd": 30.0
}, order_type="liquidation")

# LIQ 4 — Charlie: AVAX-PERP long@$38.5 -> liq@$35.2  (-$342)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=17, hours=5),
    "trader_id": WALLETS["charlie"], "market_id": "AVAX-PERP",
    "product_type": "perp", "side": "long", "price": 38.5, "size": 100, "fee_usd": 4.0
}, order_type="market")
emit({
    "event_type": "liquidation", "timestamp": base_date + timedelta(days=17, hours=14),
    "trader_id": WALLETS["charlie"], "market_id": "AVAX-PERP",
    "product_type": "perp", "side": "long", "price": 35.2, "size": 100, "fee_usd": 12.0
}, order_type="liquidation")

# LIQ 5 — Alice: SOL-PERP short@$115 -> liq@$135  (-$615)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=19, hours=4),
    "trader_id": WALLETS["alice"], "market_id": "SOL-PERP",
    "product_type": "perp", "side": "short", "price": 115, "size": 30, "fee_usd": 3.5
}, order_type="stop")
emit({
    "event_type": "liquidation", "timestamp": base_date + timedelta(days=19, hours=9),
    "trader_id": WALLETS["alice"], "market_id": "SOL-PERP",
    "product_type": "perp", "side": "short", "price": 135, "size": 30, "fee_usd": 18.0
}, order_type="liquidation")


# ================================================================================
# OPTION TRADES — Full lifecycle  
# ================================================================================

# Fiona: long SOL call, profitable close  (+$29)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=20, hours=1),
    "trader_id": WALLETS["fiona"], "market_id": "SOL-CALL-120-JAN15",
    "product_type": "option", "option_type": "call", "strike": 120,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "buy", "price": 5.0, "size": 10, "fee_usd": 0.5,
    "underlying_price": 115.0, "time_to_expiry": round(18/365, 6),
    "implied_volatility": 0.45
}, order_type="stop")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=21, hours=0),
    "trader_id": WALLETS["fiona"], "market_id": "SOL-CALL-120-JAN15",
    "product_type": "option", "option_type": "call", "strike": 120,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "sell", "price": 8.0, "size": 10, "fee_usd": 0.5,
    "underlying_price": 122.0, "time_to_expiry": round(17/365, 6),
    "implied_volatility": 0.50
}, order_type="stop")

# George: short SOL put, profitable buyback  (+$36.10)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=21, hours=1, minutes=30),
    "trader_id": WALLETS["george"], "market_id": "SOL-PUT-90-JAN15",
    "product_type": "option", "option_type": "put", "strike": 90,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "sell", "price": 4.0, "size": 15, "fee_usd": 0.7,
    "underlying_price": 118.0, "time_to_expiry": round(17/365, 6),
    "implied_volatility": 0.40
}, order_type="stop")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=22, hours=12),
    "trader_id": WALLETS["george"], "market_id": "SOL-PUT-90-JAN15",
    "product_type": "option", "option_type": "put", "strike": 90,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "buy", "price": 1.5, "size": 15, "fee_usd": 0.7,
    "underlying_price": 120.0, "time_to_expiry": round(15/365, 6),
    "implied_volatility": 0.30
}, order_type="market")

# Hannah: long ETH put, losing close  (-$127)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=22, hours=2),
    "trader_id": WALLETS["hannah"], "market_id": "ETH-PUT-1900-JAN15",
    "product_type": "option", "option_type": "put", "strike": 1900,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "buy", "price": 45.0, "size": 5, "fee_usd": 1.0,
    "underlying_price": 2050.0, "time_to_expiry": round(16/365, 6),
    "implied_volatility": 0.55
}, order_type="stop")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=24, hours=0),
    "trader_id": WALLETS["hannah"], "market_id": "ETH-PUT-1900-JAN15",
    "product_type": "option", "option_type": "put", "strike": 1900,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "sell", "price": 20.0, "size": 5, "fee_usd": 1.0,
    "underlying_price": 2100.0, "time_to_expiry": round(14/365, 6),
    "implied_volatility": 0.40
}, order_type="limit")

# Ivan: long BTC call, exercised ITM  (+$2980)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=24, hours=3),
    "trader_id": WALLETS["ivan"], "market_id": "BTC-CALL-50000-JAN15",
    "product_type": "option", "option_type": "call", "strike": 50000,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "buy", "price": 2000.0, "size": 1, "fee_usd": 10.0,
    "underlying_price": 51000.0, "time_to_expiry": round(14/365, 6),
    "implied_volatility": 0.60
}, order_type="market")
emit({
    "event_type": "exercise", "timestamp": now - timedelta(days=1),
    "trader_id": WALLETS["ivan"], "market_id": "BTC-CALL-50000-JAN15",
    "product_type": "option", "option_type": "call", "strike": 50000,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "exercise", "size": 1, "fee_usd": 10.0,
    "underlying_price": 55000.0, "time_to_expiry": round(1/365, 6),
    "implied_volatility": 0.65
})

# Julia: long SOL put, expired worthless  (-$60.20)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=25, hours=4),
    "trader_id": WALLETS["julia"], "market_id": "SOL-PUT-80-JAN15",
    "product_type": "option", "option_type": "put", "strike": 80,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "buy", "price": 3.0, "size": 20, "fee_usd": 0.2,
    "underlying_price": 117.0, "time_to_expiry": round(13/365, 6),
    "implied_volatility": 0.50
}, order_type="market")
emit({
    "event_type": "expire", "timestamp": now - timedelta(hours=12),
    "trader_id": WALLETS["julia"], "market_id": "SOL-PUT-80-JAN15",
    "product_type": "option", "option_type": "put", "strike": 80,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "expire", "price": 0.0, "size": 20, "fee_usd": 0.0,
    "underlying_price": 95.0, "time_to_expiry": 0.0,
    "implied_volatility": 0.50
})

# Alice: long SOL call, partial close (2 legs)  (+$108)
emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=26, hours=5),
    "trader_id": WALLETS["alice"], "market_id": "SOL-CALL-110-JAN15",
    "product_type": "option", "option_type": "call", "strike": 110,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "buy", "price": 8.0, "size": 20, "fee_usd": 1.0,
    "underlying_price": 116.0, "time_to_expiry": round(12/365, 6),
    "implied_volatility": 0.48
}, order_type="market")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=27, hours=2),
    "trader_id": WALLETS["alice"], "market_id": "SOL-CALL-110-JAN15",
    "product_type": "option", "option_type": "call", "strike": 110,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "sell", "price": 12.0, "size": 10, "fee_usd": 0.5,
    "underlying_price": 119.0, "time_to_expiry": round(11/365, 6),
    "implied_volatility": 0.52
}, order_type="market")
emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=28, hours=2),
    "trader_id": WALLETS["alice"], "market_id": "SOL-CALL-110-JAN15",
    "product_type": "option", "option_type": "call", "strike": 110,
    "expiry": (base_date + timedelta(days=38)).isoformat().replace("+00:00", "Z"),
    "side": "sell", "price": 15.0, "size": 10, "fee_usd": 0.5,
    "underlying_price": 123.0, "time_to_expiry": round(10/365, 6),
    "implied_volatility": 0.55
}, order_type="market")

# ================================================================================
# OPEN POSITIONS
# ================================================================================

emit({
    "event_type": "open", "timestamp": now - timedelta(days=2, hours=7),
    "trader_id": WALLETS["alice"], "market_id": "BTC/USDC",
    "product_type": "spot", "side": "buy", "price": 51000, "size": 0.5, "fee_usd": 5.0
}, order_type="market")

emit({
    "event_type": "open", "timestamp": now - timedelta(days=1, hours=8),
    "trader_id": WALLETS["bob"], "market_id": "AVAX-PERP",
    "product_type": "perp", "side": "long", "price": 35.5, "size": 100, "fee_usd": 1.5
}, order_type="limit")

emit({
    "event_type": "open", "timestamp": now - timedelta(hours=12),
    "trader_id": WALLETS["charlie"], "market_id": "ETH-CALL-2200-FEB13",
    "product_type": "option", "option_type": "call", "strike": 2200,
    "expiry": (now + timedelta(days=15)).isoformat().replace("+00:00", "Z"),
    "side": "buy", "price": 85.0, "size": 3, "fee_usd": 0.5
}, order_type="limit")


# ================================================================================
# EDGE CASES
# ================================================================================

emit({
    "event_type": "open", "timestamp": base_date + timedelta(days=5, minutes=60),
    "trader_id": WALLETS["alice"], "market_id": "SOL/USDC",
    "product_type": "spot", "side": "buy", "price": 105, "size": 5, "fee_usd": 0.3
}, order_type="stop")

emit({
    "event_type": "close", "timestamp": base_date + timedelta(days=10, hours=10),
    "trader_id": "GhostWallet1111111111111111111111111111",
    "market_id": "GHOST-PERP", "product_type": "perp",
    "side": "long", "price": 999, "size": 1, "fee_usd": 0.1
}, order_type="stop")

emit({
    "event_type": "trade", "timestamp": base_date + timedelta(days=3, minutes=15),
    "trader_id": "MarketMaker1111111111111111111111111",
    "market_id": "SOL/USDC", "product_type": "spot",
    "side": "buy", "price": 101, "size": 100, "fee_usd": 1.0
})

emit({
    "event_type": "trade", "timestamp": base_date + timedelta(days=8, minutes=45),
    "trader_id": "MarketMaker1111111111111111111111111",
    "market_id": "ETH-PERP", "product_type": "perp",
    "side": "sell", "price": 2105, "size": 50, "fee_usd": 5.0
})


# ================================================================================
# WRITE OUTPUT
# ================================================================================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(events, f, indent=2)

spot_closes = [e for e in events if e.get("product_type") == "spot" and e.get("event_type") == "close"]
print(f"\nSpot closed trades: {len(spot_closes)}")
perp_closes = [e for e in events if e.get("product_type") == "perp" and e.get("event_type") == "close"]
print(f"\nPerp closed trades: {len(perp_closes)}")
option_closes = [e for e in events if e.get("product_type") == "option" and e.get("event_type") == "close"]
print(f"\nOption closed trades: {len(option_closes)}")
print(f"\nGenerated {len(events)} events -> {OUTPUT_PATH}")
print(f"\nAll Data Generated Completely")
