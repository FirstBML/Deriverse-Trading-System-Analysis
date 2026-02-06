PRODUCT_TYPES = {"spot", "perp", "option"}

REQUIRED_FIELDS = {
    "event_id": str,
    "product_type": str,    # spot | perp | option
    "event_type": str,      # trade, open, close, exercise, expiry
    "timestamp": int,

    "market": str,
    "trader_id": str,

    "side": str,            # buy/sell OR long/short
    "price": float,
    "size": float,
}

OPTIONAL_FIELDS = {
    # common
    "fee": float,

    # perp-specific
    "pnl": float,
    "funding_rate": float,

    # option-specific
    "option_type": str,     # call / put
    "strike": float,
    "expiry": int,
    "premium": float,
    "exercise_pnl": float,
}
