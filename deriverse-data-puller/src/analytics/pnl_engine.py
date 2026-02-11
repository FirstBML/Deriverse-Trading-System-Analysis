# src/analytics/pnl_engine.py
import pandas as pd
import hashlib
import logging

logger = logging.getLogger(__name__)


def compute_realized_pnl(events: pd.DataFrame):
    """
    Canonical PnL engine with full options lifecycle support.
    
    Supports:
    - Spot: buy/sell (different sides for open/close)
    - Perps: long/short (same side for open/close)
    - Options: buy/sell/exercise/expire (different sides)
    
    Options PnL logic:
    - buy: Pay premium (negative cash flow)
    - sell: Receive premium or exit price (positive cash flow)
    - exercise: Intrinsic value - fees
    - expire: Total loss of premium paid
    """

    required_cols = {
        "event_type", "timestamp", "trader_id",
        "market_id", "product_type", "side",
        "price", "size", "fee"
    }

    missing = required_cols - set(events.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    events = events.sort_values("timestamp")

    open_positions = {}
    closed_positions = []

    # Validation stats
    stats = {
        "duplicate_opens": 0,
        "close_without_open": 0,
        "oversized_closes": 0,
    }

    for _, event in events.iterrows():

        # POSITION KEY GENERATION
        # For options that open with SELL (short positions), we need to track them differently

        if event["product_type"] == "perp":
            # Perps: Include side (long stays long, short stays short)
            key = (
                event["trader_id"],
                event["market_id"],
                event["product_type"],
                event["side"]
            )
        elif event["product_type"] == "option":
            # Options: Exclude side from key
            # BUT track the opening side in the position data
            key = (
                event["trader_id"],
                event["market_id"],
                event["product_type"]
            )
        else:  # spot
            # Spot: Exclude side (buy opens, sell closes)
            key = (
                event["trader_id"],
                event["market_id"],
                event["product_type"]
            )

        # ==========================================
        # OPEN POSITION
        # ==========================================
        if event["event_type"] == "open":
            if key in open_positions:
                stats["duplicate_opens"] += 1
                continue

            position_data = (
                f"{event['trader_id']}|{event['market_id']}|"
                f"{event['timestamp']}|{event.get('side', '')}"
            )
            position_id = hashlib.sha256(position_data.encode()).hexdigest()[:16]

            open_positions[key] = {
                "position_id": position_id,
                "open_time": event["timestamp"],
                "entry_price": event["price"],
                "size": event["size"],
                "fees": event["fee"],
                "trader_id": event["trader_id"],
                "market_id": event["market_id"],
                "product_type": event["product_type"],
                "side": event["side"],
            }
            
            # Store option-specific fields
            if event["product_type"] == "option":
                open_positions[key]["option_type"] = event.get("option_type")
                open_positions[key]["strike"] = event.get("strike")
                open_positions[key]["expiry"] = event.get("expiry")

        # ==========================================
        # CLOSE POSITION (close, liquidation, exercise, expire)
        # ==========================================
        elif event["event_type"] in {"close", "liquidation", "exercise", "expire"}:
            if key not in open_positions:
                stats["close_without_open"] += 1
                continue

            pos = open_positions[key]
            close_size = event["size"]

            if close_size > pos["size"]:
                stats["oversized_closes"] += 1
                continue

            # Calculate fees
            fee_ratio = close_size / pos["size"]
            allocated_open_fee = pos["fees"] * fee_ratio
            close_fee = event.get("fee", 0)
            total_fees = allocated_open_fee + close_fee

            # ==========================================
            # OPTIONS PNL CALCULATION
            # ==========================================
            if pos["product_type"] == "option":
                gross_pnl = calculate_option_pnl(
                    event_type=event["event_type"],
                    option_type=pos.get("option_type"),
                    side=pos["side"],
                    entry_price=pos["entry_price"],
                    exit_price=event.get("price", 0),
                    strike=pos.get("strike"),
                    underlying_price=event.get("underlying_price"),
                    size=close_size
                )
                net_pnl = gross_pnl - total_fees
                exit_price = event.get("price", 0)

            # ==========================================
            # SPOT/PERP PNL CALCULATION
            # ==========================================
            else:
                exit_price = event["price"]

                # If PnL provided in event, use it (already net)
                if pd.notna(event.get("pnl")):
                    net_pnl = event["pnl"]
                    gross_pnl = net_pnl + total_fees
                else:
                    # Calculate from price difference
                    if pos["side"] in {"long", "buy"}:
                        gross_pnl = (exit_price - pos["entry_price"]) * close_size
                    else:  # short/sell
                        gross_pnl = (pos["entry_price"] - exit_price) * close_size

                    net_pnl = gross_pnl - total_fees

            # Record closed position
            closed_positions.append({
                "position_id": pos["position_id"],
                "open_time": pos["open_time"],
                "close_time": event["timestamp"],
                "trader_id": pos["trader_id"],
                "market_id": pos["market_id"],
                "product_type": pos["product_type"],
                "side": pos["side"],
                "entry_price": pos["entry_price"],
                "exit_price": exit_price,
                "size": close_size,
                "gross_pnl": round(gross_pnl, 4),
                "net_pnl": round(net_pnl, 4),
                "realized_pnl": round(net_pnl, 4),
                "fees": round(total_fees, 4),
                "close_reason": event["event_type"],
            })

            # Update or remove position
            pos["size"] -= close_size
            pos["fees"] -= allocated_open_fee

            if pos["size"] <= 0:
                open_positions.pop(key)

    positions_df = pd.DataFrame(closed_positions)

    # Log validation summary
    logger.info(
        "PnL validation summary | "
        f"duplicate_opens={stats['duplicate_opens']} | "
        f"close_without_open={stats['close_without_open']} | "
        f"oversized_closes={stats['oversized_closes']}"
    )

    if positions_df.empty:
        return positions_df, pd.DataFrame()

    # Build daily PnL aggregates
    pnl_df = (
        positions_df
        .assign(date=lambda df: pd.to_datetime(df["close_time"]).dt.date)
        .groupby(
            ["date", "trader_id", "market_id", "product_type"],
            as_index=False
        )
        .agg(
            net_pnl=("net_pnl", "sum"),
            realized_pnl=("realized_pnl", "sum"),
            fees=("fees", "sum"),
            trade_count=("position_id", "count")
        )
    )

    logger.info(
        f"PnL engine results: {len(positions_df)} closed positions, "
        f"{len(open_positions)} still open"
    )

    return positions_df, pnl_df


def calculate_option_pnl(
    event_type: str,
    option_type: str,
    side: str,
    entry_price: float,
    exit_price: float,
    strike: float,
    underlying_price: float,
    size: float
) -> float:
    """
    Calculate options PnL based on event type.
    
    Args:
        event_type: close, exercise, or expire
        option_type: call or put
        side: buy or sell
        entry_price: Premium paid when opening
        exit_price: Premium received when closing (if close event)
        strike: Strike price
        underlying_price: Current underlying price (for exercise/expire)
        size: Number of contracts
    
    Returns:
        Gross PnL (before fees)
    """
    
    # ==========================================
    # CASE 1: NORMAL CLOSE (sell option back)
    # ==========================================
    if event_type == "close":
        if side == "buy":
            # Bought option, now selling it back
            gross_pnl = (exit_price - entry_price) * size
        else:  # side == "sell"
            # Sold option, now buying it back
            gross_pnl = (entry_price - exit_price) * size
        return gross_pnl
    
    # ==========================================
    # CASE 2: EXERCISE (convert to underlying)
    # ==========================================
    elif event_type == "exercise":
        if side == "buy":
            # Long option holder exercises
            if option_type == "call":
                # Call: Right to BUY at strike
                intrinsic_value = max(0, underlying_price - strike)
            else:  # put
                # Put: Right to SELL at strike
                intrinsic_value = max(0, strike - underlying_price)
            
            # PnL = intrinsic value - premium paid
            gross_pnl = (intrinsic_value - entry_price) * size
        else:
            # Short option holder (assigned) - opposite side
            if option_type == "call":
                intrinsic_value = max(0, underlying_price - strike)
            else:
                intrinsic_value = max(0, strike - underlying_price)
            
            # PnL = premium received - intrinsic value paid out
            gross_pnl = (entry_price - intrinsic_value) * size
        
        return gross_pnl
    
    # ==========================================
    # CASE 3: EXPIRE (worthless)
    # ==========================================
    elif event_type == "expire":
        if side == "buy":
            # Long option expires worthless - lose premium
            gross_pnl = -entry_price * size
        else:  # side == "sell"
            # Short option expires worthless - keep premium
            gross_pnl = entry_price * size
        
        return gross_pnl
    
    # Fallback
    return 0.0