import pandas as pd


def compute_drawdown(cumulative_pnl: pd.Series) -> pd.Series:
    """
    Compute drawdown from cumulative PnL.
    """
    rolling_max = cumulative_pnl.cummax()
    drawdown = cumulative_pnl - rolling_max
    return drawdown
