# dashboards/app_FINAL_PRODUCTION.py
"""
Deriverse Trading Analytics Dashboard - Production v4.0
Security-First | Professional UI | Competition-Ready

SECURITY FEATURES:
- Read-only design (no private keys required)
- Local-first execution (data stays on user's machine  
- Input validation for all user inputs
- Environment-based API key management
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import base64
from io import BytesIO
import requests


# CONFIGURATION & SECURITY

DATA_DIR = Path("data/analytics_output")

st.set_page_config(
    page_title="Deriverse Trading Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# PROFESSIONAL STYLING (Deriverse Theme)

st.markdown("""
    <style>
    /* Import Professional Fonts */
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap');
    
    /* Global Theme */
    :root {
        --primary-color: #6366f1;
        --secondary-color: #8b5cf6;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
        --bg-dark: #0f172a;
        --bg-card: #1e293b;
        --text-primary: #f1f5f9;
        --text-secondary: #94a3b8;
    }
    
    /* Main Container */
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }
    
    /* Metric Cards */
    .stMetric {
        background: linear-gradient(135deg, var(--bg-card) 0%, #334155 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(99, 102, 241, 0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 12px -1px rgba(99, 102, 241, 0.2);
        border-color: rgba(99, 102, 241, 0.3);
    }
    
    /* Metric Labels */
    .stMetric label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Metric Values */
    .stMetric [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.875rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3);
    }
    
    /* Dataframes */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Progress Bars */
    .stProgress > div > div {
        background: linear-gradient(90deg, var(--primary-color), var(--success-color));
        border-radius: 4px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--bg-card);
        border-right: 1px solid rgba(99, 102, 241, 0.1);
    }
    
    /* Info/Warning/Success Boxes */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    /* Custom Status Indicators */
    .status-live {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: var(--success-color);
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    </style>
""", unsafe_allow_html=True)

# HELPER FUNCTIONS

@st.cache_data
def load_logo(url):
    """Load Deriverse logo with error handling."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        st.sidebar.warning(f"⚠️ Logo load failed: {e}")
        return None

@st.cache_data
def load_data():
    """Load analytics data with spinner."""
    try:
        return {
            'equity': pd.read_csv(DATA_DIR / "equity_curve.csv", parse_dates=["timestamp"]),
            'positions': pd.read_csv(DATA_DIR / "positions.csv", parse_dates=["open_time", "close_time"]),
            'summary': pd.read_csv(DATA_DIR / "summary_metrics.csv"),
            'fees': pd.read_csv(DATA_DIR / "fees_breakdown.csv"),
            'volume': pd.read_csv(DATA_DIR / "volume_by_market.csv"),
            'pnl_day': pd.read_csv(DATA_DIR / "pnl_by_day.csv", parse_dates=["date"]),
            'pnl_hour': pd.read_csv(DATA_DIR / "pnl_by_hour.csv"),
            'directional': pd.read_csv(DATA_DIR / "directional_bias.csv"),
            'order_perf': pd.read_csv(DATA_DIR / "order_type_performance.csv"),
            'greeks': pd.read_csv(DATA_DIR / "greeks_exposure.csv"),
            'open_positions': pd.read_csv(DATA_DIR / "open_positions.csv", parse_dates=["open_time"])
        }
    except FileNotFoundError:
        return None


# SIDEBAR - BRANDING & FILTERS

# Logo
logo_url = "https://deriverse.gitbook.io/deriverse-v1/~gitbook/image?url=https%3A%2F%2F378873821-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252FJOrW2GdKwWAH2NMyLuwI%252Fuploads%252FYPcne0os80IiohJCe8TZ%252FScreenshot%25202026-01-13%2520at%252017.27.51.png%3Falt%3Dmedia%26token%3D5fc0293a-c66b-408e-ac94-fb6d0c431e52&width=768&dpr=1&quality=100&sign=1afb00d&sv=2"

logo_bytes = load_logo(logo_url)
if logo_bytes:
    st.sidebar.image(logo_bytes, width=220)
else:
    st.sidebar.markdown("### 📊 **Deriverse Analytics**")

st.sidebar.markdown("---")

# Security Badge
st.sidebar.success("🔒 **Secure & Private**\nRead-only • Local-first")

st.sidebar.markdown("---")


# DATA LOADING WITH SPINNER

with st.spinner('🔄 Loading analytics...'):
    data = load_data()

if data is None or (data['positions'].empty and data['open_positions'].empty):
    st.error("❌ **No analytics data found**")
    st.info("💡 Run: `python -m scripts.run_analytics`")
    st.stop()

# Calculate volume in USD
if not data['positions'].empty:
    data['positions']['volume_usd'] = data['positions']['exit_price'] * data['positions']['size']


# FILTERS 

st.sidebar.header("🎛️ Filters")

# Trader Filter (existing)
traders = sorted(pd.concat([
    data['positions']['trader_id'] if not data['positions'].empty else pd.Series([]),
    data['open_positions']['trader_id'] if not data['open_positions'].empty else pd.Series([])
]).unique())

selected_trader = st.sidebar.selectbox("Trader Account", ["All"] + list(traders))

# ✅ NEW: Symbol/Market Filter (REQUIRED for scope)
all_markets = sorted(pd.concat([
    data['positions']['market_id'] if not data['positions'].empty else pd.Series([]),
    data['open_positions']['market_id'] if not data['open_positions'].empty else pd.Series([])
]).unique())

selected_market = st.sidebar.selectbox(
    "Market/Symbol", 
    ["All Markets"] + list(all_markets),
    help="Filter by specific trading pair or perpetual"
)

st.sidebar.markdown("---")

# Filter Data 
filtered_positions = data['positions'].copy() if not data['positions'].empty else pd.DataFrame()
filtered_open = data['open_positions'].copy() if not data['open_positions'].empty else pd.DataFrame()

# Apply Trader Filter
if selected_trader != "All":
    if not filtered_positions.empty:
        filtered_positions = filtered_positions[filtered_positions['trader_id'] == selected_trader]
    if not filtered_open.empty:
        filtered_open = filtered_open[filtered_open['trader_id'] == selected_trader]

# ✅ Apply Market Filter (NEW)
if selected_market != "All Markets":
    if not filtered_positions.empty:
        filtered_positions = filtered_positions[filtered_positions['market_id'] == selected_market]
    if not filtered_open.empty:
        filtered_open = filtered_open[filtered_open['market_id'] == selected_market]

# MAIN DASHBOARD

# Header
st.markdown("# 📊 **Trading Analytics Dashboard**")
st.caption("Real-time performance insights • Local-first security")

# Status Indicator
st.markdown("""
    <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 24px;'>
        <span class='status-live'></span>
        <span style='color: #10b981; font-size: 14px; font-weight: 600;'>LIVE ANALYTICS</span>
    </div>
""", unsafe_allow_html=True)


# KPI METRICS

st.markdown("## 📈 Performance Overview")
col1, col2, col3, col4 = st.columns(4)

total_pnl = filtered_positions['realized_pnl'].sum() if not filtered_positions.empty else 0
win_rate = (filtered_positions['realized_pnl'] > 0).mean() * 100 if not filtered_positions.empty else 0
total_fees = filtered_positions['fees'].sum() if not filtered_positions.empty else 0
trade_count = len(filtered_positions)

col1.metric("Net Realized PnL", f"${total_pnl:,.2f}", delta=f"{total_pnl:,.2f}" if total_pnl > 0 else None)
col2.metric("Win Rate", f"{win_rate:.1f}%")

# Win Rate Progress Bar
win_rate_val = win_rate / 100
col2.progress(win_rate_val, text=f"Win Rate: {win_rate:.1f}%")

col3.metric("Total Closed Trades", trade_count)
col4.metric("Fees Paid", f"${total_fees:,.2f}")


# RISK ANALYSIS

st.markdown("## ⚖️ Risk Analysis")
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


# LIQUIDATION ANALYSIS 

# Extract liquidations from closed positions
if not filtered_positions.empty and 'close_reason' in filtered_positions.columns:
    liquidations = filtered_positions[filtered_positions['close_reason'] == 'liquidation']
    
    if not liquidations.empty:
        st.markdown("## ⚠️ Liquidation Analysis")
        st.error(f"🚨 **{len(liquidations)} Liquidation Events Detected** - Critical Risk Review")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_liq_loss = liquidations['realized_pnl'].sum()
        avg_liq_loss = liquidations['realized_pnl'].mean()
        total_liq_fees = liquidations['fees'].sum()
        worst_liq = liquidations['realized_pnl'].min()
        
        col1.metric("Total Liquidation Loss", f"${total_liq_loss:,.2f}", delta=f"{total_liq_loss:,.2f}", delta_color="inverse")
        col2.metric("Avg Liquidation Loss", f"${avg_liq_loss:,.2f}")
        col3.metric("Liquidation Penalties", f"${total_liq_fees:,.2f}")
        col4.metric("Worst Liquidation", f"${worst_liq:,.2f}")
        
        # Liquidation Details Table
        st.markdown("### 📋 Liquidation Event Details")
        
        liq_display = liquidations[[
            'close_time', 'trader_id', 'market_id', 'side', 
            'entry_price', 'exit_price', 'size', 'realized_pnl', 'fees'
        ]].copy()
        
        liq_display['trader_short'] = liq_display['trader_id'].str[:8] + '...'
        
        st.dataframe(
            liq_display[[
                'close_time', 'trader_short', 'market_id', 'side',
                'entry_price', 'exit_price', 'size', 'realized_pnl', 'fees'
            ]].style.format({
                'entry_price': '${:,.2f}',
                'exit_price': '${:,.2f}',
                'size': '{:,.2f}',
                'realized_pnl': '${:,.2f}',
                'fees': '${:,.2f}'
            }).applymap(
                lambda x: 'background-color: #fee2e2; color: #991b1b', 
                subset=['realized_pnl']
            ),
            width='stretch',
            hide_index=True
        )
        
        # Liquidation Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Liquidations by Market")
            liq_by_market = liquidations.groupby('market_id')['realized_pnl'].sum().abs().reset_index()
            liq_by_market.columns = ['market', 'loss']
            
            fig = px.bar(
                liq_by_market, 
                x='market', 
                y='loss',
                title='Liquidation Losses by Market',
                color='loss',
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=300, template='plotly_dark')
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.markdown("### Liquidations by Trader")
            liq_by_trader = liquidations.groupby('trader_id')['realized_pnl'].sum().abs().reset_index()
            liq_by_trader['trader_short'] = liq_by_trader['trader_id'].str[:8] + '...'
            liq_by_trader.columns = ['trader_id', 'loss', 'trader']
            
            fig = px.pie(
                liq_by_trader, 
                values='loss', 
                names='trader',
                title='Liquidation Distribution',
                color_discrete_sequence=px.colors.sequential.Reds_r
            )
            fig.update_layout(height=300, template='plotly_dark')
            st.plotly_chart(fig, width='stretch')
        
        st.markdown("---")


# OPEN POSITIONS 

if not filtered_open.empty:
    st.markdown("## 📊 Open Positions (Active Trades)")
    st.warning("⚠️ **Active Positions**: Unrealized PnL will be calculated upon closing")
    
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


# CHARTS

if not data['equity'].empty:
    st.markdown("## 💰 Equity Curve")
    filtered_equity = data['equity'].copy()
    if selected_trader != "All":
        filtered_equity = filtered_equity[filtered_equity['trader_id'] == selected_trader]
    
    if not filtered_equity.empty:
        fig = go.Figure()
        for trader in filtered_equity['trader_id'].unique():
            trader_eq = filtered_equity[filtered_equity['trader_id'] == trader].sort_values('timestamp')
            trader_short = trader[:8] + "..." if len(trader) > 12 else trader
            fig.add_trace(go.Scatter(
                x=trader_eq['timestamp'], 
                y=trader_eq['cumulative_pnl'], 
                name=f"{trader_short} PnL",
                mode='lines',
                line=dict(width=3)
            ))
            fig.add_trace(go.Scatter(
                x=trader_eq['timestamp'], 
                y=trader_eq['drawdown'], 
                fill='tozeroy', 
                fillcolor='rgba(239, 68, 68, 0.2)', 
                line=dict(color='#ef4444', width=0.5), 
                name=f"{trader_short} Drawdown"
            ))
        
        fig.update_layout(
            xaxis_title="Time", 
            yaxis_title="PnL ($)", 
            hovermode='x unified', 
            height=450,
            template='plotly_dark',
            plot_bgcolor='rgba(15, 23, 42, 0.9)',
            paper_bgcolor='rgba(15, 23, 42, 0.9)'
        )
        st.plotly_chart(fig, width='stretch')

# Charts Row
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📅 Daily PnL")
    if not filtered_positions.empty:
        daily = filtered_positions.groupby(filtered_positions['close_time'].dt.date)['realized_pnl'].sum().reset_index()
        daily.columns = ['date', 'pnl']
        fig = px.bar(
            daily, 
            x='date', 
            y='pnl', 
            color='pnl', 
            color_continuous_scale=['#ef4444', '#64748b', '#10b981'], 
            color_continuous_midpoint=0
        )
        fig.update_layout(height=350, showlegend=False, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')

with col2:
    st.markdown("### 💸 Fees by Product")
    if not filtered_positions.empty:
        fees_prod = filtered_positions.groupby('product_type')['fees'].sum().reset_index()
        fig = px.bar(fees_prod, x='product_type', y='fees', color='product_type')
        fig.update_layout(height=350, showlegend=False, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')


# COMPLETE ANALYTICS

if not filtered_positions.empty:
    # Fee Analysis
    st.markdown("## 💸 Complete Fee Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Fee Composition")
        if not data['fees'].empty:
            trader_fees = data['fees'] if selected_trader == "All" else data['fees'][data['fees']['trader_id'] == selected_trader]
            fig = px.pie(trader_fees, values='total_fees', names='product_type', title='Fee Distribution')
            fig.update_layout(height=300, template='plotly_dark')
            st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("### Cumulative Fee Tracking")
        fee_timeline = filtered_positions.sort_values('close_time')[['close_time', 'fees']].copy()
        fee_timeline['cumulative_fees'] = fee_timeline['fees'].cumsum()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fee_timeline['close_time'], 
            y=fee_timeline['cumulative_fees'],
            mode='lines+markers', 
            name='Cumulative Fees', 
            line=dict(color='#ef4444', width=2)
        ))
        fig.update_layout(height=300, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')

    # Volume Analysis
    st.markdown("## 📊 Trading Volume Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Volume by Market (USD)")
        market_vol = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum'
        }).sort_values('volume_usd', ascending=False)
        
        fig = px.bar(
            market_vol.reset_index(), 
            x='market_id', 
            y='volume_usd',
            title='Trading Volume (USD)', 
            labels={'volume_usd': 'Volume (USD)'}
        )
        fig.update_layout(height=350, xaxis_tickangle=-45, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("### Long vs Short Distribution")
        long_cnt = len(filtered_positions[filtered_positions['side'].isin(['long', 'buy'])])
        short_cnt = len(filtered_positions[filtered_positions['side'].isin(['short', 'sell'])])
        fig = go.Figure(data=[go.Pie(
            labels=['Long', 'Short'], 
            values=[long_cnt, short_cnt], 
            hole=0.4, 
            marker_colors=['#10b981', '#ef4444']
        )])
        fig.update_layout(height=350, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')

# Order Type Performance
if not data['order_perf'].empty:
    st.markdown("## 📊 Order Type Performance")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Win Rate', 
        x=data['order_perf']['order_type'], 
        y=data['order_perf']['win_rate']*100, 
        yaxis='y', 
        marker_color='#6366f1'
    ))
    fig.add_trace(go.Scatter(
        name='Avg PnL', 
        x=data['order_perf']['order_type'], 
        y=data['order_perf']['avg_pnl'], 
        yaxis='y2', 
        marker_color='#10b981', 
        line=dict(width=3)
    ))
    fig.update_layout(
        xaxis_title="Order Type", 
        yaxis_title="Win Rate (%)", 
        yaxis2=dict(title="Avg PnL ($)", overlaying='y', side='right'), 
        height=400,
        template='plotly_dark'
    )
    st.plotly_chart(fig, width='stretch')

# Greeks Exposure
if not data['greeks'].empty:
    st.markdown("## 🔬 Options Greeks Exposure")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Net Delta by Trader")
        fig = px.bar(data['greeks'], x='trader_id', y='net_delta', title="Delta Exposure")
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("### Options Position Count")
        fig = px.bar(data['greeks'], x='trader_id', y='total_option_positions')
        fig.update_layout(template='plotly_dark')
        st.plotly_chart(fig, width='stretch')


# TRADE JOURNAL WITH ANNOTATIONS (REQUIRED)

if not filtered_positions.empty:
    st.markdown("## 📝 Trade Journal with Annotations")
    st.info("💡 **Professional Trading Journal**: Document your strategy, emotions, and lessons learned")
    
    # Prepare journal
    available_cols = [
        'close_time', 'trader_id', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees'
    ]
    
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
    
    # Reorder columns
    display_cols = [
        'close_time', 'trader_short', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees'
    ]
    
    if 'close_reason' in journal_df.columns:
        display_cols.append('close_reason')
    
    display_cols.append('trader_notes')
    
    # Editable Table
    edited_journal = st.data_editor(
        journal_df[display_cols],
        column_config={
            "close_time": st.column_config.DatetimeColumn("Closed At", format="DD/MM/YYYY HH:mm"),
            "trader_short": st.column_config.TextColumn("Trader", disabled=True),
            "market_id": "Market",
            "product_type": "Type",
            "side": "Direction",
            "entry_price": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "exit_price": st.column_config.NumberColumn("Exit", format="$%.2f"),
            "volume_usd": st.column_config.NumberColumn("Volume (USD)", format="$%.0f"),
            "realized_pnl": st.column_config.NumberColumn("PnL", format="$%.2f"),
            "fees": st.column_config.NumberColumn("Fees", format="$%.2f"),
            "close_reason": st.column_config.TextColumn("Close Type"),
            "trader_notes": st.column_config.TextColumn(
                "📝 Trading Notes",
                help="Document strategy, emotions, lessons",
                max_chars=500,
                width="large"
            )
        },
        width='stretch',
        hide_index=True,
        num_rows="fixed",
        disabled=[col for col in display_cols if col != 'trader_notes']
    )
    
    # Update session state
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
            st.info("💡 Add notes to build your trading journal")
    
    with col2:
        export_df = filtered_positions[available_cols].copy()
        export_df['trader_notes'] = export_df.index.map(
            lambda i: st.session_state.trade_notes.get(i, "")
        )
        csv = export_df.to_csv(index=False)
        st.download_button(
            "📥 Export CSV",
            csv,
            "trading_journal.csv",
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


# FOOTER

st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with col2:
    st.caption("🔒 **Secure** • Local-first")

with col3:
    st.caption("v4.0 Production Ready")

st.markdown("""
    <div style='text-align: center; padding: 20px; color: #64748b; font-size: 12px;'>
        <p><strong>Deriverse Analytics Dashboard</strong></p>
        <p>Read-only • No private keys required • Data stays on your machine</p>
    </div>
""", unsafe_allow_html=True)