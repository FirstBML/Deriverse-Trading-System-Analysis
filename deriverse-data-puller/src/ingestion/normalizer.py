# src/ingestion/normalizer.py
"""
Event normalization with support for enhanced mock data fields.
Handles position_id, tx_hash, entry_price, and fee_usd.
"""

from typing import Dict, Any
from datetime import datetime, timezone
import hashlib

def normalize_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw event data into canonical schema.
    Preserves new fields: position_id, tx_hash, entry_price, fee_usd
    """
    event = raw_event.copy()

    ts = event.get("timestamp")
    if isinstance(ts, (int, float)):
        event["timestamp"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    elif isinstance(ts, datetime):
        event["timestamp"] = ts.isoformat()
    elif isinstance(ts, str):
        try:
            ts_clean = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            event["timestamp"] = dt.isoformat().replace("+00:00", "Z")
        except ValueError:
            pass

    key_mappings = {
        "trader": "trader_id",
        "market": "market_id", 
        "type": "event_type",
        "product": "product_type",
        "optionType": "option_type",
        "impliedVol": "implied_vol",
        "fee": "fee_usd"
    }
    
    for old_key, new_key in key_mappings.items():
        if old_key in event and new_key not in event:
            event[new_key] = event.pop(old_key)

    if "product_type" in event:
        product = event["product_type"].lower()
        if product in ["perpetual", "future", "futures", "perp"]:
            event["product_type"] = "perp"
        elif product in ["options", "option"]:
            event["product_type"] = "option"
        elif product in ["spot", "cash"]:
            event["product_type"] = "spot"

    if "side" in event and event.get("product_type") in ["spot", "option"]:
        side = event["side"].lower()
        
        if event.get("event_type") in ["open", "close", "trade"]:
            if side == "long":
                event["side"] = "buy"
            elif side == "short":
                event["side"] = "sell"

    if event.get("product_type") == "option":
        if "option_type" in event:
            event["option_type"] = event["option_type"].lower()
        
        if "expiry" in event and event["expiry"]:
            expiry = event["expiry"]
            if isinstance(expiry, str):
                try:
                    expiry_clean = expiry.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(expiry_clean)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    event["expiry"] = dt.isoformat().replace("+00:00", "Z")
                except ValueError:
                    pass

    if "event_id" not in event:
        raw_parts = [
            str(event.get('event_type', '')),
            str(event.get('timestamp', '')),
            str(event.get('trader_id', '')),
            str(event.get('market_id', '')),
            str(event.get('product_type', ''))
        ]
        raw = "|".join(raw_parts)
        event["event_id"] = hashlib.sha256(raw.encode()).hexdigest()

    numeric_fields = ["price", "size", "fee_usd", "pnl", "strike", "delta", 
                     "gamma", "theta", "vega", "implied_vol", "underlying_price", "entry_price"]
    
    for field in numeric_fields:
        if field in event and event[field] is not None:
            try:
                event[field] = float(event[field])
            except (ValueError, TypeError):
                pass

    return event