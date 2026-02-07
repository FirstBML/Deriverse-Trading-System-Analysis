# src/ingestion/normalizer.py
from typing import Dict, Any
from datetime import datetime, timezone
import hashlib

def normalize_event(raw_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw event data into canonical schema.
    - Convert keys to expected schema names
    - Convert Unix timestamps to ISO 8601
    - Ensure event_id exists
    """
    event = raw_event.copy()

    # --- Normalize timestamp ---
    ts = event.get("timestamp")
    if isinstance(ts, (int, float)):
        # Convert Unix timestamp (seconds) to ISO 8601 UTC
        event["timestamp"] = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    elif isinstance(ts, str):
        # Attempt to parse string timestamp and standardize
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            event["timestamp"] = dt.isoformat()
        except ValueError:
            # Leave as-is; validation will catch errors
            pass

    # --- Normalize keys for backward compatibility ---
    if "trader" in event:
        event["trader_id"] = event.pop("trader")
    if "market" in event:
        event["market_id"] = event.pop("market")
    if "type" in event and "event_type" not in event:
        event["event_type"] = event.pop("type")
    if "product" in event and "product_type" not in event:
        event["product_type"] = event.pop("product")

    # --- Ensure event_id exists ---
    if "event_id" not in event:
        raw = f"{event.get('event_type')}|{event.get('timestamp')}|{event.get('trader_id')}|{event.get('market_id')}"
        event["event_id"] = hashlib.sha256(raw.encode()).hexdigest()

    return event
