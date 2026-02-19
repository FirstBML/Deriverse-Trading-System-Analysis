# dashboards/app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
from datetime import datetime, timedelta
import requests
from plotly.subplots import make_subplots
import json
import re
import os
import time
from datetime import date
from dotenv import load_dotenv
from scipy.stats import norm  

load_dotenv()

# ============================================================================
# CONFIGURATION
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
# URL PARAMETER HANDLER - For secret admin activation
# ============================================================================

def check_url_for_admin():
    """Check if URL contains admin activation parameter."""
    try:
        query_params = st.query_params
        if "admin" in query_params and query_params["admin"] == "1":
            return True
    except:
        pass
    return False

# ============================================================================
# MINIMAL CSS - Sidebar sticky container
# ============================================================================

st.markdown("""
<style>
    /* Hide Streamlit's default header */
    header[data-testid="stHeader"] { 
        display: none !important; 
    }
    
    /* Hide the sidebar collapse/expand button - multiple selectors for different Streamlit versions */
    button[kind="header"],
    button[data-testid="baseButton-header"],
    .stApp [data-testid="stSidebar"] button[kind="header"],
    .stApp [data-testid="stSidebar"] button[data-testid="baseButton-header"] {
        display: none !important;
    }
    
    /* Hide any potential sidebar toggle buttons */
    [data-testid="collapsedControl"],
    .st-emotion-cache-1d3st0z,
    .st-emotion-cache-1wmy9hl {
        display: none !important;
    }
    
    /* Ensure sidebar is always expanded */
    section[data-testid="stSidebar"] {
        width: 21rem !important;
        min-width: 21rem !important;
        margin-left: 0 !important;
        transform: none !important;
    }
    
    /* Make entire sidebar scrollable */
    section[data-testid="stSidebar"] > div {
        height: 100vh !important;
        overflow-y: auto !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding-top: 0 !important;
    }
    
    /* Sticky container for branding */
    .sidebar-sticky-header {
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 16px 16px 8px 16px;
        margin: 0 !important;
        border-bottom: 1px solid rgba(99, 102, 241, 0.3);
        backdrop-filter: blur(8px);
        width: 100%;
    }
    
    /* Make the branding container expand full width */
    .sidebar-sticky-header .stHorizontalBlock {
        gap: 8px !important;
        align-items: center !important;
    }
    
    /* Ensure content below sticky header scrolls properly */
    .sidebar-content {
        padding: 16px;
    }
    
    /* Larger sidebar section headers */
    .stSidebar .stMarkdown h3 {
        font-size: 1.2rem !important;
        margin-top: 20px !important;
        margin-bottom: 15px !important;
        color: #f1f5f9 !important;
    }
    
    .stSidebar .stMarkdown h4 {
        font-size: 1.1rem !important;
        margin-top: 15px !important;
        color: #e2e8f0 !important;
    }
    
    /* Larger sidebar text elements */
    .stSidebar .stMarkdown p, 
    .stSidebar .stMarkdown li,
    .stSidebar .stTextInput label,
    .stSidebar .stSelectbox label,
    .stSidebar .stMultiselect label,
    .stSidebar .stRadio label {
        font-size: 1rem !important;
    }
    
    /* Larger input fields */
    .stSidebar .stTextInput input,
    .stSidebar .stSelectbox div[data-baseweb="select"] span,
    .stSidebar .stMultiselect div[data-baseweb="select"] span {
        font-size: 1rem !important;
        padding: 10px 12px !important;
    }
    
    /* Larger buttons */
    .stSidebar .stButton button {
        font-size: 1rem !important;
        padding: 10px 16px !important;
        height: auto !important;
    }
    
    /* Larger radio options */
    .stSidebar div.row-widget.stRadio > div {
        gap: 8px !important;
    }
    
    .stSidebar div.row-widget.stRadio > div > label {
        padding: 12px 16px !important;
        font-size: 1rem !important;
    }
    
    /* Larger expander content */
    .stSidebar .streamlit-expanderContent {
        font-size: 1rem !important;
    }
    
    /* Larger sidebar KPI cards */
    .sidebar-kpi {
        background: linear-gradient(135deg, #1e293b, #334155);
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 10px;
        padding: 12px 15px !important;
        text-align: center;
        margin-bottom: 10px !important;
    }
    .sidebar-kpi-label {
        font-size: 0.8rem !important;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px !important;
    }
    .sidebar-kpi-value {
        font-size: 1.3rem !important;
        font-weight: 700;
        color: #f1f5f9;
        font-family: 'IBM Plex Mono', monospace;
    }
    
    /* Larger profile badge */
    .profile-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 6px 16px !important;
        border-radius: 24px;
        font-weight: 600;
        font-size: 1rem !important;
        display: inline-block;
        margin: 12px 0 !important;
    }
    
    /* Larger section dividers */
    .stSidebar hr {
        margin: 20px 0 !important;
        border-color: rgba(99, 102, 241, 0.2) !important;
    }
    
    /* Main content area - full width */
    .main > div {
        padding: 2rem !important;
        max-width: 100% !important;
    }
    
    /* KPI cards styling */
    .metric-major {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 16px 20px;
        border-radius: 12px;
        border: 1px solid rgba(99, 102, 241, 0.4);
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        margin-bottom: 16px;
    }

    .metric-major-label {
        font-size: 0.85rem;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }

    .metric-major-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f1f5f9;
        line-height: 1.2;
        font-family: 'IBM Plex Mono', monospace;
    }
    
    /* Transaction table */
    .tx-table { 
        width: 100%; 
        border-collapse: collapse; 
        font-size: 0.85rem; 
    }
    
    .tx-table th { 
        background: #1e293b; 
        color: #94a3b8; 
        padding: 10px 12px;
        text-align: left; 
        border-bottom: 2px solid #334155; 
    }
    
    .tx-table td { 
        padding: 8px 12px; 
        border-bottom: 1px solid rgba(51,65,85,0.4); 
        color: #e2e8f0; 
    }
    
    .tx-table tr:hover td { 
        background: rgba(99,102,241,0.1); 
    }

    /* Verify links */
    .verify-link { 
        color: #10b981 !important; 
        text-decoration: none; 
        font-weight: 600; 
    }
    
    .verify-link:hover { 
        text-decoration: underline; 
        color: #34d399 !important; 
    }
    
    /* Debug container - only visible to admins */
    .debug-info {
        background: #1e293b;
        border-left: 4px solid #f59e0b;
        padding: 8px 16px;
        border-radius: 4px;
        margin: 10px 0;
        font-size: 0.85rem;
        color: #e2e8f0;
    }
    
    /* Active navigation styling */
    div.row-widget.stRadio > div {
        flex-direction: column;
        gap: 6px !important;
    }
    div.row-widget.stRadio > div > label {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 8px;
        padding: 12px 18px !important;
        font-weight: 500;
        font-size: 1rem !important;
        transition: all 0.2s;
    }
    div.row-widget.stRadio > div > label:hover {
        background: rgba(99,102,241,0.2);
        border-color: #6366f1;
    }
    div.row-widget.stRadio > div > label[data-baseweb="radio"] > div:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ADAPTIVE VISUALIZATION FRAMEWORK
# ============================================================================

def get_data_density(df):
    """Classify data density for adaptive visualization."""
    count = len(df)
    if count == 0:
        return "empty"
    elif count == 1:
        return "single"
    elif count < 5:
        return "sparse"
    elif count < 15:
        return "moderate"
    else:
        return "dense"

def context_note(msg):
    """Display a contextual note for adaptive views."""
    st.info(f"ℹ️ {msg}")

def should_show_chart(df, min_points=5, min_variance=0.1):
    """Determine if a chart is meaningful based on data."""
    if len(df) < min_points:
        return False
    if df['realized_pnl'].std() < min_variance:
        return False
    return True

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

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
    return trader_stats.nlargest(n, 'count').index.tolist()

def load_trader_notes(trader_id):
    """Load trade notes from JSON file."""
    notes_dir = Path("data/trader_notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_file = notes_dir / f"{trader_id}.json"
    
    if notes_file.exists():
        with open(notes_file, 'r') as f:
            return json.load(f)
    return {}

def save_trader_notes(trader_id, notes):
    """Save trade notes to JSON file."""
    notes_dir = Path("data/trader_notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    with open(notes_dir / f"{trader_id}.json", 'w') as f:
        json.dump(notes, f, indent=2)

def calculate_volume_usd(df):
    """Calculate USD volume from price and size."""
    df = df.copy()
    df['volume_usd'] = df['exit_price'] * df['size']
    return df

# Chart styling constants
CHART_BG = dict(
    template='plotly_dark',
    plot_bgcolor='rgba(15,23,42,0.9)',
    paper_bgcolor='rgba(15,23,42,0.9)'
)

# ============================================================================
# TRADER PERFORMANCE SUMMARY
# ============================================================================

def create_trader_summary_table(equity_df, positions_df):
    """Trader summary table with actual equity sparklines."""
    
    st.markdown("### 📋 Trader Performance Summary")
    
    if equity_df.empty or positions_df.empty:
        st.info("No performance data available")
        return
    
    traders = []
    for trader in positions_df['trader_id'].unique():
        te = equity_df[equity_df['trader_id'] == trader].sort_values('timestamp')
        tp = positions_df[positions_df['trader_id'] == trader]
        
        if te.empty or tp.empty:
            continue
        
        total_pnl = tp['realized_pnl'].sum()
        win_rate = (tp['realized_pnl'] > 0).mean() * 100 if len(tp) > 0 else 0
        max_dd = te['drawdown'].min()
        
        timestamps = te['timestamp'].values
        equity_values = te['cumulative_pnl'].values
        
        if len(equity_values) > 1:
            min_val = equity_values.min()
            max_val = equity_values.max()
            norm_curve = (equity_values - min_val) / (max_val - min_val) if max_val > min_val else np.ones_like(equity_values) * 0.5
        else:
            norm_curve = np.array([0.5])
            timestamps = [0]
        
        traders.append({
            'trader_masked': mask_trader_id(trader),
            'pnl': total_pnl,
            'win_rate': win_rate,
            'max_dd': abs(max_dd),
            'trades': len(tp),
            'equity_curve': norm_curve,
            'timestamps': timestamps,
            'raw_equity': equity_values,
            'trader_id': trader
        })
    
    traders.sort(key=lambda x: x['pnl'], reverse=True)
    
    if not traders:
        st.info("No trader data available")
        return
    
    cols = st.columns([1.2, 2.0, 0.8, 0.8, 0.8, 0.8])
    headers = ["**Trader**", "**Equity Curve**", "**PnL**", "**Win Rate**", "**Max DD**", "**Trades**"]
    for col, header in zip(cols, headers):
        col.markdown(header)
    
    st.divider()
    
    for i, t in enumerate(traders):
        cols = st.columns([1.2, 2.0, 0.8, 0.8, 0.8, 0.8])
        
        cols[0].markdown(f"`{t['trader_masked']}`")
        
        fig = go.Figure()
        
        x_values = t['timestamps'] if len(t['timestamps']) > 1 else list(range(len(t['equity_curve'])))
        
        color = '#10b981' if t['pnl'] > 0 else '#ef4444'
        
        fig.add_trace(go.Scatter(
            x=x_values,
            y=t['equity_curve'],
            mode='lines',
            line=dict(color=color, width=2),
            showlegend=False,
            hovertemplate='<b>Equity Curve</b><br>Value: %{customdata[0]:,.0f}<extra></extra>',
            customdata=list(zip(t['raw_equity'])) if len(t['raw_equity']) > 0 else None
        ))
        
        fig.update_layout(
            height=45,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, 1]),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        cols[1].plotly_chart(
            fig, width='stretch',
            config={'displayModeBar': False},
            key=f"equity_curve_fixed_{i}"
        )
        
        pnl_color = '#10b981' if t['pnl'] > 0 else '#ef4444'
        cols[2].markdown(f"<span style='color:{pnl_color};font-weight:600;'>${t['pnl']:,.0f}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"{t['win_rate']:.0f}%")
        cols[4].markdown(f"${t['max_dd']:,.0f}")
        cols[5].markdown(f"{t['trades']}")

# ============================================================================
# PROTOCOL EQUITY CHART
# ============================================================================

def create_protocol_equity_charts(positions_df, compact=False):
    """Protocol equity + drawdown as two separate charts — with compact option."""
    
    ps = positions_df.sort_values('close_time').copy()
    ps['cumulative_pnl'] = ps['realized_pnl'].cumsum()
    
    
    eq_height = 250 if compact else 350
    dd_height = 180 if compact else 250
    
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(
        x=ps['close_time'],
        y=ps['cumulative_pnl'],
        line=dict(color='#6366f1', width=3),
        fill='tozeroy',
        fillcolor='rgba(99,102,241,0.1)',
        showlegend=False,
        hovertemplate='Date: %{x}<br>PnL: $%{y:,.2f}<extra></extra>'
    ))
    fig_eq.update_layout(
        title="📈 Protocol PnL" if compact else "📈 Protocol Cumulative PnL",
        xaxis_title="Date" if not compact else "",
        yaxis_title="PnL ($)",
        height=eq_height,
        margin=dict(l=40, r=40, t=40 if compact else 40, b=40),
        **CHART_BG
    )
    
    rolling_max = ps['cumulative_pnl'].cummax()
    drawdown = ps['cumulative_pnl'] - rolling_max
    max_dd = drawdown.min()
    
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=ps['close_time'], y=drawdown,
        line=dict(color='#ef4444', width=2.5),
        fill='tozeroy', fillcolor='rgba(239,68,68,0.15)',
        showlegend=False
    ))
    fig_dd.add_hline(y=max_dd, line_dash="dash", line_color="#ef4444",
                    annotation_text=f"Max: ${max_dd:,.0f}" if compact else f"Max DD: ${max_dd:,.0f}",
                    annotation_position="bottom right")
    fig_dd.update_layout(
        title="📉 Drawdown" if compact else "📉 Drawdown from Peak",
        xaxis_title="Date" if not compact else "",
        yaxis_title="Drawdown ($)",
        height=dd_height,
        margin=dict(l=40, r=40, t=40 if compact else 40, b=40),
        **CHART_BG
    )
    
    return fig_eq, fig_dd

# ============================================================================
# PERSONAL EQUITY CHART
# ============================================================================

def create_personal_equity_chart(trader_positions, is_sparse_mode=False, compact=False):
    """Adaptive equity chart for personal mode with drawdown option."""
    
    if is_sparse_mode:
        # Just show a simple bar chart for sparse data
        fig = go.Figure()
        
        # Sort by date for timeline
        df = trader_positions.sort_values('close_time')
        
        colors = ['#10b981' if x > 0 else '#ef4444' for x in df['realized_pnl']]
        
        fig.add_trace(go.Bar(
            x=df['close_time'],
            y=df['realized_pnl'],
            marker_color=colors,
            text=df['realized_pnl'].apply(lambda x: f"${x:,.0f}"),
            textposition='outside',
            name='Trade PnL'
        ))
        
        fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)
        
        fig.update_layout(
            title="📊 Your Trades (Individual)",
            xaxis_title="Date",
            yaxis_title="PnL ($)",
            height=300,
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40),
            **CHART_BG
        )
        
        return fig, None  # Return None for drawdown chart
    
    # Original adaptive logic for non-sparse mode
    density = get_data_density(trader_positions)
    
    if density == "single":
        pnl = trader_positions['realized_pnl'].iloc[0]
        fig = go.Figure(go.Bar(
            x=['Your Trade'], y=[pnl],
            marker_color='#10b981' if pnl > 0 else '#ef4444',
            text=[f"${pnl:,.2f}"], textposition='outside', width=0.4
        ))
        fig.update_layout(
            title=f"Trade Result: {'🟢 Profit' if pnl > 0 else '🔴 Loss'}",
            yaxis_title="PnL ($)", height=300, showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40), **CHART_BG
        )
        
        # No drawdown for single trade
        return fig, None
    
    tp = trader_positions.sort_values('close_time').copy()
    tp['cumulative'] = tp['realized_pnl'].cumsum()
    
    if density == "sparse":
        # Step chart with markers
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=tp['close_time'], y=tp['cumulative'],
            mode='lines+markers',
            line=dict(shape='hv', width=3, color='#6366f1'),
            marker=dict(size=12, symbol='diamond', color='#6366f1'),
            fill='tozeroy', fillcolor='rgba(99,102,241,0.1)', name='Your PnL'
        ))
        fig.update_layout(
            title="📈 Your Trading Performance",
            xaxis_title="Date", yaxis_title="Cumulative PnL ($)",
            height=300, margin=dict(l=40, r=40, t=40, b=40), **CHART_BG
        )
        
        # Calculate drawdown for sparse data
        rolling_max = tp['cumulative'].cummax()
        tp['drawdown'] = tp['cumulative'] - rolling_max
        max_dd = tp['drawdown'].min()
        
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=tp['close_time'],
            y=tp['drawdown'],
            line=dict(color='#ef4444', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(239,68,68,0.15)',
            showlegend=False
        ))
        fig_dd.add_hline(
            y=max_dd,
            line_dash="dash",
            line_color="#ef4444",
            annotation_text=f"Max DD: ${max_dd:,.0f}",
            annotation_position="bottom right"
        )
        fig_dd.update_layout(
            title="📉 Your Drawdown",
            xaxis_title="Date",
            yaxis_title="Drawdown ($)",
            height=200,
            margin=dict(l=40, r=40, t=40, b=40),
            **CHART_BG
        )
        
        return fig, fig_dd
    
    # Dense: full equity curve
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tp['close_time'], y=tp['cumulative'],
        line=dict(color='#6366f1', width=3),
        fill='tozeroy', fillcolor='rgba(99,102,241,0.1)', name='Your PnL'
    ))
    
    # Set heights based on compact mode
    height_eq = 250 if compact else 300
    height_dd = 150 if compact else 200
    
    fig.update_layout(
        title="📈 Your Equity Curve",
        xaxis_title="Date", yaxis_title="Cumulative PnL ($)",
        height=height_eq,  # ← USE THE VARIABLE HERE
        margin=dict(l=40, r=40, t=40, b=40),
        **CHART_BG
    )
    
    # Calculate drawdown for dense data
    rolling_max = tp['cumulative'].cummax()
    tp['drawdown'] = tp['cumulative'] - rolling_max
    max_dd = tp['drawdown'].min()
    
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=tp['close_time'],
        y=tp['drawdown'],
        line=dict(color='#ef4444', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(239,68,68,0.15)',
        showlegend=False
    ))
    
    fig_dd.add_hline(
        y=max_dd,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"Max DD: ${max_dd:,.0f}",
        annotation_position="bottom right"
    )
    
    fig_dd.update_layout(
        title="📉 Your Drawdown from Peak",
        xaxis_title="Date",
        yaxis_title="Drawdown ($)",
        height=height_dd,  # ← USE THE VARIABLE HERE
        margin=dict(l=40, r=40, t=40, b=40),
        **CHART_BG
    )
    
    return fig, fig_dd
    
# ============================================================================
# ADAPTIVE INFORMATION CARDS 
# ============================================================================

def display_trade_summary_cards(positions_df, title="Trade Summary"):
    """Display key trade metrics as information cards when charts aren't meaningful."""
    
    if positions_df.empty:
        st.info("No trade data available")
        return
    
    st.subheader(f"📊 {title}")
    st.caption("Detailed trade information (chart not shown due to limited data)")
    
    # Key metrics in cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trades = len(positions_df)
        st.metric("Total Trades", total_trades)
    
    with col2:
        winning_trades = (positions_df['realized_pnl'] > 0).sum()
        st.metric("Winning Trades", winning_trades)
    
    with col3:
        losing_trades = (positions_df['realized_pnl'] < 0).sum()
        st.metric("Losing Trades", losing_trades)
    
    with col4:
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        st.metric("Win Rate", f"{win_rate:.1f}%")
    
    # Trade list in expander
    with st.expander("📋 View Individual Trades", expanded=True):
        display_df = positions_df.copy()
        display_df['symbol'] = display_df['market_id'].apply(simplify_symbol)
        display_df = display_df[['close_time', 'symbol', 'product_type', 'side', 
                                 'entry_price', 'exit_price', 'size', 'realized_pnl', 'fees']]
        
        # Format for display
        display_df['close_time'] = pd.to_datetime(display_df['close_time']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
        display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}")
        display_df['size'] = display_df['size'].apply(lambda x: f"{x:,.4f}")
        display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
        display_df['fees'] = display_df['fees'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(display_df, width='stretch', hide_index=True)


def display_performance_cards(positions_df, title="Performance Summary"):
    """Display performance metrics as cards for sparse data."""
    
    if positions_df.empty:
        st.info("No performance data available")
        return
    
    st.subheader(f"📈 {title}")
    
    # Calculate metrics
    total_pnl = positions_df['realized_pnl'].sum()
    avg_win = positions_df[positions_df['realized_pnl'] > 0]['realized_pnl'].mean() if (positions_df['realized_pnl'] > 0).any() else 0
    avg_loss = positions_df[positions_df['realized_pnl'] < 0]['realized_pnl'].mean() if (positions_df['realized_pnl'] < 0).any() else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total PnL", f"${total_pnl:,.2f}")
    
    with col2:
        st.metric("Avg Win", f"${avg_win:,.2f}" if avg_win != 0 else "N/A")
    
    with col3:
        st.metric("Avg Loss", f"${avg_loss:,.2f}" if avg_loss != 0 else "N/A")
    
    with col4:
        profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
        st.metric("Profit Factor", f"{profit_factor:.2f}x" if profit_factor != float('inf') else "∞")
    
    # Trade timeline
    st.subheader("📅 Trade Timeline")
    timeline_df = positions_df.sort_values('close_time')[['close_time', 'market_id', 'realized_pnl']].copy()
    timeline_df['market_id'] = timeline_df['market_id'].apply(simplify_symbol)
    timeline_df['close_time'] = pd.to_datetime(timeline_df['close_time']).dt.strftime('%Y-%m-%d')
    timeline_df.columns = ['Date', 'Symbol', 'PnL']
    
    st.dataframe(timeline_df, width='stretch', hide_index=True)
    
# ============================================================================
# PERSONAL DRAWDOWN CHART 
# ============================================================================

def create_personal_drawdown_chart(trader_positions):
    """Create drawdown chart for personal trader dashboard."""
    
    if trader_positions.empty:
        return None
    
    # Calculate cumulative PnL and drawdown
    df = trader_positions.sort_values('close_time').copy()
    df['cumulative_pnl'] = df['realized_pnl'].cumsum()
    rolling_max = df['cumulative_pnl'].cummax()
    df['drawdown'] = df['cumulative_pnl'] - rolling_max
    max_dd = df['drawdown'].min()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['close_time'],
        y=df['drawdown'],
        line=dict(color='#ef4444', width=2.5),
        fill='tozeroy',
        fillcolor='rgba(239,68,68,0.15)',
        showlegend=False,
        hovertemplate='Date: %{x}<br>Drawdown: $%{y:,.2f}<extra></extra>'
    ))
    
    fig.add_hline(
        y=max_dd,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text=f"Max DD: ${max_dd:,.0f}",
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        title="📉 Your Drawdown from Peak",
        xaxis_title="Date",
        yaxis_title="Drawdown ($)",
        height=250,
        margin=dict(l=40, r=40, t=40, b=40),
        **CHART_BG
    )
    
    return fig

# ============================================================================
# LIQUIDATION ANALYTICS
# ============================================================================

def display_liquidation_analytics(positions_df, is_personal_mode=False, trader_id=None):
    """Liquidation analysis with close_reason handling and adaptive logic."""
    
    st.header("⚠️ Liquidation Risk Monitoring")
    
    if 'close_reason' not in positions_df.columns:
        st.info("ℹ️ Liquidation tracking not available")
        return
    
    # Get symbol filter state from session
    has_symbol_filter = False
    if 'selected_symbols' in st.session_state:
        has_symbol_filter = len(st.session_state.selected_symbols) > 0
    
    # SPARSE DATA DETECTION - Check if we should show simplified view
    trade_count = len(positions_df)
    is_sparse_mode = False
    sparse_reason = ""
    
    # Very few trades overall
    if trade_count < 3:
        is_sparse_mode = True
        sparse_reason = "Very few trades available"
    # Symbol filter with few trades
    elif has_symbol_filter and trade_count < 8:
        is_sparse_mode = True
        symbol_text = f"for selected symbol{'s' if len(st.session_state.selected_symbols) > 1 else ''}"
        sparse_reason = f"Limited data {symbol_text}"
    # Date range with few trades
    elif 'start_date' in st.session_state and 'end_date' in st.session_state:
        days_selected = (st.session_state.end_date - st.session_state.start_date).days
        if days_selected <= 7 and trade_count < 10:
            is_sparse_mode = True
            sparse_reason = "Limited data for selected period"
    
    # Personal mode handling
    if is_personal_mode and trader_id:
        tp = positions_df[positions_df['trader_id'] == trader_id]
        liq = tp[tp['close_reason'] == 'liquidation']
        
        st.markdown("### ⚠️ Your Riskiest Trades")
        
        if liq.empty:
            st.success("✅ No liquidations in your history!")
            return
        
        # Even in personal mode, check if we should show simplified view
        if is_sparse_mode:
            context_note(f"{sparse_reason} - showing your loss-making trades")
            worst = tp.nsmallest(min(5, len(tp)), 'realized_pnl').copy()
            worst['symbol'] = worst['market_id'].apply(simplify_symbol)
            
            # Show as table instead of chart for sparse data
            st.dataframe(
                worst[['close_time', 'symbol', 'side', 'realized_pnl']].assign(
                    close_time=pd.to_datetime(worst['close_time']).dt.strftime('%Y-%m-%d %H:%M'),
                    realized_pnl=worst['realized_pnl'].apply(lambda x: f"${x:,.2f}")
                ),
                width='stretch',
                hide_index=True,
                column_config={
                    "close_time": "Time",
                    "symbol": "Symbol",
                    "side": "Side",
                    "realized_pnl": "Loss"
                }
            )
            return
        
        # Normal personal mode with chart
        worst = tp.nsmallest(5, 'realized_pnl').copy()
        worst['symbol'] = worst['market_id'].apply(simplify_symbol)
        
        fig = px.bar(worst, x='symbol', y='realized_pnl',
                    title='Your Top 5 Loss-Making Trades',
                    color='realized_pnl', color_continuous_scale='Reds_r',
                    labels={'realized_pnl': 'Loss ($)'})
        fig.update_layout(height=350, **CHART_BG)
        st.plotly_chart(fig, width='stretch', key="personal_liq_bar")
        return
    
    # Protocol mode
    liq = positions_df[positions_df['close_reason'] == 'liquidation']
    
    if liq.empty:
        st.success("✅ No liquidations in selected period")
        return
    
    # SPARSE MODE - Show simplified view
    if is_sparse_mode:
        context_note(f"{sparse_reason} - showing liquidation summary")
        
        # Show key metrics
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Liquidations", len(liq))
        c2.metric("Affected Traders", liq['trader_id'].nunique())
        c3.metric("Total Loss", f"${abs(liq['realized_pnl'].sum()):,.0f}")
        
        # Show liquidation list instead of charts
        st.subheader("📋 Liquidation Events")
        liq_display = liq[['close_time', 'trader_id', 'market_id', 'side', 'realized_pnl']].copy()
        liq_display['trader'] = liq_display['trader_id'].apply(mask_trader_id)
        liq_display['symbol'] = liq_display['market_id'].apply(simplify_symbol)
        liq_display['close_time'] = pd.to_datetime(liq_display['close_time']).dt.strftime('%Y-%m-%d %H:%M')
        liq_display['realized_pnl'] = liq_display['realized_pnl'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            liq_display[['close_time', 'trader', 'symbol', 'side', 'realized_pnl']],
            width='stretch',
            hide_index=True
        )
        return
    
    # NORMAL MODE - Full analytics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Liquidations", len(liq))
    c2.metric("Affected Traders", liq['trader_id'].nunique())
    c3.metric("Total Loss", f"${abs(liq['realized_pnl'].sum()):,.0f}")
    
    st.subheader("📊 Liquidation Distribution by Trader")
    
    liq_by_trader = liq.groupby('trader_id').agg({
        'realized_pnl': lambda x: abs(x.sum()),
        'position_id': 'count'
    }).reset_index()
    liq_by_trader.columns = ['trader_id', 'loss', 'count']
    liq_by_trader['trader'] = liq_by_trader['trader_id'].apply(mask_trader_id)
    liq_by_trader = liq_by_trader.sort_values('loss', ascending=False)
    
    fig = go.Figure(data=[go.Pie(
        labels=liq_by_trader['trader'],
        values=liq_by_trader['loss'],
        textinfo='label+percent', textposition='outside',
        insidetextorientation='radial',
        marker=dict(colors=px.colors.sequential.Reds_r,
                   line=dict(color='#1e293b', width=2)),
        hovertemplate='<b>%{label}</b><br>Loss: $%{value:,.0f}<br>Liquidations: %{customdata}<extra></extra>',
        customdata=liq_by_trader['count']
    )])
    
    fig.update_layout(height=400, showlegend=False, **CHART_BG)
    st.plotly_chart(fig, width='stretch', key="liq_pie")
    
    st.subheader("📊 Liquidation Rate by Trader")
    
    stats = []
    for trader in positions_df['trader_id'].unique():
        td = positions_df[positions_df['trader_id'] == trader]
        
        total = len(td[td['close_reason'].isin(['close', 'liquidation'])])
        
        if total > 0:
            liq_n = len(td[td['close_reason'] == 'liquidation'])
            close_n = len(td[td['close_reason'] == 'close'])
            
            stats.append({
                'trader': mask_trader_id(trader),
                'liq_rate': (liq_n / total) * 100,
                'liq_count': liq_n,
                'close_count': close_n,
                'total_trades': total
            })
    
    if stats:
        df = pd.DataFrame(stats)
        
        df_with_liq = df[df['liq_count'] > 0].copy()
        
        if not df_with_liq.empty:
            df_top5 = df_with_liq.sort_values('liq_rate', ascending=False).head(5)
            df_top5 = df_top5.sort_values('liq_rate', ascending=True)
            
            colors = []
            for rate in df_top5['liq_rate']:
                if rate < 2:
                    colors.append('#10b981')
                elif rate < 5:
                    colors.append('#f59e0b')
                else:
                    colors.append('#ef4444')
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=df_top5['trader'], x=df_top5['liq_rate'],
                orientation='h', marker_color=colors,
                text=df_top5['liq_rate'].apply(lambda x: f"{x:.1f}%"),
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Rate: %{x:.1f}%<br>Liquidations: %{customdata[0]}/%{customdata[1]} trades<extra></extra>',
                customdata=df_top5[['liq_count', 'total_trades']].values
            ))
            
            fig.add_vline(x=2, line_dash="dash", line_color="#10b981",
                          annotation_text="Low Risk", annotation_position="top")
            fig.add_vline(x=5, line_dash="dash", line_color="#ef4444",
                          annotation_text="High Risk", annotation_position="top")
            
            fig.update_layout(
                title="Top 5 Traders by Liquidation Rate",
                xaxis_title="Liquidation Rate (%)", yaxis_title="",
                height=250, margin=dict(l=120, r=40, t=60, b=40), **CHART_BG
            )
            fig.update_xaxes(range=[0, 100])
            
            st.plotly_chart(fig, width='stretch', key="liq_rate_top5")
            
            excluded_count = len(df[df['liq_count'] == 0])
            if excluded_count > 0:
                st.caption(f"ℹ️ {excluded_count} traders with 0% liquidation rate not shown")
        else:
            st.info("No traders with liquidations to display")
    
    st.subheader("💰 Financial Impact")
    c1, c2 = st.columns(2)
    
    with c1:
        bm = liq.groupby('market_id')['realized_pnl'].sum().abs().reset_index()
        bm['symbol'] = bm['market_id'].apply(simplify_symbol)
        bm = bm.sort_values('realized_pnl', ascending=False).head(5)
        fig = px.bar(bm, x='symbol', y='realized_pnl',
                    title='Top 5 Markets by Liq Loss',
                    color='realized_pnl', color_continuous_scale='Reds')
        fig.update_layout(height=300, **CHART_BG)
        st.plotly_chart(fig, width='stretch', key="liq_mkt")
    
    with c2:
        bt = liq.groupby('trader_id')['realized_pnl'].sum().abs().reset_index()
        bt['trader'] = bt['trader_id'].apply(mask_trader_id)
        bt = bt.sort_values('realized_pnl', ascending=False).head(5)
        fig = px.bar(bt, x='trader', y='realized_pnl',
                    title='Top 5 Traders by Liq Loss',
                    color='realized_pnl', color_continuous_scale='Reds')
        fig.update_layout(height=300, **CHART_BG)
        st.plotly_chart(fig, width='stretch', key="liq_trader")

# ============================================================================
# TIME-BASED PERFORMANCE ANALYSIS
# ============================================================================

def display_time_performance(positions_df, pnl_day_df=None, pnl_hour_df=None):
    st.header("📅 Time-Based Performance")

    if positions_df.empty:
        st.info("No performance data available")
        return

    # ── Avg Duration metric (dynamic to all filters) ──
    if 'duration_seconds' in positions_df.columns:
        avg_dur_h  = positions_df['duration_seconds'].mean() / 3600
        med_dur_h  = positions_df['duration_seconds'].median() / 3600
        max_dur_h  = positions_df['duration_seconds'].max() / 3600
        d1, d2, d3 = st.columns(3)
        d1.metric("Avg Trade Duration",    f"{avg_dur_h:.1f}h")
        d2.metric("Median Trade Duration", f"{med_dur_h:.1f}h")
        d3.metric("Longest Trade",         f"{max_dur_h:.1f}h")
        st.markdown("---")
    
    # Daily PnL chart
    if pnl_day_df is not None and not pnl_day_df.empty:
        st.subheader("📊 Daily Performance")
        
        # Ensure date column is datetime
        if 'date' in pnl_day_df.columns:
            pnl_day_df['date'] = pd.to_datetime(pnl_day_df['date'])
        
        # Daily PnL bar chart
        fig = go.Figure()
        
        colors = ['#10b981' if x > 0 else '#ef4444' for x in pnl_day_df['daily_pnl']]
        
        fig.add_trace(go.Bar(
            x=pnl_day_df['date'],
            y=pnl_day_df['daily_pnl'],
            marker_color=colors,
            text=pnl_day_df['daily_pnl'].apply(lambda x: f"${x:,.0f}"),
            textposition='outside',
            hovertemplate='Date: %{x}<br>PnL: $%{y:,.2f}<br>Trades: %{customdata}<extra></extra>',
            customdata=pnl_day_df['trade_count'] if 'trade_count' in pnl_day_df.columns else None
        ))
        
        fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)
        
        fig.update_layout(
            title="Daily PnL",
            xaxis_title="Date",
            yaxis_title="PnL ($)",
            height=350,
            **CHART_BG
        )
        
        st.plotly_chart(fig, width='stretch', key="daily_pnl")
        
        # Daily statistics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Best Day", f"${pnl_day_df['daily_pnl'].max():,.0f}")
        c2.metric("Worst Day", f"${pnl_day_df['daily_pnl'].min():,.0f}")
        c3.metric("Avg Daily PnL", f"${pnl_day_df['daily_pnl'].mean():,.0f}")
        winning_days = (pnl_day_df['daily_pnl'] > 0).sum()
        total_days = len(pnl_day_df)
        c4.metric("Winning Days", f"{winning_days}/{total_days} ({winning_days/total_days*100:.0f}%)")
    
    else:
        # Generate from positions if pnl_day not available
        st.subheader("📊 Daily Performance")
        
        daily = positions_df.copy()
        daily['date'] = pd.to_datetime(daily['close_time']).dt.date
        
        daily_pnl = daily.groupby('date').agg({
            'realized_pnl': ['sum', 'count']
        }).reset_index()
        daily_pnl.columns = ['date', 'daily_pnl', 'trade_count']
        
        colors = ['#10b981' if x > 0 else '#ef4444' for x in daily_pnl['daily_pnl']]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=daily_pnl['date'],
            y=daily_pnl['daily_pnl'],
            marker_color=colors,
            text=daily_pnl['daily_pnl'].apply(lambda x: f"${x:,.0f}"),
            textposition='outside',
            hovertemplate='Date: %{x}<br>PnL: $%{y:,.2f}<br>Trades: %{customdata}<extra></extra>',
            customdata=daily_pnl['trade_count']
        ))
        
        fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)
        fig.update_layout(
            title="Daily PnL",
            xaxis_title="Date",
            yaxis_title="PnL ($)",
            height=350,
            **CHART_BG
        )
        
        st.plotly_chart(fig, width='stretch', key="daily_pnl_gen")
    
    # Hourly performance
    if pnl_hour_df is not None and not pnl_hour_df.empty and 'hour' in pnl_hour_df.columns:
        st.subheader("🕐 Hourly Performance Pattern")
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=pnl_hour_df['hour'],
            y=pnl_hour_df['avg_pnl'] if 'avg_pnl' in pnl_hour_df.columns else pnl_hour_df['total_pnl'],
            marker_color='#6366f1',
            text=pnl_hour_df['trade_count'] if 'trade_count' in pnl_hour_df.columns else None,
            texttemplate='%{text} trades',
            textposition='outside',
            hovertemplate='Hour: %{x}:00<br>Avg PnL: $%{y:,.2f}<extra></extra>'
        ))
        
        fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)
        
        fig.update_layout(
            title="Average PnL by Hour of Day (UTC)",
            xaxis_title="Hour (24h format)",
            yaxis_title="Average PnL ($)",
            height=300,
            **CHART_BG
        )
        fig.update_xaxes(tickmode='linear', dtick=2)
        
        st.plotly_chart(fig, width='stretch', key="hourly_pnl")
        
        # Best/worst trading hours
        if 'avg_pnl' in pnl_hour_df.columns:
            best_hour = pnl_hour_df.loc[pnl_hour_df['avg_pnl'].idxmax()]
            worst_hour = pnl_hour_df.loc[pnl_hour_df['avg_pnl'].idxmin()]
            
            c1, c2 = st.columns(2)
            c1.metric(
                "Best Trading Hour", 
                f"{int(best_hour['hour'])}:00 UTC",
                f"${best_hour['avg_pnl']:,.0f} avg"
            )
            c2.metric(
                "Worst Trading Hour",
                f"{int(worst_hour['hour'])}:00 UTC",
                f"${worst_hour['avg_pnl']:,.0f} avg"
            )
    
    else:
        # Generate from positions
        st.subheader("🕐 Hourly Performance Pattern")
        
        hourly = positions_df.copy()
        hourly['hour'] = pd.to_datetime(hourly['close_time']).dt.hour
        
        hourly_pnl = hourly.groupby('hour').agg({
            'realized_pnl': ['mean', 'count']
        }).reset_index()
        hourly_pnl.columns = ['hour', 'avg_pnl', 'trade_count']
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=hourly_pnl['hour'],
            y=hourly_pnl['avg_pnl'],
            marker_color='#6366f1',
            text=hourly_pnl['trade_count'],
            texttemplate='%{text} trades',
            textposition='outside',
            hovertemplate='Hour: %{x}:00<br>Avg PnL: $%{y:,.2f}<extra></extra>'
        ))
        
        fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.3)
        fig.update_layout(
            title="Average PnL by Hour of Day (UTC)",
            xaxis_title="Hour (24h format)",
            yaxis_title="Average PnL ($)",
            height=300,
            **CHART_BG
        )
        fig.update_xaxes(tickmode='linear', dtick=2)
        
        st.plotly_chart(fig, width='stretch', key="hourly_pnl_gen")
                
# ============================================================================
# VOLUME ANALYSIS
# ============================================================================

def display_volume_analysis(positions_df):
    """Volume analysis with product tabs, progress bars, and trade duration."""
    
    st.header("📊 Trading Volume Analysis")
    
    if positions_df.empty:
        st.info("No volume data available")
        return
    
    # Check if we have symbol filter applied and sparse data
    has_symbol_filter = len(selected_symbols) > 0
    trade_count = len(positions_df)
    
    if has_symbol_filter and trade_count < 5:
        context_note(f"Limited volume data for selected symbol{'s' if len(selected_symbols)>1 else ''} - showing summary cards")
        display_trade_summary_cards(positions_df, "Volume Summary")
        return
    
    positions_df = calculate_volume_usd(positions_df)  
    product_counts = positions_df['product_type'].value_counts()
    st.caption(f"Product types present: {', '.join([f'{k}({v})' for k, v in product_counts.items()])}")
    
    total_vol = positions_df['volume_usd'].sum()
    total_fees = positions_df['fees'].sum()
    unique_sym = positions_df['market_id'].apply(simplify_symbol).nunique()
    
    vol_shares = positions_df.groupby(
        positions_df['market_id'].apply(simplify_symbol))['volume_usd'].sum() / total_vol
    hhi = (vol_shares ** 2).sum() * 10000
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Volume", f"${total_vol:,.0f}")
    c2.metric("Total Fees", f"${total_fees:,.0f}")
    c3.metric("Active Symbols", unique_sym)
    
    conc = "Low" if hhi < 1500 else "Medium" if hhi < 2500 else "High"
    c4.metric("Concentration", f"{hhi:.0f} ({conc})")
    
    density = get_data_density(positions_df)
    
    if density in ["sparse", "moderate", "dense"]:
        st.subheader("📊 Trade Size Distribution")
        
        c1, c2 = st.columns(2)
        with c1:
            fig = px.box(
                positions_df, x='product_type', y='volume_usd', points='all',
                title='Trade Size by Product Type', color='product_type',
                color_discrete_map={'spot':'#10b981','perp':'#6366f1','option':'#f59e0b'}
            )
            fig.update_layout(height=300, showlegend=False, **CHART_BG)
            st.plotly_chart(fig, width='stretch', key="box_overall")
        
        with c2:
            fig = px.histogram(
                positions_df, x='volume_usd', nbins=30,
                title='Trade Size Histogram',
                color_discrete_sequence=['#6366f1']
            )
            fig.update_layout(height=300, showlegend=False, **CHART_BG)
            st.plotly_chart(fig, width='stretch', key="hist_overall")
        
        vals = positions_df['volume_usd']
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Median", f"${vals.median():,.0f}")
        s2.metric("Mean", f"${vals.mean():,.0f}")
        s3.metric("P25", f"${vals.quantile(0.25):,.0f}")
        s4.metric("P75", f"${vals.quantile(0.75):,.0f}")
        s5.metric("Max", f"${vals.max():,.0f}")
    
    # ==========================================================================
    # TRADE DURATION ANALYSIS 
    # ==========================================================================
    if 'duration_seconds' in positions_df.columns:
        st.subheader("⏱️ Trade Duration Analysis")
        
        # Convert to hours for better readability
        positions_df['duration_hours'] = positions_df['duration_seconds'] / 3600
        
        # Duration metrics
        c1, c2, c3 = st.columns(3)
        
        avg_duration = positions_df['duration_hours'].mean()
        median_duration = positions_df['duration_hours'].median()
        max_duration = positions_df['duration_hours'].max()
        
        c1.metric("Average Duration", f"{avg_duration:.1f}h")
        c2.metric("Median Duration", f"{median_duration:.1f}h")
        c3.metric("Longest Trade", f"{max_duration:.1f}h")
        
        # Duration by product type - box plot
        fig = px.box(
            positions_df,
            x='product_type',
            y='duration_hours',
            points='all',
            title='Trade Duration by Product Type',
            color='product_type',
            color_discrete_map={'spot':'#10b981','perp':'#6366f1','option':'#f59e0b'},
            labels={'duration_hours': 'Duration (hours)', 'product_type': 'Product Type'}
        )
        fig.update_layout(height=300, showlegend=False, **CHART_BG)
        st.plotly_chart(fig, width='stretch', key="duration_box")
        
        # Duration categories for PnL analysis
        def categorize_duration(hours):
            if hours < 1:
                return 'Scalp (<1h)'
            elif hours < 24:
                return 'Intraday (1-24h)'
            elif hours < 168:  # 7 days
                return 'Swing (1-7d)'
            else:
                return 'Position (>7d)'
        
        positions_df['duration_category'] = positions_df['duration_hours'].apply(categorize_duration)
        
        # Calculate statistics by category
        cat_stats = positions_df.groupby('duration_category').agg({
            'realized_pnl': ['count', 'mean', 'sum']
        }).round(2)
        cat_stats.columns = ['Trades', 'Avg PnL', 'Total PnL']
        cat_stats = cat_stats.reset_index()
        
        # Add win rate
        win_rates = positions_df.groupby('duration_category')['realized_pnl'].apply(
            lambda x: (x > 0).mean() * 100
        ).values
        cat_stats['Win Rate'] = win_rates
        
        # Sort categories in logical order
        category_order = ['Scalp (<1h)', 'Intraday (1-24h)', 'Swing (1-7d)', 'Position (>7d)']
        cat_stats['duration_category'] = pd.Categorical(
            cat_stats['duration_category'], 
            categories=category_order, 
            ordered=True
        )
        cat_stats = cat_stats.sort_values('duration_category')
        
        # Bar chart of PnL by duration category
        fig = px.bar(
            cat_stats,
            x='duration_category',
            y='Total PnL',
            text='Trades',
            title='PnL by Trade Duration Category',
            color='Total PnL',
            color_continuous_scale='RdYlGn',
            labels={
                'duration_category': 'Duration Category', 
                'Total PnL': 'Total PnL ($)'
            }
        )
        fig.update_traces(
            texttemplate='%{text} trades', 
            textposition='outside',
            textfont=dict(size=12)
        )
        fig.update_layout(height=300, **CHART_BG)
        st.plotly_chart(fig, width='stretch', key="duration_pnl")
        
        # Optional: Show the detailed table in an expander
        with st.expander("📋 View Duration Category Details"):
            display_df = cat_stats.copy()
            display_df['Avg PnL'] = display_df['Avg PnL'].apply(lambda x: f"${x:,.2f}")
            display_df['Total PnL'] = display_df['Total PnL'].apply(lambda x: f"${x:,.0f}")
            display_df['Win Rate'] = display_df['Win Rate'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                display_df[['duration_category', 'Trades', 'Win Rate', 'Avg PnL', 'Total PnL']],
                width='stretch',
                hide_index=True,
                column_config={
                    "duration_category": "Duration Category",
                    "Trades": "Trade Count",
                    "Win Rate": "Win Rate",
                    "Avg PnL": "Avg PnL",
                    "Total PnL": "Total PnL"
                }
            )
    
    # ==========================================================================
    # PRODUCT TABS 
    # ==========================================================================
    tabs = st.tabs(["📈 All", "📍 Spot", "⚡ Perp", "🎯 Options"])
    products = {
        "All": positions_df,
        "Spot": positions_df[positions_df['product_type'] == 'spot'],
        "Perp": positions_df[positions_df['product_type'] == 'perp'],
        "Options": positions_df[positions_df['product_type'] == 'option']
    }
    
    for tidx, (tab, (pname, pdf)) in enumerate(zip(tabs, products.items())):
        with tab:
            if pdf.empty:
                st.info(f"No {pname} trades in selected period")
                continue
            
            st.caption(f"{len(pdf)} trades")
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("#### Volume by Symbol - Top 5")
                
                sym_vol = pdf.groupby(pdf['market_id'].apply(simplify_symbol)).agg(
                    volume_usd=('volume_usd','sum'),
                    realized_pnl=('realized_pnl','sum')
                ).sort_values('volume_usd', ascending=False).head(5)
                
                if not sym_vol.empty:
                    total = sym_vol['volume_usd'].sum()
                    for sym, row in sym_vol.iterrows():
                        pct = (row['volume_usd'] / total * 100) if total > 0 else 0
                        pc = "#10b981" if row['realized_pnl'] > 0 else "#ef4444"
                        
                        st.markdown(f"""
                        <div style='background:rgba(30,41,59,0.4); border-radius:8px; padding:10px; margin-bottom:8px;'>
                            <div style='display:flex; justify-content:space-between; margin-bottom:4px;'>
                                <span style='color:#94a3b8; font-size:0.85rem;'>{sym}</span>
                                <span style='color:#f1f5f9; font-size:0.9rem; font-weight:600;'>
                                    ${row['volume_usd']:,.0f} ({pct:.1f}%)
                                    <span style='color:{pc};'>${row['realized_pnl']:,.0f}</span>
                                </span>
                            </div>
                            <div style='background:rgba(100,116,139,0.3); border-radius:4px; height:6px;'>
                                <div style='background:#6366f1; width:{pct}%; height:100%; border-radius:4px;'></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("#### Fee Generation")
                fsym = pdf.groupby(pdf['market_id'].apply(simplify_symbol))['fees'].sum()\
                    .sort_values(ascending=False).head(5)
                
                if not fsym.empty:
                    fig = px.bar(x=fsym.values, y=fsym.index, orientation='h',
                                title='Top 5 Symbols by Fees',
                                color=fsym.values, color_continuous_scale='Reds')
                    fig.update_layout(height=200, **CHART_BG, margin=dict(l=80))
                    st.plotly_chart(fig, width='stretch', key=f"fee_{tidx}")
            
            with c2:
                st.markdown("#### Long vs Short Distribution")
                
                long_vol = pdf[pdf['side'].str.lower().isin(['long','buy'])]['volume_usd'].sum()
                short_vol = pdf[pdf['side'].str.lower().isin(['short','sell'])]['volume_usd'].sum()
                total_v = long_vol + short_vol
                
                if total_v > 0:
                    lp, sp = long_vol/total_v*100, short_vol/total_v*100
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        y=['Direction'], x=[lp], name='Long', orientation='h',
                        marker_color='#10b981', text=f'{lp:.1f}%',
                        textposition='inside', textfont=dict(color='white', size=14)
                    ))
                    fig.add_trace(go.Bar(
                        y=['Direction'], x=[sp], name='Short', orientation='h',
                        marker_color='#ef4444', text=f'{sp:.1f}%',
                        textposition='inside', textfont=dict(color='white', size=14)
                    ))
                    
                    fig.update_layout(
                        barmode='stack', height=100,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=40, r=20, t=30, b=10), **CHART_BG
                    )
                    st.plotly_chart(fig, width='stretch', key=f"ls_{tidx}")
                    
                    ratio = long_vol / short_vol if short_vol > 0 else float('inf')
                    st.metric("Long/Short Ratio", f"{ratio:.2f}x" if ratio != float('inf') else "(No shorts)")
                
                st.markdown("#### PnL Distribution")
                
                if should_show_chart(pdf, min_points=3):
                    fig = px.histogram(pdf, x='realized_pnl', nbins=20,
                                      title='PnL Distribution',
                                      color_discrete_sequence=['#6366f1'])
                    fig.add_vline(x=0, line_dash="dash", line_color="gray")
                    fig.update_layout(height=250, **CHART_BG)
                    st.plotly_chart(fig, width='stretch', key=f"pnl_hist_{tidx}")
                else:
                    context_note("Too few trades for distribution chart - showing individual trades")
                    st.dataframe(
                        pdf[['market_id','side','realized_pnl']].assign(
                            market_id=pdf['market_id'].apply(simplify_symbol),
                            realized_pnl=pdf['realized_pnl'].apply(lambda x: f"${x:,.2f}")
                        ),
                        width='stretch', hide_index=True, key=f"pnl_list_{tidx}"
                    )
                    
# ============================================================================
# ORDER TYPE PERFORMANCE
# ============================================================================

def display_order_type_performance(order_df, positions_df=None):
    """Enhanced order type performance with multiple visualizations."""
    
    st.header("📊 Order Type Performance Analysis")
    
    # Check if we have any positions data
    if positions_df is None or positions_df.empty:
        st.info("ℹ️ No trades in the selected period to analyze order types")
        return
     
    # Get symbol filter state from session
    has_symbol_filter = False
    if 'selected_symbols' in st.session_state:
        has_symbol_filter = len(st.session_state.selected_symbols) > 0
    
    # SPARSE DATA DETECTION - Check if we should show simplified view
    is_sparse_mode = False
    sparse_reason = ""
    
    if positions_df is not None and not positions_df.empty:
        trade_count = len(positions_df)
        
        # Very few trades overall
        if trade_count < 3:
            is_sparse_mode = True
            sparse_reason = "Very few trades available"
        # Symbol filter with few trades
        elif has_symbol_filter and trade_count < 8:
            is_sparse_mode = True
            symbol_text = f"for selected symbol{'s' if len(st.session_state.selected_symbols) > 1 else ''}"
            sparse_reason = f"Limited data {symbol_text}"
        # Date range with few trades
        elif 'start_date' in st.session_state and 'end_date' in st.session_state:
            days_selected = (st.session_state.end_date - st.session_state.start_date).days
            if days_selected <= 7 and trade_count < 10:
                is_sparse_mode = True
                sparse_reason = "Limited data for selected period"
    
    # If sparse mode, show simplified card view
    if is_sparse_mode and positions_df is not None and not positions_df.empty:
        context_note(f"{sparse_reason} - showing individual trade breakdown")
        
        # Prepare data for display
        display_df = positions_df.copy()
        display_df['symbol'] = display_df['market_id'].apply(simplify_symbol)
        display_df = display_df[['close_time', 'symbol', 'product_type', 'side', 
                                 'entry_price', 'exit_price', 'size', 'realized_pnl', 'fees']]
        
        # Format for display
        display_df['close_time'] = pd.to_datetime(display_df['close_time']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"${x:,.2f}")
        display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"${x:,.2f}")
        display_df['size'] = display_df['size'].apply(lambda x: f"{x:,.4f}")
        display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
        display_df['fees'] = display_df['fees'].apply(lambda x: f"${x:,.2f}")
        
        st.subheader("📋 Individual Trades by Type")
        st.dataframe(display_df, width='stretch', hide_index=True)
        
        # Show summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Trades", len(positions_df))
        with col2:
            win_rate = (positions_df['realized_pnl'] > 0).mean() * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col3:
            total_pnl = positions_df['realized_pnl'].sum()
            st.metric("Total PnL", f"${total_pnl:,.2f}")
        with col4:
            product_types = positions_df['product_type'].nunique()
            st.metric("Product Types", product_types)
        
        return
    
    # NORMAL MODE - Full analysis
    # ALWAYS derive from positions_df if available
    if positions_df is not None and not positions_df.empty:
        df = positions_df.copy()
        
        if 'volume_usd' not in df.columns:
            df['volume_usd'] = df['exit_price'] * df['size']
        
        if 'product_type' in df.columns:
            df['order_category'] = df['product_type']
            category_name = "Product Type"
            product_counts = df['product_type'].value_counts()
            st.caption(f"📊 Distribution: {', '.join([f'{k}({v})' for k, v in product_counts.items()])}")
        else:
            df['order_category'] = df.apply(lambda row: 
                'scalp' if row.get('duration_seconds', 0) < 300 else
                'intraday' if row.get('duration_seconds', 0) < 3600 else
                'swing' if row.get('duration_seconds', 0) < 86400 else
                'position', axis=1
            )
            category_name = "Trade Duration"
        
        # Calculate metrics
        order_stats = df.groupby('order_category').agg({
            'realized_pnl': ['count', 'mean', 'sum'],
            'fees': 'sum',
            'volume_usd': 'sum'
        }).round(2)
        
        order_stats.columns = ['trade_count', 'avg_pnl', 'total_pnl', 'total_fees', 'total_volume']
        order_stats = order_stats.reset_index()
        
        order_stats['win_rate'] = df.groupby('order_category')['realized_pnl'].apply(
            lambda x: (x > 0).mean() * 100
        ).values
        
        order_stats['fee_ratio'] = (order_stats['total_fees'] / order_stats['total_volume'] * 100).fillna(0)
        order_stats.rename(columns={'order_category': 'order_type'}, inplace=True)
        
        st.info(f"📌 Classified by: **{category_name}**")
        order_df = order_stats
    
    # SAFETY CHECK - if still no data or missing columns
    if order_df is None or order_df.empty:
        st.warning("⚠️ No order type data available for selected filters.")
        st.info("💡 Try selecting a wider date range or different symbols.")
        return
    
    # Ensure required columns exist
    required_cols = ['order_type', 'trade_count', 'win_rate', 'avg_pnl']
    missing_cols = [col for col in required_cols if col not in order_df.columns]
    
    if missing_cols:
        st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
        st.info("💡 This usually happens when the date filter excludes all trades.")
        return
    
    # Add total_pnl 
    if 'total_pnl' not in order_df.columns:
        order_df['total_pnl'] = order_df['avg_pnl'] * order_df['trade_count']
    
    # Add volume/fee columns 
    if 'total_volume' not in order_df.columns:
        order_df['total_volume'] = 0
    if 'total_fees' not in order_df.columns:
        order_df['total_fees'] = 0
    if 'fee_ratio' not in order_df.columns:
        order_df['fee_ratio'] = 0
           
    # Create four columns for key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_trades = order_df['trade_count'].sum()
    avg_win_rate = order_df['win_rate'].mean()
    best_order = order_df.loc[order_df['win_rate'].idxmax(), 'order_type']
    worst_order = order_df.loc[order_df['win_rate'].idxmin(), 'order_type']
    
    col1.metric("Total Orders", f"{total_trades}")
    col2.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")
    col3.metric("Best Performer", best_order.upper())
    col4.metric("Worst Performer", worst_order.upper())
    
    # Tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Performance Matrix", 
        "📈 Win Rate Analysis", 
        "💰 PnL Breakdown",
        "📋 Detailed Table"
    ])
    
    with tab1:
        # Performance Matrix - Bubble chart
        fig = px.scatter(
            order_df,
            x='win_rate',
            y='avg_pnl',
            size='trade_count',
            color='order_type',
            text='order_type',
            title="Order Type Performance Matrix",
            labels={
                'win_rate': 'Win Rate (%)',
                'avg_pnl': 'Average PnL ($)',
                'trade_count': 'Number of Trades'
            },
            size_max=60,
            color_discrete_map={
                'spot': '#10b981',
                'perp': '#6366f1',
                'option': '#f59e0b'
            }
        )
        
        fig.update_traces(
            textposition='top center',
            textfont=dict(size=12, color='white')
        )
        
        # Add quadrant lines
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Annotate quadrants
        fig.add_annotation(
            x=75, 
            y=order_df['avg_pnl'].max() * 0.8, 
            text="🌟 STAR PERFORMERS", 
            showarrow=False,
            font=dict(color="#10b981", size=14)
        )
        fig.add_annotation(
            x=25, 
            y=order_df['avg_pnl'].min() * 0.8, 
            text="⚠️ NEEDS REVIEW", 
            showarrow=False,
            font=dict(color="#ef4444", size=14)
        )
        
        fig.update_layout(height=500, **CHART_BG)
        st.plotly_chart(fig, width='stretch', key="order_matrix")
        
        # Add explanation
        with st.expander("📖 How to read this chart"):
            st.markdown("""
            - **Top Right Quadrant** 🌟: High win rate + positive PnL (Best performers)
            - **Top Left Quadrant** 📈: Low win rate but positive PnL (Few big wins)
            - **Bottom Right Quadrant** 📉: High win rate but negative PnL (Many small losses)
            - **Bottom Left Quadrant** ⚠️: Low win rate + negative PnL (Needs review)
            
            Bubble size = Number of trades
            """)
    
    with tab2:
        # Win Rate Analysis - Horizontal bar chart with risk coloring
        df_sorted = order_df.sort_values('win_rate', ascending=True)
        
        colors = []
        for rate in df_sorted['win_rate']:
            if rate >= 60:
                colors.append('#10b981')  # Green - Good
            elif rate >= 40:
                colors.append('#f59e0b')  # Orange - Medium
            else:
                colors.append('#ef4444')  # Red - Poor
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_sorted['order_type'],
            x=df_sorted['win_rate'],
            orientation='h',
            marker_color=colors,
            text=df_sorted['win_rate'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Win Rate: %{x:.1f}%<br>Trades: %{customdata}<extra></extra>',
            customdata=df_sorted['trade_count']
        ))
        
        fig.add_vline(
            x=50, 
            line_dash="dash", 
            line_color="gray", 
            annotation_text="50% Benchmark", 
            annotation_position="top"
        )
        
        fig.update_layout(
            title="Win Rate by Product Type",
            xaxis_title="Win Rate (%)",
            yaxis_title="",
            height=300,
            margin=dict(l=100, r=40, t=50, b=40),
            **CHART_BG
        )
        fig.update_xaxes(range=[0, 100])
        
        st.plotly_chart(fig, width='stretch', key="order_winrate")
        
        # Win rate confidence intervals
        st.subheader("📊 Statistical Confidence")
        
        for _, row in order_df.iterrows():
            trades = row['trade_count']
            win_rate = row['win_rate'] / 100
            
            # Calculate confidence interval (simplified)
            if trades > 0:
                std_error = np.sqrt(win_rate * (1 - win_rate) / trades)
                ci_lower = max(0, (win_rate - 1.96 * std_error) * 100)
                ci_upper = min(100, (win_rate + 1.96 * std_error) * 100)
                
                st.markdown(f"""
                <div style='background:rgba(30,41,59,0.4); padding:10px; border-radius:8px; margin-bottom:8px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#94a3b8;'><b>{row['order_type'].upper()}</b></span>
                        <span style='color:#f1f5f9;'>{row['trade_count']} trades</span>
                    </div>
                    <div style='margin-top:5px;'>
                        <div style='background:#1e293b; height:20px; border-radius:10px; position:relative;'>
                            <div style='background:#6366f1; width:{win_rate*100}%; height:20px; border-radius:10px;'></div>
                        </div>
                        <div style='display:flex; justify-content:space-between; margin-top:3px;'>
                            <span style='color:#94a3b8;'>95% CI: {ci_lower:.1f}% - {ci_upper:.1f}%</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with tab3:
        # PnL Breakdown - Dual axis chart
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Bar chart for total PnL
        fig.add_trace(
            go.Bar(
                x=order_df['order_type'],
                y=order_df['total_pnl'],
                name='Total PnL',
                marker_color='#6366f1',
                text=order_df['total_pnl'].apply(lambda x: f"${x:,.0f}"),
                textposition='outside',
            ),
            secondary_y=False,
        )
        
        # Line chart for avg PnL
        colors = ['#10b981' if x > 0 else '#ef4444' for x in order_df['avg_pnl']]
        
        fig.add_trace(
            go.Scatter(
                x=order_df['order_type'],
                y=order_df['avg_pnl'],
                name='Avg PnL',
                mode='lines+markers',
                line=dict(color='#f1f5f9', width=3),
                marker=dict(size=12, color=colors),
                text=order_df['avg_pnl'].apply(lambda x: f"${x:,.0f}"),
                textposition='top center',
            ),
            secondary_y=True,
        )
        
        fig.update_layout(
            title="PnL Analysis by Product Type",
            xaxis_title="Product Type",
            hovermode='x unified',
            height=400,
            **CHART_BG,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_yaxes(title_text="Total PnL ($)", secondary_y=False)
        fig.update_yaxes(title_text="Average PnL ($)", secondary_y=True)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=True)
        
        st.plotly_chart(fig, width='stretch', key="order_pnl")
        
        # Fee analysis
        if 'total_fees' in order_df.columns and 'total_volume' in order_df.columns:
            st.subheader("💰 Fee Efficiency")
            
            fig = px.bar(
                order_df,
                x='order_type',
                y='fee_ratio',
                title='Fee Ratio by Product Type (% of Volume)',
                color='fee_ratio',
                color_continuous_scale='Reds',
                text=order_df['fee_ratio'].apply(lambda x: f"{x:.2f}%"),
                labels={'order_type': 'Product Type', 'fee_ratio': 'Fee Ratio (%)'}
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(height=300, **CHART_BG)
            st.plotly_chart(fig, width='stretch', key="order_fees")
            
            st.caption("💰 Lower fee ratio means more cost-efficient trading")
    
    with tab4:
        # Detailed table
        st.subheader("📋 Detailed Statistics")
        
        display_df = order_df.copy()
        display_df['win_rate'] = display_df['win_rate'].apply(lambda x: f"{x:.1f}%")
        display_df['avg_pnl'] = display_df['avg_pnl'].apply(lambda x: f"${x:,.2f}")
        display_df['total_pnl'] = display_df['total_pnl'].apply(lambda x: f"${x:,.2f}")
        display_df['total_fees'] = display_df['total_fees'].apply(lambda x: f"${x:,.2f}")
        display_df['total_volume'] = display_df['total_volume'].apply(lambda x: f"${x:,.0f}")
        display_df['fee_ratio'] = display_df['fee_ratio'].apply(lambda x: f"{x:.2f}%")
        
        column_order = ['order_type', 'trade_count', 'win_rate', 'avg_pnl', 
                       'total_pnl', 'total_volume', 'total_fees', 'fee_ratio']
        
        st.dataframe(
            display_df[column_order], 
            width='stretch', 
            hide_index=True,
            column_config={
                "order_type": "Product Type",
                "trade_count": "Trades",
                "win_rate": "Win Rate",
                "avg_pnl": "Avg PnL",
                "total_pnl": "Total PnL",
                "total_volume": "Volume",
                "total_fees": "Fees",
                "fee_ratio": "Fee %"
            }
        )
        
        csv = order_df.to_csv(index=False)
        st.download_button(
            "📥 Download Order Data",
            csv,
            f"order_analysis_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )
        
# ============================================================================
# GREEKS ANALYSIS
# ============================================================================
# ============================================================================
# GREEKS ANALYSIS - USING PRE-CALCULATED DATA FROM ANALYTICS BUILDER
# ============================================================================

def extract_strike_from_market_id(market_id):
    """Extract strike price from market_id string for display purposes only."""
    import re
    match = re.search(r'(?:CALL|PUT)-(\d+)', str(market_id))
    return float(match.group(1)) if match else None

def extract_option_type_from_market_id(market_id):
    """Extract option type (call/put) from market_id string for display purposes only."""
    if 'CALL' in str(market_id).upper():
        return 'call'
    elif 'PUT' in str(market_id).upper():
        return 'put'
    return None

# ============================================================================
# GREEKS ANALYSIS 
# ============================================================================
# ============================================================================
# GREEKS ANALYSIS - FIXED VERSION (NO position_id ASSUMPTION)
# ============================================================================

def display_greeks_analysis(greeks_df, positions_df, is_personal=False):
    """Greeks analysis with adaptive filtering across date, symbol, and personal mode."""
    
    st.header("🔬 Options Greeks Exposure")
    
    # Get filter states from session
    has_symbol_filter = False
    if 'selected_symbols' in st.session_state:
        has_symbol_filter = len(st.session_state.selected_symbols) > 0
    
    # Check if we have any option positions in the filtered data
    if positions_df is not None and not positions_df.empty:
        option_positions = positions_df[positions_df['product_type'] == 'option'].copy()
        
        if option_positions.empty:
            st.info("No options positions match the current filters")
            return
        
        # Fix date parsing for display
        option_positions['close_time'] = pd.to_datetime(option_positions['close_time'])
        
        # Extract display fields from market_id
        option_positions['symbol'] = option_positions['market_id'].apply(simplify_symbol)
        option_positions['strike'] = option_positions['market_id'].apply(
            lambda x: re.search(r'(?:CALL|PUT)-(\d+)', str(x)).group(1) if re.search(r'(?:CALL|PUT)-(\d+)', str(x)) else None
        )
        option_positions['option_type'] = option_positions['market_id'].apply(
            lambda x: 'call' if 'CALL' in str(x).upper() else 'put' if 'PUT' in str(x).upper() else None
        )
        
        # Store for display
        st.session_state.filtered_option_positions = option_positions
        
        # Get unique traders from filtered options
        filtered_traders = option_positions['trader_id'].unique()
    else:
        st.info("No options data available for current filters")
        return
    
    # Filter the pre-calculated Greeks data to match current filters
    if not greeks_df.empty:
        # Filter Greeks by traders who appear in filtered options
        filtered_greeks = greeks_df[greeks_df['trader_id'].isin(filtered_traders)].copy()
        
        if filtered_greeks.empty:
            st.info("No pre-calculated Greeks data for filtered options")
            # Fall back to showing just positions without Greeks
            show_positions_only(option_positions)
            return
    else:
        st.info("No pre-calculated Greeks data available. Run analytics builder first.")
        show_positions_only(option_positions)
        return
    
    # IMPROVED SPARSE DATA DETECTION
    trade_count = len(option_positions)
    is_sparse_mode = False
    sparse_reason = ""
    
    # Only trigger sparse mode for VERY few options
    if trade_count < 3:
        is_sparse_mode = True
        sparse_reason = "Very few options trades"
    elif has_symbol_filter and trade_count < 3:
        is_sparse_mode = True
        symbol_text = f"for selected symbol{'s' if len(st.session_state.selected_symbols) > 1 else ''}"
        sparse_reason = f"Limited options data {symbol_text}"
    
    if is_sparse_mode:
        st.info(f"ℹ️ {sparse_reason} - showing per-position breakdown")
        
        # Format display without trying to merge per-position delta
        display_df = option_positions[['close_time', 'symbol', 'side', 'size', 
                                      'strike', 'option_type', 'underlying_price', 
                                      'realized_pnl']].copy()
        
        display_df['close_time'] = pd.to_datetime(display_df['close_time']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
        display_df['underlying_price'] = display_df['underlying_price'].apply(lambda x: f"${x:,.2f}")
        
        st.subheader("📋 Individual Option Positions")
        st.dataframe(display_df, width='stretch', hide_index=True)
        
        # Show simple totals from filtered data
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Options", len(option_positions))
        with col2:
            st.metric("Net Delta", f"{filtered_greeks['net_delta'].sum():.2f}" if 'net_delta' in filtered_greeks.columns else "N/A")
        with col3:
            total_pnl = option_positions['realized_pnl'].sum()
            st.metric("Options PnL", f"${total_pnl:,.2f}")
        return
    
    # NORMAL MODE - Full Greeks analysis using pre-calculated data
    total_delta_exposure = filtered_greeks['net_delta'].sum() if 'net_delta' in filtered_greeks.columns else 0
    total_pos = len(option_positions)
    
    # Show filter context
    if has_symbol_filter:
        st.caption(f"📊 Showing Greeks for selected symbol{'s' if len(st.session_state.selected_symbols) > 1 else ''}")
    if is_personal:
        st.caption(f"👤 Showing Greeks for your positions only")
    
    # Metrics cards using pre-calculated data
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Net Delta Exposure", f"{total_delta_exposure:,.2f}")
    with c2:
        gamma_value = filtered_greeks['gamma'].sum() if 'gamma' in filtered_greeks.columns else 0
        st.metric("Gamma", f"{gamma_value:,.4f}" if 'gamma' in filtered_greeks.columns else "N/A")
    with c3:
        theta_value = filtered_greeks['theta'].sum() if 'theta' in filtered_greeks.columns else 0
        st.metric("Theta", f"${theta_value:,.2f}" if 'theta' in filtered_greeks.columns else "N/A")
    with c4:
        st.metric("Positions", f"{int(total_pos)}")
    
    # Show option positions WITHOUT trying to merge per-position delta
    st.subheader("📊 Option Positions")
    
    display_df = option_positions[['close_time', 'symbol', 'side', 'size', 
                                  'strike', 'option_type', 'underlying_price', 
                                  'realized_pnl']].copy()
    
    display_df['close_time'] = pd.to_datetime(display_df['close_time']).dt.strftime('%Y-%m-%d %H:%M')
    display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
    display_df['underlying_price'] = display_df['underlying_price'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    st.caption(f"Note: Net delta exposure = {total_delta_exposure:,.2f} (sum of delta × size)")
    
    # MULTI-TRADER VIEW - Fixed aggregation without position_id
    if not is_personal and len(filtered_traders) > 1:
        st.subheader("📊 Delta Exposure by Trader")
        
        # Safely aggregate based on what columns exist
        agg_dict = {'net_delta': 'sum'}
        
        # Add position count if we have a way to count
        if 'trader_id' in filtered_greeks.columns:
            # Count rows per trader as position count proxy
            trader_exposure = filtered_greeks.groupby('trader_id').agg({
                'net_delta': 'sum',
                'trader_id': 'count'  # This counts rows per trader
            }).rename(columns={'trader_id': 'position_count'}).reset_index()
        else:
            trader_exposure = filtered_greeks.groupby('trader_id').agg({
                'net_delta': 'sum'
            }).reset_index()
            trader_exposure['position_count'] = 0
        
        trader_exposure['trader'] = trader_exposure['trader_id'].apply(mask_trader_id)
        trader_exposure = trader_exposure.sort_values('net_delta', ascending=False)
        
        # Limit to top 10 traders
        if len(trader_exposure) > 10:
            st.info("Showing top 10 traders by delta exposure")
            display_trader = trader_exposure.head(10)
        else:
            display_trader = trader_exposure
        
        # Bar chart
        fig = px.bar(display_trader, x='trader', y='net_delta', color='net_delta',
                    color_continuous_scale='RdBu', color_continuous_midpoint=0,
                    title='Net Delta Exposure by Trader (delta × size)',
                    labels={'net_delta': 'Net Exposure', 'trader': 'Trader'})
        fig.update_layout(height=400, **CHART_BG)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, width='stretch', key="delta_bar_multi")
        
        # Simple table
        st.subheader("📋 Greeks Breakdown by Trader")
        st.dataframe(
            display_trader[['trader', 'position_count', 'net_delta']].style.format({
                'net_delta': '{:,.2f}',
                'position_count': '{:.0f}'
            }),
            width='stretch', hide_index=True
        )

def show_positions_only(option_positions):
    """Helper function to show positions when no Greeks data is available."""
    st.subheader("📋 Option Positions (No Greeks Data)")
    
    display_df = option_positions[['close_time', 'symbol', 'side', 'size', 
                                  'strike', 'option_type', 'underlying_price', 
                                  'realized_pnl']].copy()
    display_df['close_time'] = pd.to_datetime(display_df['close_time']).dt.strftime('%Y-%m-%d %H:%M')
    display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
    display_df['underlying_price'] = display_df['underlying_price'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Options", len(option_positions))
    with col2:
        st.metric("Unique Traders", option_positions['trader_id'].nunique())
    with col3:
        total_pnl = option_positions['realized_pnl'].sum()
        st.metric("Options PnL", f"${total_pnl:,.2f}")
        
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Options", len(option_positions))
    with col2:
        st.metric("Unique Traders", option_positions['trader_id'].nunique())
    with col3:
        total_pnl = option_positions['realized_pnl'].sum()
        st.metric("Options PnL", f"${total_pnl:,.2f}")

def show_positions_only(option_positions):
    """Helper function to show positions when no Greeks data is available."""
    st.subheader("📋 Option Positions (No Greeks Data)")
    
    display_df = option_positions[['close_time', 'symbol', 'side', 'size', 
                                  'strike', 'option_type', 'underlying_price', 
                                  'realized_pnl']].copy()
    display_df['close_time'] = pd.to_datetime(display_df['close_time']).dt.strftime('%Y-%m-%d %H:%M')
    display_df['realized_pnl'] = display_df['realized_pnl'].apply(lambda x: f"${x:,.2f}")
    display_df['underlying_price'] = display_df['underlying_price'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Options", len(option_positions))
    with col2:
        st.metric("Unique Traders", option_positions['trader_id'].nunique())
    with col3:
        total_pnl = option_positions['realized_pnl'].sum()
        st.metric("Options PnL", f"${total_pnl:,.2f}")

    
# ============================================================================
# TRANSACTION HISTORY
# ============================================================================

def display_transaction_history(positions_df):
    """Transaction history with pagination and blockchain verify links ahead of real injection."""
    
    st.markdown("### 📋 Transaction History")
    
    # Add info about expired options
    if not positions_df.empty and 'close_reason' in positions_df.columns:
        if (positions_df['close_reason'] == 'expire').any():
            st.info("ℹ️ **Expired Options:** When options expire worthless, exit price = $0, so volume = $0. The PnL shows the premium paid + fees.")
    
    if positions_df.empty:
        st.info("No transactions to display")
        return
           
    df = positions_df.copy()
    
    df['symbol'] = df['market_id'].apply(simplify_symbol)
    df['trader'] = df['trader_id'].apply(mask_trader_id)
    df['volume_usd'] = df['exit_price'] * df['size']
    
    df = df.sort_values('close_time', ascending=False)
    
    page_size = 10
    total_pages = max(1, (len(df) - 1) // page_size + 1)
    page = st.number_input("Page", 1, total_pages, 1, key="tx_page")
    
    start = (page - 1) * page_size
    end = min(page * page_size, len(df))
    ddf = df.iloc[start:end].copy()
    
    ddf['close_time'] = pd.to_datetime(ddf['close_time']).dt.strftime('%Y-%m-%d %H:%M')
    ddf['entry_price'] = ddf['entry_price'].apply(lambda x: f"${x:,.2f}")
    ddf['exit_price'] = ddf['exit_price'].apply(lambda x: f"${x:,.2f}")
    ddf['size'] = ddf['size'].apply(lambda x: f"{x:,.4f}")
    ddf['volume_usd'] = ddf['volume_usd'].apply(lambda x: f"${x:,.0f}")
    ddf['realized_pnl'] = ddf['realized_pnl'].apply(lambda x: f"${x:,.2f}")
    ddf['fees'] = ddf['fees'].apply(lambda x: f"${x:,.2f}")
    
    cols = ['close_time','trader','symbol','product_type','side',
            'entry_price','exit_price','size','volume_usd','realized_pnl','fees','close_reason']
    
    if 'close_tx_hash' in ddf.columns:
        ddf['Verify'] = ddf['close_tx_hash'].apply(
            lambda tx: f'<a href="https://solscan.io/tx/{tx}" target="_blank" class="verify-link">🔗 Verify</a>'
            if pd.notna(tx) and str(tx).strip() else '—'
        )
        cols.append('Verify')
    
    def color_pnl(val):
        if isinstance(val, str):
            if '$-' in val:
                return 'color: #ef4444; font-weight: bold;'
            elif '$' in val and val != '$0.00':
                return 'color: #10b981; font-weight: bold;'
        return ''
    
    html = '<div style="overflow-x: auto; margin: 10px 0;"><table class="tx-table">'
    html += '<thead><tr>'
    for col in cols:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    
    for _, row in ddf[cols].iterrows():
        html += '<tr>'
        for col in cols:
            cell = str(row[col])
            style = color_pnl(cell) if col == 'realized_pnl' else ''
            html += f'<td style="{style}">{cell}</td>'
        html += '</tr>'
    
    html += '</tbody></table></div>'
    
    st.markdown(html, unsafe_allow_html=True)
    st.caption(f"Showing {start+1}–{end} of {len(df)} transactions")
    
    csv = positions_df.to_csv(index=False)
    st.download_button(
        "📥 Download CSV", csv,
        f"transactions_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv"
    )

# ============================================================================
# GLOBAL KPIs 
# ============================================================================

def compute_ratios(positions_df):
    """Calculate Sharpe and Sortino from actual filtered positions."""
    if positions_df.empty or len(positions_df) < 2:
        return 0, 0
    returns = positions_df['realized_pnl'].values
    mean_r = returns.mean()
    std_r = returns.std()
    sharpe = round(mean_r / std_r, 2) if std_r > 0 else 0
    downside = returns[returns < 0]
    sortino = round(mean_r / downside.std(), 2) if len(downside) > 1 and downside.std() > 0 else 0
    return sharpe, sortino

def display_sidebar_kpis(closed_positions, selected_trader=None, is_personal_mode=False):
    if is_personal_mode and selected_trader:
        pos = closed_positions[closed_positions['trader_id'] == selected_trader]
        label = "YOUR PERFORMANCE"
    else:
        pos = closed_positions
        label = "PROTOCOL PERFORMANCE"

    if not pos.empty and 'position_id' in pos.columns:
        pos = pos.drop_duplicates(subset=['position_id'])

    total_pnl  = pos['realized_pnl'].sum() if not pos.empty else 0
    win_rate   = (pos['realized_pnl'] > 0).mean() * 100 if not pos.empty else 0
    trade_count = len(pos)
    total_fees = pos['fees'].sum() if not pos.empty and 'fees' in pos.columns else 0
    pnl_color  = "#10b981" if total_pnl >= 0 else "#ef4444"

    st.sidebar.markdown(
        f"<div style='text-align:center;color:#6366f1;font-size:0.68rem;"
        f"font-weight:700;letter-spacing:0.08em;margin:8px 0 6px;'>{label}</div>",
        unsafe_allow_html=True
    )

    kpi_data = [
        ("NET PNL",    f"${total_pnl:,.2f}",  pnl_color),
        ("WIN RATE",   f"{win_rate:.1f}%",     "#f1f5f9"),
        ("TRADES",     str(trade_count),        "#f1f5f9"),
        ("TOTAL FEES", f"${total_fees:,.2f}",  "#f59e0b"),
    ]

    for i in range(0, len(kpi_data), 2):
        cols = st.sidebar.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(kpi_data):
                lbl, val, color = kpi_data[i + j]
                col.markdown(
                    f"<div class='sidebar-kpi'>"
                    f"<div class='sidebar-kpi-label'>{lbl}</div>"
                    f"<div class='sidebar-kpi-value' style='color:{color};'>{val}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_logo(url):
    """Load Deriverse logo."""
    try:
        r = requests.get(url, timeout=5)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None

@st.cache_data
def load_data():
    """Load all analytics data."""
    try:
        return {
            'equity': pd.read_csv(DATA_DIR / "equity_curve.csv", parse_dates=["timestamp"]),
            'positions': pd.read_csv(DATA_DIR / "positions.csv", parse_dates=["open_time","close_time"]),
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

# Load data
with st.spinner('🔄 Loading analytics...'):
    data = load_data()

if data is None or (data['positions'].empty and data['open_positions'].empty):
    st.error("❌ No analytics data found")
    st.info("💡 Run: `python -m scripts.run_analytics`")
    st.stop()

# ============================================================================
# INITIALIZE ADMIN STATE - HIDDEN FROM REGULAR USERS
# ============================================================================

# Check URL for admin activation
if check_url_for_admin():
    st.session_state.show_admin = True

# Initialize admin states
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

is_admin = st.session_state.admin_authenticated

# ============================================================================
# SIDEBAR — Brand + KPIs + Tab Nav + Filters 
# ============================================================================

logo_url = ("https://deriverse.gitbook.io/deriverse-v1/~gitbook/image"
            "?url=https%3A%2F%2F3705106568-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com"
            "%2Fo%2Forganizations%252FVbKUpgicSXo9QHWM7uzI%252Fsites%252Fsite_oPxtF%252Ficon%252FNsfAUtLJH778Cn5Dd7zK"
            "%252Ffavicon.ico%3Falt%3Dmedia%26token%3D4099bf73-ccd6-4d9f-8bbb-01cdc664ddb0"
            "&width=32&dpr=3&quality=100&sign=13d31bb2&sv=2")

logo_bytes = load_logo(logo_url)

# ── Sticky Brand header in sidebar ──
with st.sidebar:
    # Sticky header container
    st.markdown('<div class="sidebar-sticky-header">', unsafe_allow_html=True)
    
    # Brand header
    sb_logo, sb_title = st.columns([1, 3])
    with sb_logo:
        if logo_bytes:
            st.image(logo_bytes, width=48)
        else:
            st.markdown("### 🔷")
    with sb_title:
        st.markdown(
            "<div style='padding-top:4px;'>"
            "<div style='font-size:1.2rem;font-weight:700;color:#f1f5f9;'>Deriverse</div>"
            "<div style='font-size:0.85rem;color:#94a3b8;'>Trading Analytics</div>"
            "</div>",
            unsafe_allow_html=True
        )
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close sticky header
    
    # Scrollable content container
    st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)
    
    st.markdown("---")

    # ============================================================================
    # TRADER ACCESS 
    # ============================================================================

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
            key="wallet_address_input_sidebar_unique"  # Unique key
        )
        
        if st.sidebar.button("🔑 Enter Personal Dashboard", key="enter_personal_btn_sidebar_unique"):  # Unique key
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
            st.sidebar.success(f"✅ **Personal Mode:** {mask_trader_id(st.session_state.authenticated_trader)}")
            if st.sidebar.button("👥 Return to All Traders View", key="return_to_all_traders_btn_sidebar_unique"):  # Unique key
                st.session_state.view_mode = "all_traders"
                st.rerun()

    st.sidebar.markdown("---")

    # ============================================================================
    # FILTERS - Admin features only visible when authenticated
    # ============================================================================

    st.sidebar.header("🎛️ Filters")
    st.sidebar.markdown("**📅 Date Range**")

    # Regular users see limited options
    if is_admin:
        date_option = st.sidebar.radio(
            "Range",
            ["Last 7 Days", "Last 30 Days", "All Time", "Custom"],
            index=1, horizontal=True, label_visibility="collapsed",
            key="date_range_radio_admin_sidebar_unique"  # Unique key
        )
    else:
        date_option = st.sidebar.radio(
            "Range",
            ["Last 7 Days", "Last 30 Days"],
            index=1, horizontal=True, label_visibility="collapsed",
            key="date_range_radio_user_sidebar_unique"  # Unique key
        )

    from datetime import date

    if not data['positions'].empty:
        min_date = data['positions']['close_time'].min().date()
        max_date = data['positions']['close_time'].max().date()
        today = date.today()

        if date_option == "Last 7 Days":
            start_date, end_date = today - timedelta(7), today
        elif date_option == "Last 30 Days":
            start_date, end_date = today - timedelta(30), today
        elif date_option == "All Time" and is_admin:
            start_date, end_date = min_date, max_date
        elif date_option == "Custom" and is_admin:
            sc1, sc2 = st.sidebar.columns(2)
            start_date = sc1.date_input("From", min_date, min_value=min_date, max_value=max_date, key="date_from_sidebar_unique")  # Unique key
            end_date = sc2.date_input("To", max_date, min_value=min_date, max_value=max_date, key="date_to_sidebar_unique")  # Unique key
        else:
            start_date, end_date = today - timedelta(30), today

    all_markets = sorted(data['positions']['market_id'].unique()) if not data['positions'].empty else []
    unique_symbols = sorted(set(simplify_symbol(m) for m in all_markets))
    selected_symbols = st.sidebar.multiselect("Symbols", unique_symbols, default=[], key="symbols_multiselect_sidebar_unique")  # Unique key
    selected_markets = [m for m in all_markets if simplify_symbol(m) in selected_symbols] if selected_symbols else []

    st.sidebar.markdown("---")

    # ============================================================================
    # ADMIN ACCESS - COMPLETELY HIDDEN FROM REGULAR USERS
    # ============================================================================

    # Initialize admin attempts if not exists
    if "admin_attempts" not in st.session_state:
        st.session_state.admin_attempts = 0

    # Only show admin section if activated via URL
    if st.session_state.show_admin:
        st.sidebar.header("🔐 Admin Access")
        
        if not st.session_state.admin_authenticated:
            with st.sidebar.expander("Admin Login", expanded=False):
                st.caption("Internal use only")
                
                # Check for rate limiting
                if st.session_state.admin_attempts >= 5:
                    st.error("Too many attempts. Try again in 30 seconds.")
                    time.sleep(30)
                    st.session_state.admin_attempts = 0  # Reset after wait
                else:
                    password = st.text_input("Password", type="password", key="admin_password_input_sidebar_unique")  # Unique key
                    if st.button("Authenticate", key="admin_auth_btn_sidebar_unique"):  # Unique key
                        if password == ADMIN_PASSWORD:
                            st.session_state.admin_authenticated = True
                            st.session_state.admin_attempts = 0  # Reset on success
                            st.success("✅ Admin access granted")
                            st.rerun()
                        else:
                            st.session_state.admin_attempts += 1  # Increment on failure
                            remaining = 5 - st.session_state.admin_attempts
                            st.error(f"❌ Invalid password ({remaining} attempts remaining)")
        else:
            # Show logout when authenticated
            st.sidebar.success("✅ Admin Mode Active")
            if st.sidebar.button("🔓 Logout", key="admin_logout_btn_sidebar_unique"):  # Unique key
                st.session_state.admin_authenticated = False
                st.rerun()

    # Update is_admin after authentication check
    is_admin = st.session_state.admin_authenticated

    # ============================================================================
    # APPLY FILTERS
    # ============================================================================

    filtered_positions = data['positions'].copy() if not data['positions'].empty else pd.DataFrame()
    filtered_open = data['open_positions'].copy() if not data['open_positions'].empty else pd.DataFrame()

    # IMPORTANT: Remove duplicates by position_id to ensure accurate counting
    if not filtered_positions.empty and 'position_id' in filtered_positions.columns:
        # Check for duplicates
        duplicate_count = filtered_positions.duplicated(subset=['position_id']).sum()
        if duplicate_count > 0:
            # Remove duplicates, keeping first occurrence
            filtered_positions = filtered_positions.drop_duplicates(subset=['position_id'], keep='first')

    # Admin debug info - COMPLETELY HIDDEN from regular users
    if is_admin:
        with st.sidebar.expander("📊 Data Debug (Admin)", expanded=False):
            st.write(f"Total positions: {len(filtered_positions)}")
            if not filtered_positions.empty:
                st.write(f"Spot: {len(filtered_positions[filtered_positions['product_type'] == 'spot'])}")
                st.write(f"Perp: {len(filtered_positions[filtered_positions['product_type'] == 'perp'])}")
                st.write(f"Option: {len(filtered_positions[filtered_positions['product_type'] == 'option'])}")
            st.write(f"Open positions: {len(filtered_open)}")
            st.write(f"Date range: {start_date} to {end_date}")

    # Trader filter
    if st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state:
        selected_trader = st.session_state.authenticated_trader
        if not filtered_positions.empty:
            filtered_positions = filtered_positions[filtered_positions['trader_id'] == selected_trader]
        if not filtered_open.empty:
            filtered_open = filtered_open[filtered_open['trader_id'] == selected_trader]
    else:
        selected_trader = None

    # Date filter
    if not filtered_positions.empty:
        filtered_positions = filtered_positions[
            (filtered_positions['close_time'].dt.date >= start_date) &
            (filtered_positions['close_time'].dt.date <= end_date)
        ]

    # Symbol filter
    if selected_markets:
        if not filtered_positions.empty:
            filtered_positions = filtered_positions[filtered_positions['market_id'].isin(selected_markets)]
        if not filtered_open.empty:
            filtered_open = filtered_open[filtered_open['market_id'].isin(selected_markets)]

    if not filtered_positions.empty:
        filtered_positions = calculate_volume_usd(filtered_positions)

    # ============================================================================
    # GLOBAL KPIs IN SIDEBAR (STICKY)
    # ============================================================================

    is_personal = (st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state)
    display_sidebar_kpis(filtered_positions, selected_trader, is_personal_mode=is_personal)

    st.sidebar.markdown("---")

    # ============================================================================
    # TAB NAVIGATION IN SIDEBAR (STICKY)
    # ============================================================================

    st.sidebar.markdown("### 📍 Navigation")

    # Define tabs
    tab_options = [
        "📊 Overview",
        "📈 Performance",
        "📅 Time Analysis",
        "⚠️ Risk",
        "📊 Volume",
        "📋 Orders",
        "🔬 Greeks",
        "📝 Journal"
    ]

    # Initialize session state for active tab if not exists
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = tab_options[0]

    # Create radio buttons for navigation
    selected_tab = st.sidebar.radio(
        "Go to",
        tab_options,
        index=tab_options.index(st.session_state.active_tab),
        label_visibility="collapsed",
        key="navigation_radio_sidebar_unique"  # Unique key
    )

    # Update session state if changed
    if selected_tab != st.session_state.active_tab:
        st.session_state.active_tab = selected_tab
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption("🔒 Read-only • Local-first")
    
    # Close the scrollable content container
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# MAIN CONTENT AREA (SCROLLABLE)
# ============================================================================

# Personal mode badge (if applicable)
if st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state:
    st.markdown(
        f"<div class='profile-badge'>🔐 {mask_trader_id(st.session_state.authenticated_trader)}</div>",
        unsafe_allow_html=True
    )

# ============================================================================
# RENDER ACTIVE TAB CONTENT
# ============================================================================

if st.session_state.active_tab == "📊 Overview":
    # --- OVERVIEW TAB ---
    if not filtered_positions.empty and not selected_trader:
        st.markdown("## 🏆 Top Performers Analysis")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### 📈 Top 5 Profitable Traders")
            top_winners = get_top_traders(filtered_positions, n=5, by='profit')
            
            if top_winners:
                rows = []
                for t in top_winners:
                    tp = filtered_positions[filtered_positions['trader_id'] == t]
                    rows.append({
                        'Trader': mask_trader_id(t),
                        'Total PnL': tp['realized_pnl'].sum(),
                        'Trades': len(tp),
                        'Win Rate': (tp['realized_pnl'] > 0).mean() * 100
                    })
                
                df2 = pd.DataFrame(rows)
                fig = px.bar(df2, x='Trader', y='Total PnL',
                            color='Total PnL', color_continuous_scale='Greens',
                            text='Total PnL')
                fig.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
                fig.update_layout(height=200, showlegend=False, **CHART_BG)
                st.plotly_chart(fig, width='stretch', key="top_profit")
                
                st.dataframe(
                    df2.style.format({'Total PnL':'${:,.2f}','Win Rate':'{:.1f}%'}),
                    width='stretch', hide_index=True
                )
        
        with c2:
            st.markdown("### 📉 Top 5 Loss-Making Traders")
            top_losers = get_top_traders(filtered_positions, n=5, by='loss')
            
            if top_losers:
                rows = []
                for t in top_losers:
                    tp = filtered_positions[filtered_positions['trader_id'] == t]
                    rows.append({
                        'Trader': mask_trader_id(t),
                        'Total PnL': tp['realized_pnl'].sum(),
                        'Trades': len(tp),
                        'Win Rate': (tp['realized_pnl'] > 0).mean() * 100
                    })
                
                df2 = pd.DataFrame(rows)
                fig = px.bar(df2, x='Trader', y='Total PnL',
                            color='Total PnL', color_continuous_scale='Reds_r',
                            text='Total PnL')
                fig.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
                fig.update_layout(height=200, showlegend=False, **CHART_BG)
                st.plotly_chart(fig, width='stretch', key="top_loss")
                
                st.dataframe(
                    df2.style.format({'Total PnL':'${:,.2f}','Win Rate':'{:.1f}%'}),
                    width='stretch', hide_index=True
                )
        
        st.markdown("---")
    
    display_transaction_history(filtered_positions)
    
    if not filtered_open.empty:
        st.markdown("### 📊 Open Positions")
        st.warning(f"⚠️ **{len(filtered_open)} Open Positions** - Unrealized PnL not included")
        
        od = filtered_open.copy()
        od['symbol'] = od['market_id'].apply(simplify_symbol)
        od['trader'] = od['trader_id'].apply(mask_trader_id)
        
        st.dataframe(
            od[['trader','symbol','product_type','side','entry_price','size']],
            width='stretch', hide_index=True
        )

elif st.session_state.active_tab == "📈 Performance":
    if filtered_positions.empty:
        st.info("📈 No performance data available for the selected filters")
        st.caption("Try expanding your date range or selecting different symbols")
    else:
        if 'position_id' in filtered_positions.columns:
            display_positions = filtered_positions.drop_duplicates(subset=['position_id'])
        else:
            display_positions = filtered_positions

        days_selected     = (end_date - start_date).days
        trade_count       = len(display_positions)
        has_symbol_filter = len(selected_symbols) > 0
        is_sparse_mode    = False

        if trade_count < 5:
            is_sparse_mode = True
            context_note("Very few trades in selected period - showing compact view with trade details")
        elif days_selected <= 7 and trade_count < 10:
            is_sparse_mode = True
            context_note("Limited data for selected period - showing compact charts + trade cards")
        elif has_symbol_filter and trade_count < 8:
            is_sparse_mode = True
            context_note(f"Limited data for selected symbol{'s' if len(selected_symbols)>1 else ''} - showing compact view")

        # ── Helper: compute all extended metrics from filtered positions ──
        def perf_metrics(pos):
            wins   = pos[pos['realized_pnl'] > 0]['realized_pnl']
            losses = pos[pos['realized_pnl'] < 0]['realized_pnl']
            avg_win  = wins.mean()  if len(wins)   > 0 else 0
            avg_loss = losses.mean() if len(losses) > 0 else 0
            long_vol  = pos[pos['side'].str.lower().isin(['long','buy'])]['volume_usd'].sum()  if 'volume_usd' in pos.columns else 0
            short_vol = pos[pos['side'].str.lower().isin(['short','sell'])]['volume_usd'].sum() if 'volume_usd' in pos.columns else 0
            total_vol = long_vol + short_vol
            long_pct  = long_vol  / total_vol * 100 if total_vol > 0 else 0
            short_pct = short_vol / total_vol * 100 if total_vol > 0 else 0
            # Max drawdown
            cum = pos.sort_values('close_time')['realized_pnl'].cumsum()
            max_dd = (cum - cum.cummax()).min() if len(cum) > 1 else 0
            sharpe, sortino = compute_ratios(pos)
            return avg_win, avg_loss, long_pct, short_pct, max_dd, sharpe, sortino

        def render_perf_metrics(pos):
            """Render the extended metrics row — always dynamic to current filters."""
            avg_win, avg_loss, long_pct, short_pct, max_dd, sharpe, sortino = perf_metrics(pos)
            st.markdown("#### 📊 Key Metrics")
            c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
            c1.metric("Avg Win",    f"${avg_win:,.2f}"  if avg_win  != 0 else "N/A")
            c2.metric("Avg Loss",   f"${avg_loss:,.2f}" if avg_loss != 0 else "N/A")
            c3.metric("Long %",     f"{long_pct:.1f}%")
            c4.metric("Short %",    f"{short_pct:.1f}%")
            c5.metric("Max DD",     f"${max_dd:,.2f}")
            c6.metric("Sharpe",     f"{sharpe:.2f}" if len(pos) > 1 else "N/A")
            c7.metric("Sortino",    f"{sortino:.2f}" if len(pos) > 1 else "N/A")
            st.markdown("---")

        if st.session_state.view_mode == "personal" and selected_trader:
            fig, fig_dd = create_personal_equity_chart(display_positions, is_sparse_mode, compact=is_sparse_mode)
            if is_sparse_mode and fig_dd is not None:
                col_left, col_right = st.columns(2)
                with col_left:
                    st.plotly_chart(fig, width='stretch', key="personal_eq")
                with col_right:
                    st.plotly_chart(fig_dd, width='stretch', key="personal_dd")
                st.caption("Equity (left) and Drawdown (right) - compact view")
            else:
                st.plotly_chart(fig, width='stretch', key="personal_eq")
                if fig_dd is not None:
                    st.plotly_chart(fig_dd, width='stretch', key="personal_dd")
                    st.caption("Drawdown from peak equity")

            render_perf_metrics(display_positions)

            if is_sparse_mode:
                display_performance_cards(display_positions, "Your Performance Details")
        else:
            st.markdown("## 📊 Protocol Performance")
            fig_eq, fig_dd = create_protocol_equity_charts(display_positions, compact=is_sparse_mode)
            if is_sparse_mode:
                col_left, col_right = st.columns(2)
                with col_left:
                    st.plotly_chart(fig_eq, width='stretch', key="proto_eq")
                with col_right:
                    st.plotly_chart(fig_dd, width='stretch', key="proto_dd")
                st.caption("Protocol PnL (left) and Drawdown (right) - compact view")
            else:
                st.plotly_chart(fig_eq, width='stretch', key="proto_eq")
                st.caption("Protocol cumulative PnL")
                st.plotly_chart(fig_dd, width='stretch', key="proto_dd")
                st.caption("Drawdown from peak equity")

            render_perf_metrics(display_positions)

            if is_sparse_mode:
                display_performance_cards(display_positions, "Protocol Performance Details")
            if not selected_trader and not data['equity'].empty and not is_sparse_mode:
                create_trader_summary_table(data['equity'], display_positions)
                                
elif st.session_state.active_tab == "📅 Time Analysis":
    # --- TIME ANALYSIS TAB ---
    if filtered_positions.empty:
        st.info("📅 No time-based data available for the selected filters")
        st.caption("Try expanding your date range or selecting different symbols")
    else:
        days_selected = (end_date - start_date).days
        trade_count = len(filtered_positions)
        has_symbol_filter = len(selected_symbols) > 0
        
        is_sparse_mode = False
        
        if trade_count < 5:
            is_sparse_mode = True
            context_note("Very few trades - showing trade timeline instead of daily/hourly charts")
        elif days_selected <= 7 and trade_count < 10:
            is_sparse_mode = True
            context_note("Limited time data - showing trade timeline instead of daily/hourly charts")
        elif has_symbol_filter and trade_count < 8:
            is_sparse_mode = True
            context_note(f"Limited data for selected symbol{'s' if len(selected_symbols)>1 else ''} - showing individual trades")
        
        if is_sparse_mode:
            display_trade_summary_cards(filtered_positions, "Trade Timeline")
        else:
            trader_pnl_day = None
            trader_pnl_hour = None
            
            if st.session_state.view_mode == "personal" and selected_trader:
                trader_positions = filtered_positions.copy()
                
                if data.get('pnl_day') is not None and not data['pnl_day'].empty:
                    day_df = data['pnl_day'].copy()
                    if 'trader_id' in day_df.columns:
                        day_df = day_df[day_df['trader_id'] == selected_trader]
                    if 'date' in day_df.columns:
                        day_df['date'] = pd.to_datetime(day_df['date'])
                        trader_pnl_day = day_df[
                            (day_df['date'].dt.date >= start_date) & 
                            (day_df['date'].dt.date <= end_date)
                        ].copy()
                
                if data.get('pnl_hour') is not None and not data['pnl_hour'].empty:
                    hour_df = data['pnl_hour'].copy()
                    if 'trader_id' in hour_df.columns:
                        trader_pnl_hour = hour_df[hour_df['trader_id'] == selected_trader].copy()
                
                display_time_performance(
                    trader_positions,
                    trader_pnl_day,
                    trader_pnl_hour
                )
            else:
                pnl_day_filtered = None
                if data.get('pnl_day') is not None and not data['pnl_day'].empty:
                    day_df = data['pnl_day'].copy()
                    if 'date' in day_df.columns:
                        day_df['date'] = pd.to_datetime(day_df['date'])
                        pnl_day_filtered = day_df[
                            (day_df['date'].dt.date >= start_date) & 
                            (day_df['date'].dt.date <= end_date)
                        ].copy()
                
                display_time_performance(
                    filtered_positions,
                    pnl_day_filtered,
                    data.get('pnl_hour')
                )

elif st.session_state.active_tab == "⚠️ Risk":
    # --- RISK TAB ---
    if filtered_positions.empty:
        st.info("⚠️ No risk data available for the selected filters")
        st.caption("Try expanding your date range or selecting different symbols")
    else:
        display_liquidation_analytics(
            filtered_positions,
            is_personal_mode=(st.session_state.view_mode == "personal"),
            trader_id=selected_trader
        )

elif st.session_state.active_tab == "📊 Volume":
    # --- VOLUME TAB ---
    if filtered_positions.empty:
        st.info("📊 No volume data available for the selected filters")
        st.caption("Try expanding your date range or selecting different symbols")
    else:
        display_volume_analysis(filtered_positions)

elif st.session_state.active_tab == "📋 Orders":
    # --- ORDERS TAB ---
    if filtered_positions.empty:
        st.info("📊 No order data available for the selected filters")
        st.caption("Try expanding your date range or selecting different symbols")
    else:
        display_order_type_performance(data['order_perf'], filtered_positions)

elif st.session_state.active_tab == "🔬 Greeks":
    # --- GREEKS TAB ---
    has_options = False
    if not filtered_positions.empty:
        has_options = (filtered_positions['product_type'] == 'option').any()
    
    if filtered_positions.empty or not has_options:
        st.info("📊 No options data available for the selected filters")
        st.caption("Try expanding your date range or selecting different symbols")
    else:
        display_greeks_analysis(
            data['greeks'].copy() if not data['greeks'].empty else pd.DataFrame(),
            filtered_positions,
            is_personal=(selected_trader is not None)
        )

elif st.session_state.active_tab == "📝 Journal":
    # --- JOURNAL TAB ---
    st.header("📝 Trade Journal with Annotations")
    
    if filtered_positions.empty:
        st.info("No trades to journal")
    
    elif st.session_state.view_mode == "personal" and selected_trader:
        trader = selected_trader
        
        st.info("📌 Type your notes and press Enter to save. Changes are saved automatically.")
        
        trader_notes = load_trader_notes(trader)
        
        if 'journal_last_saved' not in st.session_state:
            st.session_state.journal_last_saved = trader_notes.copy()
        
        jdf = filtered_positions[filtered_positions['trader_id'] == trader].sort_values('close_time', ascending=False).copy()
        
        if jdf.empty:
            st.info("No trades found for this trader in the selected date range")
            st.stop()
        
        jdf['symbol'] = jdf['market_id'].apply(simplify_symbol)
        jdf['volume_usd'] = jdf['exit_price'] * jdf['size']
        jdf['notes'] = jdf['position_id'].map(lambda pid: trader_notes.get(str(pid), ""))
        
        
        if 'delta' in data['greeks'].columns:
            # Merge pre-calculated delta from greeks data
            greeks_delta = data['greeks'][['position_id', 'delta']].copy()
            jdf = jdf.merge(greeks_delta, on='position_id', how='left', suffixes=('', '_precalc'))
            if 'delta_precalc' in jdf.columns:
                jdf['delta'] = jdf['delta_precalc']
                jdf.drop('delta_precalc', axis=1, inplace=True)
        
        jdf_unique = jdf.drop_duplicates(subset=['position_id']).copy()
        
        notes_count = sum(1 for n in jdf_unique['notes'].values if n and str(n).strip() != "")
        total_trades = len(jdf_unique)
        
        st.info(f"📝 **{notes_count}** of **{total_trades}** trades annotated ({notes_count/total_trades*100:.1f}%)")
        
        page_size = 10  
        total_pages = max(1, (len(jdf_unique) - 1) // page_size + 1)
        
        col_p1, col_p2, col_p3 = st.columns([2, 1, 2])
        with col_p2:
            journal_page = st.number_input(
                "Page", 
                min_value=1, 
                max_value=total_pages, 
                value=1, 
                key="journal_personal_page"
            )
        
        start_idx = (journal_page - 1) * page_size
        end_idx = min(journal_page * page_size, len(jdf_unique))
        jdf_page = jdf_unique.iloc[start_idx:end_idx].copy()
        
        st.caption(f"Showing trades {start_idx + 1}–{end_idx} of {len(jdf_unique)}")
        
        avail_cols = ['close_time','symbol','product_type','side',
                      'entry_price','exit_price','size','volume_usd','realized_pnl','fees']

        if 'delta' in jdf_page.columns and (jdf_page['product_type'] == 'option').any():
            avail_cols.append('delta')
            
        avail_cols.append('notes')

        col_cfg = {
            "close_time": st.column_config.DatetimeColumn("Closed At", format="DD/MM/YYYY HH:mm"),
            "symbol": "Symbol",
            "product_type": "Type",
            "side": "Direction",
            "entry_price": st.column_config.NumberColumn("Entry", format="$%.2f"),
            "exit_price": st.column_config.NumberColumn("Exit", format="$%.2f"),
            "size": st.column_config.NumberColumn("Size", format="%.4f"),
            "volume_usd": st.column_config.NumberColumn("Volume", format="$%.0f"),
            "realized_pnl": st.column_config.NumberColumn("PnL", format="$%.2f"),
            "fees": st.column_config.NumberColumn("Fees", format="$%.2f"),
            "notes": st.column_config.TextColumn("📝 Your Notes", max_chars=500, width="large"),
        }

        if 'delta' in avail_cols:
            col_cfg["delta"] = st.column_config.NumberColumn("Delta", format="%.2f")
        
        editor_key = f"journal_editor_{selected_trader}_{journal_page}"

        edited = st.data_editor(
            jdf_page[avail_cols],
            column_config=col_cfg,
            width='stretch', 
            hide_index=True, 
            num_rows="fixed",
            disabled=[c for c in avail_cols if c != 'notes'],
            key=editor_key
        )
        
        updated = {}
        has_changes = False
        
        for position_idx in range(len(edited)):
            pid = str(jdf_page.iloc[position_idx]['position_id'])
            note = str(edited.iloc[position_idx]['notes']).strip() if 'notes' in edited.columns else ""
            
            if note:
                updated[pid] = note
            
            old_note = st.session_state.journal_last_saved.get(pid, "")
            if note != old_note:
                has_changes = True
        
        if has_changes:
            all_notes = load_trader_notes(trader)
            all_notes.update(updated)
            save_trader_notes(trader, all_notes)
            st.session_state.journal_last_saved = all_notes.copy()
            st.success("✅ Notes saved automatically!")
            st.rerun()
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            csv_data = jdf_unique[avail_cols].copy()
            csv_data['close_time'] = pd.to_datetime(csv_data['close_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
            st.download_button(
                "📥 Export All",
                csv_data.to_csv(index=False),
                f"journal_{mask_trader_id(trader)}.csv",
                "text/csv"
            )
        with col3:
            if st.button("🗑️ Clear All Notes"):
                save_trader_notes(trader, {})
                st.session_state.journal_last_saved = {}
                st.success("🗑️ All notes cleared")
                st.rerun()
    
    else:
        if selected_trader:
            st.info(f"👁️ Read-Only View: {mask_trader_id(selected_trader)}")
        else:
            st.info("📖 Viewing all traders' annotated trades")
        
        all_notes = {}
        notes_dir = Path("data/trader_notes")
        if notes_dir.exists():
            for notes_file in notes_dir.glob("*.json"):
                trader_id = notes_file.stem
                try:
                    with open(notes_file, 'r') as f:
                        trader_notes_data = json.load(f)
                        for pos_id, note in trader_notes_data.items():
                            if note and str(note).strip():
                                all_notes[pos_id] = {'trader_id': trader_id, 'note': note}
                except Exception:
                    continue
        
        jdf = filtered_positions.sort_values('close_time', ascending=False).copy()
        jdf['trader'] = jdf['trader_id'].apply(mask_trader_id)
        jdf['symbol'] = jdf['market_id'].apply(simplify_symbol)
        jdf['volume_usd'] = jdf['exit_price'] * jdf['size']
        jdf['notes'] = jdf['position_id'].map(
            lambda pid: all_notes.get(str(pid), {}).get('note', '')
        )
        
        jdf_unique = jdf.drop_duplicates(subset=['position_id']).copy()
        
        annotated_count = sum(1 for n in jdf_unique['notes'].values if n and str(n).strip() != "")
        total_count = len(jdf_unique)
        
        if annotated_count > 0:
            st.success(f"📝 **{annotated_count}** of **{total_count}** trades have annotations ({annotated_count/total_count*100:.1f}%)")
        else:
            st.info("📝 No trades have been annotated yet")
        
        show_all = st.checkbox("Show all trades", value=True, key="show_all_trades")
        
        if not show_all:
            jdf_unique = jdf_unique[jdf_unique['notes'].str.strip() != '']
            if jdf_unique.empty:
                st.info("No annotated trades to display")
                st.stop()
            st.caption(f"Showing {len(jdf_unique)} annotated trades")
        
        page_size = 10
        total_pages = max(1, (len(jdf_unique) - 1) // page_size + 1)
        
        col_p1, col_p2, col_p3 = st.columns([2, 1, 2])
        with col_p2:
            all_journal_page = st.number_input(
                "Page", 
                min_value=1, 
                max_value=total_pages, 
                value=1, 
                key="journal_all_page"
            )
        
        start_idx = (all_journal_page - 1) * page_size
        end_idx = min(all_journal_page * page_size, len(jdf_unique))
        jdf_page = jdf_unique.iloc[start_idx:end_idx].copy()
        
        st.caption(f"Showing trades {start_idx + 1}–{end_idx} of {len(jdf_unique)}")
        
        display_cols = ['close_time','trader','symbol','product_type','side',
                       'entry_price','exit_price','size','volume_usd','realized_pnl','fees','notes']
        
        display_df = jdf_page[display_cols].copy()
        display_df['close_time'] = pd.to_datetime(display_df['close_time']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(
            display_df.style.format({
                'entry_price': '${:,.2f}', 
                'exit_price': '${:,.2f}',
                'size': '{:,.4f}', 
                'volume_usd': '${:,.0f}',
                'realized_pnl':'${:,.2f}', 
                'fees': '${:,.2f}'
            }).apply(lambda x: ['background-color: rgba(99,102,241,0.1)' if x['notes'] else '' for _ in x], axis=1),
            width='stretch', 
            hide_index=True,
            column_config={
                "notes": st.column_config.TextColumn("📝 Trader Notes", width="large")
            }
        )
        
        csv_data = jdf_unique[display_cols].copy()
        csv_data['close_time'] = pd.to_datetime(csv_data['close_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        st.download_button(
            "📥 Download All Trades with Notes",
            csv_data.to_csv(index=False),
            f"all_trades_with_notes_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv"
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
fc1, fc2, fc3 = st.columns([2, 1, 1])
fc1.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
fc2.caption("🔐 **Admin Mode**" if is_admin else "🔒 **Secure** • Local-first")
fc3.caption("v9.0 Sidebar Navigation")

st.markdown("""
<div style='text-align:center;padding:20px;color:#64748b;font-size:12px;'>
    <strong>Deriverse Analytics Dashboard</strong><br>
    Read-only • No private keys required • Data stays on your machine
</div>
""", unsafe_allow_html=True)
