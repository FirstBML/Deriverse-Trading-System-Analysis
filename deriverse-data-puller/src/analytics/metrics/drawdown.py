import pandas as pd

def build_drawdowns(equity_df: pd.DataFrame) -> pd.DataFrame:
    out = []

    for trader, df in equity_df.groupby("trader_id"):
        df = df.sort_values("timestamp")
        peak = df["cumulative_pnl"].cummax()
        drawdown = df["cumulative_pnl"] - peak

        out.append({
            "trader_id": trader,
            "max_drawdown": drawdown.min()
        })

    return pd.DataFrame(out)
