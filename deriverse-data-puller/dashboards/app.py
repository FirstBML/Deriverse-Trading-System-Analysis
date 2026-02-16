# dashboards/app.py
"""
Deriverse Trading Analytics Dashboard - Enhanced v6.0
Features:
- Privacy-aware trader masking
- Authenticated profile mode
- Adaptive visualizations across all sections
- Enhanced filtering (date range, symbols)
- Top performers analysis with charts
- Persistent trade notes (JSON storage)
- Admin controls for full data access
- Navigation bar for section jumping
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime, timedelta
import requests
import json
import hmac
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

DATA_DIR = Path("data/analytics_output")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ADMIN_PASSWORD")  

st.set_page_config(
    page_title="Deriverse Trading Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_admin_password():
    """Verify admin password for all-time access."""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        with st.sidebar.expander("🔐 Admin Access"):
            password = st.text_input("Password", type="password")
            if st.button("Authenticate"):
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.success("✅ Admin access granted")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
    
    return st.session_state.admin_authenticated


def mask_trader_id(trader_id):
    """Format trader wallet address for privacy."""
    if pd.isna(trader_id):
        return "Unknown"
    s = str(trader_id)
    return f"{s[:4]}..{s[-4:]}" if len(s) > 8 else s


def simplify_symbol(market_id):
    """Extract base symbol from market identifier."""
    if pd.isna(market_id):
        return market_id
    s = str(market_id)
    return s.split('/')[0].split('-')[0]


def get_top_traders(positions_df, n=5, by='profit'):
    """Get top N traders by specified criteria."""
    if positions_df.empty:
        return []
    
    trader_stats = positions_df.groupby('trader_id')['realized_pnl'].agg(['sum', 'count'])
    
    if by == 'profit':
        return trader_stats.nlargest(n, 'sum').index.tolist()
    elif by == 'loss':
        return trader_stats.nsmallest(n, 'sum').index.tolist()
    else:
        return trader_stats.nlargest(n, 'count').index.tolist()


def load_trader_notes(trader_id):
    """Load trade notes from JSON file for specific trader."""
    notes_dir = Path("data/trader_notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    notes_file = notes_dir / f"{trader_id}.json"
    
    if notes_file.exists():
        with open(notes_file, 'r') as f:
            return json.load(f)
    return {}


def save_trader_notes(trader_id, notes):
    """Save trade notes to JSON file for specific trader."""
    notes_dir = Path("data/trader_notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    
    notes_file = notes_dir / f"{trader_id}.json"
    
    with open(notes_file, 'w') as f:
        json.dump(notes, f, indent=2)


def get_trade_density(filtered_positions):
    """Classify data density for adaptive visualization selection."""
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


def calculate_volume_usd(df):
    """Calculate USD volume from price and size."""
    df = df.copy()
    df['volume_usd'] = df['exit_price'] * df['size']
    return df


# ============================================================================
# STYLING & CSS
# ============================================================================

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
    
    .fixed-header-container {
        position: sticky;
        top: 0;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        z-index: 1000;
        padding: 15px 20px 10px 20px;
        border-bottom: 2px solid rgba(99, 102, 241, 0.3);
        margin-bottom: 20px;
        width: 100%;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .header-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        color: #f1f5f9;
        margin: 0;
        padding: 0;
        letter-spacing: -0.02em;
    }
    
    .header-subtitle {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-top: 4px;
    }
    
    .nav-bar {
        display: flex;
        gap: 8px;
        margin-top: 15px;
        flex-wrap: wrap;
    }
    
    .nav-item {
        padding: 8px 16px;
        border-radius: 8px;
        background: rgba(30, 41, 59, 0.6);
        color: #94a3b8;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        border: 1px solid rgba(99, 102, 241, 0.1);
        text-align: center;
        flex: 1;
        min-width: 80px;
    }
    
    .nav-item:hover {
        background: rgba(99, 102, 241, 0.2);
        color: #f1f5f9;
        border-color: #6366f1;
        transform: translateY(-2px);
    }
    
    .nav-item-active {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.3);
    }
    
    .nav-item-active:hover {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        color: white;
    }
    
    .profile-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        margin: 10px 0 5px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .section-header {
        position: sticky;
        top: 180px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        z-index: 998;
        padding: 10px 0;
        border-bottom: 1px solid rgba(99, 102, 241, 0.1);
        margin-bottom: 15px;
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
    
    .progress-bar-container {
        background: rgba(30, 41, 59, 0.4);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
    }
    
    .progress-bar-label {
        color: #94a3b8;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 6px;
    }
    
    .progress-bar-value {
        color: #f1f5f9;
        font-size: 1rem;
        font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
    }
    
    .coming-soon {
        background: rgba(245, 158, 11, 0.1);
        border: 1px dashed #f59e0b;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        color: #f59e0b;
        font-weight: 600;
    }
    
    .note-instruction {
        background: rgba(99, 102, 241, 0.1);
        border-left: 4px solid var(--primary-color);
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        color: #e2e8f0;
        font-size: 0.95rem;
    }
    
    .note-instruction code {
        background: #1e293b;
        padding: 4px 8px;
        border-radius: 4px;
        color: var(--primary-color);
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_logo(url):
    """Load Deriverse logo with error handling."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
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
    except FileNotFoundError as e:
        st.error(f"❌ Data files not found: {e}")
        return None


# ============================================================================
# ADAPTIVE CHART FUNCTIONS
# ============================================================================

def create_clean_equity_chart(equity_df, positions_df, authenticated_trader=None):
    """Create clean equity chart with PnL on top, drawdown below."""
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("📈 Cumulative PnL by Trader", "📉 Drawdown Analysis"),
        vertical_spacing=0.12,
        row_heights=[0.7, 0.3]
    )
    
    colors = px.colors.qualitative.Set2
    
    traders_to_show = equity_df['trader_id'].unique()
    if not authenticated_trader and len(traders_to_show) > 5:
        top_traders = get_top_traders(positions_df, n=5, by='activity')
        equity_df = equity_df[equity_df['trader_id'].isin(top_traders)]
        traders_to_show = equity_df['trader_id'].unique()
    
    for i, trader in enumerate(traders_to_show):
        trader_data = equity_df[equity_df['trader_id'] == trader].sort_values('timestamp')
        
        if authenticated_trader and trader == authenticated_trader:
            display_name = f"{trader[:8]}...{trader[-8:]}"
        else:
            display_name = mask_trader_id(trader)
        
        fig.add_trace(
            go.Scatter(
                x=trader_data['timestamp'],
                y=trader_data['cumulative_pnl'],
                name=display_name,
                line=dict(width=2, color=colors[i % len(colors)]),
                legendgroup=f"trader_{i}",
                hovertemplate="<b>%{fullData.name}</b><br>" +
                            "Date: %{x}<br>" +
                            "PnL: $%{y:,.2f}<br>" +
                            "<extra></extra>"
            ),
            row=1, col=1
        )
    
    for i, trader in enumerate(traders_to_show):
        trader_data = equity_df[equity_df['trader_id'] == trader].sort_values('timestamp')
        
        fig.add_trace(
            go.Scatter(
                x=trader_data['timestamp'],
                y=trader_data['drawdown'],
                name=f"DD",
                line=dict(width=1.5, dash='dot', color=colors[i % len(colors)]),
                legendgroup=f"trader_{i}",
                showlegend=False,
                hovertemplate="<b>Drawdown</b><br>" +
                            "Date: %{x}<br>" +
                            "Drawdown: $%{y:,.2f}<br>" +
                            "<extra></extra>"
            ),
            row=2, col=1
        )
    
    all_drawdowns = equity_df['drawdown'].min()
    fig.add_hline(
        y=all_drawdowns, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Max System Drawdown: ${all_drawdowns:,.0f}",
        annotation_position="bottom right",
        row=2, col=1
    )
    
    fig.update_layout(
        height=600,
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(15, 23, 42, 0.9)',
        paper_bgcolor='rgba(15, 23, 42, 0.9)',
        legend=dict(
            title="Traders",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_xaxes(title_text="", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Cumulative PnL ($)", row=1, col=1)
    fig.update_yaxes(title_text="Drawdown ($)", row=2, col=1)
    
    return fig


def create_trader_focus_chart(equity_df, positions_df, trader_id):
    """Create detailed view for a single trader."""
    
    trader_equity = equity_df[equity_df['trader_id'] == trader_id].sort_values('timestamp')
    trader_positions = positions_df[positions_df['trader_id'] == trader_id]
    
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=(
            f"Cumulative PnL - {mask_trader_id(trader_id)}",
            "Daily Returns",
            "Drawdown from Peak"
        ),
        vertical_spacing=0.1,
        row_heights=[0.5, 0.25, 0.25]
    )
    
    fig.add_trace(
        go.Scatter(
            x=trader_equity['timestamp'],
            y=trader_equity['cumulative_pnl'],
            name="Equity",
            line=dict(color='#6366f1', width=3),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)'
        ),
        row=1, col=1
    )
    
    wins = trader_positions[trader_positions['realized_pnl'] > 0]
    if not wins.empty:
        fig.add_trace(
            go.Scatter(
                x=wins['close_time'],
                y=[trader_equity[trader_equity['timestamp'] == t]['cumulative_pnl'].iloc[0] 
                   if any(trader_equity['timestamp'] == t) else None 
                   for t in wins['close_time']],
                mode='markers',
                name='Wins',
                marker=dict(color='#10b981', size=8, symbol='triangle-up')
            ),
            row=1, col=1
        )
    
    losses = trader_positions[trader_positions['realized_pnl'] < 0]
    if not losses.empty:
        fig.add_trace(
            go.Scatter(
                x=losses['close_time'],
                y=[trader_equity[trader_equity['timestamp'] == t]['cumulative_pnl'].iloc[0] 
                   if any(trader_equity['timestamp'] == t) else None 
                   for t in losses['close_time']],
                mode='markers',
                name='Losses',
                marker=dict(color='#ef4444', size=8, symbol='triangle-down')
            ),
            row=1, col=1
        )
    
    daily = trader_positions.groupby(
        trader_positions['close_time'].dt.date
    )['realized_pnl'].sum().reset_index()
    
    colors = ['#10b981' if x > 0 else '#ef4444' for x in daily['realized_pnl']]
    
    fig.add_trace(
        go.Bar(
            x=daily['close_time'],
            y=daily['realized_pnl'],
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=trader_equity['timestamp'],
            y=trader_equity['drawdown'],
            name='Drawdown',
            line=dict(color='#ef4444', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)'
        ),
        row=3, col=1
    )
    
    max_dd = trader_equity['drawdown'].min()
    fig.add_hline(
        y=max_dd,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"Max DD: ${max_dd:,.0f}",
        row=3, col=1
    )
    
    fig.update_layout(
        height=800,
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(15, 23, 42, 0.9)',
        paper_bgcolor='rgba(15, 23, 42, 0.9)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig


def create_trader_summary_table(equity_df, positions_df):
    """Create summary table with mini sparklines."""
    
    st.markdown("### 📋 Trader Performance Summary")
    
    traders = []
    for trader in equity_df['trader_id'].unique()[:10]:
        trader_equity = equity_df[equity_df['trader_id'] == trader].sort_values('timestamp')
        trader_positions = positions_df[positions_df['trader_id'] == trader]
        
        total_pnl = trader_positions['realized_pnl'].sum()
        win_rate = (trader_positions['realized_pnl'] > 0).mean() * 100
        max_dd = trader_equity['drawdown'].min()
        trades = len(trader_positions)
        
        sparkline = trader_equity['cumulative_pnl'].values
        if len(sparkline) > 1:
            normalized = (sparkline - sparkline.min()) / (sparkline.max() - sparkline.min() + 1)
        else:
            normalized = [0.5]
        
        traders.append({
            'trader': mask_trader_id(trader),
            'pnl': total_pnl,
            'win_rate': win_rate,
            'max_dd': max_dd,
            'trades': trades,
            'sparkline': normalized[-20:],
            'trend': '📈' if total_pnl > 0 and len(sparkline) > 1 and sparkline[-1] > sparkline[0] else '📉'
        })
    
    traders.sort(key=lambda x: x['pnl'], reverse=True)
    
    cols = st.columns([1.2, 1.5, 1, 1, 1, 2])
    cols[0].markdown("**Trader**")
    cols[1].markdown("**Equity Trend**")
    cols[2].markdown("**PnL**")
    cols[3].markdown("**Win Rate**")
    cols[4].markdown("**Max DD**")
    cols[5].markdown("**Activity**")
    
    st.divider()
    
    for i, t in enumerate(traders):
        cols = st.columns([1.2, 1.5, 1, 1, 1, 2])
        
        cols[0].markdown(f"`{t['trader']}`")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=t['sparkline'],
            mode='lines',
            line=dict(color='#10b981' if t['pnl'] > 0 else '#ef4444', width=2),
            showlegend=False
        ))
        fig.update_layout(
            height=40,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False, showgrid=False),
            yaxis=dict(showticklabels=False, showgrid=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        cols[1].plotly_chart(
            fig, 
            width='stretch',
            config={'displayModeBar': False},
            key=f"sparkline_{i}"
        )
        
        pnl_color = "#10b981" if t['pnl'] > 0 else "#ef4444"
        cols[2].markdown(f"<span style='color:{pnl_color};font-weight:600;'>${t['pnl']:,.0f}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"{t['win_rate']:.0f}%")
        cols[4].markdown(f"${abs(t['max_dd']):,.0f}")
        cols[5].markdown(f"{t['trades']} trades {t['trend']}")


def display_equity_section(equity_df, positions_df, authenticated_trader=None):
    """Complete equity analysis section with tabs."""
    
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("📈 Performance Analysis")
    st.markdown('</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs([
        "📊 Overview Comparison", 
        "👤 Individual Analysis", 
        "📋 Summary Table"
    ])
    
    with tab1:
        st.subheader("Multi-Trader Performance")
        st.caption("Top panel: Cumulative PnL | Bottom panel: Drawdown")
        
        fig = create_clean_equity_chart(equity_df, positions_df, authenticated_trader)
        st.plotly_chart(fig, width='stretch')
        
        col1, col2 = st.columns(2)
        with col1:
            if not equity_df.empty:
                best_trader = equity_df.groupby('trader_id')['cumulative_pnl'].last().idxmax()
                best_pnl = equity_df.groupby('trader_id')['cumulative_pnl'].last().max()
                st.info(f"🏆 **Best Performer:** {mask_trader_id(best_trader)} (${best_pnl:,.2f})")
        
        with col2:
            if not equity_df.empty:
                worst_dd_trader = equity_df.groupby('trader_id')['drawdown'].min().idxmin()
                worst_dd = equity_df.groupby('trader_id')['drawdown'].min().min()
                st.warning(f"⚠️ **Highest Risk:** {mask_trader_id(worst_dd_trader)} (Max DD: ${worst_dd:,.2f})")
    
    with tab2:
        if authenticated_trader:
            fig = create_trader_focus_chart(equity_df, positions_df, authenticated_trader)
            st.plotly_chart(fig, width='stretch')
        else:
            traders = equity_df['trader_id'].unique()
            selected = st.selectbox(
                "Select Trader to Analyze",
                traders,
                format_func=mask_trader_id
            )
            if selected:
                fig = create_trader_focus_chart(equity_df, positions_df, selected)
                st.plotly_chart(fig, width='stretch')
    
    with tab3:
        create_trader_summary_table(equity_df, positions_df)


def display_liquidation_analytics(positions_df):
    """Complete liquidation analysis with risk dashboard."""
    
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("⚠️ Liquidation Risk Monitoring")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if 'close_reason' not in positions_df.columns:
        st.info("ℹ️ Liquidation tracking not available for this data")
        return
    
    liquidations = positions_df[positions_df['close_reason'] == 'liquidation'].copy()
    
    if liquidations.empty:
        st.success("✅ No liquidations in selected period - clean trading!")
        return
    
    col1, col2, col3 = st.columns(3)
    
    total_liq = len(liquidations)
    unique_traders = liquidations['trader_id'].nunique()
    total_liq_loss = liquidations['realized_pnl'].sum()
    
    with col1:
        st.metric("Total Liquidations", total_liq)
    with col2:
        st.metric("Affected Traders", unique_traders)
    with col3:
        st.metric("Total Loss", f"${abs(total_liq_loss):,.0f}")
    
    st.subheader("📊 Liquidation Rate by Trader")
    st.caption("Shows % of trades that ended in liquidation - lower is better")
    
    trader_stats = []
    for trader in positions_df['trader_id'].unique():
        trader_trades = positions_df[positions_df['trader_id'] == trader]
        trader_liq = len(trader_trades[trader_trades['close_reason'] == 'liquidation'])
        total_closed = len(trader_trades[trader_trades['close_reason'].isin(['closed', 'liquidation'])])
        
        if total_closed > 0:
            liq_rate = (trader_liq / total_closed) * 100
            trader_stats.append({
                'trader': mask_trader_id(trader),
                'liq_rate': liq_rate,
                'liq_count': trader_liq,
                'total_trades': total_closed
            })
    
    if trader_stats:
        df = pd.DataFrame(trader_stats).sort_values('liq_rate', ascending=False)
        
        colors = ['#10b981' if x < 2 else '#f59e0b' if x < 5 else '#ef4444' 
                  for x in df['liq_rate']]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df['trader'],
            y=df['liq_rate'],
            marker_color=colors,
            text=[f"{rate:.1f}%<br>({liq}/{total})" 
                  for rate, liq, total in zip(df['liq_rate'], df['liq_count'], df['total_trades'])],
            textposition='outside'
        ))
        
        fig.add_hline(y=2, line_dash="dash", line_color="#10b981", 
                      annotation_text="Low Risk", annotation_position="bottom right")
        fig.add_hline(y=5, line_dash="dash", line_color="#f59e0b",
                      annotation_text="Medium Risk", annotation_position="bottom right")
        
        fig.update_layout(
            height=400,
            xaxis_title="Trader",
            yaxis_title="Liquidation Rate (%)",
            template='plotly_dark',
            plot_bgcolor='rgba(15, 23, 42, 0.9)',
            paper_bgcolor='rgba(15, 23, 42, 0.9)'
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, width='stretch', key="liquidation_rate_chart")
    
    st.subheader("💰 Financial Impact Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        liq_by_market = liquidations.groupby('market_id')['realized_pnl'].sum().abs().reset_index()
        liq_by_market['symbol'] = liq_by_market['market_id'].apply(simplify_symbol)
        liq_by_market = liq_by_market.sort_values('realized_pnl', ascending=False).head(5)
        
        fig = px.bar(
            liq_by_market,
            x='symbol',
            y='realized_pnl',
            title='Top 5 Markets by Liquidation Loss',
            color='realized_pnl',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=300, template='plotly_dark')
        st.plotly_chart(fig, width='stretch', key="liquidation_by_market")
    
    with col2:
        liq_by_trader = liquidations.groupby('trader_id')['realized_pnl'].sum().abs().reset_index()
        liq_by_trader['trader'] = liq_by_trader['trader_id'].apply(mask_trader_id)
        liq_by_trader = liq_by_trader.sort_values('realized_pnl', ascending=False).head(5)
        
        fig = px.bar(
            liq_by_trader,
            x='trader',
            y='realized_pnl',
            title='Top 5 Traders by Liquidation Loss',
            color='realized_pnl',
            color_continuous_scale='Reds'
        )
        fig.update_layout(height=300, template='plotly_dark')
        st.plotly_chart(fig, width='stretch', key="liquidation_by_trader")
    
    with st.expander("🔍 Pattern Analysis"):
        
        col1, col2 = st.columns(2)
        
        with col1:
            liquidations['hour'] = pd.to_datetime(liquidations['close_time']).dt.hour
            liq_by_hour = liquidations.groupby('hour').size().reset_index(name='count')
            
            fig = px.line(
                liq_by_hour,
                x='hour',
                y='count',
                title='Liquidations by Hour of Day',
                markers=True
            )
            fig.update_layout(height=300, template='plotly_dark')
            st.plotly_chart(fig, width='stretch', key="liquidation_by_hour")
        
        with col2:
            top_market = liquidations['market_id'].mode()
            if not top_market.empty:
                st.info(f"🔥 **Riskiest Market:** {simplify_symbol(top_market.iloc[0])}")
            
            liq_hours = pd.to_datetime(liquidations['close_time']).dt.hour
            top_hour = liq_hours.mode()
            if not top_hour.empty:
                st.info(f"⏰ **Riskiest Hour:** {top_hour.iloc[0]}:00 UTC")
            
            avg_loss = liquidations['realized_pnl'].mean()
            st.metric("Average Loss per Liquidation", f"${abs(avg_loss):,.2f}")
            
            with st.expander("📋 Liquidation History"):
                liq_display = liquidations[['close_time', 'trader_id', 'market_id', 'side', 
                                           'size', 'exit_price', 'realized_pnl', 'fees']].copy()
                liq_display['trader'] = liq_display['trader_id'].apply(mask_trader_id)
                liq_display['symbol'] = liq_display['market_id'].apply(simplify_symbol)
                liq_display = liq_display.sort_values('close_time', ascending=False)
                
                st.dataframe(
                    liq_display[['close_time', 'trader', 'symbol', 'side', 
                                'size', 'exit_price', 'realized_pnl', 'fees']].style.format({
                        'close_time': lambda x: x.strftime('%Y-%m-%d %H:%M'),
                        'size': '{:.4f}',
                        'exit_price': '${:.2f}',
                        'realized_pnl': '${:.2f}',
                        'fees': '${:.2f}'
                    }).map(
                        lambda x: 'color: #ef4444; font-weight: bold',
                        subset=['realized_pnl']
                    ),
                    width='stretch',
                    hide_index=True,
                    column_config={
                        "close_time": "Time",
                        "trader": "Trader",
                        "symbol": "Symbol",
                        "side": "Side",
                        "size": "Size",
                        "exit_price": "Price",
                        "realized_pnl": "Loss",
                        "fees": "Fees"
                    }
                )


def display_order_type_performance(order_perf_df, positions_df):
    """Order type chart with proper classification."""
    
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("📊 Order Type Performance")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if positions_df.empty:
        st.info("No trade data available")
        return
    
    df = positions_df.copy()
    
    if 'order_type' in df.columns and not df['order_type'].isna().all():
        order_types = df['order_type'].value_counts()
        st.caption(f"📊 Based on {len(order_types)} order types from trade data")
    else:
        df['order_type'] = df.apply(lambda row: 
            f"{row['product_type']}" if row['product_type'] in ['option'] else
            f"{row['product_type']}_market" if row['duration_seconds'] < 300 else
            f"{row['product_type']}_limit" if row['duration_seconds'] < 3600 else
            f"{row['product_type']}_stop",
            axis=1
        )
        st.caption("📊 Order types derived from product type and duration")
    
    result = []
    for order_type, group in df.groupby('order_type'):
        trade_count = len(group)
        if trade_count > 0:
            result.append({
                'order_type': order_type,
                'trade_count': trade_count,
                'avg_pnl': group['realized_pnl'].mean(),
                'win_rate': (group['realized_pnl'] > 0).mean(),
                'total_pnl': group['realized_pnl'].sum()
            })
    
    if not result:
        st.warning("Insufficient data for order type analysis")
        return
    
    order_df = pd.DataFrame(result)
    order_df = order_df.sort_values('trade_count', ascending=False)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Bar(
            x=order_df['order_type'],
            y=order_df['win_rate'] * 100,
            name='Win Rate',
            marker_color='#6366f1',
            text=[f"{w:.1f}%" for w in order_df['win_rate'] * 100],
            textposition='inside',
            textfont=dict(color='white'),
            hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>',
            customdata=order_df['trade_count']
        ),
        secondary_y=False,
    )
    
    colors = ['#10b981' if x > 0 else '#ef4444' for x in order_df['avg_pnl']]
    
    fig.add_trace(
        go.Scatter(
            x=order_df['order_type'],
            y=order_df['avg_pnl'],
            name='Avg PnL',
            mode='lines+markers',
            line=dict(color='#f1f5f9', width=3),
            marker=dict(size=10, color=colors),
            text=[f"${x:,.0f}" for x in order_df['avg_pnl']],
            textposition='top center',
            hovertemplate='<b>%{x}</b><br>Avg PnL: $%{y:,.2f}<extra></extra>'
        ),
        secondary_y=True,
    )
    
    fig.update_layout(
        title="Order Type Performance: Win Rate vs Average PnL",
        xaxis_title="Order Type",
        hovermode='x unified',
        height=500,
        template='plotly_dark',
        plot_bgcolor='rgba(15, 23, 42, 0.9)',
        paper_bgcolor='rgba(15, 23, 42, 0.9)',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig.update_yaxes(title_text="Win Rate (%)", secondary_y=False, range=[0, 100])
    fig.update_yaxes(title_text="Average PnL ($)", secondary_y=True)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=True)
    
    st.plotly_chart(fig, width='stretch')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_win = order_df.loc[order_df['win_rate'].idxmax()]
        st.metric(
            "🏆 Best Win Rate",
            f"{best_win['win_rate']*100:.1f}%",
            f"{best_win['order_type']}"
        )
    
    with col2:
        best_pnl = order_df.loc[order_df['avg_pnl'].idxmax()]
        st.metric(
            "💰 Best Avg PnL",
            f"${best_pnl['avg_pnl']:,.2f}",
            f"{best_pnl['order_type']}"
        )
    
    with col3:
        most_used = order_df.loc[order_df['trade_count'].idxmax()]
        st.metric(
            "📊 Most Used",
            f"{most_used['trade_count']} trades",
            f"{most_used['order_type']}"
        )


def display_volume_analysis(positions_df):
    """Volume analysis with product tabs and progress bars."""
    
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("📊 Trading Volume Analysis")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if positions_df.empty:
        st.info("No volume data available")
        return
    
    positions_df = calculate_volume_usd(positions_df)
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_volume = positions_df['volume_usd'].sum()
    total_fees = positions_df['fees'].sum()
    unique_symbols = positions_df['market_id'].apply(simplify_symbol).nunique()
    
    symbol_vol = positions_df.groupby(positions_df['market_id'].apply(simplify_symbol))['volume_usd'].sum()
    vol_shares = symbol_vol / total_volume if total_volume > 0 else pd.Series([0])
    hhi = (vol_shares ** 2).sum() * 10000
    
    with col1:
        st.metric("Total Volume", f"${total_volume:,.0f}")
    with col2:
        st.metric("Total Fees", f"${total_fees:,.0f}")
    with col3:
        st.metric("Active Symbols", unique_symbols)
    with col4:
        concentration = "Low" if hhi < 1500 else "Medium" if hhi < 2500 else "High"
        st.metric("Concentration", f"{hhi:.0f} ({concentration})")
    
    product_tabs = st.tabs(["📈 All Products", "📍 Spot", "⚡ Perpetual", "🎯 Options"])
    
    products = {
        "📈 All Products": positions_df,
        "📍 Spot": positions_df[positions_df['product_type'] == 'spot'],
        "⚡ Perpetual": positions_df[positions_df['product_type'] == 'perp'],
        "🎯 Options": positions_df[positions_df['product_type'] == 'option']
    }
    
    for tab_idx, (tab, (tab_name, product_df)) in enumerate(zip(product_tabs, products.items())):
        with tab:
            if product_df.empty:
                st.info(f"No {tab_name} trades in selected period")
                continue
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"#### Volume by Symbol - Top 5")
                
                symbol_vol = product_df.groupby(product_df['market_id'].apply(simplify_symbol)).agg({
                    'volume_usd': 'sum',
                    'realized_pnl': 'sum',
                    'fees': 'sum'
                }).sort_values('volume_usd', ascending=False).head(5)
                
                total = symbol_vol['volume_usd'].sum()
                
                for symbol, row in symbol_vol.iterrows():
                    pct = (row['volume_usd'] / total * 100) if total > 0 else 0
                    pnl_color = "#10b981" if row['realized_pnl'] > 0 else "#ef4444"
                    
                    st.markdown(f"""
                    <div class='progress-bar-container'>
                        <div style='display: flex; justify-content: space-between; margin-bottom: 6px;'>
                            <span class='progress-bar-label'>{symbol}</span>
                            <span class='progress-bar-value'>
                                ${row['volume_usd']:,.0f} ({pct:.1f}%) 
                                <span style='color:{pnl_color};'>${row['realized_pnl']:,.0f}</span>
                            </span>
                        </div>
                        <div style='background: rgba(100, 116, 139, 0.3); border-radius: 4px; height: 8px;'>
                            <div style='
                                background: #6366f1;
                                width: {pct}%;
                                height: 100%;
                                border-radius: 4px;
                                transition: width 0.3s ease;
                            '></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("#### Fee Generation")
                fee_by_symbol = product_df.groupby(product_df['market_id'].apply(simplify_symbol))['fees'].sum().sort_values(ascending=False).head(5)
                
                fig = px.bar(
                    x=fee_by_symbol.values,
                    y=fee_by_symbol.index,
                    orientation='h',
                    title='Top 5 Symbols by Fees',
                    color=fee_by_symbol.values,
                    color_continuous_scale='Reds'
                )
                fig.update_layout(height=250, template='plotly_dark')
                st.plotly_chart(fig, width='stretch', key=f"fee_chart_{tab_idx}")
            
            with col2:
                st.markdown(f"#### Long vs Short Distribution")
                
                if tab_name == "🎯 Options" and 'option_type' in product_df.columns:
                    calls = product_df[product_df['option_type'] == 'call']['volume_usd'].sum()
                    puts = product_df[product_df['option_type'] == 'put']['volume_usd'].sum()
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=['Calls', 'Puts'],
                        values=[calls, puts],
                        hole=0.4,
                        marker_colors=['#10b981', '#f59e0b']
                    )])
                    fig.update_layout(height=300, template='plotly_dark')
                    st.plotly_chart(fig, width='stretch', key=f"options_pie_{tab_idx}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        avg_premium = product_df['exit_price'].mean()
                        st.metric("Avg Premium", f"${avg_premium:,.2f}")
                    with col2:
                        total_options = len(product_df)
                        st.metric("Option Trades", total_options)
                
                else:
                    long_vol = product_df[product_df['side'].isin(['long', 'buy'])]['volume_usd'].sum()
                    short_vol = product_df[product_df['side'].isin(['short', 'sell'])]['volume_usd'].sum()
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=['Long', 'Short'],
                        values=[long_vol, short_vol],
                        hole=0.4,
                        marker_colors=['#10b981', '#ef4444']
                    )])
                    fig.update_layout(height=300, template='plotly_dark')
                    st.plotly_chart(fig, width='stretch', key=f"long_short_pie_{tab_idx}")
                    
                    ratio = (long_vol / short_vol) if short_vol > 0 else float('inf')
                    st.metric("Long/Short Ratio", f"{ratio:.2f}x")
                
                st.markdown("#### Average Trade Size")
                avg_size = product_df['volume_usd'].mean()
                median_size = product_df['volume_usd'].median()
                
                fig = go.Figure()
                fig.add_trace(go.Box(
                    y=product_df['volume_usd'],
                    name='Trade Size Distribution',
                    boxmean='sd',
                    marker_color='#6366f1'
                ))
                fig.update_layout(height=200, template='plotly_dark', showlegend=False)
                st.plotly_chart(fig, width='stretch', key=f"box_chart_{tab_idx}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Average", f"${avg_size:,.0f}")
                with col2:
                    st.metric("Median", f"${median_size:,.0f}")


def display_greeks_analysis(greeks_df):
    """Greeks analysis with 'Available Soon' for missing metrics."""
    
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("🔬 Options Greeks Exposure")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if greeks_df.empty:
        st.info("No options Greeks data available")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_delta = greeks_df['net_delta'].sum()
    delta_color = "#10b981" if total_delta > 0 else "#ef4444"
    
    with col1:
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Net Delta</div>
                <div class='greeks-metric-value' style='color: {delta_color}'>{total_delta:,.2f}</div>
                <div class='greeks-metric-help'>Directional exposure</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Gamma</div>
                <div class='greeks-metric-value'>🔜 Available Soon</div>
                <div class='greeks-metric-help'>Delta sensitivity</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Theta</div>
                <div class='greeks-metric-value'>🔜 Available Soon</div>
                <div class='greeks-metric-help'>Time decay/day</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col4:
        total_positions = greeks_df['total_option_positions'].sum()
        st.markdown(f"""
            <div class='greeks-metric'>
                <div class='greeks-metric-label'>Positions</div>
                <div class='greeks-metric-value'>{int(total_positions)}</div>
                <div class='greeks-metric-help'>Active contracts</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.subheader("📊 Delta Exposure by Trader")
    
    display_df = greeks_df.copy()
    display_df['trader'] = display_df['trader_id'].apply(mask_trader_id)
    display_df = display_df.sort_values('net_delta', ascending=False)
    
    fig = px.bar(
        display_df,
        x='trader',
        y='net_delta',
        color='net_delta',
        color_continuous_scale='RdBu',
        color_continuous_midpoint=0,
        title='Net Delta by Trader'
    )
    fig.update_layout(
        height=400,
        template='plotly_dark',
        plot_bgcolor='rgba(15, 23, 42, 0.9)',
        paper_bgcolor='rgba(15, 23, 42, 0.9)'
    )
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, width='stretch')
    
    st.subheader("📋 Greeks Breakdown")
    
    st.dataframe(
        display_df[['trader', 'total_option_positions', 'net_delta']].style.format({
            'net_delta': '{:,.2f}',
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
            "trader": "Trader",
            "total_option_positions": "Positions",
            "net_delta": "Delta"
        }
    )


# ============================================================================
# DATA LOADING
# ============================================================================

with st.spinner('🔄 Loading analytics...'):
    data = load_data()

if data is None or (data['positions'].empty and data['open_positions'].empty):
    st.error("❌ **No analytics data found**")
    st.info("💡 Run: `python -m scripts.run_analytics`")
    st.stop()

# ============================================================================
# SIDEBAR
# ============================================================================

logo_url = "https://deriverse.gitbook.io/deriverse-v1/~gitbook/image?url=https%3A%2F%2F3705106568-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com%2Fo%2Forganizations%252FVbKUpgicSXo9QHWM7uzI%252Fsites%252Fsite_oPxtF%252Ficon%252FNsfAUtLJH778Cn5Dd7zK%252Ffavicon.ico%3Falt%3Dmedia%26token%3D4099bf73-ccd6-4d9f-8bbb-01cdc664ddb0&width=32&dpr=3&quality=100&sign=13d31bb2&sv=2"

logo_bytes = load_logo(logo_url)
if logo_bytes:
    st.sidebar.image(logo_bytes, width=220)
else:
    st.sidebar.markdown("### 🔷 **Deriverse Analytics**")

st.sidebar.markdown("---")
st.sidebar.success("🔒 **Secure & Private**\nRead-only • Local-first")
st.sidebar.markdown("---")

st.sidebar.header("🔐 Access Control")
is_admin = check_admin_password()

st.sidebar.header("👤 Trader Access")

all_traders = sorted(pd.concat([
    data['positions']['trader_id'] if not data['positions'].empty else pd.Series([]),
    data['open_positions']['trader_id'] if not data['open_positions'].empty else pd.Series([])
]).unique())

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "all_traders"

if st.session_state.view_mode == "all_traders":
    st.sidebar.info("🌐 **Mode:** All Traders View")
    
    wallet_input = st.sidebar.text_input(
        "Enter Your Wallet Address",
        placeholder="7KNXqvHu2QWvDq8cGPGvKZhFvYnz...",
        help="Enter your wallet to access personal dashboard"
    )
    
    if st.sidebar.button("🔑 Enter Personal Dashboard"):
        if wallet_input and len(wallet_input) > 32:
            if wallet_input in all_traders:
                st.session_state.authenticated_trader = wallet_input
                st.session_state.view_mode = "personal"
                st.rerun()
            else:
                st.sidebar.error("❌ Wallet not found in trading data")
        else:
            st.sidebar.warning("⚠️ Please enter a valid wallet address")

else:
    if "authenticated_trader" in st.session_state:
        trader = st.session_state.authenticated_trader
        st.sidebar.success(f"✅ **Personal Mode:** {mask_trader_id(trader)}")
        
        if st.sidebar.button("👥 Return to All Traders View"):
            st.session_state.view_mode = "all_traders"
            st.rerun()

st.sidebar.markdown("---")

st.sidebar.header("🎛️ Filters")
st.sidebar.markdown("**📅 Date Range**")

if is_admin:
    date_option = st.sidebar.radio(
        "Range (Admin)",
        ["Last 7 Days", "Last 30 Days", "All Time", "Custom"],
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )
else:
    date_option = st.sidebar.radio(
        "Range",
        ["Last 7 Days", "Last 30 Days", "Custom (Admin Only)"],
        index=1,
        horizontal=True,
        label_visibility="collapsed"
    )
    
    if date_option == "Custom (Admin Only)":
        st.sidebar.warning("🔐 Custom date range requires admin authentication")
        date_option = "Last 30 Days"

if data and not data['positions'].empty:
    min_date = data['positions']['close_time'].min().date()
    max_date = data['positions']['close_time'].max().date()
    
    if date_option == "Last 7 Days":
        start_date = max_date - timedelta(days=7)
        end_date = max_date
    elif date_option == "Last 30 Days":
        start_date = max_date - timedelta(days=30)
        end_date = max_date
    elif date_option == "Custom" or date_option == "Custom (Admin Only)":
        if is_admin:
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date = st.date_input("From", min_date, min_value=min_date, max_value=max_date)
            with col2:
                end_date = st.date_input("To", max_date, min_value=min_date, max_value=max_date)
        else:
            start_date = max_date - timedelta(days=30)
            end_date = max_date
    else:
        start_date = min_date
        end_date = max_date

if data and not data['positions'].empty:
    all_markets = sorted(data['positions']['market_id'].unique())
    symbol_map = {m: simplify_symbol(m) for m in all_markets}
    unique_symbols = sorted(set(symbol_map.values()))
    
    selected_symbols = st.sidebar.multiselect(
        "Symbols",
        unique_symbols,
        default=[],
        help="Select symbols to analyze (empty = all symbols)"
    )
    
    if selected_symbols:
        selected_markets = [m for m in all_markets if simplify_symbol(m) in selected_symbols]
    else:
        selected_markets = []
else:
    selected_markets = []

st.sidebar.markdown("---")


# ============================================================================
# FIXED HEADER & NAVIGATION - NEVER SCROLLS
# ============================================================================

if "nav" not in st.session_state:
    st.session_state.nav = "overview"

with st.container():
    st.markdown('<div class="fixed-header-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 8])
    
    with col1:
        if logo_bytes:
            st.image(logo_bytes, width=60)
        else:
            st.markdown("### 🔷")
    
    with col2:
        st.markdown('<div class="header-title">Deriverse Trading Analytics</div>', unsafe_allow_html=True)
        st.markdown('<div class="header-subtitle">Real-time performance insights • Local-first security</div>', unsafe_allow_html=True)
    
    if st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state:
        st.markdown(f"""
            <div class='profile-badge'>
                🔐 {mask_trader_id(st.session_state.authenticated_trader)}
            </div>
        """, unsafe_allow_html=True)
    
    nav_items = [
        ("📊 Overview", "overview"),
        ("📈 Performance", "performance"),
        ("⚠️ Risk", "risk"),
        ("📊 Volume", "volume"),
        ("📋 Orders", "orders"),
        ("🔬 Greeks", "greeks"),
        ("📝 Journal", "journal")
    ]
    
    nav_cols = st.columns(len(nav_items))
    
    for idx, (col, (label, nav_key)) in enumerate(zip(nav_cols, nav_items)):
        with col:
            is_active = (st.session_state.nav == nav_key)
            if st.button(
                label,
                key=f"nav_{nav_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.nav = nav_key
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)


# ============================================================================
# APPLY FILTERS
# ============================================================================

filtered_positions = data['positions'].copy() if not data['positions'].empty else pd.DataFrame()
filtered_open = data['open_positions'].copy() if not data['open_positions'].empty else pd.DataFrame()

if st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state:
    selected_trader = st.session_state.authenticated_trader
    if not filtered_positions.empty:
        filtered_positions = filtered_positions[filtered_positions['trader_id'] == selected_trader]
    if not filtered_open.empty:
        filtered_open = filtered_open[filtered_open['trader_id'] == selected_trader]
else:
    selected_trader = None

if not filtered_positions.empty:
    filtered_positions = filtered_positions[
        (filtered_positions['close_time'].dt.date >= start_date) &
        (filtered_positions['close_time'].dt.date <= end_date)
    ]

if selected_markets and not filtered_positions.empty:
    filtered_positions = filtered_positions[filtered_positions['market_id'].isin(selected_markets)]
if selected_markets and not filtered_open.empty:
    filtered_open = filtered_open[filtered_open['market_id'].isin(selected_markets)]

if not filtered_positions.empty:
    filtered_positions = calculate_volume_usd(filtered_positions)

if not data['equity'].empty:
    filtered_equity = data['equity'].copy()
    if selected_trader:
        filtered_equity = filtered_equity[filtered_equity['trader_id'] == selected_trader]
    filtered_equity = filtered_equity[
        (filtered_equity['timestamp'].dt.date >= start_date) &
        (filtered_equity['timestamp'].dt.date <= end_date)
    ]
else:
    filtered_equity = pd.DataFrame()


# ============================================================================
# OPEN POSITIONS TABLE
# ============================================================================

if not filtered_open.empty:
    st.warning(f"⚠️ **{len(filtered_open)} Open Positions** - Unrealized PnL not included")
    
    open_display = filtered_open.copy()
    
    if 'time_held_seconds' in open_display.columns:
        open_display['time_held'] = (open_display['time_held_seconds'] / 3600).round(1)
    elif 'open_time' in open_display.columns:
        open_display['time_held'] = ((pd.Timestamp.now() - pd.to_datetime(open_display['open_time'])).dt.total_seconds() / 3600).round(1)
    else:
        open_display['time_held'] = 0
    
    open_display['trader_display'] = open_display['trader_id'].apply(
        lambda x: f"{x[:8]}...{x[-8:]}" if selected_trader and x == selected_trader else mask_trader_id(x)
    )
    open_display['symbol'] = open_display['market_id'].apply(simplify_symbol)
    
    display_cols = ['trader_display', 'symbol', 'product_type', 'side', 'entry_price', 'size']
    
    if 'fees_paid' in open_display.columns:
        display_cols.append('fees_paid')
    elif 'fees' in open_display.columns:
        open_display['fees_paid'] = open_display['fees']
        display_cols.append('fees_paid')
    
    display_cols.append('time_held')
    
    st.dataframe(
        open_display[display_cols].rename(columns={
            'trader_display': 'Trader',
            'symbol': 'Symbol',
            'product_type': 'Type',
            'side': 'Direction',
            'entry_price': 'Entry Price',
            'size': 'Size',
            'fees_paid': 'Fees Paid',
            'time_held': 'Hours Held'
        }).style.format({
            'Entry Price': '${:,.2f}',
            'Fees Paid': '${:,.2f}',
            'Size': '{:,.4f}',
            'Hours Held': '{:.1f}h'
        }),
        width='stretch',
        hide_index=True
    )


# ============================================================================
# SECTION RENDERING BASED ON NAVIGATION
# ============================================================================

if st.session_state.nav == "overview":
    
    st.markdown("## 📈 Performance Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_pnl = filtered_positions['realized_pnl'].sum() if not filtered_positions.empty else 0
    win_rate = (filtered_positions['realized_pnl'] > 0).mean() * 100 if not filtered_positions.empty else 0
    total_fees = filtered_positions['fees'].sum() if not filtered_positions.empty else 0
    trade_count = len(filtered_positions)
    
    col1.metric("Net Realized PnL", f"${total_pnl:,.2f}", delta=f"{total_pnl:,.2f}" if total_pnl != 0 else None)
    col2.metric("Win Rate", f"{win_rate:.1f}%")
    
    win_rate_val = win_rate / 100 if win_rate > 0 else 0
    col2.progress(win_rate_val, text=f"{win_rate_val*100:.1f}%")
    
    col3.metric("Total Closed Trades", trade_count)
    col4.metric("Fees Paid", f"${total_fees:,.2f}")
    
    st.markdown("## ⚖️ Risk Analysis")
    col1, col2, col3, col4 = st.columns(4)
    
    if not filtered_positions.empty:
        winning = filtered_positions[filtered_positions['realized_pnl'] > 0]
        losing = filtered_positions[filtered_positions['realized_pnl'] < 0]
        
        avg_win = winning['realized_pnl'].mean() if len(winning) > 0 else 0
        avg_loss = losing['realized_pnl'].mean() if len(losing) > 0 else 0
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        
        if selected_trader and not data['summary'].empty:
            trader_data = data['summary'][data['summary']['trader_id'] == selected_trader]
            max_dd = trader_data['max_drawdown'].iloc[0] if not trader_data.empty else 0
            sharpe = trader_data['sharpe_ratio'].iloc[0] if not trader_data.empty else 0
        else:
            max_dd = data['summary']['max_drawdown'].min() if not data['summary'].empty else 0
            sharpe = data['summary']['sharpe_ratio'].mean() if not data['summary'].empty else 0
    else:
        avg_win = avg_loss = max_dd = sharpe = profit_factor = 0
    
    col1.metric("Average Win", f"${avg_win:,.2f}")
    col2.metric("Average Loss", f"${avg_loss:,.2f}")
    col3.metric("Profit Factor", f"{profit_factor:.2f}x")
    col4.metric("Sharpe Ratio", f"{sharpe:.2f}")
    
    if not filtered_positions.empty and not selected_trader:
        st.markdown("## 🏆 Top Performers Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Top 5 Profitable Traders")
            top_winners = get_top_traders(filtered_positions, n=5, by='profit')
            
            if top_winners:
                winner_stats = []
                for trader in top_winners:
                    trader_pos = filtered_positions[filtered_positions['trader_id'] == trader]
                    winner_stats.append({
                        'Trader': mask_trader_id(trader),
                        'Total PnL': trader_pos['realized_pnl'].sum(),
                        'Trades': len(trader_pos),
                        'Win Rate': (trader_pos['realized_pnl'] > 0).mean() * 100
                    })
                
                winner_df = pd.DataFrame(winner_stats)
                
                fig = px.bar(
                    winner_df,
                    x='Trader',
                    y='Total PnL',
                    color='Total PnL',
                    color_continuous_scale='Greens',
                    text='Total PnL'
                )
                fig.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
                fig.update_layout(height=200, showlegend=False, template='plotly_dark')
                st.plotly_chart(fig, width='stretch')
                
                st.dataframe(
                    winner_df.style.format({
                        'Total PnL': '${:,.2f}',
                        'Win Rate': '{:.1f}%'
                    }),
                    width='stretch',
                    hide_index=True
                )
        
        with col2:
            st.markdown("### 📉 Top 5 Loss-Making Traders")
            top_losers = get_top_traders(filtered_positions, n=5, by='loss')
            
            if top_losers:
                loser_stats = []
                for trader in top_losers:
                    trader_pos = filtered_positions[filtered_positions['trader_id'] == trader]
                    loser_stats.append({
                        'Trader': mask_trader_id(trader),
                        'Total PnL': trader_pos['realized_pnl'].sum(),
                        'Trades': len(trader_pos),
                        'Win Rate': (trader_pos['realized_pnl'] > 0).mean() * 100
                    })
                
                loser_df = pd.DataFrame(loser_stats)
                
                fig = px.bar(
                    loser_df,
                    x='Trader',
                    y='Total PnL',
                    color='Total PnL',
                    color_continuous_scale='Reds_r',
                    text='Total PnL'
                )
                fig.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
                fig.update_layout(height=200, showlegend=False, template='plotly_dark')
                st.plotly_chart(fig, width='stretch')
                
                st.dataframe(
                    loser_df.style.format({
                        'Total PnL': '${:,.2f}',
                        'Win Rate': '{:.1f}%'
                    }),
                    width='stretch',
                    hide_index=True
                )

elif st.session_state.nav == "performance":
    if not filtered_positions.empty and not filtered_equity.empty:
        display_equity_section(filtered_equity, filtered_positions, 
                              st.session_state.authenticated_trader if st.session_state.view_mode == "personal" else None)
    else:
        st.info("No performance data for selected filters")

elif st.session_state.nav == "risk":
    if not filtered_positions.empty:
        display_liquidation_analytics(filtered_positions)
    else:
        st.info("No risk data for selected filters")

elif st.session_state.nav == "volume":
    if not filtered_positions.empty:
        display_volume_analysis(filtered_positions)
    else:
        st.info("No volume data for selected filters")

elif st.session_state.nav == "orders":
    if not data['order_perf'].empty:
        display_order_type_performance(data['order_perf'], filtered_positions)
    else:
        st.info("No order type data available")

elif st.session_state.nav == "greeks":
    if not data['greeks'].empty:
        greeks_filtered = data['greeks'].copy()
        if selected_trader:
            greeks_filtered = greeks_filtered[greeks_filtered['trader_id'] == selected_trader]
        
        if not greeks_filtered.empty:
            display_greeks_analysis(greeks_filtered)
        else:
            st.info("No Greeks data for selected trader")
    else:
        st.info("No Greeks data available")

elif st.session_state.nav == "journal":
    
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("📝 Trade Journal with Annotations")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if filtered_positions.empty:
        st.info("No trades to journal")
    
    elif st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state:
        trader = st.session_state.authenticated_trader
        
        st.markdown("""
        <div class='note-instruction'>
            <strong>📌 How to take notes:</strong><br>
            1. Click on any cell in the "📝 Your Trading Notes" column<br>
            2. Type your observations, strategy notes, or lessons learned<br>
            3. Press Enter or click outside to save automatically<br>
            4. Notes are saved locally and persist between sessions
        </div>
        """, unsafe_allow_html=True)
        
        trader_notes = load_trader_notes(trader)
        
        journal_df = filtered_positions.sort_values('close_time', ascending=False).copy()
        journal_df['symbol'] = journal_df['market_id'].apply(simplify_symbol)
        journal_df['notes'] = journal_df['position_id'].map(lambda pid: trader_notes.get(str(pid), ""))
        
        notes_count = len([n for n in journal_df['notes'] if n and str(n).strip()])
        st.info(f"📝 You have {notes_count} annotated trade{'s' if notes_count != 1 else ''}")
        
        available_cols = ['close_time', 'symbol', 'product_type', 'side',
                         'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees', 'notes']
        
        edited_journal = st.data_editor(
            journal_df[available_cols],
            column_config={
                "close_time": st.column_config.DatetimeColumn("Closed At", format="DD/MM/YYYY HH:mm"),
                "symbol": "Symbol",
                "product_type": "Type",
                "side": "Direction",
                "entry_price": st.column_config.NumberColumn("Entry", format="$%.2f"),
                "exit_price": st.column_config.NumberColumn("Exit", format="$%.2f"),
                "volume_usd": st.column_config.NumberColumn("Volume", format="$%.0f"),
                "realized_pnl": st.column_config.NumberColumn("PnL", format="$%.2f"),
                "fees": st.column_config.NumberColumn("Fees", format="$%.2f"),
                "notes": st.column_config.TextColumn(
                    "📝 Your Trading Notes",
                    help="Document your strategy, emotions, and lessons learned",
                    max_chars=500,
                    width="large"
                )
            },
            width='stretch',
            hide_index=True,
            num_rows="fixed",
            disabled=[col for col in available_cols if col != 'notes']
        )
        
        updated_notes = {}
        for idx, row in edited_journal.iterrows():
            pid = journal_df.loc[idx, 'position_id']
            note = row.get('notes', '')
            if pd.notna(note) and str(note).strip():
                updated_notes[str(pid)] = note
        
        if updated_notes != trader_notes:
            save_trader_notes(trader, updated_notes)
            st.success("✅ Notes saved!")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col2:
            export_df = journal_df[available_cols].copy()
            csv = export_df.to_csv(index=False)
            st.download_button(
                "📥 Export CSV",
                csv,
                f"journal_{trader[:8]}.csv",
                "text/csv",
                width='stretch'
            )
        
        with col3:
            if st.button("🗑️ Clear All Notes", width='stretch'):
                save_trader_notes(trader, {})
                st.rerun()
    
    elif selected_trader:
        st.info(f"👁️ **Read-Only View:** Viewing {mask_trader_id(selected_trader)}")
        st.caption("💡 To add notes, authenticate with your wallet in the sidebar")
        
        journal_df = filtered_positions.sort_values('close_time', ascending=False).copy()
        journal_df['trader'] = journal_df['trader_id'].apply(mask_trader_id)
        journal_df['symbol'] = journal_df['market_id'].apply(simplify_symbol)
        
        st.dataframe(
            journal_df[['close_time', 'trader', 'symbol', 'product_type', 'side',
                       'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees']].style.format({
                'entry_price': '${:,.2f}',
                'exit_price': '${:,.2f}',
                'volume_usd': '${:,.0f}',
                'realized_pnl': '${:,.2f}',
                'fees': '${:,.2f}'
            }),
            width='stretch',
            hide_index=True
        )
    
    else:
        st.info("👥 Select a specific trader or authenticate to add notes")
        
        journal_df = filtered_positions.sort_values('close_time', ascending=False).copy()
        journal_df['trader'] = journal_df['trader_id'].apply(mask_trader_id)
        journal_df['symbol'] = journal_df['market_id'].apply(simplify_symbol)
        
        st.dataframe(
            journal_df[['close_time', 'trader', 'symbol', 'product_type', 'side',
                       'entry_price', 'exit_price', 'volume_usd', 'realized_pnl', 'fees']].style.format({
                'entry_price': '${:,.2f}',
                'exit_price': '${:,.2f}',
                'volume_usd': '${:,.0f}',
                'realized_pnl': '${:,.2f}',
                'fees': '${:,.2f}'
            }),
            width='stretch',
            hide_index=True
        )


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with col2:
    if is_admin:
        st.caption("🔐 **Admin Mode** • All Time Access")
    else:
        st.caption("🔒 **Secure** • Local-first")

with col3:
    st.caption("v6.0 Enhanced")

st.markdown("""
    <div style='text-align: center; padding: 20px; color: #64748b; font-size: 12px;'>
        <p><strong>Deriverse Analytics Dashboard</strong></p>
        <p>Read-only • No private keys required • Data stays on your machine</p>
    </div>
""", unsafe_allow_html=True)