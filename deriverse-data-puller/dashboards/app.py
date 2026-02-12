# dashboards/app.py - PRODUCTION READY v3.0
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
    .stMetric { background: #f0f2f6; padding: 15px; border-radius: 8px; }
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
        open_pos = pd.read_csv(DATA_DIR / "open_positions.csv", parse_dates=["open_time"])  # ✅ NEW
        
        return {
            'equity': equity, 'positions': positions, 'summary': summary,
            'fees': fees, 'volume': volume, 'pnl_day': pnl_day,
            'pnl_hour': pnl_hour, 'directional': directional, 
            'order_perf': order_perf, 'greeks': greeks,
            'open_positions': open_pos  # ✅ NEW
        }
    except FileNotFoundError:
        st.error("Analytics files not found. Run: python -m scripts.run_analytics")
        return None

data = load_data()

if data is None or (data['positions'].empty and data['open_positions'].empty):
    st.warning("No trading data available.")
    st.stop()

# Calculate volume in USD
if not data['positions'].empty:
    data['positions']['volume_usd'] = data['positions']['exit_price'] * data['positions']['size']

# Sidebar Filters
st.sidebar.header("🎛️ Filters")
traders = sorted(pd.concat([
    data['positions']['trader_id'] if not data['positions'].empty else pd.Series([]),
    data['open_positions']['trader_id'] if not data['open_positions'].empty else pd.Series([])
]).unique())
selected_trader = st.sidebar.selectbox("Trader Account", ["All"] + list(traders))

# Filter Data
filtered_positions = data['positions'].copy() if not data['positions'].empty else pd.DataFrame()
filtered_open = data['open_positions'].copy() if not data['open_positions'].empty else pd.DataFrame()

if selected_trader != "All":
    if not filtered_positions.empty:
        filtered_positions = filtered_positions[filtered_positions['trader_id'] == selected_trader]
    if not filtered_open.empty:
        filtered_open = filtered_open[filtered_open['trader_id'] == selected_trader]

# KPI Tiles
st.header("📈 Performance Overview")
col1, col2, col3, col4 = st.columns(4)

total_pnl = filtered_positions['realized_pnl'].sum() if not filtered_positions.empty else 0
win_rate = (filtered_positions['realized_pnl'] > 0).mean() * 100 if not filtered_positions.empty else 0
total_fees = filtered_positions['fees'].sum() if not filtered_positions.empty else 0
trade_count = len(filtered_positions)

col1.metric("Net Realized PnL", f"${total_pnl:,.2f}", delta=f"{total_pnl:,.2f}" if total_pnl > 0 else None)
col2.metric("Win Rate", f"{win_rate:.1f}%")
col3.metric("Total Closed Trades", trade_count)
col4.metric("Fees Paid", f"${total_fees:,.2f}")

# Risk Management Metrics
st.header("⚖️ Risk Analysis")
c1, c2, c3, c4 = st.columns(4)

if not filtered_positions.empty:
    winning = filtered_positions[filtered_positions['realized_pnl'] > 0]
    losing = filtered_positions[filtered_positions['realized_pnl'] < 0]
    
    avg_win = winning['realized_pnl'].mean() if len(winning) > 0 else 0
    avg_loss = losing['realized_pnl'].mean() if len(losing) > 0 else 0
    
    if selected_trader != "All" and not data['summary'].empty:
        trader_data = data['summary'][data['summary']['trader_id'] == selected_trader]
        max_dd = trader_data['max_drawdown'].iloc[0] if not trader_data.empty else 0
        sharpe = trader_data['sharpe_ratio'].iloc[0] if not trader_data.empty else 0
    else:
        max_dd = data['summary']['max_drawdown'].min() if not data['summary'].empty else 0
        sharpe = data['summary']['sharpe_ratio'].mean() if not data['summary'].empty else 0
else:
    avg_win = avg_loss = max_dd = sharpe = 0

c1.metric("Average Win", f"${avg_win:,.2f}")
c2.metric("Average Loss", f"${avg_loss:,.2f}")
c3.metric("Max Drawdown", f"${max_dd:,.2f}")
c4.metric("Sharpe Ratio", f"{sharpe:.2f}")

# ✅ OPEN POSITIONS - REAL DATA, NO UNREALIZED PNL
if not filtered_open.empty:
    st.header("📊 Open Positions (Active Trades)")
    st.caption("💡 Current positions still held. Unrealized PnL calculated at closing.")
    
    # Prepare display
    open_display = filtered_open.copy()
    open_display['time_held'] = (open_display['time_held_seconds'] / 3600).round(1)
    
    # Format for display
    display_open = open_display[[
        'position_id', 'trader_id', 'market_id', 'product_type', 'side',
        'entry_price', 'size', 'fees_paid', 'open_time', 'time_held'
    ]].copy()
    
    display_open = display_open.rename(columns={
        'position_id': 'Position ID',
        'trader_id': 'Trader',
        'market_id': 'Market',
        'product_type': 'Type',
        'side': 'Direction',
        'entry_price': 'Entry Price',
        'size': 'Size',
        'fees_paid': 'Fees Paid',
        'open_time': 'Opened At',
        'time_held': 'Hours Held'
    })
    
    st.dataframe(
        display_open.style.format({
            'Entry Price': '${:,.2f}',
            'Fees Paid': '${:,.2f}',
            'Size': '{:,.4f}',
            'Hours Held': '{:,.1f}h'
        }),
        width='stretch',
        hide_index=True
    )

# Equity Curve
if not data['equity'].empty:
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
            fig.add_trace(go.Scatter(x=trader_eq['timestamp'], y=trader_eq['drawdown'], fill='tozeroy', 
                                    fillcolor='rgba(255,0,0,0.2)', line=dict(color='red', width=0.5), 
                                    name=f"{trader_short} DD"))
        fig.update_layout(xaxis_title="Time", yaxis_title="PnL ($)", hovermode='x unified', height=400)
        st.plotly_chart(fig, width='stretch')

# Charts Row 1
col1, col2 = st.columns(2)

with col1:
    st.subheader("📅 Daily PnL")
    if not filtered_positions.empty:
        daily = filtered_positions.groupby(filtered_positions['close_time'].dt.date)['realized_pnl'].sum().reset_index()
        daily.columns = ['date', 'pnl']
        fig = px.bar(daily, x='date', y='pnl', color='pnl', color_continuous_scale=['red', 'gray', 'green'], 
                    color_continuous_midpoint=0)
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, width='stretch')

with col2:
    st.subheader("💸 Fees by Product")
    if not filtered_positions.empty:
        fees_prod = filtered_positions.groupby('product_type')['fees'].sum().reset_index()
        fig = px.bar(fees_prod, x='product_type', y='fees', color='product_type')
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, width='stretch')

# Complete Fee Analysis
if not filtered_positions.empty:
    st.header("💸 Complete Fee Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Fee Composition")
        if not data['fees'].empty:
            trader_fees = data['fees'] if selected_trader == "All" else data['fees'][data['fees']['trader_id'] == selected_trader]
            fig = px.pie(trader_fees, values='total_fees', names='product_type', title='Fee Distribution')
            fig.update_layout(height=300)
            st.plotly_chart(fig, width='stretch')
        
        fee_summary = filtered_positions.groupby('product_type').agg({
            'fees': ['sum', 'mean', 'count']
        }).round(2)
        fee_summary.columns = ['Total Fees', 'Avg Fee', 'Trade Count']
        st.dataframe(fee_summary, width='stretch')
    
    with col2:
        st.subheader("Cumulative Fee Tracking")
        fee_timeline = filtered_positions.sort_values('close_time')[['close_time', 'fees']].copy()
        fee_timeline['cumulative_fees'] = fee_timeline['fees'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=fee_timeline['close_time'], y=fee_timeline['cumulative_fees'],
                                mode='lines+markers', name='Cumulative Fees', line=dict(color='red', width=2)))
        fig.update_layout(xaxis_title="Time", yaxis_title="Cumulative Fees ($)", height=300)
        st.plotly_chart(fig, width='stretch')

# Complete Volume Analysis
if not filtered_positions.empty:
    st.header("📊 Trading Volume Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Volume by Market (USD)")
        market_vol = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum'
        }).sort_values('volume_usd', ascending=False)
        
        fig = px.bar(market_vol.reset_index(), x='market_id', y='volume_usd',
                    title='Trading Volume (USD)', labels={'volume_usd': 'Volume (USD)'})
        fig.update_layout(height=350, xaxis_tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("Volume vs PnL")
        market_stats = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum',
            'size': 'sum'
        }).sort_values('volume_usd', ascending=False).head(10)
        
        display_stats = market_stats.copy()
        display_stats.columns = ['Volume (USD)', 'PnL ($)', 'Size (Units)']
        st.dataframe(display_stats.style.format({
            'Volume (USD)': '${:,.2f}',
            'PnL ($)': '${:,.2f}',
            'Size (Units)': '{:,.2f}'
        }), width='stretch')

# Charts Row 2
if not filtered_positions.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚖️ Long vs Short")
        long_cnt = len(filtered_positions[filtered_positions['side'].isin(['long', 'buy'])])
        short_cnt = len(filtered_positions[filtered_positions['side'].isin(['short', 'sell'])])
        fig = go.Figure(data=[go.Pie(labels=['Long', 'Short'], values=[long_cnt, short_cnt], 
                                     hole=0.4, marker_colors=['#00cc96', '#ef553b'])])
        fig.update_layout(height=300)
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("🕐 Hourly Performance")
        hourly = filtered_positions.copy()
        hourly['hour'] = hourly['close_time'].dt.hour
        hour_pnl = hourly.groupby('hour')['realized_pnl'].mean().reset_index()
        fig = px.line(hour_pnl, x='hour', y='realized_pnl', markers=True)
        fig.update_layout(height=300, xaxis_title="Hour", yaxis_title="Avg PnL")
        st.plotly_chart(fig, width='stretch')

# Order Type Performance
if not data['order_perf'].empty:
    st.header("📊 Order Type Performance")
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Win Rate', x=data['order_perf']['order_type'], 
                        y=data['order_perf']['win_rate']*100, yaxis='y', marker_color='lightblue'))
    fig.add_trace(go.Scatter(name='Avg PnL', x=data['order_perf']['order_type'], 
                            y=data['order_perf']['avg_pnl'], yaxis='y2', marker_color='green', 
                            line=dict(width=3)))
    fig.update_layout(xaxis_title="Order Type", yaxis_title="Win Rate (%)", 
                     yaxis2=dict(title="Avg PnL ($)", overlaying='y', side='right'), height=400)
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
        fig = px.bar(data['greeks'], x='trader_id', y='total_option_positions')
        st.plotly_chart(fig, width='stretch')

# ✅ TRADE JOURNAL WITH ANNOTATIONS
if not filtered_positions.empty:
    st.header("📝 Trade Journal with Annotations")
    st.caption("✏️ Document your trading decisions, lessons learned, and strategy insights")
    
    # Add explanatory info
    with st.expander("ℹ️ What are trade annotations? Click to learn more..."):
        st.markdown("""
        **Trade annotations** are your personal trading journal entries where you document:
        - 📊 **Market conditions** when you entered/exited
        - 🎯 **Why you took the trade** (setup, strategy, conviction level)
        - 🧠 **Emotional state** (FOMO, confident, fearful, disciplined)
        - ✅ **What went right** (good entries, proper risk management)
        - ❌ **What went wrong** (early exit, late entry, ignored signals)
        - 📚 **Lessons learned** for future trades
        
        **Example notes:**
        - "Entered too early before confirmation - wait for volume spike next time"
        - "Perfect setup: broke resistance on high volume, followed plan exactly"
        - "Emotional revenge trade after previous loss - took too much risk"
        - "News-driven: Fed announcement caused spike - set tighter stops for news events"
        
        These notes help you identify patterns, improve your strategy, and become a better trader.
        """)
    
    # Prepare journal
    available_cols = [
        'close_time', 'trader_id', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees'
    ]
    
    # Add close_reason if it exists
    if 'close_reason' in filtered_positions.columns:
        available_cols.append('close_reason')
    
    journal_df = filtered_positions[available_cols].copy()
    journal_df = journal_df.sort_values('close_time', ascending=False)
    
    # Shorten trader IDs for display
    journal_df['trader_short'] = journal_df['trader_id'].str[:8] + '...'
    
    # Initialize notes in session state
    if 'trade_notes' not in st.session_state:
        st.session_state.trade_notes = {}
    
    # Add notes column
    journal_df['trader_notes'] = journal_df.index.map(
        lambda i: st.session_state.trade_notes.get(i, "")
    )
    
    # Reorder columns for display
    display_cols = [
        'close_time', 'trader_short', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees'
    ]
    
    if 'close_reason' in journal_df.columns:
        display_cols.append('close_reason')
    
    display_cols.append('trader_notes')
    
    # ✅ EDITABLE DATA TABLE
    edited_journal = st.data_editor(
        journal_df[display_cols],
        column_config={
            "close_time": st.column_config.DatetimeColumn(
                "Closed At",
                format="DD/MM/YYYY HH:mm"
            ),
            "trader_short": st.column_config.TextColumn(
                "Trader",
                help="First 8 characters of wallet address",
                disabled=True
            ),
            "market_id": "Market",
            "product_type": "Type",
            "side": "Direction",
            "entry_price": st.column_config.NumberColumn(
                "Entry",
                format="$%.2f"
            ),
            "exit_price": st.column_config.NumberColumn(
                "Exit",
                format="$%.2f",
                help="None for exercised/expired options (PnL calculated from intrinsic value)"
            ),
            "volume_usd": st.column_config.NumberColumn(
                "Volume (USD)",
                format="$%.0f"
            ),
            "realized_pnl": st.column_config.NumberColumn(
                "PnL",
                format="$%.2f"
            ),
            "fees": st.column_config.NumberColumn(
                "Fees",
                format="$%.2f"
            ),
            "close_reason": st.column_config.TextColumn(
                "Close Type",
                help="How position was closed: close (normal), liquidation, exercise, expire"
            ),
            "trader_notes": st.column_config.TextColumn(
                "📝 Your Trading Notes",
                help="Document your analysis: strategy, emotions, lessons learned, improvements for next time",
                max_chars=500,
                width="large"
            )
        },
        width='stretch',
        hide_index=True,
        num_rows="fixed",
        disabled=[col for col in display_cols if col != 'trader_notes']
    )
    
    # Update session state with edited notes
    for idx, row in edited_journal.iterrows():
        if pd.notna(row.get('trader_notes')) and row['trader_notes']:
            st.session_state.trade_notes[idx] = row['trader_notes']
    
    # Export functionality
    st.markdown("---")
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        notes_count = len([n for n in st.session_state.trade_notes.values() if n])
        if notes_count > 0:
            st.success(f"✅ {notes_count} trade{'s' if notes_count != 1 else ''} annotated")
        else:
            st.info("💡 Click on the 'Your Trading Notes' column to add annotations")
    
    with col2:
        # Export with full trader IDs
        export_df = filtered_positions[available_cols].copy()
        export_df['trader_notes'] = export_df.index.map(
            lambda i: st.session_state.trade_notes.get(i, "")
        )
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            csv,
            "trading_journal_annotated.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col3:
        if st.button("🗑️ Clear Notes", use_container_width=True):
            if st.session_state.trade_notes:
                st.session_state.trade_notes = {}
                st.rerun()
    
    with col4:
        if st.button("📊 Stats", use_container_width=True):
            st.toast(f"Trades: {len(journal_df)} | Annotated: {notes_count}")

    # Download button
    csv = edited_journal.to_csv(index=False)
    st.download_button("📥 Download Annotated Journal", csv, "trading_journal_annotated.csv", "text/csv")

# Footer
st.markdown("---")
st.caption(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Deriverse Analytics v3.0 - Production Ready")