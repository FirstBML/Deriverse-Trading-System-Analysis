# scripts/diagnose_data.py
"""
Data quality diagnostic tool.
Run after analytics to verify all data is properly processed.
"""

import pandas as pd
from pathlib import Path
import json

print("=" * 60)
print("DATA QUALITY DIAGNOSTIC")
print("=" * 60)

# Check positions file
positions_path = Path("data/analytics_output/positions.csv")
if positions_path.exists():
    positions = pd.read_csv(positions_path)
    
    print(f"\n📊 POSITIONS SUMMARY ({len(positions)} total)")
    print("\n✅ By Product Type:")
    product_counts = positions['product_type'].value_counts()
    for product, count in product_counts.items():
        print(f"  {product:10} {count:>3} positions")
    
    print("\n✅ By Market:")
    market_counts = positions['market_id'].value_counts()
    for market, count in market_counts.items():
        print(f"  {market:25} {count:>3} positions")
    
    print("\n✅ By Trader:")
    trader_counts = positions['trader_id'].value_counts()
    for trader, count in trader_counts.items():
        print(f"  {trader:10} {count:>3} positions")
    
    print("\n💰 PnL BY PRODUCT TYPE:")
    pnl_by_product = positions.groupby('product_type')['realized_pnl'].sum()
    for product, pnl in pnl_by_product.items():
        print(f"  {product:10} ${pnl:>12,.2f}")
    
    print("\n🔍 OPTION POSITIONS DETAIL:")
    option_positions = positions[positions['product_type'] == 'option']
    if not option_positions.empty:
        print(f"  Found {len(option_positions)} option positions")
        for _, row in option_positions.iterrows():
            print(f"    • {row['market_id']:30} {row['trader_id']:10} ${row['realized_pnl']:>10,.2f}")
    else:
        print("  ❌ NO OPTION POSITIONS FOUND")
    
    print("\n📋 ALL POSITIONS SUMMARY:")
    # Check which columns exist
    available_cols = ['position_id', 'trader_id', 'market_id', 'product_type', 'side', 'realized_pnl']
    if 'close_reason' in positions.columns:
        available_cols.append('close_reason')
    
    print(positions[available_cols].to_string(index=False))
    
else:
    print("❌ positions.csv not found")

# Check normalized events
events_path = Path("data/normalized/events.jsonl")
if events_path.exists():
    events = []
    with open(events_path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    
    df = pd.DataFrame(events)
    
    print(f"\n📥 NORMALIZED EVENTS ({len(df)} total)")
    print("\n✅ By Event Type:")
    event_counts = df['event_type'].value_counts()
    for event_type, count in event_counts.items():
        print(f"  {event_type:10} {count:>3} events")
    
    print("\n✅ By Product Type:")
    product_counts = df['product_type'].value_counts()
    for product, count in product_counts.items():
        print(f"  {product:10} {count:>3} events")
    
    print("\n🎯 OPTION EVENTS BREAKDOWN:")
    option_events = df[df['product_type'] == 'option']
    print(f"  Total option events: {len(option_events)}")
    if not option_events.empty:
        print("\n  By event type:")
        option_event_counts = option_events['event_type'].value_counts()
        for event_type, count in option_event_counts.items():
            print(f"    {event_type:10} {count:>3}")
        
        print("\n  By market:")
        option_market_counts = option_events['market_id'].value_counts()
        for market, count in option_market_counts.items():
            print(f"    {market:30} {count:>3}")
    else:
        print("  ❌ NO OPTION EVENTS")
else:
    print("❌ events.jsonl not found")

# Check raw mock data
mock_path = Path("configs/mock_data.json")
if mock_path.exists():
    with open(mock_path) as f:
        mock_data = json.load(f)
    
    print(f"\n📦 RAW MOCK DATA ({len(mock_data)} events)")
    mock_df = pd.DataFrame(mock_data)
    
    print("\n✅ By Event Type:")
    event_counts = mock_df['event_type'].value_counts()
    for event_type, count in event_counts.items():
        print(f"  {event_type:10} {count:>3} events")
    
    print("\n✅ By Product Type:")
    product_counts = mock_df['product_type'].value_counts()
    for product, count in product_counts.items():
        print(f"  {product:10} {count:>3} events")
else:
    print("\n❌ configs/mock_data.json not found")

print("\n" + "=" * 60)

# Check for duplicates
if events_path.exists():
    print("\n🔍 CHECKING FOR DUPLICATES...")
    event_ids = [e['event_id'] for e in events]
    unique_ids = set(event_ids)
    
    if len(event_ids) != len(unique_ids):
        print(f"  ⚠️  WARNING: Found {len(event_ids) - len(unique_ids)} duplicate events!")
        print(f"  Total events: {len(event_ids)}, Unique: {len(unique_ids)}")
    else:
        print(f"  ✅ No duplicates found ({len(event_ids)} unique events)")

print("=" * 60)