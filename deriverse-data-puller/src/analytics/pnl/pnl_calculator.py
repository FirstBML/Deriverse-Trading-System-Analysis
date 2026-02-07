def calculate_trade_pnl(row):
    if row["product_type"] == "option":
        return row["exercise_pnl"] - row["premium"] - row["fees"]

    direction = 1 if row["side"].lower() == "long" else -1
    gross_pnl = (row["exit_price"] - row["entry_price"]) * row["size"] * direction
    return gross_pnl - row["fees"]
