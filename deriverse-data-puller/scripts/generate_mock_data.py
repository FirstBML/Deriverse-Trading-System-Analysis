# scripts/generate_mock_data.py
from datetime import datetime, timedelta, timezone
import random
import uuid
import json
from pathlib import Path

MOCK_PATH = Path("configs/mock_data.json")

def iso_ts(dt):
    return dt.replace(tzinfo=timezone.utc).isoformat()

def generate_mock_events(n=12, start_time=None):
    """
    Generate mock events for testing.
    Event types: open, trade, close ONLY (no exercise/option_exercise).
    Product types: spot, perp, option (all allowed).
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc)
        
    events = []
    # ✅ Keep all markets including SOL-OPT
    markets = ["SOL/USDC", "SOL-PERP", "BTC-PERP", "SOL-OPT"]
    product_map = {
        "SOL/USDC": "spot",
        "SOL-PERP": "perp",
        "BTC-PERP": "perp",
        "SOL-OPT": "option",  # ✅ Keep option product type
    }
    
    for i in range(n):
        market = random.choice(markets)
        product_type = product_map[market]
        
        # ✅ ONLY GENERATE: open, trade, close (removed exercise/option_exercise)
        event_type = random.choice(["trade", "open", "close"])
        
        base = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": iso_ts(start_time + timedelta(minutes=5 * i)),
            "trader_id": f"trader_{random.choice(['A','B','C','D'])}",
            "market_id": market,
            "product_type": product_type,
            "fee": round(random.uniform(0.05, 1.0), 2),
        }
        
        if event_type == "trade":
            base.update({
                "side": random.choice(["buy", "sell"]),
                "price": round(random.uniform(90, 26000), 2),
                "size": random.randint(1, 20),
            })
        elif event_type in ["open", "close"]:
            base.update({
                "side": random.choice(["long", "short"]),
                "price": round(random.uniform(90, 26000), 2),
                "size": random.randint(1, 20),
                "pnl": round(random.uniform(-50, 200), 2) if event_type == "close" else None,
            })
        
        events.append(base)
    
    return events

def write_mock_data(n=12):
    """Generate and write mock events to configs/mock_data.json"""
    events = generate_mock_events(n=n)
    MOCK_PATH.parent.mkdir(exist_ok=True)
    with open(MOCK_PATH, "w") as f:
        json.dump(events, f, indent=2)
    return len(events)

if __name__ == "__main__":
    count = write_mock_data()
    print(f"✅ Generated {count} mock events (open, trade, close only)")