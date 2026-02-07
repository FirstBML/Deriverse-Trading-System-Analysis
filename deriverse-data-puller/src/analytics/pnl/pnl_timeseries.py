import pandas as pd
from .pnl_calculator import calculate_trade_pnl


def build_pnl_timeseries(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build daily and cumulative PnL series.
    """
    trades_df["pnl"] = trades_df.apply(calculate_trade_pnl, axis=1)

    daily_pnl = (
        trades_df
        .groupby("trade_date", as_index=False)["pnl"]
        .sum()
        .sort_values("trade_date")
    )

    daily_pnl["cumulative_pnl"] = daily_pnl["pnl"].cumsum()
    return daily_pnl
