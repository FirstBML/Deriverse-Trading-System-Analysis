# dashboards/app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data/analytics_output")

st.set_page_config(page_title="Deriverse Trading Analytics", layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card { padding: 20px; border-radius: 10px; background: #f0f2f6; }
    .stMetric { background: white; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Deriverse Trading Analytics Dashboard")

# Load data with error handling
@st.cache_data
def load_data():
    try:
        equity = pd.read_csv(DATA_DIR / "equity_curve.csv", parse_dates=["timestamp"])
        positions = pd.read_csv(DATA_DIR / "positions.csv", parse_dates=["open_time", "close_time"])
        summary = pd.read_csv(DATA_DIR / "summary_metrics.csv")
        fees = pd.read_csv(DATA_DIR / "fees_breakdown.csv")
        volume = pd.read_csv(DATA_DIR / "volume_by_market.csv")
        pnl_day = pd.read_csv(DATA_DIR / "pnl_by_day.csv", parse_dates=["date"])
        pnl_hour = pd.read_csv(DATA_DIR / "pnl_by_hour.csv")
        directional = pd.read_csv(DATA_DIR / "directional_bias.csv")
        order_perf = pd.read_csv(DATA_DIR / "order_type_performance.csv")
        
        return {
            'equity': equity,
            'positions': positions,
            'summary': summary,
            'fees': fees,
            'volume': volume,
            'pnl_day': pnl_day,
            'pnl_hour': pnl_hour,
            'directional': directional,
            'order_perf': order_perf
        }
    except FileNotFoundError as e:
        st.error(f"Analytics files not found. Please run: python -m scripts.run_analytics")
        return None

data = load_data()

if data is None or data['positions'].empty:
    st.warning("No trading data available. Please generate mock data and run analytics.")
    st.stop()

# Sidebar filters
st.sidebar.header("🎛️ Filters")

# Trader selector
traders = sorted(data['positions']['trader_id'].unique())
selected_trader = st.sidebar.selectbox("Select Trader", ["All Traders"] + traders)

# Date range filter
min_date = data['positions']['close_time'].min().date()
max_date = data['positions']['close_time'].max().date()
date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Market selector
markets = sorted(data['positions']['market_id'].unique())
selected_market = st.sidebar.selectbox("Select Market", ["All Markets"] + markets)

# Filter data based on selections
filtered_positions = data['positions'].copy()
filtered_equity = data['equity'].copy()

if selected_trader != "All Traders":
    filtered_positions = filtered_positions[filtered_positions['trader_id'] == selected_trader]
    filtered_equity = filtered_equity[filtered_equity['trader_id'] == selected_trader]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_positions = filtered_positions[
        (filtered_positions['close_time'].dt.date >= start_date) &
        (filtered_positions['close_time'].dt.date <= end_date)
    ]

if selected_market != "All Markets":
    filtered_positions = filtered_positions[filtered_positions['market_id'] == selected_market]

# KPI Tiles
st.header("📈 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_pnl = filtered_positions['realized_pnl'].sum()
    st.metric(
        "Total PnL",
        f"${total_pnl:,.2f}",
        delta=f"{total_pnl:,.2f}" if total_pnl > 0 else None
    )

with col2:
    win_rate = (filtered_positions['realized_pnl'] > 0).mean() * 100
    st.metric("Win Rate", f"{win_rate:.1f}%")

with col3:
    if selected_trader != "All Traders":
        trader_data = data['summary'][data['summary']['trader_id'] == selected_trader]
        if not trader_data.empty:
            max_dd = trader_data['max_drawdown'].iloc[0]
        else:
            max_dd = 0
    else:
        max_dd = data['summary']['max_drawdown'].min()
    st.metric("Max Drawdown", f"${max_dd:,.2f}")

with col4:
    total_fees = filtered_positions['fees'].sum()
    st.metric("Total Fees", f"${total_fees:,.2f}")

# Equity Curve with Drawdown
st.header("💰 Equity Curve")

if not filtered_equity.empty:
    fig_equity = go.Figure()
    
    for trader in filtered_equity['trader_id'].unique():
        trader_equity = filtered_equity[filtered_equity['trader_id'] == trader].sort_values('timestamp')
        
        # Cumulative PnL line
        fig_equity.add_trace(go.Scatter(
            x=trader_equity['timestamp'],
            y=trader_equity['cumulative_pnl'],
            name=f"{trader} - PnL",
            mode='lines'
        ))
        
        # Drawdown shading
        fig_equity.add_trace(go.Scatter(
            x=trader_equity['timestamp'],
            y=trader_equity['drawdown'],
            name=f"{trader} - Drawdown",
            fill='tozeroy',
            fillcolor='rgba(255,0,0,0.2)',
            line=dict(color='red', width=0.5)
        ))
    
    fig_equity.update_layout(
        xaxis_title="Time",
        yaxis_title="PnL ($)",
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig_equity, width='stretch')
else:
    st.info("No equity data for selected filters")

# Two column layout
col_left, col_right = st.columns(2)

# Daily PnL Chart
with col_left:
    st.subheader("📅 Daily PnL")
    if not filtered_positions.empty:
        daily_pnl = filtered_positions.groupby(
            filtered_positions['close_time'].dt.date
        )['realized_pnl'].sum().reset_index()
        daily_pnl.columns = ['date', 'pnl']
        
        fig_daily = px.bar(
            daily_pnl,
            x='date',
            y='pnl',
            color='pnl',
            color_continuous_scale=['red', 'gray', 'green'],
            color_continuous_midpoint=0
        )
        fig_daily.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_daily, width='stretch')
    else:
        st.info("No data")

# Fees Breakdown
with col_right:
    st.subheader("💸 Fees by Product Type")
    if not filtered_positions.empty:
        fees_by_product = filtered_positions.groupby('product_type')['fees'].sum().reset_index()
        
        fig_fees = px.bar(
            fees_by_product,
            x='product_type',
            y='fees',
            color='product_type'
        )
        fig_fees.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_fees, width='stretch')
    else:
        st.info("No data")

# Long vs Short Ratio
col_left2, col_right2 = st.columns(2)

with col_left2:
    st.subheader("⚖️ Long vs Short Ratio")
    if not filtered_positions.empty:
        long_count = len(filtered_positions[filtered_positions['side'].isin(['long', 'buy'])])
        short_count = len(filtered_positions[filtered_positions['side'].isin(['short', 'sell'])])
        
        fig_ratio = go.Figure(data=[go.Pie(
            labels=['Long', 'Short'],
            values=[long_count, short_count],
            hole=0.4,
            marker_colors=['#00cc96', '#ef553b']
        )])
        fig_ratio.update_layout(height=300)
        st.plotly_chart(fig_ratio, width='stretch')
    else:
        st.info("No data")

# Time of Day Performance
with col_right2:
    st.subheader("🕐 Performance by Hour")
    if not filtered_positions.empty:
        hourly = filtered_positions.copy()
        hourly['hour'] = hourly['close_time'].dt.hour
        hour_pnl = hourly.groupby('hour')['realized_pnl'].mean().reset_index()
        
        fig_hour = px.line(
            hour_pnl,
            x='hour',
            y='realized_pnl',
            markers=True
        )
        fig_hour.update_layout(
            height=300,
            xaxis_title="Hour of Day",
            yaxis_title="Avg PnL ($)"
        )
        st.plotly_chart(fig_hour, width='stretch')
    else:
        st.info("No data")

# Trade History Table
st.header("📋 Trade History")

if not filtered_positions.empty:
    # Prepare display dataframe
    display_df = filtered_positions[[
        'position_id', 'trader_id', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'size', 'realized_pnl', 'fees',
        'open_time', 'close_time'
    ]].copy()
    
    # Format columns
    display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
    display_df['fees'] = display_df['fees'].apply(lambda x: f"${x:,.2f}")
    display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
    display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}")
    
    # Sort by close time descending
    display_df = display_df.sort_values('close_time', ascending=False)
    
    st.dataframe(
        display_df,
        width='stretch',
        height=400,
        hide_index=True
    )
    
    # Download button
    csv = filtered_positions.to_csv(index=False)
    st.download_button(
        label="📥 Download Trade History CSV",
        data=csv,
        file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
else:
    st.info("No trades match the selected filters")

# Additional Analytics
st.header("📊 Additional Analytics")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🎯 Best/Worst Trades")
    if not filtered_positions.empty:
        best = filtered_positions.loc[filtered_positions['realized_pnl'].idxmax()]
        worst = filtered_positions.loc[filtered_positions['realized_pnl'].idxmin()]
        
        st.write(f"**Best Trade:** ${best['realized_pnl']:,.2f}")
        st.write(f"Market: {best['market_id']}")
        st.write(f"Side: {best['side']}")
        st.write("")
        st.write(f"**Worst Trade:** ${worst['realized_pnl']:,.2f}")
        st.write(f"Market: {worst['market_id']}")
        st.write(f"Side: {worst['side']}")

with col2:
    st.subheader("⏱️ Average Duration")
    if not filtered_positions.empty:
        avg_duration = filtered_positions['duration_seconds'].mean()
        hours = int(avg_duration // 3600)
        minutes = int((avg_duration % 3600) // 60)
        st.metric("Avg Position Duration", f"{hours}h {minutes}m")
        
        st.write(f"**Shortest:** {filtered_positions['duration_seconds'].min() / 60:.0f} min")
        st.write(f"**Longest:** {filtered_positions['duration_seconds'].max() / 3600:.1f} hrs")

with col3:
    st.subheader("📈 Volume by Market")
    if not filtered_positions.empty:
        market_vol = filtered_positions.groupby('market_id').agg({
            'size': 'sum',
            'realized_pnl': 'sum'
        }).sort_values('size', ascending=False)
        
        for market, row in market_vol.head(5).iterrows():
            st.write(f"**{market}**")
            st.write(f"Volume: {row['size']:,.2f} | PnL: ${row['realized_pnl']:,.2f}")
            st.write("")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Deriverse Analytics v1.0")