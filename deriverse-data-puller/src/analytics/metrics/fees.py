def build_fees(trades_df):
    return (
        trades_df
        .groupby("trader_id")["fee"]
        .sum()
        .reset_index(name="total_fees")
    )
