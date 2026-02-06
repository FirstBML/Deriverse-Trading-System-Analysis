import pandas as pd
import matplotlib.pyplot as plt
import os
import json

# ---------------------------
# Paths
# ---------------------------
RAW_EVENTS_PATH = "configs/mock_data.json"
REPORT_CSV_PATH = "data/reports/protocol_overview.csv"
REPORT_JSON_PATH = "data/reports/protocol_overview.json"

os.makedirs("data/reports", exist_ok=True)

# ---------------------------
# Load events
# ---------------------------
with open(RAW_EVENTS_PATH, "r") as f:
    events = json.load(f)

df = pd.DataFrame(events)

# ---------------------------
# Ensure columns exist
# ---------------------------
required_columns = [
    'trade_value', 'product_type', 'trader_id', 'market_id'
]

for col in required_columns:
    if col not in df.columns:
        # Add empty column if missing to prevent KeyError
        df[col] = pd.NA

# ---------------------------
# Summary statistics
# ---------------------------
# Total volume per product type (Spot / Perp / Option)
volume_summary = df.groupby('product_type')['trade_value'].sum().reset_index()
volume_summary.rename(columns={'trade_value': 'volume'}, inplace=True)

# Number of unique traders per product type
traders_summary = df.groupby('product_type')['trader_id'].nunique().reset_index()
traders_summary.rename(columns={'trader_id': 'unique_traders'}, inplace=True)

# Combine summaries
summary = pd.merge(volume_summary, traders_summary, on='product_type', how='outer')

# ---------------------------
# Save report
# ---------------------------
summary.to_csv(REPORT_CSV_PATH, index=False)
summary.to_json(REPORT_JSON_PATH, orient='records', indent=4)

print("✅ Protocol overview saved to:")
print(f"- {REPORT_CSV_PATH}")
print(f"- {REPORT_JSON_PATH}")

# ---------------------------
# Plot volume per product type
# ---------------------------
plt.figure(figsize=(8, 5))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Spot, Perp, Option
plt.bar(summary['product_type'], summary['volume'], color=colors[:len(summary)])
plt.title("Trading Volume by Product Type")
plt.xlabel("Product Type")
plt.ylabel("Volume")
plt.tight_layout()
plt.show()

# ---------------------------
# Plot unique traders per product type
# ---------------------------
plt.figure(figsize=(8, 5))
plt.bar(summary['product_type'], summary['unique_traders'], color=colors[:len(summary)])
plt.title("Unique Traders by Product Type")
plt.xlabel("Product Type")
plt.ylabel("Number of Unique Traders")
plt.tight_layout()
plt.show()
