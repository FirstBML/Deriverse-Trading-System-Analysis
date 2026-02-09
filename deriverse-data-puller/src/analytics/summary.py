# src/analytics/summary.py
import pandas as pd

def compute_executive_summary(positions: pd.DataFrame, pnl: pd.DataFrame) -> dict:
    """
    Compute high-level KPIs from canonical PnL outputs.
    
    Args:
        positions: Output from compute_realized_pnl (positions_df)
        pnl: Output from compute_realized_pnl (pnl_df)
    
    Returns:
        Dictionary of KPI metrics
    """
    if positions.empty:
        return {"status": "no_data"}
    
    summary = {}
    
    # Core PnL
    summary["total_pnl"] = pnl["net_pnl"].sum()
    summary["total_fees"] = pnl["fees"].sum()
    summary["trade_count"] = len(positions)
    summary["win_rate"] = (positions["net_pnl"] > 0).mean()
    
    # Win/Loss Analysis
    winning_trades = positions[positions["net_pnl"] > 0]
    losing_trades = positions[positions["net_pnl"] < 0]
    
    summary["avg_win"] = winning_trades["net_pnl"].mean() if len(winning_trades) > 0 else 0
    summary["avg_loss"] = losing_trades["net_pnl"].mean() if len(losing_trades) > 0 else 0
    summary["best_trade"] = positions["net_pnl"].max()
    summary["worst_trade"] = positions["net_pnl"].min()
    
    # Duration Analysis
    positions = positions.copy()
    positions["duration"] = (
        pd.to_datetime(positions["close_time"]) - 
        pd.to_datetime(positions["open_time"])
    )
    summary["avg_duration"] = positions["duration"].mean()
    
    # Directional Bias
    summary["long_ratio"] = (positions["side"].isin(["long", "buy"])).mean()
    summary["short_ratio"] = (positions["side"].isin(["short", "sell"])).mean()
    
    # Drawdown
    pnl_sorted = pnl.sort_values("date")
    pnl_sorted["cum_pnl"] = pnl_sorted["net_pnl"].cumsum()
    pnl_sorted["drawdown"] = pnl_sorted["cum_pnl"] - pnl_sorted["cum_pnl"].cummax()
    summary["max_drawdown"] = pnl_sorted["drawdown"].min()
    
    return summary