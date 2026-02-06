# src/analytics/reports/protocol_overview.py
"""
Deriverse Protocol Overview Analytics

Generates:
- CSV summary: volume, unique traders, fees per market type
- JSON summary: same data
- Bar chart: volume by Spot / Perps / Options
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

# =============================
# Config: paths
# =============================
RAW_DATA_PATH = "data/normalized/events.jsonl"
CSV_OUTPUT_PATH = "data/reports/protocol_overview.csv"
JSON_OUTPUT_PATH = "data/reports/protocol_overview.json"
CHART_OUTPUT_PATH = "data/reports/volume_by_product.png"

# Ensure reports folder exists
os.makedirs(os.path.dirname(CSV_OUTPUT_PATH), exist_ok=True)

# =============================
# Load data
# =============================
try:
    df = pd.read_json(RAW_DATA_PATH, lines=True)
except FileNotFoundError:
    raise FileNotFoundError(f"Cannot find {RAW_DATA_PATH}. Make sure ingestion ran successfully.")

# =============================
# Analytics
# =============================
# Volume: sum(size * price) per market type
df['trade_value'] = df['size'] * df['price']
volume = df.groupby('product_type')['trade_value'].sum()
unique_traders = df.groupby('product_type')['trader'].nunique()
fees = df.groupby('product_type')['fee'].sum()
avg_trade_size = df.groupby('product_type')['size'].mean()
summary = pd.DataFrame({
    'volume': volume,
    'unique_traders': unique_traders,
    'fees': fees,
    'avg_trade_size': avg_trade_size
}).reset_index()

# Unique traders per market type
unique_traders = df.groupby('market_type')['trader'].nunique()

# Fee revenue per market type
fees = df.groupby('market_type')['fee'].sum()

# Average trade size per market type
avg_trade_size = df.groupby('market_type')['size'].mean()

# =============================
# Build summary table
# =============================
summary = pd.DataFrame({
    'volume': volume,
    'unique_traders': unique_traders,
    'fees': fees,
    'avg_trade_size': avg_trade_size
}).reset_index()

# Save CSV & JSON
summary.to_csv(CSV_OUTPUT_PATH, index=False)
summary.to_json(JSON_OUTPUT_PATH, orient='records', lines=True)

print(f"✅ Protocol overview saved to:\n- {CSV_OUTPUT_PATH}\n- {JSON_OUTPUT_PATH}")

# =============================
# Plot volume by market type
# =============================
plt.figure(figsize=(8,5))
plt.bar(summary['market_type'], summary['volume'], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
plt.title("Deriverse Trading Volume by Product")
plt.ylabel("Volume (USD)")
plt.xlabel("Market Type")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(CHART_OUTPUT_PATH)
plt.close()
print(f"✅ Volume chart saved to {CHART_OUTPUT_PATH}")
