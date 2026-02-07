# src/analytics/validate.py
from typing import Dict, Any
from datetime import datetime

# --- Base required fields ---
REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "timestamp",
    "trader_id",
    "market_id",
    "product_type"
}

# --- Event type schemas (ONLY: open, trade, close) ---
EVENT_TYPE_SCHEMAS = {
    "trade": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl"}
    },
    "open": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl"}
    },
    "close": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl"}
    }
}

# Allowed fields = base + all event-specific fields
ALLOWED_FIELDS = REQUIRED_FIELDS | {
    field for schema in EVENT_TYPE_SCHEMAS.values()
    for field in schema["required"] | schema["optional"]
}

class EventValidationError(Exception):
    """Raised when event fails validation."""
    pass

def validate_event(event: Dict[str, Any]) -> None:
    """
    Enforce strict event contract.
    Event types: open, trade, close ONLY (no exercise/option_exercise).
    Product types: spot, perp, option (all allowed).
    """

    # 1️⃣ Check required base fields
    missing = REQUIRED_FIELDS - event.keys()
    if missing:
        raise EventValidationError(f"Missing required fields: {missing}")

    # 2️⃣ Check extra fields (schema drift)
    extra = set(event.keys()) - ALLOWED_FIELDS
    if extra:
        raise EventValidationError(f"Unexpected fields detected: {extra}")

    # 3️⃣ Validate event type (removed exercise/option_exercise)
    event_type = event.get("event_type")
    if event_type not in EVENT_TYPE_SCHEMAS:
        raise EventValidationError(
            f"Unknown event_type: {event_type}. Allowed: {list(EVENT_TYPE_SCHEMAS.keys())}"
        )

    # 4️⃣ Check event-type-specific fields
    schema = EVENT_TYPE_SCHEMAS[event_type]
    missing_required = schema["required"] - set(event.keys())
    if missing_required:
        raise EventValidationError(
            f"Event type '{event_type}' missing required fields: {missing_required}"
        )

    # 5️⃣ Validate timestamp
    try:
        datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise EventValidationError(f"Invalid timestamp format: {event.get('timestamp')}")

    # 6️⃣ Validate numeric fields
    numeric_fields = {"price", "size", "fee", "pnl"}
    for field in numeric_fields & event.keys():
        value = event[field]
        if value is not None and not isinstance(value, (int, float)):
            raise EventValidationError(
                f"Field '{field}' must be numeric or null, got {type(value)}"
            )

    # 7️⃣ Validate side values
    if "side" in event:
        valid_sides = {"buy", "sell", "long", "short"}
        if event["side"] not in valid_sides:
            raise EventValidationError(
                f"Invalid side: {event['side']}. Must be one of {valid_sides}"
            )

    # 8️⃣ Validate product_type (✅ option is allowed)
    valid_products = {"spot", "perp", "option"}
    if event.get("product_type") not in valid_products:
        raise EventValidationError(
            f"Invalid product_type: {event.get('product_type')}. Allowed: {valid_products}"
        )