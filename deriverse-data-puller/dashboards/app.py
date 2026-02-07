import streamlit as st
import pandas as pd
from pathlib import Path

DATA = Path("data/analytics_output")

st.set_page_config(layout="wide")
st.title("Deriverse Trading Analytics")

equity = pd.read_csv(DATA / "equity_curve.csv", parse_dates=["timestamp"])
win_rate = pd.read_csv(DATA / "win_rate.csv")
fees = pd.read_csv(DATA / "fees.csv")

trader = st.selectbox("Select trader", equity["trader_id"].unique())

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total PnL",
        f"{equity[equity.trader_id == trader].cumulative_pnl.iloc[-1]:.2f}"
    )

with col2:
    st.metric(
        "Win Rate",
        f"{win_rate[win_rate.trader_id == trader].win_rate.iloc[0]*100:.1f}%"
    )

with col3:
    st.metric(
        "Total Fees",
        f"{fees[fees.trader_id == trader].total_fees.iloc[0]:.2f}"
    )

st.subheader("Equity Curve")
st.line_chart(
    equity[equity.trader_id == trader]
    .set_index("timestamp")["cumulative_pnl"]
)
