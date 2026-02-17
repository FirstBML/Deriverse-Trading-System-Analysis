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
import os
from dotenv import load_dotenv

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
# MINIMAL CSS - Only essential styling, no layout overrides
# ============================================================================

st.markdown("""
<style>
    /* Hide Streamlit's default header only */
    header[data-testid="stHeader"] { 
        display: none !important; 
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
    
    /* Profile badge */
    .profile-badge {
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
        margin: 8px 0;
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
    
    /* Debug container */
    .debug-info {
        background: #1e293b;
        border-left: 4px solid #f59e0b;
        padding: 8px 16px;
        border-radius: 4px;
        margin: 10px 0;
        font-size: 0.85rem;
        color: #e2e8f0;
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
            fig, use_container_width=True,
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

def create_protocol_equity_charts(positions_df):
    """Protocol equity + drawdown as two separate charts — no trend line."""
    
    ps = positions_df.sort_values('close_time').copy()
    ps['cumulative_pnl'] = ps['realized_pnl'].cumsum()
    
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
        title="📈 Protocol Cumulative PnL",
        xaxis_title="Date", yaxis_title="Cumulative PnL ($)",
        height=350, margin=dict(l=40, r=40, t=40, b=40), **CHART_BG
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
                    annotation_text=f"Max DD: ${max_dd:,.0f}",
                    annotation_position="bottom right")
    fig_dd.update_layout(
        title="📉 Drawdown from Peak",
        xaxis_title="Date", yaxis_title="Drawdown ($)",
        height=250, margin=dict(l=40, r=40, t=40, b=40), **CHART_BG
    )
    
    return fig_eq, fig_dd

# ============================================================================
# PERSONAL EQUITY CHART
# ============================================================================

def create_personal_equity_chart(trader_positions):
    """Adaptive equity chart for personal mode — no trend line for sparse data."""
    
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
            yaxis_title="PnL ($)", height=350, showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40), **CHART_BG
        )
        return fig
    
    tp = trader_positions.sort_values('close_time').copy()
    tp['cumulative'] = tp['realized_pnl'].cumsum()
    
    if density == "sparse":
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
            height=350, margin=dict(l=40, r=40, t=40, b=40), **CHART_BG
        )
        return fig
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tp['close_time'], y=tp['cumulative'],
        line=dict(color='#6366f1', width=3),
        fill='tozeroy', fillcolor='rgba(99,102,241,0.1)', name='Your PnL'
    ))
    
    fig.update_layout(
        title="📈 Your Equity Curve",
        xaxis_title="Date", yaxis_title="Cumulative PnL ($)",
        height=350, margin=dict(l=40, r=40, t=40, b=40), **CHART_BG
    )
    return fig

# ============================================================================
# LIQUIDATION ANALYTICS
# ============================================================================

def display_liquidation_analytics(positions_df, is_personal_mode=False, trader_id=None):
    """Liquidation analysis with close_reason handling."""
    
    st.header("⚠️ Liquidation Risk Monitoring")
    
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
        
        fig = px.bar(worst, x='symbol', y='realized_pnl',
                    title='Your Top 5 Loss-Making Trades',
                    color='realized_pnl', color_continuous_scale='Reds_r',
                    labels={'realized_pnl': 'Loss ($)'})
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
    st.plotly_chart(fig, use_container_width=True, key="liq_pie")
    
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
            
            st.plotly_chart(fig, use_container_width=True, key="liq_rate_top5")
            
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
        st.plotly_chart(fig, use_container_width=True, key="liq_mkt")
    
    with c2:
        bt = liq.groupby('trader_id')['realized_pnl'].sum().abs().reset_index()
        bt['trader'] = bt['trader_id'].apply(mask_trader_id)
        bt = bt.sort_values('realized_pnl', ascending=False).head(5)
        fig = px.bar(bt, x='trader', y='realized_pnl',
                    title='Top 5 Traders by Liq Loss',
                    color='realized_pnl', color_continuous_scale='Reds')
        fig.update_layout(height=300, **CHART_BG)
        st.plotly_chart(fig, use_container_width=True, key="liq_trader")

# ============================================================================
# VOLUME ANALYSIS
# ============================================================================

def display_volume_analysis(positions_df):
    """Volume analysis with product tabs and progress bars."""
    
    st.header("📊 Trading Volume Analysis")
    
    if positions_df.empty:
        st.info("No volume data available")
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
            st.plotly_chart(fig, use_container_width=True, key="box_overall")
        
        with c2:
            fig = px.histogram(
                positions_df, x='volume_usd', nbins=30,
                title='Trade Size Histogram',
                color_discrete_sequence=['#6366f1']
            )
            fig.update_layout(height=300, showlegend=False, **CHART_BG)
            st.plotly_chart(fig, use_container_width=True, key="hist_overall")
        
        vals = positions_df['volume_usd']
        s1, s2, s3, s4, s5 = st.columns(5)
        s1.metric("Median", f"${vals.median():,.0f}")
        s2.metric("Mean", f"${vals.mean():,.0f}")
        s3.metric("P25", f"${vals.quantile(0.25):,.0f}")
        s4.metric("P75", f"${vals.quantile(0.75):,.0f}")
        s5.metric("Max", f"${vals.max():,.0f}")
    
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
                    st.plotly_chart(fig, use_container_width=True, key=f"fee_{tidx}")
            
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
                    st.plotly_chart(fig, use_container_width=True, key=f"ls_{tidx}")
                    
                    ratio = long_vol / short_vol if short_vol > 0 else float('inf')
                    st.metric("Long/Short Ratio", f"{ratio:.2f}x" if ratio != float('inf') else "(No shorts)")
                
                st.markdown("#### PnL Distribution")
                
                if should_show_chart(pdf, min_points=3):
                    fig = px.histogram(pdf, x='realized_pnl', nbins=20,
                                      title='PnL Distribution',
                                      color_discrete_sequence=['#6366f1'])
                    fig.add_vline(x=0, line_dash="dash", line_color="gray")
                    fig.update_layout(height=250, **CHART_BG)
                    st.plotly_chart(fig, use_container_width=True, key=f"pnl_hist_{tidx}")
                else:
                    context_note("Too few trades for distribution chart - showing individual trades")
                    st.dataframe(
                        pdf[['market_id','side','realized_pnl']].assign(
                            market_id=pdf['market_id'].apply(simplify_symbol),
                            realized_pnl=pdf['realized_pnl'].apply(lambda x: f"${x:,.2f}")
                        ),
                        use_container_width=True, hide_index=True, key=f"pnl_list_{tidx}"
                    )

# ============================================================================
# ORDER TYPE PERFORMANCE
# ============================================================================

# ============================================================================
# INTEGRATED ORDER TYPE PERFORMANCE - Uses product type with all visualizations
# ============================================================================

def display_order_type_performance(order_df, positions_df=None):
    """Enhanced order type performance with multiple visualizations.
    
    Uses PRODUCT TYPE as the primary classification (spot/perp/option) 
    which is more meaningful than duration-based heuristics.
    """
    
    st.header("📊 Order Type Performance Analysis")
    
    # If we have positions data, derive order types from product type
    if positions_df is not None and not positions_df.empty:
        df = positions_df.copy()
        
        # Ensure volume_usd exists
        if 'volume_usd' not in df.columns:
            df['volume_usd'] = df['exit_price'] * df['size']
        
        # Use PRODUCT TYPE as the primary classification (more meaningful)
        if 'product_type' in df.columns:
            df['order_category'] = df['product_type']
            category_name = "Product Type"
            
            # Show distribution of product types
            product_counts = df['product_type'].value_counts()
            st.caption(f"📊 Distribution: {', '.join([f'{k}({v})' for k, v in product_counts.items()])}")
        else:
            # Fallback to duration-based if product_type missing
            df['order_category'] = df.apply(lambda row: 
                'scalp' if row['duration_seconds'] < 300 else
                'intraday' if row['duration_seconds'] < 3600 else
                'swing' if row['duration_seconds'] < 86400 else
                'position', axis=1
            )
            category_name = "Trade Duration"
        
        # Calculate metrics by category
        order_stats = df.groupby('order_category').agg({
            'realized_pnl': ['count', 'mean', 'sum'],
            'fees': 'sum',
            'volume_usd': 'sum'
        }).round(2)
        
        order_stats.columns = ['trade_count', 'avg_pnl', 'total_pnl', 'total_fees', 'total_volume']
        order_stats = order_stats.reset_index()
        
        # Calculate win rate
        order_stats['win_rate'] = df.groupby('order_category')['realized_pnl'].apply(
            lambda x: (x > 0).mean() * 100
        ).values
        
        # Calculate fee ratio
        order_stats['fee_ratio'] = (order_stats['total_fees'] / order_stats['total_volume'] * 100).fillna(0)
        
        # Rename for consistency with rest of dashboard
        order_stats.rename(columns={'order_category': 'order_type'}, inplace=True)
        
        # Add classification info
        st.info(f"📌 Classified by: **{category_name}**")
        
        # Use this as our order_df
        order_df = order_stats
    
    # Check if we have data
    if order_df.empty or len(order_df) == 0:
        st.warning("⚠️ No order type data available. Generate more trades to see patterns.")
        return
    
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
        st.plotly_chart(fig, use_container_width=True, key="order_matrix")
        
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
        
        st.plotly_chart(fig, use_container_width=True, key="order_winrate")
        
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
        
        st.plotly_chart(fig, use_container_width=True, key="order_pnl")
        
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
            st.plotly_chart(fig, use_container_width=True, key="order_fees")
            
            # Add fee efficiency explanation
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
        
        # Reorder columns for better readability
        column_order = ['order_type', 'trade_count', 'win_rate', 'avg_pnl', 
                       'total_pnl', 'total_volume', 'total_fees', 'fee_ratio']
        
        st.dataframe(
            display_df[column_order], 
            use_container_width=True, 
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
        
        # Download button
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

def compute_greeks_per_position(positions_df):
    """Compute delta for each option position."""
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
        rows.append({
            'position_id': pos['position_id'],
            'trader_id': pos['trader_id'],
            'delta': delta
        })
    return pd.DataFrame(rows)

def display_greeks_analysis(greeks_df, is_personal=False):
    """Greeks analysis — limited to 5 traders in multi-view."""
    
    st.header("🔬 Options Greeks Exposure")
    
    if greeks_df.empty:
        st.info("No options Greeks data available")
        return
    
    total_delta = greeks_df['net_delta'].sum()
    delta_color = "#10b981" if total_delta > 0 else "#ef4444"
    total_pos = greeks_df['total_option_positions'].sum()
    
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Net Delta", f"{total_delta:,.2f}", delta=None)
    with c2:
        st.metric("Gamma", "🔜 Soon", delta=None)
    with c3:
        st.metric("Theta", "🔜 Soon", delta=None)
    with c4:
        st.metric("Positions", f"{int(total_pos)}", delta=None)
    
    disp = greeks_df.copy()
    disp['trader'] = disp['trader_id'].apply(mask_trader_id)
    disp = disp.sort_values('net_delta', ascending=False)
    
    if not is_personal and len(disp) > 5:
        st.info("Showing top 5 traders by delta exposure")
        disp = disp.head(5)
    
    if is_personal or disp['trader_id'].nunique() == 1:
        st.subheader("📊 Per-Position Delta")
        
        per_pos = compute_greeks_per_position(
            pd.DataFrame({'product_type': ['option'], 'market_id': ['CALL'],
                         'side': ['buy'], 'size': [1], 'position_id': [0], 'trader_id': [0]})
        )
        
        disp2 = disp[['trader','net_delta','total_option_positions']].copy()
        disp2.columns = ['Trader','Net Delta','Option Positions']
        disp2['Net Delta'] = disp2['Net Delta'].apply(lambda x: f"{x:+.3f}")
        st.dataframe(disp2, use_container_width=True, hide_index=True)
    
    else:
        st.subheader("📊 Delta Exposure by Trader")
        
        fig = px.bar(disp, x='trader', y='net_delta', color='net_delta',
                    color_continuous_scale='RdBu', color_continuous_midpoint=0,
                    title='Net Delta by Trader')
        fig.update_layout(height=350, **CHART_BG)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True, key="delta_bar_multi")
    
    st.subheader("📋 Greeks Breakdown")
    st.dataframe(
        disp[['trader','total_option_positions','net_delta']].style.format(
            {'net_delta':'{:,.2f}','total_option_positions':'{:.0f}'}
        ),
        use_container_width=True, hide_index=True
    )

# ============================================================================
# TRANSACTION HISTORY
# ============================================================================

def display_transaction_history(positions_df):
    """Transaction history with pagination and blockchain verify links."""
    
    st.markdown("### 📋 Transaction History")
    
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

def display_global_kpis(closed_positions, summary_df, selected_trader=None):
    """Display global KPIs using ONLY closed positions."""
    
    total_pnl = closed_positions['realized_pnl'].sum() if not closed_positions.empty else 0
    win_rate = (closed_positions['realized_pnl'] > 0).mean() * 100 if not closed_positions.empty else 0
    trade_count = len(closed_positions)  # This now counts ONLY closed trades
    
    if selected_trader and not summary_df.empty:
        td = summary_df[summary_df['trader_id'] == selected_trader]
        sharpe = td['sharpe_ratio'].iloc[0] if not td.empty else 0
        sortino = td['sortino_ratio'].iloc[0] if not td.empty and 'sortino_ratio' in td.columns else 0
    else:
        sharpe = summary_df['sharpe_ratio'].mean() if not summary_df.empty and 'sharpe_ratio' in summary_df.columns else 0
        sortino = summary_df['sortino_ratio'].mean() if not summary_df.empty and 'sortino_ratio' in summary_df.columns else 0
    
    cols = st.columns(5)
    values = [f"${total_pnl:,.2f}", f"{win_rate:.1f}%", str(trade_count), f"{sharpe:.2f}", f"{sortino:.2f}"]
    labels = ["NET PNL", "WIN RATE", "TRADES", "SHARPE", "SORTINO"]
    
    for col, label, val in zip(cols, labels, values):
        col.markdown(f"""
        <div class='metric-major'>
            <div class='metric-major-label'>{label}</div>
            <div class='metric-major-value'>{val}</div>
        </div>
        """, unsafe_allow_html=True)

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
# SIDEBAR
# ============================================================================

logo_url = ("https://deriverse.gitbook.io/deriverse-v1/~gitbook/image"
            "?url=https%3A%2F%2F3705106568-files.gitbook.io%2F%7E%2Ffiles%2Fv0%2Fb%2Fgitbook-x-prod.appspot.com"
            "%2Fo%2Forganizations%252FVbKUpgicSXo9QHWM7uzI%252Fsites%252Fsite_oPxtF%252Ficon%252FNsfAUtLJH778Cn5Dd7zK"
            "%252Ffavicon.ico%3Falt%3Dmedia%26token%3D4099bf73-ccd6-4d9f-8bbb-01cdc664ddb0"
            "&width=32&dpr=3&quality=100&sign=13d31bb2&sv=2")

logo_bytes = load_logo(logo_url)
if logo_bytes:
    st.sidebar.image(logo_bytes, width=60)
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
    date_option = st.sidebar.radio("Range",
        ["Last 7 Days", "Last 30 Days", "All Time", "Custom"],
        index=1, horizontal=True, label_visibility="collapsed")
else:
    date_option = st.sidebar.radio("Range",
        ["Last 7 Days", "Last 30 Days", "Custom (Admin Only)"],
        index=1, horizontal=True, label_visibility="collapsed")
    if date_option == "Custom (Admin Only)":
        st.sidebar.warning("🔐 Requires admin authentication")
        date_option = "Last 30 Days"

if not data['positions'].empty:
    min_date = data['positions']['close_time'].min().date()
    max_date = data['positions']['close_time'].max().date()
    
    if date_option == "Last 7 Days":
        start_date, end_date = max_date - timedelta(7), max_date
    elif date_option == "Last 30 Days":
        start_date, end_date = max_date - timedelta(30), max_date
    elif date_option in ("Custom", "Custom (Admin Only)") and is_admin:
        sc1, sc2 = st.sidebar.columns(2)
        start_date = sc1.date_input("From", min_date, min_value=min_date, max_value=max_date)
        end_date = sc2.date_input("To", max_date, min_value=min_date, max_value=max_date)
    else:
        start_date, end_date = min_date, max_date

all_markets = sorted(data['positions']['market_id'].unique()) if not data['positions'].empty else []
unique_symbols = sorted(set(simplify_symbol(m) for m in all_markets))
selected_symbols = st.sidebar.multiselect("Symbols", unique_symbols, default=[])
selected_markets = [m for m in all_markets if simplify_symbol(m) in selected_symbols] if selected_symbols else []

st.sidebar.markdown("---")

# ============================================================================
# APPLY FILTERS
# ============================================================================

filtered_positions = data['positions'].copy() if not data['positions'].empty else pd.DataFrame()
filtered_open = data['open_positions'].copy() if not data['open_positions'].empty else pd.DataFrame()

# Debug info in sidebar
with st.sidebar.expander("📊 Quick Data check", expanded=False):
    st.write(f"Total positions: {len(filtered_positions)}")
    if not filtered_positions.empty:
        st.write(f"Spot: {len(filtered_positions[filtered_positions['product_type'] == 'spot'])}")
        st.write(f"Perp: {len(filtered_positions[filtered_positions['product_type'] == 'perp'])}")
        st.write(f"Option: {len(filtered_positions[filtered_positions['product_type'] == 'option'])}")
closed_positions = filtered_positions.copy()  

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
# MAIN DASHBOARD LAYOUT - Using native Streamlit
# ============================================================================

# Header section
col1, col2 = st.columns([1, 5])
with col1:
    if logo_bytes:
        st.image(logo_bytes, width=80)
    else:
        st.markdown("### 🔷")
with col2:
    st.title("Deriverse Trading Analytics")
    st.caption("Real-time performance insights • Local-first security")

if st.session_state.view_mode == "personal" and "authenticated_trader" in st.session_state:
    st.markdown(f"<div class='profile-badge'>🔐 {mask_trader_id(st.session_state.authenticated_trader)}</div>", 
                unsafe_allow_html=True)

# Global KPIs

display_global_kpis(closed_positions, data['summary'], selected_trader)

# Navigation tabs
tab_overview, tab_performance, tab_risk, tab_volume, tab_orders, tab_greeks, tab_journal = st.tabs([
    "📊 Overview", "📈 Performance", "⚠️ Risk", "📊 Volume", "📋 Orders", "🔬 Greeks", "📝 Journal"
])

# ============================================================================
# OVERVIEW TAB
# ============================================================================

with tab_overview:
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
                st.plotly_chart(fig, use_container_width=True, key="top_profit")
                
                st.dataframe(
                    df2.style.format({'Total PnL':'${:,.2f}','Win Rate':'{:.1f}%'}),
                    use_container_width=True, hide_index=True
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
                st.plotly_chart(fig, use_container_width=True, key="top_loss")
                
                st.dataframe(
                    df2.style.format({'Total PnL':'${:,.2f}','Win Rate':'{:.1f}%'}),
                    use_container_width=True, hide_index=True
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
            use_container_width=True, hide_index=True
        )

# ============================================================================
# PERFORMANCE TAB
# ============================================================================

with tab_performance:
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

# ============================================================================
# RISK TAB
# ============================================================================

with tab_risk:
    if not filtered_positions.empty:
        display_liquidation_analytics(
            filtered_positions,
            is_personal_mode=(st.session_state.view_mode == "personal"),
            trader_id=selected_trader
        )
    else:
        st.info("No risk data for selected filters")

# ============================================================================
# VOLUME TAB
# ============================================================================

with tab_volume:
    if not filtered_positions.empty:
        display_volume_analysis(filtered_positions)
    else:
        st.info("No volume data for selected filters")

# ============================================================================
# ORDERS TAB
# ============================================================================

with tab_orders:
    display_order_type_performance(data['order_perf'], filtered_positions)
# ============================================================================
# GREEKS TAB
# ============================================================================

with tab_greeks:
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

# ============================================================================
# JOURNAL TAB
# ============================================================================

with tab_journal:
    st.header("📝 Trade Journal with Annotations")
    
    if filtered_positions.empty:
        st.info("No trades to journal")
    
    elif st.session_state.view_mode == "personal" and selected_trader:
        trader = selected_trader
        
        st.info("📌 Click any cell in the 'Notes' column to add your observations. Notes auto-save.")
        
        trader_notes = load_trader_notes(trader)
        greeks_df = compute_greeks_per_position(filtered_positions)
        
        jdf = filtered_positions.sort_values('close_time', ascending=False).copy()
        jdf['symbol'] = jdf['market_id'].apply(simplify_symbol)
        jdf['volume_usd'] = jdf['exit_price'] * jdf['size']
        jdf['notes'] = jdf['position_id'].map(lambda pid: trader_notes.get(str(pid), ""))
        
        if not greeks_df.empty:
            jdf = jdf.merge(greeks_df[['position_id','delta']], on='position_id', how='left')
        
        notes_count = sum(1 for n in jdf['notes'] if n and str(n).strip())
        st.info(f"📝 {notes_count} annotated trade{'s' if notes_count != 1 else ''}")
        
        avail_cols = ['close_time','symbol','product_type','side',
                      'entry_price','exit_price','size','volume_usd','realized_pnl','fees']
        if 'delta' in jdf.columns:
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
            "delta": st.column_config.NumberColumn("Delta", format="%.2f"),
            "notes": st.column_config.TextColumn("📝 Notes", max_chars=500, width="large"),
        }
        
        edited = st.data_editor(
            jdf[avail_cols], column_config=col_cfg,
            use_container_width=True, hide_index=True, num_rows="fixed",
            disabled=[c for c in avail_cols if c != 'notes']
        )
        
        updated = {}
        for idx, row in edited.iterrows():
            pid = jdf.loc[idx, 'position_id']
            note = row.get('notes', '')
            if pd.notna(note) and str(note).strip():
                updated[str(pid)] = note
        
        if updated != trader_notes:
            save_trader_notes(trader, updated)
            st.success("✅ Notes saved!")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            st.download_button("📥 Export CSV",
                jdf[avail_cols].to_csv(index=False),
                f"journal_{trader[:8]}.csv", "text/csv")
        with col3:
            if st.button("🗑️ Clear Notes"):
                save_trader_notes(trader, {})
                st.rerun()
    
    else:
        if selected_trader:
            st.info(f"👁️ Read-Only View: {mask_trader_id(selected_trader)}")
        else:
            st.info("👥 Authenticate your wallet to add notes")
        
        jdf = filtered_positions.sort_values('close_time', ascending=False).copy()
        jdf['trader'] = jdf['trader_id'].apply(mask_trader_id)
        jdf['symbol'] = jdf['market_id'].apply(simplify_symbol)
        jdf['volume_usd'] = jdf['exit_price'] * jdf['size']
        
        st.dataframe(
            jdf[['close_time','trader','symbol','product_type','side',
                 'entry_price','exit_price','size','volume_usd','realized_pnl','fees']].style.format({
                'entry_price': '${:,.2f}', 'exit_price': '${:,.2f}',
                'size': '{:,.4f}', 'volume_usd': '${:,.0f}',
                'realized_pnl':'${:,.2f}', 'fees': '${:,.2f}'
            }),
            use_container_width=True, hide_index=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
fc1, fc2, fc3 = st.columns([2, 1, 1])
fc1.caption(f"🕐 Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
fc2.caption("🔐 **Admin Mode**" if is_admin else "🔒 **Secure** • Local-first")
fc3.caption("v8.0 Native Layout")

st.markdown("""
<div style='text-align:center;padding:20px;color:#64748b;font-size:12px;'>
    <strong>Deriverse Analytics Dashboard</strong><br>
    Read-only • No private keys required • Data stays on your machine
</div>
""", unsafe_allow_html=True)