# dashboards/app.py - COMPLETE FINAL VERSION
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("data/analytics_output")

st.set_page_config(page_title="Deriverse Trading Analytics", layout="wide")

st.markdown("""
    <style>
    .metric-card { padding: 20px; border-radius: 10px; background: #f0f2f6; }
    .stMetric { background: white; padding: 15px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Deriverse Trading Analytics Dashboard")

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
        greeks = pd.read_csv(DATA_DIR / "greeks_exposure.csv")
        
        return {
            'equity': equity, 'positions': positions, 'summary': summary,
            'fees': fees, 'volume': volume, 'pnl_day': pnl_day,
            'pnl_hour': pnl_hour, 'directional': directional, 
            'order_perf': order_perf, 'greeks': greeks
        }
    except FileNotFoundError:
        st.error("Analytics files not found. Run: python -m scripts.run_analytics")
        return None

data = load_data()

if data is None or data['positions'].empty:
    st.warning("No trading data available.")
    st.stop()

# ✅ ADD: Calculate volume in USD for positions
if not data['positions'].empty:
    data['positions']['volume_usd'] = data['positions']['exit_price'] * data['positions']['size']

# Sidebar Filters
st.sidebar.header("🎛️ Filters")
traders = sorted(data['positions']['trader_id'].unique())
selected_trader = st.sidebar.selectbox("Trader", ["All"] + traders)

min_date = data['positions']['close_time'].min().date()
max_date = data['positions']['close_time'].max().date()
date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date))

markets = sorted(data['positions']['market_id'].unique())
selected_market = st.sidebar.selectbox("Market", ["All"] + markets)

# Filter Data
filtered_positions = data['positions'].copy()
if selected_trader != "All":
    filtered_positions = filtered_positions[filtered_positions['trader_id'] == selected_trader]
if len(date_range) == 2:
    start, end = date_range
    filtered_positions = filtered_positions[
        (filtered_positions['close_time'].dt.date >= start) &
        (filtered_positions['close_time'].dt.date <= end)
    ]
if selected_market != "All":
    filtered_positions = filtered_positions[filtered_positions['market_id'] == selected_market]

# KPI Tiles
st.header("📈 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_pnl = filtered_positions['realized_pnl'].sum()
    st.metric("Total PnL", f"${total_pnl:,.2f}", delta=f"{total_pnl:,.2f}" if total_pnl > 0 else None)

with col2:
    win_rate = (filtered_positions['realized_pnl'] > 0).mean() * 100
    st.metric("Win Rate", f"{win_rate:.1f}%")

with col3:
    if selected_trader != "All":
        trader_data = data['summary'][data['summary']['trader_id'] == selected_trader]
        max_dd = trader_data['max_drawdown'].iloc[0] if not trader_data.empty else 0
    else:
        max_dd = data['summary']['max_drawdown'].min()
    st.metric("Max Drawdown", f"${max_dd:,.2f}")

with col4:
    total_fees = filtered_positions['fees'].sum()
    st.metric("Total Fees", f"${total_fees:,.2f}")

# Win/Loss Analysis
st.header("💹 Win/Loss Analysis")
col1, col2, col3 = st.columns(3)

with col1:
    winning = filtered_positions[filtered_positions['realized_pnl'] > 0]
    avg_win = winning['realized_pnl'].mean() if len(winning) > 0 else 0
    st.metric("Average Win", f"${avg_win:,.2f}")

with col2:
    losing = filtered_positions[filtered_positions['realized_pnl'] < 0]
    avg_loss = losing['realized_pnl'].mean() if len(losing) > 0 else 0
    st.metric("Average Loss", f"${avg_loss:,.2f}")

with col3:
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
    st.metric("Profit Factor", f"{profit_factor:.2f}x")

# Risk-Adjusted Returns
if 'sharpe_ratio' in data['summary'].columns:
    st.header("📊 Risk-Adjusted Returns")
    col1, col2 = st.columns(2)
    with col1:
        if selected_trader != "All":
            trader_sharpe = data['summary'][data['summary']['trader_id'] == selected_trader]['sharpe_ratio'].iloc[0] if not data['summary'][data['summary']['trader_id'] == selected_trader].empty else 0
        else:
            trader_sharpe = data['summary']['sharpe_ratio'].mean()
        st.metric("Sharpe Ratio", f"{trader_sharpe:.2f}")
    with col2:
        if selected_trader != "All":
            trader_sortino = data['summary'][data['summary']['trader_id'] == selected_trader]['sortino_ratio'].iloc[0] if not data['summary'][data['summary']['trader_id'] == selected_trader].empty else 0
        else:
            trader_sortino = data['summary']['sortino_ratio'].mean()
        st.metric("Sortino Ratio", f"{trader_sortino:.2f}")

# Equity Curve
st.header("💰 Equity Curve")
filtered_equity = data['equity'].copy()
if selected_trader != "All":
    filtered_equity = filtered_equity[filtered_equity['trader_id'] == selected_trader]

if not filtered_equity.empty:
    fig = go.Figure()
    for trader in filtered_equity['trader_id'].unique():
        trader_eq = filtered_equity[filtered_equity['trader_id'] == trader].sort_values('timestamp')
        trader_short = trader[:8] + "..." if len(trader) > 12 else trader
        fig.add_trace(go.Scatter(x=trader_eq['timestamp'], y=trader_eq['cumulative_pnl'], name=f"{trader_short} PnL"))
        fig.add_trace(go.Scatter(x=trader_eq['timestamp'], y=trader_eq['drawdown'], fill='tozeroy', fillcolor='rgba(255,0,0,0.2)', line=dict(color='red', width=0.5), name=f"{trader_short} DD"))
    fig.update_layout(xaxis_title="Time", yaxis_title="PnL ($)", hovermode='x unified', height=400)
    st.plotly_chart(fig, width='stretch')

# Charts Row 1
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Daily PnL")
    if not filtered_positions.empty:
        daily = filtered_positions.groupby(filtered_positions['close_time'].dt.date)['realized_pnl'].sum().reset_index()
        daily.columns = ['date', 'pnl']
        fig = px.bar(daily, x='date', y='pnl', color='pnl', color_continuous_scale=['red', 'gray', 'green'], color_continuous_midpoint=0)
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, width='stretch')

with col2:
    st.subheader("💸 Fees by Product")
    if not filtered_positions.empty:
        fees_prod = filtered_positions.groupby('product_type')['fees'].sum().reset_index()
        fig = px.bar(fees_prod, x='product_type', y='fees', color='product_type')
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, width='stretch')

# ✅ NEW: Complete Fee Analysis Section
st.header("💸 Complete Fee Analysis")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Fee Composition Breakdown")
    if not data['fees'].empty:
        # Get filtered trader fees
        if selected_trader != "All":
            trader_fees = data['fees'][data['fees']['trader_id'] == selected_trader]
        else:
            trader_fees = data['fees']
        
        fig = px.pie(trader_fees, values='total_fees', names='product_type', 
                     title='Fee Distribution by Product Type')
        fig.update_layout(height=300)
        st.plotly_chart(fig, width='stretch')
    
    # Show fee breakdown table
    if not filtered_positions.empty:
        fee_summary = filtered_positions.groupby('product_type').agg({
            'fees': ['sum', 'mean', 'count']
        }).round(2)
        fee_summary.columns = ['Total Fees', 'Avg Fee', 'Trade Count']
        st.dataframe(fee_summary, width='stretch')

with col2:
    st.subheader("Cumulative Fee Tracking")
    if not filtered_positions.empty:
        # Calculate cumulative fees over time
        fee_timeline = filtered_positions.sort_values('close_time')[['close_time', 'fees']].copy()
        fee_timeline['cumulative_fees'] = fee_timeline['fees'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fee_timeline['close_time'],
            y=fee_timeline['cumulative_fees'],
            mode='lines+markers',
            name='Cumulative Fees',
            line=dict(color='red', width=2)
        ))
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Cumulative Fees ($)",
            height=300
        )
        st.plotly_chart(fig, width='stretch')

# ✅ NEW: Complete Volume Analysis
st.header("📊 Complete Trading Volume Analysis")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Volume by Market (USD)")
    if not filtered_positions.empty:
        # ✅ FIXED: Calculate volume in USD properly
        market_vol = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum'
        }).sort_values('volume_usd', ascending=False)
        
        fig = px.bar(market_vol.reset_index(), x='market_id', y='volume_usd',
                     title='Trading Volume by Market (USD)',
                     labels={'volume_usd': 'Volume (USD)', 'market_id': 'Market'})
        fig.update_layout(height=350, xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')

with col2:
    st.subheader("Volume vs PnL by Market")
    if not filtered_positions.empty:
        market_stats = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum',
            'size': 'sum'
        }).sort_values('volume_usd', ascending=False).head(10)
        
        # Display as table with proper formatting
        display_stats = market_stats.copy()
        display_stats.columns = ['Volume (USD)', 'PnL ($)', 'Size (Units)']
        st.dataframe(display_stats.style.format({
            'Volume (USD)': '${:,.2f}',
            'PnL ($)': '${:,.2f}',
            'Size (Units)': '{:,.2f}'
        }), width='stretch')

# Charts Row 2
col1, col2 = st.columns(2)

with col1:
    st.subheader("⚖️ Long vs Short")
    if not filtered_positions.empty:
        long_cnt = len(filtered_positions[filtered_positions['side'].isin(['long', 'buy'])])
        short_cnt = len(filtered_positions[filtered_positions['side'].isin(['short', 'sell'])])
        fig = go.Figure(data=[go.Pie(labels=['Long', 'Short'], values=[long_cnt, short_cnt], hole=0.4, marker_colors=['#00cc96', '#ef553b'])])
        fig.update_layout(height=300)
        st.plotly_chart(fig, width='stretch')

with col2:
    st.subheader("🕐 Hourly Performance")
    if not filtered_positions.empty:
        hourly = filtered_positions.copy()
        hourly['hour'] = hourly['close_time'].dt.hour
        hour_pnl = hourly.groupby('hour')['realized_pnl'].mean().reset_index()
        fig = px.line(hour_pnl, x='hour', y='realized_pnl', markers=True)
        fig.update_layout(height=300, xaxis_title="Hour", yaxis_title="Avg PnL")
        st.plotly_chart(fig, width='stretch')

# Order Type Performance
st.header("📊 Order Type Performance")
if not data['order_perf'].empty:
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Win Rate', x=data['order_perf']['order_type'], y=data['order_perf']['win_rate']*100, yaxis='y', marker_color='lightblue'))
    fig.add_trace(go.Scatter(name='Avg PnL', x=data['order_perf']['order_type'], y=data['order_perf']['avg_pnl'], yaxis='y2', marker_color='green', line=dict(width=3)))
    fig.update_layout(xaxis_title="Order Type", yaxis_title="Win Rate (%)", yaxis2=dict(title="Avg PnL ($)", overlaying='y', side='right'), height=400)
    st.plotly_chart(fig, width='stretch')

# Greeks Exposure
if not data['greeks'].empty:
    st.header("🔬 Options Greeks Exposure")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Net Delta by Trader")
        fig = px.bar(data['greeks'], x='trader_id', y='net_delta', title="Delta Exposure")
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("Options Position Count")
        fig = px.bar(data['greeks'], x='trader_id', y='total_option_positions', title="Number of Options Positions")
        st.plotly_chart(fig, width='stretch')

# ✅ NEW: Open Positions with Unrealized PnL
st.header("📋 Open Positions (Unrealized PnL)")
st.info("⚠️ Note: This is a demo system with mock data. In production, open positions would be calculated from current market prices.")

# Create sample open positions (since all are closed in demo)
open_positions_sample = pd.DataFrame([
    {
        'position_id': 'OPEN-001',
        'trader_id': '7KNXqv...Bp9uV',
        'market_id': 'BTC-PERP',
        'product_type': 'perp',
        'side': 'long',
        'entry_price': 51000.00,
        'current_price': 52500.00,  # Mock current price
        'size': 0.5,
        'unrealized_pnl': (52500 - 51000) * 0.5,
        'open_time': datetime.now()
    },
    {
        'position_id': 'OPEN-002',
        'trader_id': '5FxM2n...fXyZ',
        'market_id': 'ETH/USDC',
        'product_type': 'spot',
        'side': 'buy',
        'entry_price': 2100.00,
        'current_price': 2150.00,
        'size': 10,
        'unrealized_pnl': (2150 - 2100) * 10,
        'open_time': datetime.now()
    }
])

st.dataframe(open_positions_sample.style.format({
    'entry_price': '${:,.2f}',
    'current_price': '${:,.2f}',
    'unrealized_pnl': '${:,.2f}',
    'size': '{:,.4f}'
}), width='stretch', hide_index=True)

st.caption("💡 In production: Unrealized PnL would be calculated using real-time market prices from the protocol")

# Trade History Table
st.header("📋 Closed Trade History")

if not filtered_positions.empty:
    # ✅ ADDED: Volume in USD column
    display_df = filtered_positions[[
        'position_id', 'trader_id', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'size', 'volume_usd', 'realized_pnl', 'fees',
        'open_time', 'close_time'
    ]].copy()
    
    # Format columns
    display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
    display_df['fees'] = display_df['fees'].apply(lambda x: f"${x:,.2f}")
    display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
    display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}")
    display_df['volume_usd'] = display_df['volume_usd'].apply(lambda x: f"${x:,.2f}")  # ✅ ADDED
    display_df['size'] = display_df['size'].apply(lambda x: f"{x:,.4f}")
    
    # Rename for display
    display_df = display_df.rename(columns={
        'position_id': 'Position ID',
        'trader_id': 'Trader',
        'market_id': 'Market',
        'product_type': 'Type',
        'side': 'Side',
        'entry_price': 'Entry',
        'exit_price': 'Exit',
        'size': 'Size',
        'volume_usd': 'Volume (USD)',  # ✅ ADDED
        'realized_pnl': 'PnL',
        'fees': 'Fees',
        'open_time': 'Opened',
        'close_time': 'Closed'
    })
    
    # Sort by close time descending
    display_df = display_df.sort_values('Closed', ascending=False)
    
    st.dataframe(display_df, width='stretch', height=400, hide_index=True)
    
    # Download button
    csv = filtered_positions.to_csv(index=False)
    st.download_button("📥 Download CSV", data=csv, file_name=f"trades_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
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
        st.write(f"Volume: ${best['volume_usd']:,.2f}")
        st.write("")
        st.write(f"**Worst Trade:** ${worst['realized_pnl']:,.2f}")
        st.write(f"Market: {worst['market_id']}")
        st.write(f"Volume: ${worst['volume_usd']:,.2f}")

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
    st.subheader("📈 Top Markets by Volume")
    if not filtered_positions.empty:
        market_vol = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum'
        }).sort_values('volume_usd', ascending=False)
        
        for market, row in market_vol.head(5).iterrows():
            market_short = market[:15] + "..." if len(market) > 18 else market
            st.write(f"**{market_short}**")
            st.write(f"Vol: ${row['volume_usd']:,.0f} | PnL: ${row['realized_pnl']:,.2f}")
            st.write("")

# Footer
st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Deriverse Analytics v2.0")