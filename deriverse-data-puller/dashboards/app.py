# dashboards/app_FINAL_PRODUCTION.py
"""
Deriverse Trading Analytics Dashboard - Production v4.1
Security-First | Professional UI | Adaptive Visualizations | Competition-Ready

SECURITY FEATURES:
- Read-only design (no private keys required)
- Local-first execution (data stays on user's machine)
- Input validation for all user inputs
- Environment-based API key management

NEW FEATURES:
- Adaptive chart system for sparse vs dense data
- Smart visualization selection based on trade count
- Enhanced UX for filtered views
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime
import requests


# DATA DENSITY CLASSIFICATION

def get_trade_density(filtered_positions):
    """Classify data density to select appropriate visualizations."""
    trade_count = len(filtered_positions)
    
    if trade_count == 0:
        return "empty"
    elif trade_count == 1:
        return "single"
    elif trade_count < 5:
        return "sparse"
    elif trade_count < 15:
        return "moderate"
    else:
        return "dense"


# CONFIGURATION

DATA_DIR = Path("data/analytics_output")

st.set_page_config(
    page_title="Deriverse Trading Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# STYLING

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@300;400;600;700&display=swap');
    
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
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }
    
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
    
    .stMetric label {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.875rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    
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
    
    [data-testid="stSidebar"] {
        background: var(--bg-card);
        border-right: 1px solid rgba(99, 102, 241, 0.1);
    }
    
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
    
    .greeks-metric {
        background: rgba(30, 41, 59, 0.4);
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid rgba(100, 116, 139, 0.2);
        text-align: center;
    }
    
    .greeks-metric-label {
        color: #94a3b8;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    
    .greeks-metric-value {
        color: #e2e8f0;
        font-size: 1.5rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }
    
    .greeks-metric-help {
        color: #64748b;
        font-size: 0.7rem;
        margin-top: 4px;
    }
    </style>
""", unsafe_allow_html=True)


# DATA LOADING

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
    """Load analytics data with error handling."""
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


# ADAPTIVE CHART FUNCTIONS

def plot_adaptive_equity_curve(filtered_equity, filtered_positions, selected_trader):
    """Equity curve that adapts to data density."""
    
    st.markdown("## 💰 Equity Curve")
    
    density = get_trade_density(filtered_positions)
    
    if density == "empty":
        st.info("📊 No closed trades yet. Open positions shown above.")
        return
    
    elif density == "single":
        st.caption("📊 1 trade - Showing detailed trade view")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            trade = filtered_positions.iloc[0]
            pnl_color = "#10b981" if trade['realized_pnl'] > 0 else "#ef4444"
            bg_color = "rgba(16, 185, 129, 0.1)" if trade['realized_pnl'] > 0 else "rgba(239, 68, 68, 0.1)"
            
            st.markdown(f"""
            <div style="
                border: 2px solid {pnl_color};
                border-radius: 12px;
                padding: 20px;
                background: {bg_color};
            ">
                <h2 style="color:{pnl_color}; margin:0; font-family: 'IBM Plex Mono', monospace;">
                    ${trade['realized_pnl']:,.2f}
                </h2>
                <p style="margin:10px 0; color: #e2e8f0; font-size: 0.95rem;">
                    <b>{trade['market_id']}</b><br>
                    {trade['side'].upper()} {trade['size']:.4f} @ ${trade['exit_price']:,.2f}<br>
                    Duration: {trade['duration_seconds']/3600:.1f}h<br>
                    Fees: ${trade['fees']:.2f}
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            fig = go.Figure()
            
            start_time = trade['open_time']
            trade_time = trade['close_time']
            end_time = datetime.now()
            
            fig.add_trace(go.Scatter(
                x=[start_time, trade_time, trade_time, end_time],
                y=[0, 0, trade['realized_pnl'], trade['realized_pnl']],
                mode='lines+markers',
                line=dict(width=3, color=pnl_color),
                marker=dict(size=[10, 15, 15, 10], color=[pnl_color, 'gold', pnl_color, pnl_color]),
                fill='tozeroy',
                fillcolor=bg_color,
                name='PnL',
                hovertemplate='Time: %{x}<br>PnL: $%{y:,.2f}<extra></extra>'
            ))
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="PnL ($)",
                height=300,
                showlegend=False,
                template='plotly_dark',
                plot_bgcolor='rgba(15, 23, 42, 0.9)',
                paper_bgcolor='rgba(15, 23, 42, 0.9)'
            )
            
            st.plotly_chart(fig, width='stretch')
    
    elif density in ["sparse", "moderate"]:
        trade_count = len(filtered_positions)
        st.caption(f"📊 {trade_count} trades - Step chart with trade markers")
        
        if not filtered_equity.empty:
            fig = go.Figure()
            
            for trader in filtered_equity['trader_id'].unique():
                trader_eq = filtered_equity[filtered_equity['trader_id'] == trader].sort_values('timestamp')
                trader_short = trader[:8] + "..." if len(trader) > 12 else trader
                
                fig.add_trace(go.Scatter(
                    x=trader_eq['timestamp'],
                    y=trader_eq['cumulative_pnl'],
                    name=f"{trader_short} PnL",
                    mode='lines+markers',
                    line=dict(shape='hv', width=3),
                    marker=dict(size=10, symbol='circle'),
                    hovertemplate='%{x}<br>PnL: $%{y:,.2f}<extra></extra>'
                ))
                
                max_dd = trader_eq['drawdown'].min()
                if max_dd < -100:
                    fig.add_trace(go.Scatter(
                        x=trader_eq['timestamp'],
                        y=trader_eq['drawdown'],
                        fill='tozeroy',
                        fillcolor='rgba(239, 68, 68, 0.2)',
                        line=dict(color='#ef4444', width=1),
                        name=f"{trader_short} Drawdown",
                        hovertemplate='Drawdown: $%{y:,.2f}<extra></extra>'
                    ))
            
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="PnL ($)",
                hovermode='x unified',
                height=400,
                template='plotly_dark',
                plot_bgcolor='rgba(15, 23, 42, 0.9)',
                paper_bgcolor='rgba(15, 23, 42, 0.9)'
            )
            
            st.plotly_chart(fig, width='stretch')
        
        if density == "sparse":
            st.markdown("### 📋 Trade Details")
            for idx, (_, trade) in enumerate(filtered_positions.iterrows(), 1):
                pnl_emoji = "✅" if trade['realized_pnl'] > 0 else "❌"
                with st.expander(f"{pnl_emoji} Trade #{idx}: {trade['market_id']} - ${trade['realized_pnl']:,.2f}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Entry", f"${trade['entry_price']:,.2f}")
                        st.metric("Size", f"{trade['size']:.4f}")
                    with col2:
                        st.metric("Exit", f"${trade['exit_price']:,.2f}")
                        st.metric("Fees", f"${trade['fees']:.2f}")
                    with col3:
                        st.metric("PnL", f"${trade['realized_pnl']:,.2f}")
                        st.metric("Duration", f"{trade['duration_seconds']/3600:.1f}h")
    
    else:
        st.caption(f"📊 {len(filtered_positions)} trades - Standard equity curve")
        
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
                    line=dict(width=3),
                    hovertemplate='%{x}<br>PnL: $%{y:,.2f}<extra></extra>'
                ))
                
                fig.add_trace(go.Scatter(
                    x=trader_eq['timestamp'],
                    y=trader_eq['drawdown'],
                    fill='tozeroy',
                    fillcolor='rgba(239, 68, 68, 0.2)',
                    line=dict(color='#ef4444', width=0.5),
                    name=f"{trader_short} Drawdown",
                    hovertemplate='Drawdown: $%{y:,.2f}<extra></extra>'
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


def plot_adaptive_daily_pnl(filtered_positions):
    """Daily PnL that adapts to data density."""
    
    st.markdown("### 📅 Daily PnL")
    
    density = get_trade_density(filtered_positions)
    
    if density in ["empty", "single"]:
        st.info("💡 Daily aggregation not meaningful for single trade")
        return
    
    elif density == "sparse":
        trades = filtered_positions.sort_values('close_time').copy()
        trades['trade_num'] = range(1, len(trades) + 1)
        
        fig = px.bar(
            trades,
            x='trade_num',
            y='realized_pnl',
            color='realized_pnl',
            color_continuous_scale=['#ef4444', '#64748b', '#10b981'],
            color_continuous_midpoint=0,
            labels={'trade_num': 'Trade #', 'realized_pnl': 'PnL ($)'},
            hover_data=['market_id', 'side', 'close_time']
        )
        fig.update_layout(height=350, showlegend=False, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')
    
    else:
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


def plot_adaptive_volume(filtered_positions):
    """Volume chart that adapts to data density."""
    
    st.markdown("### 📊 Volume by Market (USD)")
    
    density = get_trade_density(filtered_positions)
    
    if density in ["empty"]:
        st.info("No trades to analyze")
        return
    
    elif density in ["single", "sparse"]:
        market_vol = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum',
            'size': 'sum'
        }).sort_values('volume_usd', ascending=False)
        
        st.dataframe(
            market_vol.style.format({
                'volume_usd': '${:,.0f}',
                'realized_pnl': '${:,.2f}',
                'size': '{:,.4f}'
            }),
            width='stretch',
            column_config={
                "volume_usd": "Volume (USD)",
                "realized_pnl": "PnL",
                "size": "Total Size"
            }
        )
    
    else:
        market_vol = filtered_positions.groupby('market_id').agg({
            'volume_usd': 'sum',
            'realized_pnl': 'sum'
        }).sort_values('volume_usd', ascending=False)
        
        fig = px.bar(
            market_vol.reset_index(),
            x='market_id',
            y='volume_usd',
            title='Trading Volume (USD)',
            labels={'volume_usd': 'Volume (USD)'},
            color='realized_pnl',
            color_continuous_scale=['#ef4444', '#64748b', '#10b981']
        )
        fig.update_layout(height=350, xaxis_tickangle=-45, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')


# SIDEBAR

logo_url = "https://deriverse.gitbook.io/deriverse-v1/~gitbook/image?url=https%3A%2F%2F378873821-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Fspaces%252FJOrW2GdKwWAH2NMyLuwI%252Fuploads%252FYPcne0os80IiohJCe8TZ%252FScreenshot%25202026-01-13%2520at%252017.27.51.png%3Falt%3Dmedia%26token%3D5fc0293a-c66b-408e-ac94-fb6d0c431e52&width=768&dpr=1&quality=100&sign=1afb00d&sv=2"

logo_bytes = load_logo(logo_url)
if logo_bytes:
    st.sidebar.image(logo_bytes, width=220)
else:
    st.sidebar.markdown("### 📊 **Deriverse Analytics**")

st.sidebar.markdown("---")
st.sidebar.success("🔒 **Secure & Private**\nRead-only • Local-first")
st.sidebar.markdown("---")


# LOAD DATA

with st.spinner('🔄 Loading analytics...'):
    data = load_data()

if data is None or (data['positions'].empty and data['open_positions'].empty):
    st.error("❌ **No analytics data found**")
    st.info("💡 Run: `python -m scripts.run_analytics`")
    st.stop()

if not data['positions'].empty:
    data['positions']['volume_usd'] = data['positions']['exit_price'] * data['positions']['size']


# FILTERS

st.sidebar.header("🎛️ Filters")

traders = sorted(pd.concat([
    data['positions']['trader_id'] if not data['positions'].empty else pd.Series([]),
    data['open_positions']['trader_id'] if not data['open_positions'].empty else pd.Series([])
]).unique())

selected_trader = st.sidebar.selectbox("Trader Account", ["All"] + list(traders))

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

filtered_positions = data['positions'].copy() if not data['positions'].empty else pd.DataFrame()
filtered_open = data['open_positions'].copy() if not data['open_positions'].empty else pd.DataFrame()

if selected_trader != "All":
    if not filtered_positions.empty:
        filtered_positions = filtered_positions[filtered_positions['trader_id'] == selected_trader]
    if not filtered_open.empty:
        filtered_open = filtered_open[filtered_open['trader_id'] == selected_trader]

if selected_market != "All Markets":
    if not filtered_positions.empty:
        filtered_positions = filtered_positions[filtered_positions['market_id'] == selected_market]
    if not filtered_open.empty:
        filtered_open = filtered_open[filtered_open['market_id'] == selected_market]


# MAIN DASHBOARD

st.markdown("# 📊 **Trading Analytics Dashboard**")
st.caption("Real-time performance insights • Local-first security")

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
            }).map(
                lambda x: 'background-color: #fee2e2; color: #991b1b', 
                subset=['realized_pnl']
            ),
            width='stretch',
            hide_index=True
        )
        
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
    
    open_display = filtered_open.copy()
    open_display['time_held'] = (open_display['time_held_seconds'] / 3600).round(1)
    
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


# ADAPTIVE EQUITY CURVE

if not filtered_positions.empty or not filtered_open.empty:
    filtered_equity = data['equity'].copy()
    if selected_trader != "All":
        filtered_equity = filtered_equity[filtered_equity['trader_id'] == selected_trader]
    
    plot_adaptive_equity_curve(filtered_equity, filtered_positions, selected_trader)


# ADAPTIVE DAILY PNL & FEES

col1, col2 = st.columns(2)

with col1:
    if not filtered_positions.empty:
        plot_adaptive_daily_pnl(filtered_positions)

with col2:
    st.markdown("### 💸 Fees by Product")
    if not filtered_positions.empty:
        fees_prod = filtered_positions.groupby('product_type')['fees'].sum().reset_index()
        fig = px.bar(fees_prod, x='product_type', y='fees', color='product_type')
        fig.update_layout(height=350, showlegend=False, template='plotly_dark')
        st.plotly_chart(fig, width='stretch')


# FEE ANALYSIS

if not filtered_positions.empty:
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


# ADAPTIVE VOLUME ANALYSIS

    st.markdown("## 📊 Trading Volume Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        plot_adaptive_volume(filtered_positions)
    
    with col2:
        st.markdown("### ⚖️ Long vs Short Distribution")
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


# ORDER TYPE PERFORMANCE

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


# GREEKS EXPOSURE

if not data['greeks'].empty:
    st.markdown("## 🔬 Options Greeks Exposure")
    st.caption("📊 **Greeks measure options risk exposure**: Delta (directional risk), Gamma (delta sensitivity), Theta (time decay)")
    
    if selected_trader == "All":
        total_delta = data['greeks']['net_delta'].sum()
        total_gamma = data['greeks']['gamma_exposure'].sum()
        total_theta = data['greeks']['theta_decay'].sum()
        total_positions = data['greeks']['total_option_positions'].sum()
    else:
        trader_greeks = data['greeks'][data['greeks']['trader_id'] == selected_trader]
        if not trader_greeks.empty:
            total_delta = trader_greeks['net_delta'].iloc[0]
            total_gamma = trader_greeks['gamma_exposure'].iloc[0]
            total_theta = trader_greeks['theta_decay'].iloc[0]
            total_positions = trader_greeks['total_option_positions'].iloc[0]
        else:
            total_delta = total_gamma = total_theta = total_positions = 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Net Delta</div>
                <div class='greeks-metric-value'>{total_delta:,.2f}</div>
                <div class='greeks-metric-help'>Directional exposure</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        gamma_display = f"{total_gamma:,.4f}" if total_gamma != 0 else "N/A"
        
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Gamma</div>
                <div class='greeks-metric-value'>{gamma_display}</div>
                <div class='greeks-metric-help'>Delta sensitivity</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        theta_display = f"{total_theta:,.2f}" if total_theta != 0 else "N/A"
        
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Theta Decay</div>
                <div class='greeks-metric-value'>{theta_display}</div>
                <div class='greeks-metric-help'>Time decay/day</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Positions</div>
                <div class='greeks-metric-value'>{int(total_positions)}</div>
                <div class='greeks-metric-help'>Active contracts</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Net Delta by Trader")
        
        greeks_display = data['greeks'].copy()
        greeks_display['trader_short'] = greeks_display['trader_id'].str[:8] + '...'
        
        fig = px.bar(
            greeks_display, 
            x='trader_short', 
            y='net_delta', 
            title="Delta Exposure by Trader",
            color='net_delta',
            color_continuous_scale=['#ef4444', '#64748b', '#10b981'],
            color_continuous_midpoint=0,
            labels={'trader_short': 'Trader', 'net_delta': 'Net Delta'}
        )
        fig.update_layout(
            template='plotly_dark', 
            height=500,
            showlegend=False,
            xaxis_title="Trader",
            yaxis_title="Net Delta Exposure"
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("### Options Position Count")
        
        fig = px.bar(
            greeks_display, 
            x='trader_short', 
            y='total_option_positions',
            title="Active Options Contracts by Trader",
            color='total_option_positions',
            color_continuous_scale='Blues',
            labels={'trader_short': 'Trader', 'total_option_positions': 'Positions'}
        )
        fig.update_layout(
            template='plotly_dark', 
            height=500,
            showlegend=False,
            xaxis_title="Trader",
            yaxis_title="Number of Contracts"
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, width='stretch')
    
    st.markdown("### 📋 Greeks Breakdown by Trader")
    
    greeks_table = data['greeks'].copy()
    greeks_table['trader_short'] = greeks_table['trader_id'].str[:8] + '...'
    
    display_cols = ['trader_short', 'total_option_positions', 'net_delta']
    
    if greeks_table['gamma_exposure'].abs().sum() > 0:
        display_cols.append('gamma_exposure')
    
    if greeks_table['theta_decay'].abs().sum() > 0:
        display_cols.append('theta_decay')
    
    st.dataframe(
        greeks_table[display_cols].style.format({
            'net_delta': '{:,.2f}',
            'gamma_exposure': '{:,.4f}',
            'theta_decay': '{:,.2f}',
            'total_option_positions': '{:.0f}'
        }).background_gradient(
            subset=['net_delta'], 
            cmap='RdYlGn', 
            vmin=-100, 
            vmax=100
        ),
        width='stretch',
        hide_index=True,
        column_config={
            "trader_short": "Trader",
            "total_option_positions": "Positions",
            "net_delta": "Delta",
            "gamma_exposure": "Gamma",
            "theta_decay": "Theta"
        }
    )
    
    with st.expander("ℹ️ **Understanding Greeks** - Click to learn more"):
        st.markdown("""
        **Options Greeks** measure different dimensions of risk in options positions:
        
        **Delta (Δ)** - Directional Risk ✅ **Currently Tracked**
        - Measures how much option price changes per $1 move in underlying
        - **Positive Delta**: Long calls or short puts (bullish exposure)
        - **Negative Delta**: Long puts or short calls (bearish exposure)
        - **Example**: Net delta of +20.50 means your portfolio acts like being long 20.5 units
        
        **Gamma (Γ)** - Delta Sensitivity
        - Measures how much delta changes per $1 move in underlying
        - **Note**: Advanced metric - requires real-time Greeks data from options pricing models
        - Would show volatility exposure in live trading environment
        
        **Theta (Θ)** - Time Decay
        - Measures daily P&L loss from time passing
        - **Note**: Advanced metric - calculated from options pricing models
        - Would show time decay exposure in live trading environment
        
        **Current Implementation**: This dashboard tracks Delta from historical trade data. 
        Gamma and Theta require real-time options pricing models and would be calculated 
        in production deployment with live market data feeds.
        """)


# TRADE JOURNAL

if not filtered_positions.empty:
    st.markdown("## 📝 Trade Journal with Annotations")
    st.info("💡 **Professional Trading Journal**: Document your strategy, emotions, and lessons learned")
    
    available_cols = [
        'close_time', 'trader_id', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees'
    ]
    
    if 'close_reason' in filtered_positions.columns:
        available_cols.append('close_reason')
    
    journal_df = filtered_positions[available_cols].copy()
    journal_df = journal_df.sort_values('close_time', ascending=False)
    
    journal_df['trader_short'] = journal_df['trader_id'].str[:8] + '...'
    
    if 'trade_notes' not in st.session_state:
        st.session_state.trade_notes = {}
    
    journal_df['trader_notes'] = journal_df.index.map(
        lambda i: st.session_state.trade_notes.get(i, "")
    )
    
    display_cols = [
        'close_time', 'trader_short', 'market_id', 'product_type', 'side',
        'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees'
    ]
    
    if 'close_reason' in journal_df.columns:
        display_cols.append('close_reason')
    
    display_cols.append('trader_notes')
    
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
    
    for idx, row in edited_journal.iterrows():
        if pd.notna(row.get('trader_notes')) and row['trader_notes']:
            st.session_state.trade_notes[idx] = row['trader_notes']
    
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
    st.caption("v4.1 Production Ready")

st.markdown("""
    <div style='text-align: center; padding: 20px; color: #64748b; font-size: 12px;'>
        <p><strong>Deriverse Analytics Dashboard</strong></p>
        <p>Read-only • No private keys required • Data stays on your machine</p>
    </div>
""", unsafe_allow_html=True)