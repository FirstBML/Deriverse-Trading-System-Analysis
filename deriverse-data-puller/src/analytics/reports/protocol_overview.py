import pandas as pd
import matplotlib.pyplot as plt
import os
import json
import numpy as np

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
# Calculate volume correctly per product type
# ---------------------------
# Volume definition:
# - Option: premium
# - Spot/Perp: price * size
df["volume"] = np.where(
    df["product_type"] == "option",
    df["premium"].fillna(0),
    (df["price"].fillna(0) * df["size"].fillna(0))
)

# ---------------------------
# Summary statistics
# ---------------------------
summary = (
    df.groupby("product_type")
      .agg(
          volume=("volume", "sum"),
          unique_traders=("trader_id", "nunique")
      )
      .reset_index()
)

# Add volume share percentage to summary
summary["volume_share_pct"] = (
    summary["volume"] / summary["volume"].sum() * 100
).round(2)

# ---------------------------
# Save report
# ---------------------------
summary.to_csv(REPORT_CSV_PATH, index=False)
summary.to_json(REPORT_JSON_PATH, orient='records', indent=4)

print("✅ Protocol overview saved to:")
print(f"- {REPORT_CSV_PATH}")
print(f"- {REPORT_JSON_PATH}")
print("\n📊 Summary:")
print(summary.to_string(index=False))

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
plt.savefig("data/reports/volume_by_product.png", dpi=150)
plt.close()  # Close to prevent blocking

# ---------------------------
# Plot unique traders per product type
# ---------------------------
plt.figure(figsize=(8, 5))
plt.bar(summary['product_type'], summary['unique_traders'], color=colors[:len(summary)])
plt.title("Unique Traders by Product Type")
plt.xlabel("Product Type")
plt.ylabel("Number of Unique Traders")
plt.tight_layout()
plt.savefig("data/reports/traders_by_product.png", dpi=150)
plt.close()  

print("\n📊 Charts saved to:")
print("- data/reports/volume_by_product.png")
print("- data/reports/traders_by_product.png")
