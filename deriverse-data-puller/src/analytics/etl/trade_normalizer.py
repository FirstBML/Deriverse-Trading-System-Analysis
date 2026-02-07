import pandas as pd

def normalize_trades(events_df: pd.DataFrame) -> pd.DataFrame:
    trades = events_df[events_df["event_type"] == "trade"].copy()

    trades["trade_date"] = pd.to_datetime(trades["ts"]).dt.date

    trades["entry_price"] = trades["price"]
    trades["exit_price"] = trades["price"]  # placeholder
    trades["fees"] = trades["fee"].fillna(0)

    def infer_product(market_id: str) -> str:
        m = market_id.lower()
        if "perp" in m:
            return "perp"
        if "option" in m:
            return "option"
        return "spot"

    trades["product_type"] = trades["market_id"].apply(infer_product)

    return trades[
        [
            "trade_date",
            "trader_id",
            "product_type",
            "entry_price",
            "exit_price",
            "size",
            "side",
            "fees"
        ]
    ]
