# src/ingestion/normalizer.py
from typing import Dict, Any
from datetime import datetime, timezone
import hashlib

def normalize_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw event data into canonical schema.
    - Convert keys to expected schema names
    - Convert timestamps to ISO 8601
    - Ensure event_id exists
    - Handle option-specific fields
    - Normalize position terminology (long→buy, short→sell for options/spot)
    """
    event = raw_event.copy()

    # --- Normalize timestamp ---
    ts = event.get("timestamp")
    if isinstance(ts, (int, float)):
        # Convert Unix timestamp (seconds) to ISO 8601 UTC
        event["timestamp"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    elif isinstance(ts, datetime):
        # Convert datetime object to ISO string
        event["timestamp"] = ts.isoformat()
    elif isinstance(ts, str):
        # Ensure proper ISO format with timezone
        try:
            # Handle different formats
            ts_clean = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(ts_clean)
            # Standardize to UTC with Z suffix
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            event["timestamp"] = dt.isoformat().replace("+00:00", "Z")
        except ValueError:
            # Leave as-is; validation will catch errors
            pass

    # --- Normalize keys for backward compatibility ---
    key_mappings = {
        "trader": "trader_id",
        "market": "market_id", 
        "type": "event_type",
        "product": "product_type",
        "optionType": "option_type",  # Handle camelCase
        "impliedVol": "implied_vol"
    }
    
    for old_key, new_key in key_mappings.items():
        if old_key in event and new_key not in event:
            event[new_key] = event.pop(old_key)

    # --- Normalize product_type ---
    if "product_type" in event:
        product = event["product_type"].lower()
        if product in ["perpetual", "future", "futures", "perp"]:
            event["product_type"] = "perp"
        elif product in ["options", "option"]:
            event["product_type"] = "option"
        elif product in ["spot", "cash"]:
            event["product_type"] = "spot"

    # --- Normalize side terminology ---
    # Convert position terms (long/short) to trading terms (buy/sell) for spot and options
    # Keep long/short for perps
    if "side" in event and event.get("product_type") in ["spot", "option"]:
        side = event["side"].lower()
        
        # Only normalize for open/close events, not for exercise/expire
        if event.get("event_type") in ["open", "close", "trade"]:
            if side == "long":
                event["side"] = "buy"
            elif side == "short":
                event["side"] = "sell"
            # Already buy/sell stays as-is

    # --- Normalize option-specific fields ---
    if event.get("product_type") == "option":
        # Normalize option_type
        if "option_type" in event:
            event["option_type"] = event["option_type"].lower()
        
        # Normalize expiry timestamp
        if "expiry" in event and event["expiry"]:
            expiry = event["expiry"]
            if isinstance(expiry, str):
                try:
                    expiry_clean = expiry.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(expiry_clean)
                    # Standardize format
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    event["expiry"] = dt.isoformat().replace("+00:00", "Z")
                except ValueError:
                    # Leave as-is
                    pass

    # --- Ensure event_id exists ---
    if "event_id" not in event:
        # Create deterministic event ID
        raw_parts = [
            str(event.get('event_type', '')),
            str(event.get('timestamp', '')),
            str(event.get('trader_id', '')),
            str(event.get('market_id', '')),
            str(event.get('product_type', ''))
        ]
        raw = "|".join(raw_parts)
        event["event_id"] = hashlib.sha256(raw.encode()).hexdigest()

    # --- Normalize numeric fields ---
    numeric_fields = ["price", "size", "fee", "pnl", "strike", "delta", 
                     "gamma", "theta", "vega", "implied_vol", "underlying_price"]
    
    for field in numeric_fields:
        if field in event and event[field] is not None:
            try:
                event[field] = float(event[field])
            except (ValueError, TypeError):
                # Keep as-is if conversion fails
                pass

    return event