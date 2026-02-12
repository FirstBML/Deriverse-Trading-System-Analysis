# src/analytics/validate.py - WITH LIQUIDATION SUPPORT
from typing import Dict, Any, Set
from datetime import datetime

class EventValidationError(Exception):
    """Raised when event fails validation."""
    pass

# --- Base required fields for ALL events ---
BASE_REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "timestamp",
    "trader_id",
    "market_id",
    "product_type"
}

# --- Base optional fields for ALL events ---
BASE_OPTIONAL_FIELDS = {
    "side",
    "price",
    "size",
    "fee",
    "pnl",
    "order_type"
}

# --- Option-specific fields ---
OPTION_REQUIRED_FIELDS = {
    "option_type",
    "strike",
    "expiry"
}

OPTION_OPTIONAL_FIELDS = {
    "delta",
    "gamma",
    "theta",
    "vega",
    "implied_vol",
    "underlying_price"
}

# --- Event type schemas ---
EVENT_TYPE_SCHEMAS = {
    "trade": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl"}
    },
    "open": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl", "order_type"}
    },
    "close": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl", "order_type"}
    },
    "liquidation": {  # ✅ NEW: Liquidation event schema
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl", "order_type"}
    },
    "exercise": {
        "required": {"side", "size", "fee"},
        "optional": {"price", "pnl", "underlying_price"}
    },
    "expire": {
        "required": {"side", "size"},
        "optional": {"price", "fee", "pnl", "underlying_price"}
    }
}


def validate_event(event: dict) -> None:
    """
    Validate event schema and data quality.
    
    Raises:
        EventValidationError: If validation fails
    """
    event_type = event.get("event_type")
    product_type = event.get("product_type")

    # Trade events are informational only - skip position validation
    if event_type == "trade":
        return

    # Validate product type
    valid_products = {"spot", "perp", "option"}
    if product_type not in valid_products:
        raise EventValidationError(
            f"Invalid product_type: {product_type}. Allowed: {valid_products}"
        )

    # Product-specific side validation
    if product_type == "option":
        allowed_sides = {"buy", "sell", "long", "short", "exercise", "expire"}
    elif product_type == "perp":
        allowed_sides = {"long", "short"}
    elif product_type == "spot":
        allowed_sides = {"buy", "sell"}
    
    side = event.get("side")
    if side and side not in allowed_sides:
        raise EventValidationError(
            f"Invalid side '{side}' for product_type '{product_type}'. "
            f"Must be one of: {allowed_sides}"
        )

    # Build allowed fields based on product type
    allowed_fields = BASE_REQUIRED_FIELDS | BASE_OPTIONAL_FIELDS
    
    if product_type == "option":
        allowed_fields |= OPTION_REQUIRED_FIELDS | OPTION_OPTIONAL_FIELDS
    
    # Add event-specific fields
    if event_type in EVENT_TYPE_SCHEMAS:
        schema = EVENT_TYPE_SCHEMAS[event_type]
        allowed_fields |= schema["required"] | schema["optional"]

    # Check for extra fields (schema drift)
    extra_fields = set(event.keys()) - allowed_fields
    if extra_fields:
        raise EventValidationError(
            f"Unexpected fields detected: {extra_fields}. "
            f"Allowed for {product_type}/{event_type}: {allowed_fields}"
        )

    # Check event-type-specific required fields
    if event_type in EVENT_TYPE_SCHEMAS:
        schema = EVENT_TYPE_SCHEMAS[event_type]
        missing_required = schema["required"] - set(event.keys())
        if missing_required:
            raise EventValidationError(
                f"Event type '{event_type}' missing required fields: {missing_required}"
            )

    # Check option-specific required fields
    if product_type == "option":
        missing_option_required = OPTION_REQUIRED_FIELDS - set(event.keys())
        if missing_option_required:
            raise EventValidationError(
                f"Option product missing required fields: {missing_option_required}"
            )

    # Validate timestamp format
    try:
        timestamp_str = event["timestamp"]
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str.replace("Z", "+00:00")
        datetime.fromisoformat(timestamp_str)
    except (ValueError, AttributeError, TypeError) as e:
        raise EventValidationError(f"Invalid timestamp format: {event.get('timestamp')} - {e}")

    # Validate numeric fields
    numeric_fields = {"price", "size", "fee", "pnl", "strike", "delta", "gamma", 
                     "theta", "vega", "implied_vol", "underlying_price"}
    for field in numeric_fields & event.keys():
        value = event[field]
        if value is not None and not isinstance(value, (int, float)):
            raise EventValidationError(
                f"Field '{field}' must be numeric or null, got {type(value)}: {value}"
            )

    # Validate option-specific values
    if product_type == "option":
        # Validate option_type
        option_type = event.get("option_type")
        if option_type not in {"call", "put"}:
            raise EventValidationError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'")
        
        # Validate expiry format
        expiry = event.get("expiry")
        if expiry:
            try:
                if expiry.endswith("Z"):
                    expiry = expiry.replace("Z", "+00:00")
                datetime.fromisoformat(expiry)
            except (ValueError, AttributeError):
                raise EventValidationError(f"Invalid expiry format: {expiry}")