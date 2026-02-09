import pandas as pd
from datetime import datetime, timezone

from src.analytics.pnl_engine import compute_realized_pnl

def test_simple_open_close_pnl():
    events = pd.DataFrame([
        {
            "event_id": "e1",
            "event_type": "open",
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 100.0,
            "size": 1,
            "fee": 0.5,
        },
        {
            "event_id": "e2",
            "event_type": "close",
            "timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 110.0,
            "size": 1,
            "fee": 0.5,
            "pnl": 9.0,  # truth reference
        },
    ])

    positions, pnl = compute_realized_pnl(events)

    assert len(positions) == 1
    assert positions.iloc[0]["realized_pnl"] == 9.0

def test_open_without_close_has_no_pnl():
    events = pd.DataFrame([
        {
            "event_id": "e1",
            "event_type": "open",
            "timestamp": datetime.now(timezone.utc),
            "trader_id": "T1",
            "market_id": "SOL-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 50,
            "size": 2,
            "fee": 0.2,
        }
    ])

    positions, pnl = compute_realized_pnl(events)

    assert positions.empty
    assert pnl.empty

def test_pnl_only_on_close_events():
    events = pd.DataFrame([
        {
            "event_id": "e1",
            "event_type": "trade",
            "timestamp": datetime.now(timezone.utc),
            "trader_id": "T1",
            "market_id": "SOL/USDC",
            "product_type": "spot",
            "side": "buy",
            "price": 100,
            "size": 1,
            "fee": 0.1,
        }
    ])

    positions, pnl = compute_realized_pnl(events)

    assert positions.empty
    assert pnl.empty
def test_pnl_engine_is_deterministic():
    events = pd.DataFrame([
        {
            "event_id": "e1",
            "event_type": "open",
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "trader_id": "T2",
            "market_id": "ETH-PERP",
            "product_type": "perp",
            "side": "short",
            "price": 200,
            "size": 1,
            "fee": 0.3,
        },
        {
            "event_id": "e2",
            "event_type": "close",
            "timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "trader_id": "T2",
            "market_id": "ETH-PERP",
            "product_type": "perp",
            "side": "short",
            "price": 180,
            "size": 1,
            "fee": 0.3,
            "pnl": 19.4,
        },
    ])

    p1, pnl1 = compute_realized_pnl(events)
    p2, pnl2 = compute_realized_pnl(events)

    pd.testing.assert_frame_equal(p1, p2)
    pd.testing.assert_frame_equal(pnl1, pnl2)

def test_close_without_open_is_rejected():
    events = pd.DataFrame([
        {
            "event_id": "e1",
            "event_type": "close",
            "timestamp": datetime.now(timezone.utc),
            "trader_id": "T3",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 120,
            "size": 1,
            "fee": 0.4,
            "pnl": 0,
        }
    ])

    positions, pnl = compute_realized_pnl(events)

    assert positions.empty
    assert pnl.empty
def test_partial_close_pnl():
    events = pd.DataFrame([
        {
            "event_id": "e1",
            "event_type": "open",
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 100.0,
            "size": 10,
            "fee": 1.0,
        },
        {
            # partial close (50%)
            "event_id": "e2",
            "event_type": "close",
            "timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 110.0,
            "size": 5,
            "fee": 0.5,
        },
        {
            # final close
            "event_id": "e3",
            "event_type": "close",
            "timestamp": datetime(2026, 1, 3, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 120.0,
            "size": 5,
            "fee": 0.5,
        },
    ])

    positions, pnl = compute_realized_pnl(events)

    assert len(positions) == 2

    realized = positions["realized_pnl"].sum()
    assert round(realized, 2) == round(
        ((110 - 100) * 5 + (120 - 100) * 5) - 2.0, 2
    )

def test_multiple_partial_closes_order_independent():
    base_events = [
        {
            "event_id": "o1",
            "event_type": "open",
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 100,
            "size": 10,
            "fee": 1.0,
        },
        {
            "event_id": "c1",
            "event_type": "close",
            "timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 110,
            "size": 4,
            "fee": 0.4,
        },
        {
            "event_id": "c2",
            "event_type": "close",
            "timestamp": datetime(2026, 1, 3, tzinfo=timezone.utc),
            "trader_id": "T1",
            "market_id": "BTC-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 120,
            "size": 6,
            "fee": 0.6,
        },
    ]

    df1 = pd.DataFrame(base_events)
    df2 = pd.DataFrame(reversed(base_events))

    p1, pnl1 = compute_realized_pnl(df1)
    p2, pnl2 = compute_realized_pnl(df2)

    pd.testing.assert_frame_equal(p1, p2)
    pd.testing.assert_frame_equal(pnl1, pnl2)
def test_liquidation_is_partial_close():
    events = pd.DataFrame([
        {
            "event_id": "o1",
            "event_type": "open",
            "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "trader_id": "T9",
            "market_id": "ETH-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 200,
            "size": 10,
            "fee": 1.0,
        },
        {
            "event_id": "l1",
            "event_type": "liquidation",
            "timestamp": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "trader_id": "T9",
            "market_id": "ETH-PERP",
            "product_type": "perp",
            "side": "long",
            "price": 150,
            "size": 4,
            "fee": 0.5,
        },
    ])

    positions, pnl = compute_realized_pnl(events)

    assert len(positions) == 1
    assert positions.iloc[0]["close_reason"] == "liquidation"
