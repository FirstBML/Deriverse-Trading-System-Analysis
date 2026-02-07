from typing import List, Dict
from collections import defaultdict

def build_win_rate(realised_df):
    return (
        realised_df
        .assign(win=lambda x: x["realised_pnl"] > 0)
        .groupby("trader_id")["win"]
        .mean()
        .reset_index(name="win_rate")
    )
