# dashboards/app.py
"""
Deriverse Trading Analytics Dashboard - v7.4
Implements: Adaptive/Context-Aware Visualization, duplicate key fix,
sparkline trend lines, improved Greeks/Orders tabs, and all prior fixes.
"""
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
import os
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path("data/analytics_output")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ADMIN_PASSWORD")

st.set_page_config(
    page_title="Deriverse Trading Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS — fixed header, zero gap between tabs and KPIs
# ============================================================================
st.markdown("""
<style>
    /* Streamlit default header gone */
    header[data-testid="stHeader"] { display: none !important; }
    .main > div { padding-top: 0 !important; margin-top: 0 !important; }

    /* Fixed header — never scrolls */
    .fixed-header {
        position: fixed !important;
        top: 0 !important;
        left: 250px;
        right: 0;
        z-index: 999999 !important;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 8px 25px 0 25px;
        border-bottom: 2px solid rgba(99,102,241,0.3);
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }

    /* Push body content below fixed header */
    .main-content { margin-top: 260px !important; padding: 0 20px; }

    /* Zero gap between nav buttons and KPIs */
    .stButton { margin-bottom: 0 !important; }
    div.row-widget.stButton > button { margin-bottom: 0 !important; }
    .kpi-row { margin-top: 0 !important; margin-bottom: 0 !important; padding-top: 0 !important; }
    .element-container { margin-bottom: 0 !important; }

    .header-title {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.8rem; font-weight: 700; color: #f1f5f9;
        margin: 0; padding: 0; letter-spacing: -0.02em; line-height: 1.2;
    }
    .header-subtitle { color: #94a3b8; font-size: 0.8rem; margin-top: 2px; }

    .metric-major {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        padding: 8px 12px; border-radius: 10px;
        border: 2px solid rgba(99,102,241,0.3); text-align: center;
    }
    .metric-major-label { font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-major-value { font-size: 1.3rem; font-weight: 700; color: #f1f5f9; line-height: 1.2; }

    .profile-badge {
        background: linear-gradient(135deg,#10b981,#059669);
        color: white; padding: 2px 10px; border-radius: 16px;
        font-weight: 600; font-size: 0.8rem; display: inline-block;
        margin: 2px 0; border: 1px solid rgba(255,255,255,0.1);
    }
    .section-header { margin: 15px 0 10px 0; padding-bottom: 5px; border-bottom: 2px solid rgba(99,102,241,0.3); }
    .section-header h2 { font-family: 'IBM Plex Mono', monospace; font-size: 1.5rem; font-weight: 600; color: #f1f5f9; margin: 0; }

    /* Horizontal scroll for tables */
    .scroll-x { width: 100%; overflow-x: auto !important; display: block; }

    /* Adaptive context note */
    .context-note {
        background: rgba(99,102,241,0.08);
        border-left: 3px solid #6366f1;
        padding: 6px 12px; border-radius: 4px;
        color: #94a3b8; font-size: 0.78rem; margin-bottom: 8px;
    }

    /* Verify links */
    .verify-link { color: #10b981 !important; text-decoration: none; font-weight: 600; cursor: pointer; }
    .verify-link:hover { text-decoration: underline; color: #34d399 !important; }

    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
    .status-live {
        display: inline-block; width: 6px; height: 6px;
        background: #10b981; border-radius: 50%;
        animation: pulse 2s infinite; margin-right: 4px;
    }

    /* HTML table styling */
    table.tx-table { border-collapse: collapse; width: 100%; font-size: 0.82rem; }
    table.tx-table th { background: #1e293b; color: #94a3b8; padding: 6px 10px; text-align: left; border-bottom: 1px solid #334155; }
    table.tx-table td { padding: 6px 10px; border-bottom: 1px solid rgba(51,65,85,0.4); color: #e2e8f0; white-space: nowrap; }
    table.tx-table tr:hover td { background: rgba(99,102,241,0.06); }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# ADAPTIVE VISUALIZATION FRAMEWORK
# ============================================================================

def data_profile(df, metric):
    """Return count, unique value count, and variance for a metric."""
    series = df[metric].dropna()
    return {
        "count": len(series),
        "unique": series.nunique(),
        "variance": float(series.var()) if len(series) > 1 else 0.0
    }


def visualization_confidence(df, metric, expected_variance=10.0):
    """Score 0-1 indicating how well data supports a complex chart."""
    p = data_profile(df, metric)
    score = min(1.0,
        (p["count"] / 20) * 0.4 +
        (p["unique"] / 10) * 0.3 +
        (p["variance"] / max(expected_variance, 1e-6)) * 0.3
    )
    return score


def context_note(msg):
    """Render a soft info banner when simplified view is shown."""
    st.markdown(f"<div class='context-note'>ℹ️ {msg}</div>", unsafe_allow_html=True)


def choose_liquidation_chart(df):
    """Adaptive: decide chart type for liquidation section."""
    if df['trader_id'].nunique() < 5:
        return "kpi_only"
    trader_liq_rates = []
    for trader in df['trader_id'].unique():
        td = df[df['trader_id'] == trader]
        total = len(td[td['close_reason'].isin(['closed', 'liquidation'])])
        if total > 0:
            trader_liq_rates.append(len(td[td['close_reason'] == 'liquidation']) / total * 100)
    if not trader_liq_rates or pd.Series(trader_liq_rates).var() < 1:
        return "bar_chart_loss"
    return "scatter"


def choose_trade_size_chart(df):
    """Adaptive: decide chart type for trade size."""
    n = len(df)
    unique_sizes = df['volume_usd'].round(0).nunique()
    if n < 10:
        return "kpi_only"
    if unique_sizes < 5:
        return "strip"
    return "histogram"


def choose_pnl_chart(df):
    """Adaptive: decide chart type for PnL distribution."""
    n = len(df)
    if n < 5:
        return "list"
    skew = abs(float(df['realized_pnl'].skew())) if n > 2 else 0
    if skew > 2:
        return "boxplot"
    return "histogram"


def choose_win_rate_chart(df):
    """Adaptive: decide chart type for win rate."""
    sides = df['side'].str.lower().unique()
    long_sides  = {'long', 'buy'}
    short_sides = {'short', 'sell'}
    has_long  = bool(set(sides) & long_sides)
    has_short = bool(set(sides) & short_sides)
    if has_long and has_short:
        return "bar"
    return "kpi"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_admin_password():
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
    if pd.isna(trader_id):
        return "Unknown"
    s = str(trader_id)
    return f"{s[:4]}..{s[-4:]}" if len(s) > 8 else s


def simplify_symbol(market_id):
    if pd.isna(market_id):
        return market_id
    s = str(market_id)
    return s.split('/')[0].split('-')[0]


def get_top_traders(positions_df, n=5, by='profit'):
    if positions_df.empty:
        return []
    trader_stats = positions_df.groupby('trader_id')['realized_pnl'].agg(['sum', 'count'])
    if by == 'profit':
        return trader_stats.nlargest(n, 'sum').index.tolist()
    elif by == 'loss':
        return trader_stats.nsmallest(n, 'sum').index.tolist()
    return trader_stats.nlargest(n, 'count').index.tolist()


def load_trader_notes(trader_id):
    notes_dir = Path("data/trader_notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    notes_file = notes_dir / f"{trader_id}.json"
    if notes_file.exists():
        with open(notes_file, 'r') as f:
            return json.load(f)
    return {}


def save_trader_notes(trader_id, notes):
    notes_dir = Path("data/trader_notes")
    notes_dir.mkdir(parents=True, exist_ok=True)
    with open(notes_dir / f"{trader_id}.json", 'w') as f:
        json.dump(notes, f, indent=2)


def get_trade_density(positions_df):
    count = len(positions_df)
    if count == 0:   return "empty"
    if count == 1:   return "single"
    if count < 5:    return "sparse"
    return "dense"


def calculate_volume_usd(df):
    df = df.copy()
    df['volume_usd'] = df['exit_price'] * df['size']
    return df


CHART_BG = dict(
    template='plotly_dark',
    plot_bgcolor='rgba(15,23,42,0.9)',
    paper_bgcolor='rgba(15,23,42,0.9)'
)


# ============================================================================
# TRADER PERFORMANCE SUMMARY — with trend line in sparklines
# ============================================================================

def create_trader_summary_table(equity_df, positions_df):
    """Trader summary table with sparklines that include a trend overlay."""
    st.markdown("### 📋 Trader Performance Summary")

    traders = []
    for trader in equity_df['trader_id'].unique()[:10]:
        te = equity_df[equity_df['trader_id'] == trader].sort_values('timestamp')
        tp = positions_df[positions_df['trader_id'] == trader]
        total_pnl = tp['realized_pnl'].sum()
        win_rate  = (tp['realized_pnl'] > 0).mean() * 100
        max_dd    = te['drawdown'].min()
        sparkline = te['cumulative_pnl'].values
        norm = ((sparkline - sparkline.min()) / (sparkline.max() - sparkline.min() + 1e-9)) if len(sparkline) > 1 else np.array([0.5])
        traders.append({
            'trader': mask_trader_id(trader),
            'pnl': total_pnl, 'win_rate': win_rate, 'max_dd': max_dd,
            'trades': len(tp), 'sparkline': norm[-20:],
            'trend': '📈' if total_pnl > 0 and len(sparkline) > 1 and sparkline[-1] > sparkline[0] else '📉'
        })
    traders.sort(key=lambda x: x['pnl'], reverse=True)

    headers = st.columns([1.2, 1.8, 1, 1, 1, 1.5])
    for h, label in zip(headers, ["**Trader**", "**Equity Trend**", "**PnL**", "**Win Rate**", "**Max DD**", "**Activity**"]):
        h.markdown(label)
    st.divider()

    for i, t in enumerate(traders):
        cols = st.columns([1.2, 1.8, 1, 1, 1, 1.5])
        cols[0].markdown(f"`{t['trader']}`")

        # Sparkline with trend overlay
        sp = t['sparkline']
        x_idx = list(range(len(sp)))
        fig = go.Figure()
        color = '#10b981' if t['pnl'] > 0 else '#ef4444'
        fig.add_trace(go.Scatter(y=sp, mode='lines', line=dict(color=color, width=2), showlegend=False))
        # Trend line over sparkline
        if len(sp) >= 2:
            z = np.polyfit(x_idx, sp, 1)
            trend_y = np.polyval(z, x_idx)
            fig.add_trace(go.Scatter(y=trend_y, mode='lines', line=dict(color='#f59e0b', width=1.5, dash='dot'), showlegend=False))
        fig.update_layout(
            height=40, margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)'
        )
        cols[1].plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"spark_{i}")

        pnl_color = '#10b981' if t['pnl'] > 0 else '#ef4444'
        cols[2].markdown(f"<span style='color:{pnl_color};font-weight:600;'>${t['pnl']:,.0f}</span>", unsafe_allow_html=True)
        cols[3].markdown(f"{t['win_rate']:.0f}%")
        cols[4].markdown(f"${abs(t['max_dd']):,.0f}")
        cols[5].markdown(f"{t['trades']} trades {t['trend']}")


# ============================================================================
# EQUITY CHARTS — no trend line on protocol chart (removed per request)
# ============================================================================

def create_protocol_equity_charts(positions_df):
    """Protocol equity (no trend line) + drawdown chart."""
    ps = positions_df.sort_values('close_time').copy()
    ps['cumulative_pnl'] = ps['realized_pnl'].cumsum()

    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(
        x=ps['close_time'], y=ps['cumulative_pnl'],
        line=dict(color='#6366f1', width=3),
        fill='tozeroy', fillcolor='rgba(99,102,241,0.1)',
        showlegend=False,
        hovertemplate='Date: %{x}<br>PnL: $%{y:,.2f}<extra></extra>'
    ))
    fig_eq.update_layout(
        title="📈 Protocol Cumulative PnL",
        xaxis_title="Date", yaxis_title="Cumulative PnL ($)",
        height=350, margin=dict(l=40,r=40,t=40,b=40), **CHART_BG
    )

    rolling_max = ps['cumulative_pnl'].cummax()
    drawdown = ps['cumulative_pnl'] - rolling_max
    max_dd = drawdown.min()

    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=ps['close_time'], y=drawdown,
        line=dict(color='#ef4444', width=2.5),
        fill='tozeroy', fillcolor='rgba(239,68,68,0.15)', showlegend=False
    ))
    fig_dd.add_hline(y=max_dd, line_dash="dash", line_color="#ef4444",
                     annotation_text=f"Max DD: ${max_dd:,.0f}", annotation_position="bottom right")
    fig_dd.update_layout(
        title="📉 Drawdown from Peak",
        xaxis_title="Date", yaxis_title="Drawdown ($)",
        height=250, margin=dict(l=40,r=40,t=40,b=40), **CHART_BG
    )
    return fig_eq, fig_dd


def create_personal_equity_chart(trader_positions):
    """Adaptive equity chart for personal mode."""
    density = get_trade_density(trader_positions)

    if density == "single":
        pnl = trader_positions['realized_pnl'].iloc[0]
        fig = go.Figure(go.Bar(
            x=['Your Trade'], y=[pnl],
            marker_color='#10b981' if pnl > 0 else '#ef4444',
            text=[f"${pnl:,.2f}"], textposition='outside', width=0.4
        ))
        fig.update_layout(title=f"Trade Result: {'🟢 Profit' if pnl > 0 else '🔴 Loss'}",
                          yaxis_title="PnL ($)", height=350, showlegend=False,
                          margin=dict(l=40,r=40,t=40,b=40), **CHART_BG)
        return fig

    tp = trader_positions.sort_values('close_time').copy()
    tp['cumulative'] = tp['realized_pnl'].cumsum()

    if density == "sparse":
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=tp['close_time'], y=tp['cumulative'],
            mode='lines+markers', line=dict(shape='hv', width=3, color='#6366f1'),
            marker=dict(size=12, symbol='diamond', color='#6366f1'),
            fill='tozeroy', fillcolor='rgba(99,102,241,0.1)'
        ))
        fig.update_layout(title="📈 Your Trading Performance",
                          xaxis_title="Date", yaxis_title="Cumulative PnL ($)",
                          height=350, margin=dict(l=40,r=40,t=40,b=40), **CHART_BG)
        return fig

    # Dense: equity curve with trend
    tp['idx'] = range(len(tp))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tp['close_time'], y=tp['cumulative'],
        line=dict(color='#6366f1', width=3),
        fill='tozeroy', fillcolor='rgba(99,102,241,0.1)', name='Your PnL'
    ))
    z = np.polyfit(tp['idx'], tp['cumulative'], 1)
    fig.add_trace(go.Scatter(
        x=tp['close_time'], y=np.polyval(z, tp['idx']),
        mode='lines', line=dict(color='#f59e0b', width=2, dash='dash'), name='Trend'
    ))
    fig.update_layout(
        title="📈 Your Equity Curve with Trend",
        xaxis_title="Date", yaxis_title="Cumulative PnL ($)", height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40,r=40,t=40,b=40), **CHART_BG
    )
    return fig


# ============================================================================
# LIQUIDATION ANALYTICS — adaptive
# ============================================================================

def render_liquidation_kpis(positions_df):
    """Simplified KPI view when trader count is low."""
    context_note("Limited traders — showing simplified summary view")
    liq = positions_df[positions_df['close_reason'] == 'liquidation']
    total = len(positions_df[positions_df['close_reason'].isin(['closed', 'liquidation'])])
    rate = (len(liq) / total * 100) if total > 0 else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Liquidations", len(liq))
    c2.metric("Liq Rate", f"{rate:.1f}%")
    c3.metric("Loss from Liq", f"${abs(liq['realized_pnl'].sum()):,.0f}")


def render_liquidation_loss_bar(positions_df):
    """Bar chart of liquidation loss per trader."""
    context_note("Low variance in liquidation rates — showing loss comparison")
    liq = positions_df[positions_df['close_reason'] == 'liquidation']
    if liq.empty:
        st.success("✅ No liquidations in selected period")
        return
    df = liq.groupby('trader_id')['realized_pnl'].sum().abs().reset_index()
    df['trader'] = df['trader_id'].apply(mask_trader_id)
    df = df.sort_values('realized_pnl', ascending=False)
    fig = px.bar(df, x='trader', y='realized_pnl', title='Liquidation Loss by Trader',
                 color='realized_pnl', color_continuous_scale='Reds',
                 labels={'realized_pnl': 'Loss ($)'})
    fig.update_layout(height=350, **CHART_BG)
    st.plotly_chart(fig, use_container_width=True, key="liq_bar_loss")


def render_liquidation_scatter(positions_df):
    """Scatter: trading activity vs liquidation rate."""
    trader_stats = []
    for trader in positions_df['trader_id'].unique():
        td = positions_df[positions_df['trader_id'] == trader]
        total = len(td[td['close_reason'].isin(['closed', 'liquidation'])])
        if total > 0:
            liq_n = len(td[td['close_reason'] == 'liquidation'])
            trader_stats.append({
                'trader': mask_trader_id(trader),
                'total_trades': total,
                'liquidation_rate': liq_n / total * 100,
                'abs_pnl': abs(td['realized_pnl'].sum()),
                'total_pnl': td['realized_pnl'].sum(),
                'liq_count': liq_n,
                'products': ', '.join(td['product_type'].unique())
            })
    if not trader_stats:
        return
    df = pd.DataFrame(trader_stats)
    fig = px.scatter(df, x='total_trades', y='liquidation_rate', size='abs_pnl',
                     color='liquidation_rate', hover_data=['trader','liq_count','total_pnl','products'],
                     color_continuous_scale='RdYlGn_r',
                     title='Liquidation Risk vs Trading Activity',
                     labels={'total_trades':'Total Trades','liquidation_rate':'Liq Rate (%)','abs_pnl':'|PnL|'})
    fig.update_layout(height=400, **CHART_BG)
    fig.add_hline(y=5, line_dash="dash", line_color="#ef4444", annotation_text="High Risk")
    fig.add_hline(y=2, line_dash="dash", line_color="#10b981", annotation_text="Low Risk")
    st.plotly_chart(fig, use_container_width=True, key="liq_scatter")


def display_liquidation_analytics(positions_df, is_personal_mode=False, trader_id=None):
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("⚠️ Liquidation Risk Monitoring")
    st.markdown('</div>', unsafe_allow_html=True)

    if 'close_reason' not in positions_df.columns:
        st.info("ℹ️ Liquidation tracking not available")
        return

    if is_personal_mode and trader_id:
        tp = positions_df[positions_df['trader_id'] == trader_id]
        liq = tp[tp['close_reason'] == 'liquidation']
        st.markdown("### ⚠️ Your Riskiest Trades")
        if liq.empty:
            st.success("✅ No liquidations in your history!")
            return
        worst = tp.nsmallest(5, 'realized_pnl').copy()
        worst['symbol'] = worst['market_id'].apply(simplify_symbol)
        fig = px.bar(worst, x='symbol', y='realized_pnl', title='Your Top 5 Loss-Making Trades',
                     color='realized_pnl', color_continuous_scale='Reds_r',
                     labels={'realized_pnl':'Loss ($)'})
        fig.update_layout(height=350, **CHART_BG)
        st.plotly_chart(fig, use_container_width=True, key="personal_liq_bar")
        return

    liq = positions_df[positions_df['close_reason'] == 'liquidation']
    if liq.empty:
        st.success("✅ No liquidations in selected period")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Liquidations", len(liq))
    c2.metric("Affected Traders", liq['trader_id'].nunique())
    c3.metric("Total Loss", f"${abs(liq['realized_pnl'].sum()):,.0f}")

    # Adaptive chart selection
    chart_type = choose_liquidation_chart(positions_df)
    if chart_type == "kpi_only":
        render_liquidation_kpis(positions_df)
    elif chart_type == "bar_chart_loss":
        render_liquidation_loss_bar(positions_df)
    else:
        render_liquidation_scatter(positions_df)

    # Liquidation rate per trader bar
    st.subheader("📊 Liquidation Rate by Trader")
    st.caption("% of trades ending in liquidation — lower is better")
    stats = []
    for trader in positions_df['trader_id'].unique():
        td = positions_df[positions_df['trader_id'] == trader]
        total = len(td[td['close_reason'].isin(['closed','liquidation'])])
        if total > 0:
            liq_n = len(td[td['close_reason'] == 'liquidation'])
            stats.append({'trader': mask_trader_id(trader), 'liq_rate': liq_n/total*100,
                          'liq_count': liq_n, 'total_trades': total})
    if stats:
        df = pd.DataFrame(stats).sort_values('liq_rate', ascending=False)
        colors = ['#10b981' if x<2 else '#f59e0b' if x<5 else '#ef4444' for x in df['liq_rate']]
        fig = go.Figure(go.Bar(
            x=df['trader'], y=df['liq_rate'], marker_color=colors,
            text=[f"{r:.1f}%\n({l}/{t})" for r,l,t in zip(df['liq_rate'],df['liq_count'],df['total_trades'])],
            textposition='outside'
        ))
        fig.add_hline(y=2, line_dash="dash", line_color="#10b981", annotation_text="Low Risk")
        fig.add_hline(y=5, line_dash="dash", line_color="#ef4444", annotation_text="High Risk")
        fig.update_layout(height=350, xaxis_title="Trader", yaxis_title="Liq Rate (%)", **CHART_BG)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True, key="liq_rate_bar")

    st.subheader("💰 Financial Impact")
    c1, c2 = st.columns(2)
    with c1:
        bm = liq.groupby('market_id')['realized_pnl'].sum().abs().reset_index()
        bm['symbol'] = bm['market_id'].apply(simplify_symbol)
        bm = bm.sort_values('realized_pnl', ascending=False).head(5)
        fig = px.bar(bm, x='symbol', y='realized_pnl', title='Top 5 Markets by Liq Loss',
                     color='realized_pnl', color_continuous_scale='Reds')
        fig.update_layout(height=300, **CHART_BG)
        st.plotly_chart(fig, use_container_width=True, key="liq_mkt")
    with c2:
        bt = liq.groupby('trader_id')['realized_pnl'].sum().abs().reset_index()
        bt['trader'] = bt['trader_id'].apply(mask_trader_id)
        bt = bt.sort_values('realized_pnl', ascending=False).head(5)
        fig = px.bar(bt, x='trader', y='realized_pnl', title='Top 5 Traders by Liq Loss',
                     color='realized_pnl', color_continuous_scale='Reds')
        fig.update_layout(height=300, **CHART_BG)
        st.plotly_chart(fig, use_container_width=True, key="liq_trader")


# ============================================================================
# VOLUME ANALYSIS — adaptive, unique keys fix
# ============================================================================

def display_volume_analysis(positions_df):
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("📊 Trading Volume Analysis")
    st.markdown('</div>', unsafe_allow_html=True)

    if positions_df.empty:
        st.info("No volume data available")
        return

    positions_df = calculate_volume_usd(positions_df)
    product_counts = positions_df['product_type'].value_counts()
    st.caption(f"Product types present: {', '.join(f'{k}({v})' for k,v in product_counts.items())}")

    total_vol  = positions_df['volume_usd'].sum()
    total_fees = positions_df['fees'].sum()
    unique_sym = positions_df['market_id'].apply(simplify_symbol).nunique()
    vol_shares = positions_df.groupby(positions_df['market_id'].apply(simplify_symbol))['volume_usd'].sum() / total_vol
    hhi = (vol_shares**2).sum() * 10000

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Volume",  f"${total_vol:,.0f}")
    c2.metric("Total Fees",    f"${total_fees:,.0f}")
    c3.metric("Active Symbols", unique_sym)
    c4.metric("Concentration", f"{hhi:.0f} ({'Low' if hhi<1500 else 'Medium' if hhi<2500 else 'High'})")

    # Adaptive trade-size visualization
    st.subheader("📊 Trade Size Distribution")
    chart_type = choose_trade_size_chart(positions_df)
    if chart_type == "kpi_only":
        context_note("Too few trades for a distribution chart — showing summary stats")
        k1,k2 = st.columns(2)
        k1.metric("Average Trade", f"${positions_df['volume_usd'].mean():,.0f}")
        k2.metric("Median Trade",  f"${positions_df['volume_usd'].median():,.0f}")
    elif chart_type == "strip":
        context_note("Limited size variety — showing strip plot")
        fig = px.strip(positions_df, x='product_type', y='volume_usd',
                       color='product_type', title='Trade Sizes by Product',
                       color_discrete_map={'spot':'#10b981','perp':'#6366f1','option':'#f59e0b'})
        fig.update_layout(height=300, showlegend=False, **CHART_BG)
        st.plotly_chart(fig, use_container_width=True, key="strip_overall")
    else:
        # Box + histogram
        c1,c2 = st.columns(2)
        with c1:
            fig = px.box(positions_df, x='product_type', y='volume_usd', points='all',
                         title='Trade Size by Product Type',
                         color='product_type',
                         color_discrete_map={'spot':'#10b981','perp':'#6366f1','option':'#f59e0b'})
            fig.update_layout(height=300, showlegend=False, **CHART_BG)
            st.plotly_chart(fig, use_container_width=True, key="box_overall")
        with c2:
            fig = px.histogram(positions_df, x='volume_usd', nbins=30,
                               title='Trade Size Histogram',
                               color_discrete_sequence=['#6366f1'])
            fig.update_layout(height=300, showlegend=False, **CHART_BG)
            st.plotly_chart(fig, use_container_width=True, key="hist_overall")

    # Stats row
    vals = positions_df['volume_usd']
    s1,s2,s3,s4,s5 = st.columns(5)
    s1.metric("Median", f"${vals.median():,.0f}")
    s2.metric("Mean",   f"${vals.mean():,.0f}")
    s3.metric("P25",    f"${vals.quantile(0.25):,.0f}")
    s4.metric("P75",    f"${vals.quantile(0.75):,.0f}")
    s5.metric("Max",    f"${vals.max():,.0f}")

    # Per-product tabs — all plotly_chart calls get unique keys via tab_idx
    tabs = st.tabs(["📈 All", "📍 Spot", "⚡ Perp", "🎯 Options"])
    products = {
        "All":     positions_df,
        "Spot":    positions_df[positions_df['product_type'] == 'spot'],
        "Perp":    positions_df[positions_df['product_type'] == 'perp'],
        "Options": positions_df[positions_df['product_type'] == 'option'],
    }

    for tidx, (tab, (pname, pdf)) in enumerate(zip(tabs, products.items())):
        with tab:
            if pdf.empty:
                st.info(f"No {pname} trades in selected period")
                continue
            st.caption(f"{len(pdf)} trades")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### Volume by Symbol — Top 5")
                sym_vol = pdf.groupby(pdf['market_id'].apply(simplify_symbol)).agg(
                    volume_usd=('volume_usd','sum'), realized_pnl=('realized_pnl','sum')
                ).sort_values('volume_usd', ascending=False).head(5)

                if not sym_vol.empty:
                    total = sym_vol['volume_usd'].sum()
                    for sym, row in sym_vol.iterrows():
                        pct = row['volume_usd']/total*100 if total>0 else 0
                        pc  = "#10b981" if row['realized_pnl']>0 else "#ef4444"
                        st.markdown(f"""
                        <div style='background:rgba(30,41,59,0.4);border-radius:8px;padding:8px;margin-bottom:6px;'>
                            <div style='display:flex;justify-content:space-between;margin-bottom:4px;'>
                                <span style='color:#94a3b8;font-size:.8rem;'>{sym}</span>
                                <span style='color:#f1f5f9;font-size:.85rem;font-weight:600;'>
                                    ${row['volume_usd']:,.0f} ({pct:.1f}%) <span style='color:{pc};'>${row['realized_pnl']:,.0f}</span>
                                </span>
                            </div>
                            <div style='background:rgba(100,116,139,.3);border-radius:4px;height:5px;'>
                                <div style='background:#6366f1;width:{pct}%;height:100%;border-radius:4px;'></div>
                            </div>
                        </div>""", unsafe_allow_html=True)

                st.markdown("#### Fee Generation")
                fsym = pdf.groupby(pdf['market_id'].apply(simplify_symbol))['fees'].sum().sort_values(ascending=False).head(5)
                if not fsym.empty:
                    fig = px.bar(x=fsym.values, y=fsym.index, orientation='h',
                                 title='Top 5 Symbols by Fees', color=fsym.values,
                                 color_continuous_scale='Reds')
                    fig.update_layout(height=200, **CHART_BG, margin=dict(l=80))
                    st.plotly_chart(fig, use_container_width=True, key=f"fee_{tidx}")

            with c2:
                # Adaptive win-rate / long-short
                wrchart = choose_win_rate_chart(pdf)
                if wrchart == "kpi":
                    context_note("Only one direction traded — showing single KPI")
                    side_name = pdf['side'].str.lower().iloc[0]
                    win_r = (pdf['realized_pnl'] > 0).mean() * 100
                    st.metric(f"Win Rate ({side_name.title()} only)", f"{win_r:.1f}%")
                else:
                    st.markdown("#### Long vs Short Distribution")
                    long_vol  = pdf[pdf['side'].str.lower().isin(['long','buy'])]['volume_usd'].sum()
                    short_vol = pdf[pdf['side'].str.lower().isin(['short','sell'])]['volume_usd'].sum()
                    total_v   = long_vol + short_vol
                    if total_v > 0:
                        lp = long_vol/total_v*100
                        sp = short_vol/total_v*100
                        fig = go.Figure()
                        fig.add_trace(go.Bar(y=['Direction'], x=[lp], name='Long', orientation='h',
                                             marker_color='#10b981', text=f'{lp:.1f}%',
                                             textposition='inside', textfont=dict(color='white', size=14)))
                        fig.add_trace(go.Bar(y=['Direction'], x=[sp], name='Short', orientation='h',
                                             marker_color='#ef4444', text=f'{sp:.1f}%',
                                             textposition='inside', textfont=dict(color='white', size=14)))
                        fig.update_layout(barmode='stack', height=80,
                                          legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1),
                                          margin=dict(l=40,r=20,t=30,b=10), **CHART_BG)
                        st.plotly_chart(fig, use_container_width=True, key=f"ls_{tidx}")
                        ratio = long_vol/short_vol if short_vol>0 else float('inf')
                        st.metric("Long/Short Ratio", f"{ratio:.2f}x" if ratio!=float('inf') else "N/A (No shorts)")

                # Adaptive PnL distribution
                st.markdown("#### PnL Distribution")
                pnl_chart = choose_pnl_chart(pdf)
                if pnl_chart == "list":
                    context_note("Too few trades — showing individual trade list")
                    st.dataframe(pdf[['market_id','side','realized_pnl']].assign(
                        market_id=pdf['market_id'].apply(simplify_symbol),
                        realized_pnl=pdf['realized_pnl'].apply(lambda x: f"${x:,.2f}")
                    ), use_container_width=True, hide_index=True, key=f"pnl_list_{tidx}")
                elif pnl_chart == "boxplot":
                    context_note("Extreme skew detected — using box plot for clarity")
                    fig = px.box(pdf, y='realized_pnl', title='PnL Distribution (Skewed)',
                                 color_discrete_sequence=['#6366f1'])
                    fig.update_layout(height=250, **CHART_BG)
                    st.plotly_chart(fig, use_container_width=True, key=f"pnl_box_{tidx}")
                else:
                    fig = px.histogram(pdf, x='realized_pnl', nbins=20,
                                       title='PnL Distribution',
                                       color_discrete_sequence=['#6366f1'])
                    fig.add_vline(x=0, line_dash="dash", line_color="gray")
                    fig.update_layout(height=250, **CHART_BG)
                    st.plotly_chart(fig, use_container_width=True, key=f"pnl_hist_{tidx}")


# ============================================================================
# ORDER TYPE PERFORMANCE — enhanced with table + heatmap
# ============================================================================

def display_order_type_performance(order_df):
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("📋 Order Type Performance")
    st.markdown('</div>', unsafe_allow_html=True)

    if order_df.empty:
        st.info("No order type data available")
        return

    # Primary: dual-axis bar+line
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(
        x=order_df['order_type'], y=order_df['win_rate']*100,
        name='Win Rate %', marker_color='#6366f1',
        text=[f"{w:.1f}%" for w in order_df['win_rate']*100],
        textposition='inside', textfont=dict(color='white', size=11),
        hovertemplate='<b>%{x}</b><br>Win Rate: %{y:.1f}%<br>Trades: %{customdata}<extra></extra>',
        customdata=order_df['trade_count']
    ), secondary_y=False)

    colors = ['#10b981' if x>0 else '#ef4444' for x in order_df['avg_pnl']]
    fig.add_trace(go.Scatter(
        x=order_df['order_type'], y=order_df['avg_pnl'],
        name='Avg PnL $', mode='lines+markers',
        line=dict(color='#f1f5f9', width=3),
        marker=dict(size=12, color=colors, line=dict(color='#1e293b', width=2)),
        text=[f"${x:,.0f}" for x in order_df['avg_pnl']],
        textposition='top center',
        hovertemplate='<b>%{x}</b><br>Avg PnL: $%{y:,.2f}<extra></extra>'
    ), secondary_y=True)

    fig.update_layout(title="Win Rate & Avg PnL by Order Type", xaxis_title="Order Type",
                      hovermode='x unified', height=400, **CHART_BG,
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                      margin=dict(l=40,r=40,t=50,b=40))
    fig.update_yaxes(title_text="Win Rate (%)", secondary_y=False, range=[0,100])
    fig.update_yaxes(title_text="Avg PnL ($)", secondary_y=True)
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, secondary_y=True)
    st.plotly_chart(fig, use_container_width=True, key="order_main")

    # Summary KPIs
    c1,c2,c3 = st.columns(3)
    c1.metric("🏆 Best Win Rate", f"{order_df['win_rate'].max()*100:.1f}%",
              order_df.loc[order_df['win_rate'].idxmax(),'order_type'])
    c2.metric("💰 Best Avg PnL", f"${order_df['avg_pnl'].max():,.2f}",
              order_df.loc[order_df['avg_pnl'].idxmax(),'order_type'])
    c3.metric("📊 Most Used",    f"{order_df['trade_count'].max()} trades",
              order_df.loc[order_df['trade_count'].idxmax(),'order_type'])

    # Full data table
    st.subheader("📋 Detailed Breakdown")
    disp = order_df.copy()
    disp['win_rate'] = (disp['win_rate']*100).apply(lambda x: f"{x:.1f}%")
    disp['avg_pnl']  = disp['avg_pnl'].apply(lambda x: f"${x:,.2f}")
    if 'total_volume' in disp.columns:
        disp['total_volume'] = disp['total_volume'].apply(lambda x: f"${x:,.0f}")
    st.dataframe(disp, use_container_width=True, hide_index=True)

    # Volume heatmap if enough data
    if 'total_volume' in order_df.columns and len(order_df) > 2:
        st.subheader("📊 Volume & Trade Count Heatmap")
        heat_vals = order_df[['order_type','trade_count']].set_index('order_type').T
        fig2 = px.imshow(heat_vals, text_auto=True, aspect='auto',
                         color_continuous_scale='Blues',
                         title='Trade Count by Order Type')
        fig2.update_layout(height=150, **CHART_BG)
        st.plotly_chart(fig2, use_container_width=True, key="order_heatmap")


# ============================================================================
# GREEKS — adaptive for single trader
# ============================================================================

def compute_greeks_per_position(positions_df):
    opts = positions_df[positions_df['product_type'] == 'option'].copy()
    if opts.empty:
        return pd.DataFrame()
    rows = []
    for _, pos in opts.iterrows():
        is_call = 'CALL' in str(pos['market_id']).upper()
        if pos['side'] == 'buy':
            delta = abs(pos['size']) if is_call else -abs(pos['size'])
        else:
            delta = -abs(pos['size']) if is_call else abs(pos['size'])
        rows.append({'position_id': pos['position_id'], 'trader_id': pos['trader_id'], 'delta': delta})
    return pd.DataFrame(rows)


def display_greeks_analysis(greeks_df, is_personal=False):
    st.markdown('<div class="section-header">', unsafe_allow_html=True)
    st.header("🔬 Options Greeks Exposure")
    st.markdown('</div>', unsafe_allow_html=True)

    if greeks_df.empty:
        st.info("No options Greeks data available")
        return

    total_delta = greeks_df['net_delta'].sum()
    delta_color = "#10b981" if total_delta > 0 else "#ef4444"
    total_pos   = greeks_df['total_option_positions'].sum()

    c1,c2,c3,c4 = st.columns(4)
    for col, label, val, sub in [
        (c1, "Net Delta",  f"<span style='color:{delta_color};font-size:1.2rem;font-weight:600;'>{total_delta:,.2f}</span>", "Directional exposure"),
        (c2, "Gamma",      "<span style='color:#f59e0b;font-size:1.2rem;font-weight:600;'>🔜 Soon</span>", "Delta sensitivity"),
        (c3, "Theta",      "<span style='color:#f59e0b;font-size:1.2rem;font-weight:600;'>🔜 Soon</span>", "Time decay/day"),
        (c4, "Positions",  f"<span style='color:#f1f5f9;font-size:1.2rem;font-weight:600;'>{int(total_pos)}</span>", "Active contracts"),
    ]:
        col.markdown(f"""
        <div style='background:rgba(30,41,59,0.4);padding:10px;border-radius:8px;text-align:center;'>
            <div style='color:#94a3b8;font-size:.7rem;'>{label}</div>
            {val}
            <div style='color:#64748b;font-size:.6rem;'>{sub}</div>
        </div>""", unsafe_allow_html=True)

    disp = greeks_df.copy()
    disp['trader'] = disp['trader_id'].apply(mask_trader_id)
    disp = disp.sort_values('net_delta', ascending=False)

    # Adaptive: single trader gets per-position breakdown; multi-trader gets bar
    if is_personal or disp['trader_id'].nunique() == 1:
        context_note("Single trader view — showing per-position delta breakdown")
        st.subheader("📊 Per-Position Delta")
        per_pos = compute_greeks_per_position(
            pd.DataFrame({'product_type':['option'], 'market_id':['CALL'], 'side':['buy'], 'size':[1], 'position_id':[0], 'trader_id':[0]})
        )
        # Use the greeks_df data directly for display
        disp2 = disp[['trader','net_delta','total_option_positions']].copy()
        disp2.columns = ['Trader', 'Net Delta', 'Option Positions']
        disp2['Net Delta'] = disp2['Net Delta'].apply(lambda x: f"{x:+.3f}")
        st.dataframe(disp2, use_container_width=True, hide_index=True)

        # Delta gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number", value=total_delta,
            title={'text': "Net Delta Exposure"},
            gauge={'axis': {'range': [-abs(total_delta)*2, abs(total_delta)*2]},
                   'bar': {'color': "#10b981" if total_delta >= 0 else "#ef4444"},
                   'steps': [
                       {'range': [-abs(total_delta)*2, 0], 'color': 'rgba(239,68,68,0.1)'},
                       {'range': [0, abs(total_delta)*2], 'color': 'rgba(16,185,129,0.1)'}
                   ]}
        ))
        fig.update_layout(height=280, **CHART_BG)
        st.plotly_chart(fig, use_container_width=True, key="delta_gauge")
    else:
        st.subheader("📊 Delta Exposure by Trader")
        fig = px.bar(disp, x='trader', y='net_delta', color='net_delta',
                     color_continuous_scale='RdBu', color_continuous_midpoint=0,
                     title='Net Delta by Trader')
        fig.update_layout(height=350, **CHART_BG)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True, key="delta_bar_multi")


# ============================================================================
# TRANSACTION HISTORY — volume_usd, horizontal scroll, clickable verify
# ============================================================================

def display_transaction_history(positions_df):
    st.markdown("### 📋 Transaction History")
    if positions_df.empty:
        st.info("No transactions to display")
        return

    df = positions_df.copy()
    df['symbol']     = df['market_id'].apply(simplify_symbol)
    df['trader']     = df['trader_id'].apply(mask_trader_id)
    df['volume_usd'] = df['exit_price'] * df['size']

    page_size   = 10
    total_pages = max(1, (len(df) - 1) // page_size + 1)
    page        = st.number_input("Page", 1, total_pages, 1, key="tx_page")
    start, end  = (page-1)*page_size, min(page*page_size, len(df))
    ddf         = df.iloc[start:end].copy()

    cols = ['close_time','trader','symbol','product_type','side',
            'entry_price','exit_price','size','volume_usd','realized_pnl','fees','close_reason']

    fmt = {
        'close_time':   lambda x: pd.to_datetime(x).strftime('%Y-%m-%d %H:%M'),
        'entry_price':  lambda x: f"${x:,.2f}",
        'exit_price':   lambda x: f"${x:,.2f}",
        'size':         lambda x: f"{x:,.4f}",
        'volume_usd':   lambda x: f"${x:,.0f}",
        'realized_pnl': lambda x: f"${x:,.2f}",
        'fees':         lambda x: f"${x:,.2f}",
    }
    for col, fn in fmt.items():
        if col in ddf.columns:
            ddf[col] = ddf[col].apply(fn)

    if 'close_tx_hash' in ddf.columns:
        ddf['Verify'] = ddf['close_tx_hash'].apply(
            lambda tx: f'<a href="https://solscan.io/tx/{tx}" target="_blank" class="verify-link">🔗 Verify</a>'
            if pd.notna(tx) and str(tx).strip() else '—'
        )
        cols.append('Verify')

    html = ddf[cols].to_html(escape=False, index=False, classes='tx-table')
    st.markdown(f'<div class="scroll-x">{html}</div>', unsafe_allow_html=True)
    st.caption(f"Showing {start+1}–{end} of {len(df)} transactions")

    csv = positions_df.to_csv(index=False)
    st.download_button("📥 Download CSV", csv,
                       f"transactions_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")


# ============================================================================
# KPI BAR
# ============================================================================

def display_global_kpis(positions_df, summary_df, selected_trader=None):
    total_pnl  = positions_df['realized_pnl'].sum()  if not positions_df.empty else 0
    win_rate   = (positions_df['realized_pnl']>0).mean()*100 if not positions_df.empty else 0
    trade_count= len(positions_df)

    if selected_trader and not summary_df.empty:
        td = summary_df[summary_df['trader_id']==selected_trader]
        sharpe  = td['sharpe_ratio'].iloc[0]  if not td.empty else 0
        sortino = td['sortino_ratio'].iloc[0] if not td.empty and 'sortino_ratio' in td.columns else 0
    else:
        sharpe  = summary_df['sharpe_ratio'].mean()  if not summary_df.empty and 'sharpe_ratio'  in summary_df.columns else 0
        sortino = summary_df['sortino_ratio'].mean() if not summary_df.empty and 'sortino_ratio' in summary_df.columns else 0

    cols = st.columns(5)
    for col, label, val in zip(cols,
        ["NET PNL","WIN RATE","TRADES","SHARPE","SORTINO"],
        [f"${total_pnl:,.2f}", f"{win_rate:.1f}%", str(trade_count), f"{sharpe:.2f}", f"{sortino:.2f}"]
    ):
        col.markdown(f"""
        <div class='metric-major'>
            <div class='metric-major-label'>{label}</div>
            <div class='metric-major-value'>{val}</div>
        </div>""", unsafe_allow_html=True)


# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_logo(url):
    try:
        r = requests.get(url, timeout=5)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None


@st.cache_data
def load_data():
    try:
        return {
            'equity':        pd.read_csv(DATA_DIR/"equity_curve.csv",     parse_dates=["timestamp"]),
            'positions':     pd.read_csv(DATA_DIR/"positions.csv",         parse_dates=["open_time","close_time"]),
            'summary':       pd.read_csv(DATA_DIR/"summary_metrics.csv"),
            'fees':          pd.read_csv(DATA_DIR/"fees_breakdown.csv"),
            'volume':        pd.read_csv(DATA_DIR/"volume_by_market.csv"),
            'pnl_day':       pd.read_csv(DATA_DIR/"pnl_by_day.csv",        parse_dates=["date"]),
            'pnl_hour':      pd.read_csv(DATA_DIR/"pnl_by_hour.csv"),
            'directional':   pd.read_csv(DATA_DIR/"directional_bias.csv"),
            'order_perf':    pd.read_csv(DATA_DIR/"order_type_performance.csv"),
            'greeks':        pd.read_csv(DATA_DIR/"greeks_exposure.csv"),
            'open_positions':pd.read_csv(DATA_DIR/"open_positions.csv",    parse_dates=["open_time"]),
        }
    except FileNotFoundError as e:
        st.error(f"❌ Data files not found: {e}")
        return None


with st.spinner('🔄 Loading analytics...'):
    data = load_data()

if data is None or (data['positions'].empty and data['open_positions'].empty):
    st.error("❌ No analytics data found")
    st.info("💡 Run: `python -m scripts.run_analytics`")
    st.stop()


# ============================================================================
# SIDEBAR
# ============================================================================

logo_url = ("https://deriverse.gitbook.io/deriverse-v1/~gitbook/image"
            "?url=https%3A%2F%2F3705106568-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com"
            "%2Fo%2Forganizations%252FVbKUpgicSXo9QHWM7uzI%252Fsites%252Fsite_oPxtF%252Ficon%252FNsfAUtLJH778Cn5Dd7zK"
            "%252Ffavicon.ico%3Falt%3Dmedia%26token%3D4099bf73-ccd6-4d9f-8bbb-01cdc664ddb0"
            "&width=32&dpr=3&quality=100&sign=13d31bb2&sv=2")

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
    data['positions']['trader_id']      if not data['positions'].empty      else pd.Series([]),
    data['open_positions']['trader_id'] if not data['open_positions'].empty else pd.Series([])
]).unique())

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "all_traders"

if st.session_state.view_mode == "all_traders":
    st.sidebar.info("🌐 **Mode:** All Traders View")
    wallet_input = st.sidebar.text_input("Enter Your Wallet Address",
                                          placeholder="7KNXqvHu2QWvDq8cGPGvKZhFvYnz...")
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
        st.sidebar.success(f"✅ **Personal Mode:** {mask_trader_id(st.session_state.authenticated_trader)}")
        if st.sidebar.button("👥 Return to All Traders View"):
            st.session_state.view_mode = "all_traders"
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Filters")
st.sidebar.markdown("**📅 Date Range**")

if is_admin:
    date_option = st.sidebar.radio("Range", ["Last 7 Days","Last 30 Days","All Time","Custom"],
                                    index=1, horizontal=True, label_visibility="collapsed")
else:
    date_option = st.sidebar.radio("Range", ["Last 7 Days","Last 30 Days","Custom (Admin Only)"],
                                    index=1, horizontal=True, label_visibility="collapsed")
    if date_option == "Custom (Admin Only)":
        st.sidebar.warning("🔐 Requires admin authentication")
        date_option = "Last 30 Days"

if not data['positions'].empty:
    min_date = data['positions']['close_time'].min().date()
    max_date = data['positions']['close_time'].max().date()
    if   date_option == "Last 7 Days":  start_date, end_date = max_date-timedelta(7),  max_date
    elif date_option == "Last 30 Days": start_date, end_date = max_date-timedelta(30), max_date
    elif date_option in ("Custom","Custom (Admin Only)") and is_admin:
        sc1,sc2 = st.sidebar.columns(2)
        start_date = sc1.date_input("From", min_date, min_value=min_date, max_value=max_date)
        end_date   = sc2.date_input("To",   max_date, min_value=min_date, max_value=max_date)
    else:
        start_date, end_date = min_date, max_date

all_markets    = sorted(data['positions']['market_id'].unique()) if not data['positions'].empty else []
unique_symbols = sorted(set(simplify_symbol(m) for m in all_markets))
selected_symbols = st.sidebar.multiselect("Symbols", unique_symbols, default=[])
selected_markets = [m for m in all_markets if simplify_symbol(m) in selected_symbols] if selected_symbols else []
st.sidebar.markdown("---")


# ============================================================================
# APPLY FILTERS
# ============================================================================

filtered_positions = data['positions'].copy() if not data['positions'].empty else pd.DataFrame()
filtered_open      = data['open_positions'].copy() if not data['open_positions'].empty else pd.DataFrame()

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

if selected_markets:
    if not filtered_positions.empty: filtered_positions = filtered_positions[filtered_positions['market_id'].isin(selected_markets)]
    if not filtered_open.empty:      filtered_open      = filtered_open[filtered_open['market_id'].isin(selected_markets)]

if not filtered_positions.empty:
    filtered_positions = calculate_volume_usd(filtered_positions)


# ============================================================================
# FIXED HEADER
# ============================================================================

if "nav" not in st.session_state:
    st.session_state.nav = "overview"

st.markdown('<div class="fixed-header">', unsafe_allow_html=True)

hc1, hc2 = st.columns([1, 8])
with hc1:
    if logo_bytes: st.image(logo_bytes, width=50)
    else:          st.markdown("### 🔷")
with hc2:
    st.markdown('<div class="header-title">Deriverse Trading Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="header-subtitle">Real-time performance insights • Local-first security</div>', unsafe_allow_html=True)

if st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state:
    st.markdown(f"<div class='profile-badge'>🔐 {mask_trader_id(st.session_state.authenticated_trader)}</div>",
                unsafe_allow_html=True)

nav_items = [("📊 Overview","overview"),("📈 Performance","performance"),("⚠️ Risk","risk"),
             ("📊 Volume","volume"),("📋 Orders","orders"),("🔬 Greeks","greeks"),("📝 Journal","journal")]

nav_cols = st.columns(len(nav_items))
for col, (label, nav_key) in zip(nav_cols, nav_items):
    with col:
        if st.button(label, key=f"nav_{nav_key}", use_container_width=True,
                     type="primary" if st.session_state.nav==nav_key else "secondary"):
            st.session_state.nav = nav_key
            st.rerun()

st.markdown('<div class="kpi-row">', unsafe_allow_html=True)
display_global_kpis(filtered_positions, data['summary'], selected_trader)
st.markdown('</div></div>', unsafe_allow_html=True)
st.markdown('<div class="main-content">', unsafe_allow_html=True)


# ============================================================================
# OPEN POSITIONS
# ============================================================================

if st.session_state.nav == "overview" and not filtered_open.empty:
    st.markdown("### 📊 Open Positions")
    st.warning(f"⚠️ **{len(filtered_open)} Open Positions** — Unrealized PnL not included")
    od = filtered_open.copy()
    od['symbol'] = od['market_id'].apply(simplify_symbol)
    od['trader'] = od['trader_id'].apply(mask_trader_id)
    st.dataframe(od[['trader','symbol','product_type','side','entry_price','size']],
                 use_container_width=True, hide_index=True)
    st.markdown("---")


# ============================================================================
# SECTION RENDERING
# ============================================================================

if st.session_state.nav == "overview":
    if not filtered_positions.empty and not selected_trader:
        st.markdown("## 🏆 Top Performers Analysis")
        c1,c2 = st.columns(2)
        for col, label, by, scale in [(c1,"📈 Top 5 Profitable","profit","Greens"),
                                       (c2,"📉 Top 5 Loss-Making","loss","Reds_r")]:
            with col:
                st.markdown(f"### {label} Traders")
                traders = get_top_traders(filtered_positions, n=5, by=by)
                if traders:
                    rows = []
                    for t in traders:
                        tp = filtered_positions[filtered_positions['trader_id']==t]
                        rows.append({'Trader': mask_trader_id(t), 'Total PnL': tp['realized_pnl'].sum(),
                                     'Trades': len(tp), 'Win Rate': (tp['realized_pnl']>0).mean()*100})
                    df2 = pd.DataFrame(rows)
                    fig = px.bar(df2, x='Trader', y='Total PnL', color='Total PnL',
                                 color_continuous_scale=scale, text='Total PnL')
                    fig.update_traces(texttemplate='$%{text:.0f}', textposition='outside')
                    fig.update_layout(height=200, showlegend=False, **CHART_BG)
                    st.plotly_chart(fig, use_container_width=True, key=f"top_{by}")
                    st.dataframe(df2.style.format({'Total PnL':'${:,.2f}','Win Rate':'{:.1f}%'}),
                                 use_container_width=True, hide_index=True)
    st.markdown("---")
    display_transaction_history(filtered_positions)

elif st.session_state.nav == "performance":
    if not filtered_positions.empty:
        if st.session_state.view_mode == "personal" and selected_trader:
            fig = create_personal_equity_chart(filtered_positions)
            st.plotly_chart(fig, use_container_width=True, key="personal_eq")
        else:
            fig_eq, fig_dd = create_protocol_equity_charts(filtered_positions)
            st.plotly_chart(fig_eq, use_container_width=True, key="proto_eq")
            st.caption("Protocol cumulative PnL")
            st.plotly_chart(fig_dd, use_container_width=True, key="proto_dd")
            st.caption("Drawdown from peak equity")

        if not selected_trader and not data['equity'].empty:
            create_trader_summary_table(data['equity'], filtered_positions)
    else:
        st.info("No performance data for selected filters")

elif st.session_state.nav == "risk":
    if not filtered_positions.empty:
        display_liquidation_analytics(
            filtered_positions,
            is_personal_mode=(st.session_state.view_mode == "personal"),
            trader_id=selected_trader
        )
    else:
        st.info("No risk data for selected filters")

elif st.session_state.nav == "volume":
    if not filtered_positions.empty:
        display_volume_analysis(filtered_positions)
    else:
        st.info("No volume data for selected filters")

elif st.session_state.nav == "orders":
    display_order_type_performance(data['order_perf'])

elif st.session_state.nav == "greeks":
    if not data['greeks'].empty:
        gf = data['greeks'].copy()
        if selected_trader:
            gf = gf[gf['trader_id'] == selected_trader]
        if not gf.empty:
            display_greeks_analysis(gf, is_personal=(selected_trader is not None))
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

    elif st.session_state.view_mode == "personal" and selected_trader:
        trader = selected_trader
        st.markdown("""
        <div style='background:rgba(99,102,241,0.1);border-left:4px solid #6366f1;
                    padding:10px 14px;border-radius:8px;margin-bottom:16px;color:#e2e8f0;font-size:.9rem;'>
            <strong>📌 How to take notes:</strong><br>
            Click any cell in the <em>📝 Your Trading Notes</em> column and type your observations.
            Notes auto-save and persist between sessions.
        </div>""", unsafe_allow_html=True)

        trader_notes = load_trader_notes(trader)
        greeks_df    = compute_greeks_per_position(filtered_positions)

        jdf = filtered_positions.sort_values('close_time', ascending=False).copy()
        jdf['symbol']     = jdf['market_id'].apply(simplify_symbol)
        jdf['volume_usd'] = jdf['exit_price'] * jdf['size']
        jdf['notes']      = jdf['position_id'].map(lambda pid: trader_notes.get(str(pid), ""))

        if not greeks_df.empty:
            jdf = jdf.merge(greeks_df[['position_id','delta']], on='position_id', how='left')

        notes_count = sum(1 for n in jdf['notes'] if n and str(n).strip())
        st.info(f"📝 {notes_count} annotated trade{'s' if notes_count!=1 else ''}")

        avail_cols = ['close_time','symbol','product_type','side',
                      'entry_price','exit_price','size','volume_usd','realized_pnl','fees']
        if 'delta' in jdf.columns:
            avail_cols.append('delta')
        avail_cols.append('notes')

        col_cfg = {
            "close_time":   st.column_config.DatetimeColumn("Closed At", format="DD/MM/YYYY HH:mm"),
            "symbol":       "Symbol",
            "product_type": "Type",
            "side":         "Direction",
            "entry_price":  st.column_config.NumberColumn("Entry",  format="$%.2f"),
            "exit_price":   st.column_config.NumberColumn("Exit",   format="$%.2f"),
            "size":         st.column_config.NumberColumn("Size",   format="%.4f"),
            "volume_usd":   st.column_config.NumberColumn("Volume", format="$%.0f"),
            "realized_pnl": st.column_config.NumberColumn("PnL",   format="$%.2f"),
            "fees":         st.column_config.NumberColumn("Fees",   format="$%.2f"),
            "delta":        st.column_config.NumberColumn("Delta",  format="%.2f"),
            "notes":        st.column_config.TextColumn("📝 Notes", max_chars=500, width="large"),
        }

        st.markdown('<div class="scroll-x">', unsafe_allow_html=True)
        edited = st.data_editor(
            jdf[avail_cols], column_config=col_cfg,
            use_container_width=True, hide_index=True, num_rows="fixed",
            disabled=[c for c in avail_cols if c != 'notes']
        )
        st.markdown('</div>', unsafe_allow_html=True)

        updated = {}
        for idx, row in edited.iterrows():
            pid  = jdf.loc[idx, 'position_id']
            note = row.get('notes', '')
            if pd.notna(note) and str(note).strip():
                updated[str(pid)] = note
        if updated != trader_notes:
            save_trader_notes(trader, updated)
            st.success("✅ Notes saved!")

        bc1, bc2, bc3 = st.columns([3,1,1])
        with bc2:
            st.download_button("📥 Export CSV",
                               jdf[avail_cols].to_csv(index=False),
                               f"journal_{trader[:8]}.csv", "text/csv",
                               use_container_width=True)
        with bc3:
            if st.button("🗑️ Clear Notes", use_container_width=True):
                save_trader_notes(trader, {})
                st.rerun()

    else:
        if selected_trader:
            st.info(f"👁️ Read-Only View: {mask_trader_id(selected_trader)}")
        else:
            st.info("👥 Authenticate your wallet to add notes")

        jdf = filtered_positions.sort_values('close_time', ascending=False).copy()
        jdf['trader']     = jdf['trader_id'].apply(mask_trader_id)
        jdf['symbol']     = jdf['market_id'].apply(simplify_symbol)
        jdf['volume_usd'] = jdf['exit_price'] * jdf['size']
        show_cols = ['close_time','trader','symbol','product_type','side',
                     'entry_price','exit_price','size','volume_usd','realized_pnl','fees']
        st.dataframe(
            jdf[show_cols].style.format({
                'entry_price':'${:,.2f}','exit_price':'${:,.2f}','size':'{:,.4f}',
                'volume_usd':'${:,.0f}','realized_pnl':'${:,.2f}','fees':'${:,.2f}'
            }),
            use_container_width=True, hide_index=True
        )


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
fc1,fc2,fc3 = st.columns([2,1,1])
fc1.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
fc2.caption("🔐 **Admin Mode**" if is_admin else "🔒 **Secure** • Local-first")
fc3.caption("v7.4 Adaptive")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align:center;padding:20px;color:#64748b;font-size:12px;'>
    <strong>Deriverse Analytics Dashboard</strong><br>
    Read-only • No private keys required • Data stays on your machine
</div>""", unsafe_allow_html=True)