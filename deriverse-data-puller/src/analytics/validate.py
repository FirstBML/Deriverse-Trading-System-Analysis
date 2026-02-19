# src/analytics/validate.py
"""
Event validation with support for enhanced mock data fields.
Validates position_id, tx_hash, entry_price, and fee_usd.
"""

from typing import Dict, Any, Set
from datetime import datetime

class EventValidationError(Exception):
    """Raised when event fails validation."""
    pass

BASE_REQUIRED_FIELDS = {
    "event_id",
    "event_type",
    "timestamp",
    "trader_id",
    "market_id",
    "product_type"
}

BASE_OPTIONAL_FIELDS = {
    "side",
    "price",
    "size",
    "fee_usd",
    "pnl",
    "order_type",
    "position_id",
    "tx_hash",
    "entry_price"
}

OPTION_REQUIRED_FIELDS = {
    "option_type",
    "strike",
    "expiry"
}

OPTION_OPTIONAL_FIELDS = {
    "delta", "gamma", "theta", "vega",
    "implied_vol", "implied_volatility",   
    "underlying_price", "time_to_expiry"   
}

EVENT_TYPE_SCHEMAS = {
    "trade": {
        "required": {"side", "price", "size"},
        "optional": {"fee_usd", "pnl", "tx_hash"}
    },
    "open": {
        "required": {"side", "price", "size"},
        "optional": {"fee_usd", "pnl", "order_type", "position_id", "tx_hash"}
    },
    "close": {
        "required": {"side", "price", "size"},
        "optional": {"fee_usd", "pnl", "order_type", "position_id", "entry_price", "tx_hash"}
    },
    "liquidation": {
        "required": {"side", "price", "size"},
        "optional": {"fee_usd", "pnl", "order_type", "position_id", "entry_price", "tx_hash"}
    },
    "exercise": {
        "required": {"side", "size"},
        "optional": {"price", "fee_usd", "pnl", "underlying_price", "position_id", "entry_price", "tx_hash"}
    },
    "expire": {
        "required": {"side", "size"},
        "optional": {"price", "fee_usd", "pnl", "underlying_price", "position_id", "entry_price", "tx_hash"}
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

    if event_type == "trade":
        return

    valid_products = {"spot", "perp", "option"}
    if product_type not in valid_products:
        raise EventValidationError(
            f"Invalid product_type: {product_type}. Allowed: {valid_products}"
        )

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

    allowed_fields = BASE_REQUIRED_FIELDS | BASE_OPTIONAL_FIELDS
    
    if product_type == "option":
        allowed_fields |= OPTION_REQUIRED_FIELDS | OPTION_OPTIONAL_FIELDS
    
    if event_type in EVENT_TYPE_SCHEMAS:
        schema = EVENT_TYPE_SCHEMAS[event_type]
        allowed_fields |= schema["required"] | schema["optional"]

    extra_fields = set(event.keys()) - allowed_fields
    if extra_fields:
        raise EventValidationError(
            f"Unexpected fields detected: {extra_fields}. "
            f"Allowed for {product_type}/{event_type}: {allowed_fields}"
        )

    if event_type in EVENT_TYPE_SCHEMAS:
        schema = EVENT_TYPE_SCHEMAS[event_type]
        missing_required = schema["required"] - set(event.keys())
        if missing_required:
            raise EventValidationError(
                f"Event type '{event_type}' missing required fields: {missing_required}"
            )

    if product_type == "option":
        missing_option_required = OPTION_REQUIRED_FIELDS - set(event.keys())
        if missing_option_required:
            raise EventValidationError(
                f"Option product missing required fields: {missing_option_required}"
            )

    try:
        timestamp_str = event["timestamp"]
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str.replace("Z", "+00:00")
        datetime.fromisoformat(timestamp_str)
    except (ValueError, AttributeError, TypeError) as e:
        raise EventValidationError(f"Invalid timestamp format: {event.get('timestamp')} - {e}")

    numeric_fields = {"price", "size", "fee_usd", "pnl", "strike", "delta", "gamma", 
                     "theta", "vega", "implied_vol", "underlying_price", "entry_price"}
    for field in numeric_fields & event.keys():
        value = event[field]
        if value is not None and not isinstance(value, (int, float)):
            raise EventValidationError(
                f"Field '{field}' must be numeric or null, got {type(value)}: {value}"
            )

    if product_type == "option":
        option_type = event.get("option_type")
        if option_type not in {"call", "put"}:
            raise EventValidationError(f"Invalid option_type: {option_type}. Must be 'call' or 'put'")
        
        expiry = event.get("expiry")
        if expiry:
            try:
                if expiry.endswith("Z"):
                    expiry = expiry.replace("Z", "+00:00")
                datetime.fromisoformat(expiry)
            except (ValueError, AttributeError):
                raise EventValidationError(f"Invalid expiry format: {expiry}")