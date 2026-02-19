# src/analytics/pnl_engine.py
"""
Canonical PnL engine with full lifecycle support.
Handles position tracking, PnL calculation, and transaction mapping.
"""

import pandas as pd
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def compute_realized_pnl(events: pd.DataFrame):
    """
    Canonical PnL engine with full options lifecycle support.
    
    Returns:
        positions_df: Closed positions with realized PnL
        pnl_df: Daily PnL aggregates
        open_positions_df: Currently open positions
    """

    required_cols = {
        "event_type", "timestamp", "trader_id",
        "market_id", "product_type", "side",
        "price", "size"
    }

    missing = required_cols - set(events.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    events = events.sort_values("timestamp")

    open_positions = {}
    closed_positions = []

    stats = {
        "duplicate_opens": 0,
        "close_without_open": 0,
        "oversized_closes": 0,
    }

    for _, event in events.iterrows():

        if event["product_type"] == "perp":
            key = (
                event["trader_id"],
                event["market_id"],
                event["product_type"],
                event["side"]
            )
        elif event["product_type"] == "option":
            key = (
                event["trader_id"],
                event["market_id"],
                event["product_type"]
            )
        else:
            key = (
                event["trader_id"],
                event["market_id"],
                event["product_type"]
            )

        if event["event_type"] == "open":
            if key in open_positions:
                stats["duplicate_opens"] += 1
                continue

            position_id = event.get('position_id')
            if not position_id:
                position_data = (
                    f"{event['trader_id']}|{event['market_id']}|"
                    f"{event['timestamp']}|{event.get('side', '')}"
                )
                position_id = hashlib.sha256(position_data.encode()).hexdigest()[:16]

            fee_value = event.get("fee_usd", event.get("fee", 0))

            open_positions[key] = {
                "position_id": position_id,
                "open_time": event["timestamp"],
                "entry_price": event["price"],
                "size": event["size"],
                "fees": fee_value,
                "trader_id": event["trader_id"],
                "market_id": event["market_id"],
                "product_type": event["product_type"],
                "side": event["side"],
                "open_tx_hash": event.get("tx_hash"),
            }
            
            if event["product_type"] == "option":
                open_positions[key]["option_type"]      = event.get("option_type")
                open_positions[key]["strike"]           = event.get("strike")
                open_positions[key]["expiry"]           = event.get("expiry")
                open_positions[key]["underlying_price"] = event.get("underlying_price")
                open_positions[key]["time_to_expiry"]   = event.get("time_to_expiry")
                open_positions[key]["implied_volatility"] = event.get("implied_volatility")

        elif event["event_type"] in {"close", "liquidation", "exercise", "expire"}:
            if key not in open_positions:
                stats["close_without_open"] += 1
                continue

            pos = open_positions[key]
            close_size = event["size"]

            if close_size > pos["size"]:
                stats["oversized_closes"] += 1
                continue

            fee_ratio = close_size / pos["size"]
            allocated_open_fee = pos["fees"] * fee_ratio
            
            close_fee_value = event.get("fee_usd", event.get("fee", 0))
            total_fees = allocated_open_fee + close_fee_value

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

            else:
                exit_price = event["price"]

                if pd.notna(event.get("pnl")):
                    net_pnl = event["pnl"]
                    gross_pnl = net_pnl + total_fees
                else:
                    if pos["side"] in {"long", "buy"}:
                        gross_pnl = (exit_price - pos["entry_price"]) * close_size
                    else:
                        gross_pnl = (pos["entry_price"] - exit_price) * close_size

                    net_pnl = gross_pnl - total_fees

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
                "open_tx_hash": pos.get("open_tx_hash"),
                "close_tx_hash": event.get("tx_hash"),
                "underlying_price":   pos.get("underlying_price"),
                "time_to_expiry":     pos.get("time_to_expiry"),
                "implied_volatility": pos.get("implied_volatility"),
                "option_type":        pos.get("option_type"),
            })

            pos["size"] -= close_size
            pos["fees"] -= allocated_open_fee

            if pos["size"] <= 0:
                open_positions.pop(key)

    positions_df = pd.DataFrame(closed_positions)

    logger.info(
        "PnL validation summary | "
        f"duplicate_opens={stats['duplicate_opens']} | "
        f"close_without_open={stats['close_without_open']} | "
        f"oversized_closes={stats['oversized_closes']}"
    )

    if positions_df.empty:
        positions_df = pd.DataFrame()
        pnl_df = pd.DataFrame()
    else:
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

    open_positions_list = []
    for key, pos in open_positions.items():
        now = datetime.now(timezone.utc)
        open_time = pd.to_datetime(pos["open_time"])
        if open_time.tzinfo is None:
            open_time = open_time.tz_localize(timezone.utc)
        
        time_held = (now - open_time).total_seconds()
        
        open_positions_list.append({
            "position_id": pos["position_id"],
            "trader_id": pos["trader_id"],
            "market_id": pos["market_id"],
            "product_type": pos["product_type"],
            "side": pos["side"],
            "entry_price": pos["entry_price"],
            "size": pos["size"],
            "fees_paid": pos["fees"],
            "open_time": pos["open_time"],
            "time_held_seconds": time_held,
            "open_tx_hash": pos.get("open_tx_hash")
        })
    
    open_positions_df = pd.DataFrame(open_positions_list)

    logger.info(
        f"PnL engine results: {len(positions_df)} closed positions, "
        f"{len(open_positions_df)} still open"
    )

    return positions_df, pnl_df, open_positions_df


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
    """Calculate options PnL based on event type."""
    
    if event_type == "close":
        if side == "buy":
            gross_pnl = (exit_price - entry_price) * size
        else:
            gross_pnl = (entry_price - exit_price) * size
        return gross_pnl
    
    elif event_type == "exercise":
        if side == "buy":
            if option_type == "call":
                intrinsic_value = max(0, underlying_price - strike)
            else:
                intrinsic_value = max(0, strike - underlying_price)
            gross_pnl = (intrinsic_value - entry_price) * size
        else:
            if option_type == "call":
                intrinsic_value = max(0, underlying_price - strike)
            else:
                intrinsic_value = max(0, strike - underlying_price)
            gross_pnl = (entry_price - intrinsic_value) * size
        
        return gross_pnl
    
    elif event_type == "expire":
        if side == "buy":
            gross_pnl = -entry_price * size
        else:
            gross_pnl = entry_price * size
        
        return gross_pnl
    
    return 0.0