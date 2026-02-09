# src/analytics/validate.py
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
    "pnl"
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

# --- Event type schemas (open, trade, close, exercise, expire) ---
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
    },
    "exercise": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl", "underlying_price"}
    },
    "expire": {
        "required": {"side", "price", "size", "fee"},
        "optional": {"pnl", "underlying_price"}
    }
}

def validate_event(event: dict) -> None:
    event_type = event.get("event_type")
    product_type = event.get("product_type")

    # --------------------------------------------------
    # 1️⃣ Trade events are informational only
    # --------------------------------------------------
    if event_type == "trade":
        return  # Skip position validation entirely

    # --------------------------------------------------
    # 2️⃣ Position-affecting events
    # --------------------------------------------------
    if product_type == "perp":
        allowed_sides = {"long", "short"}
    elif product_type in {"spot", "option"}:
        allowed_sides = {"buy", "sell"}
    else:
        raise EventValidationError(f"Unknown product_type: {product_type}")

    side = event.get("side")
    if side not in allowed_sides:
        raise EventValidationError(
            f"Invalid side '{side}' for product_type '{product_type}'. "
            f"Must be one of: {allowed_sides}"
        )

    # 3️⃣ Get product type and determine allowed fields
    product_type = event.get("product_type")
    valid_products = {"spot", "perp", "option"}
    if product_type not in valid_products:
        raise EventValidationError(
            f"Invalid product_type: {product_type}. Allowed: {valid_products}"
        )

    # 4️⃣ Build allowed fields based on product type
    allowed_fields = BASE_REQUIRED_FIELDS | BASE_OPTIONAL_FIELDS
    
    if product_type == "option":
        allowed_fields |= OPTION_REQUIRED_FIELDS | OPTION_OPTIONAL_FIELDS
    
    # Add event-specific fields
    schema = EVENT_TYPE_SCHEMAS[event_type]
    allowed_fields |= schema["required"] | schema["optional"]

    # 5️⃣ Check for extra fields (schema drift)
    extra_fields = set(event.keys()) - allowed_fields
    if extra_fields:
        raise EventValidationError(
            f"Unexpected fields detected: {extra_fields}. "
            f"Allowed for {product_type}/{event_type}: {allowed_fields}"
        )

    # 6️⃣ Check event-type-specific required fields
    missing_event_required = schema["required"] - set(event.keys())
    if missing_event_required:
        raise EventValidationError(
            f"Event type '{event_type}' missing required fields: {missing_event_required}"
        )

    # 7️⃣ Check option-specific required fields (if product is option)
    if product_type == "option":
        missing_option_required = OPTION_REQUIRED_FIELDS - set(event.keys())
        if missing_option_required:
            raise EventValidationError(
                f"Option product missing required fields: {missing_option_required}"
            )

    # 8️⃣ Validate timestamp
    try:
        timestamp_str = event["timestamp"]
        # Handle different timestamp formats
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str.replace("Z", "+00:00")
        datetime.fromisoformat(timestamp_str)
    except (ValueError, AttributeError, TypeError) as e:
        raise EventValidationError(f"Invalid timestamp format: {event.get('timestamp')} - {e}")

    # 9️⃣ Validate numeric fields
    numeric_fields = {"price", "size", "fee", "pnl", "strike", "delta", "gamma", 
                     "theta", "vega", "implied_vol", "underlying_price"}
    for field in numeric_fields & event.keys():
        value = event[field]
        if value is not None and not isinstance(value, (int, float)):
            raise EventValidationError(
                f"Field '{field}' must be numeric or null, got {type(value)}: {value}"
            )

    # 🔟 Validate side values (context-aware)
    if "side" in event:
        side = event["side"]
        if product_type in {"spot", "option"}:
            valid_sides = {"buy", "sell", "exercise", "expire", "assign"}
        else:  # perp
            valid_sides = {"long", "short"}
        
        if side not in valid_sides:
            raise EventValidationError(
                f"Invalid side '{side}' for product_type '{product_type}'. "
                f"Must be one of: {valid_sides}"
            )

    # 1️⃣1️⃣ Validate option-specific values
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


def get_allowed_fields(product_type: str, event_type: str) -> Set[str]:
    """Get allowed fields for a specific product and event type."""
    allowed = BASE_REQUIRED_FIELDS | BASE_OPTIONAL_FIELDS
    
    if product_type == "option":
        allowed |= OPTION_REQUIRED_FIELDS | OPTION_OPTIONAL_FIELDS
    
    if event_type in EVENT_TYPE_SCHEMAS:
        allowed |= EVENT_TYPE_SCHEMAS[event_type]["required"]
        allowed |= EVENT_TYPE_SCHEMAS[event_type]["optional"]
    
    return allowed