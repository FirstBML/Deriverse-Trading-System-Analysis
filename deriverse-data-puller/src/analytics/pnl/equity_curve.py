def build_equity_curve(realised_df, funding_df):
    df = realised_df.copy()
    df["funding_payment"] = 0.0

    if not funding_df.empty:
        funding_agg = (
            funding_df
            .groupby(["timestamp", "trader_id"])["funding_payment"]
            .sum()
            .reset_index()
        )
        df = df.merge(
            funding_agg,
            on=["timestamp", "trader_id"],
            how="left",
            suffixes=("", "_fund")
        )
        df["funding_payment"] = df["funding_payment_fund"].fillna(0)
        df.drop(columns=["funding_payment_fund"], inplace=True)

    df["net_realised_pnl"] = df["realised_pnl"] + df["funding_payment"]
    df["cumulative_pnl"] = df.groupby("trader_id")["net_realised_pnl"].cumsum()
    return df
