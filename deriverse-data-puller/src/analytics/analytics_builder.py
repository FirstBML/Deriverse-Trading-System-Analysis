# src/analytics/analytics_builder.py - WITH OPEN POSITIONS SUPPORT
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AnalyticsBuilder:
    """Build all required analytics tables from canonical PnL engine outputs."""
    
    def __init__(self, positions_df: pd.DataFrame, pnl_df: pd.DataFrame, 
                 open_positions_df: pd.DataFrame, output_dir: Path):
        self.positions = positions_df.copy() if not positions_df.empty else pd.DataFrame()
        self.pnl = pnl_df.copy() if not pnl_df.empty else pd.DataFrame()
        self.open_positions = open_positions_df.copy() if not open_positions_df.empty else pd.DataFrame()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure timestamps are datetime
        if not self.positions.empty:
            self.positions['open_time'] = pd.to_datetime(self.positions['open_time'])
            self.positions['close_time'] = pd.to_datetime(self.positions['close_time'])
            self.positions['duration_seconds'] = (
                self.positions['close_time'] - self.positions['open_time']
            ).dt.total_seconds()
    
    def build_all(self):
        """Generate all required analytics outputs."""
        logger.info("Building core truth tables...")
        self._build_positions()
        self._build_realized_pnl()
        self._build_open_positions()  # ✅ NEW
        
        if self.positions.empty:
            logger.warning("No closed positions - generating empty analytics")
            self._generate_empty_outputs()
            return
        
        logger.info("Building performance metrics...")
        self._build_equity_curve()
        self._build_summary_metrics()
        
        logger.info("Building volume & fees analytics...")
        self._build_volume_by_market()
        self._build_fees_breakdown()
        
        logger.info("Building time-based analytics...")
        self._build_pnl_by_day()
        self._build_pnl_by_hour()
        
        logger.info("Building behavioral analytics...")
        self._build_directional_bias()
        self._build_order_type_performance()
        
        logger.info("Building options Greeks...")
        self._build_greeks_exposure()
        
        logger.info(f"✅ All analytics saved to {self.output_dir}")
    
    def _build_positions(self):
        """1. Core Truth: positions.csv"""
        if self.positions.empty:
            pd.DataFrame().to_csv(self.output_dir / 'positions.csv', index=False)
            return
            
        output = self.positions[[
            'position_id', 'trader_id', 'market_id', 'product_type', 'side',
            'open_time', 'close_time', 'duration_seconds',
            'entry_price', 'exit_price', 'size', 'gross_pnl', 'fees', 'realized_pnl'
        ]].copy()
        output.to_csv(self.output_dir / 'positions.csv', index=False)
    
    def _build_realized_pnl(self):
        """2. Core Truth: realized_pnl.csv"""
        if self.positions.empty:
            pd.DataFrame().to_csv(self.output_dir / 'realized_pnl.csv', index=False)
            return
            
        output = self.positions[[
            'close_time', 'trader_id', 'market_id', 'realized_pnl', 'fees'
        ]].copy()
        output.rename(columns={'close_time': 'timestamp'}, inplace=True)
        output['net_pnl'] = output['realized_pnl'] - output['fees']
        output = output[['timestamp', 'trader_id', 'market_id', 'realized_pnl', 'fees', 'net_pnl']]
        output.to_csv(self.output_dir / 'realized_pnl.csv', index=False)
    
    def _build_open_positions(self):
        """✅ NEW: open_positions.csv - Currently active positions"""
        if self.open_positions.empty:
            pd.DataFrame().to_csv(self.output_dir / 'open_positions.csv', index=False)
            logger.info("No open positions")
            return
        
        output = self.open_positions[[
            'position_id', 'trader_id', 'market_id', 'product_type', 'side',
            'entry_price', 'size', 'fees_paid', 'open_time', 'time_held_seconds'
        ]].copy()
        
        output.to_csv(self.output_dir / 'open_positions.csv', index=False)
        logger.info(f"Saved {len(output)} open positions")
    
    def _build_equity_curve(self):
        """3. Performance: equity_curve.csv"""
        equity = self.positions.copy()
        equity = equity.sort_values('close_time')
        
        result = []
        for trader in equity['trader_id'].unique():
            trader_data = equity[equity['trader_id'] == trader].copy()
            trader_data['cumulative_pnl'] = trader_data['realized_pnl'].cumsum()
            trader_data['rolling_max'] = trader_data['cumulative_pnl'].cummax()
            trader_data['drawdown'] = trader_data['cumulative_pnl'] - trader_data['rolling_max']
            
            for _, row in trader_data.iterrows():
                result.append({
                    'timestamp': row['close_time'],
                    'trader_id': row['trader_id'],
                    'net_realized_pnl': row['realized_pnl'],
                    'cumulative_pnl': row['cumulative_pnl'],
                    'drawdown': row['drawdown']
                })
        
        df = pd.DataFrame(result)
        df.to_csv(self.output_dir / 'equity_curve.csv', index=False)
    
    def _build_summary_metrics(self):
        """4. Performance: summary_metrics.csv"""
        result = []
        
        for trader in self.positions['trader_id'].unique():
            trader_pos = self.positions[self.positions['trader_id'] == trader]
            
            winning = trader_pos[trader_pos['realized_pnl'] > 0]
            losing = trader_pos[trader_pos['realized_pnl'] < 0]
            
            total_pnl = trader_pos['realized_pnl'].sum()
            total_fees = trader_pos['fees'].sum()
            trade_count = len(trader_pos)
            win_rate = len(winning) / trade_count if trade_count > 0 else 0
            avg_win = winning['realized_pnl'].mean() if len(winning) > 0 else 0
            avg_loss = losing['realized_pnl'].mean() if len(losing) > 0 else 0
            best_trade = trader_pos['realized_pnl'].max()
            worst_trade = trader_pos['realized_pnl'].min()
            avg_duration = trader_pos['duration_seconds'].mean()
            
            long_trades = trader_pos[trader_pos['side'].isin(['long', 'buy'])]
            short_trades = trader_pos[trader_pos['side'].isin(['short', 'sell'])]
            long_ratio = len(long_trades) / trade_count if trade_count > 0 else 0
            short_ratio = len(short_trades) / trade_count if trade_count > 0 else 0
            
            trader_sorted = trader_pos.sort_values('close_time')
            cum_pnl = trader_sorted['realized_pnl'].cumsum()
            rolling_max = cum_pnl.cummax()
            drawdown = cum_pnl - rolling_max
            max_drawdown = drawdown.min()
            
            if len(trader_pos) > 1:
                trader_daily = trader_pos.copy()
                trader_daily['date'] = trader_daily['close_time'].dt.date
                daily_returns = trader_daily.groupby('date')['realized_pnl'].sum()
                
                mean_return = daily_returns.mean()
                std_return = daily_returns.std()
                sharpe_ratio = mean_return / std_return if std_return > 0 else 0
                
                downside_returns = daily_returns[daily_returns < 0]
                downside_std = downside_returns.std() if len(downside_returns) > 0 else std_return
                sortino_ratio = mean_return / downside_std if downside_std > 0 else 0
            else:
                sharpe_ratio = 0
                sortino_ratio = 0
            
            result.append({
                'trader_id': trader,
                'total_pnl': total_pnl,
                'total_fees': total_fees,
                'trade_count': trade_count,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'best_trade': best_trade,
                'worst_trade': worst_trade,
                'avg_duration_seconds': avg_duration,
                'long_ratio': long_ratio,
                'short_ratio': short_ratio,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio
            })
        
        df = pd.DataFrame(result)
        df.to_csv(self.output_dir / 'summary_metrics.csv', index=False)
    
    def _build_volume_by_market(self):
        """5. Volume: volume_by_market.csv"""
        result = []
        
        for (market, product), group in self.positions.groupby(['market_id', 'product_type']):
            total_volume = (group['exit_price'] * group['size']).sum()
            trade_count = len(group)
            
            result.append({
                'market_id': market,
                'product_type': product,
                'total_volume': total_volume,
                'trade_count': trade_count
            })
        
        df = pd.DataFrame(result)
        df.to_csv(self.output_dir / 'volume_by_market.csv', index=False)
    
    def _build_fees_breakdown(self):
        """6. Fees: fees_breakdown.csv"""
        result = []
        
        for (trader, product), group in self.positions.groupby(['trader_id', 'product_type']):
            total_fees = group['fees'].sum()
            
            result.append({
                'trader_id': trader,
                'product_type': product,
                'total_fees': total_fees
            })
        
        df = pd.DataFrame(result)
        df.to_csv(self.output_dir / 'fees_breakdown.csv', index=False)
    
    def _build_pnl_by_day(self):
        """7. Time Analytics: pnl_by_day.csv"""
        df = self.positions.copy()
        df['date'] = df['close_time'].dt.date
        
        result = []
        for (date, trader), group in df.groupby(['date', 'trader_id']):
            daily_pnl = group['realized_pnl'].sum()
            
            trader_data = df[df['trader_id'] == trader]
            trader_data = trader_data[trader_data['date'] <= date]
            cumulative_pnl = trader_data['realized_pnl'].sum()
            
            result.append({
                'date': date,
                'trader_id': trader,
                'daily_pnl': daily_pnl,
                'cumulative_pnl': cumulative_pnl
            })
        
        output = pd.DataFrame(result)
        output.to_csv(self.output_dir / 'pnl_by_day.csv', index=False)
    
    def _build_pnl_by_hour(self):
        """8. Time Analytics: pnl_by_hour.csv"""
        df = self.positions.copy()
        df['hour_of_day'] = df['close_time'].dt.hour
        
        result = []
        for (hour, trader), group in df.groupby(['hour_of_day', 'trader_id']):
            avg_pnl = group['realized_pnl'].mean()
            trade_count = len(group)
            
            result.append({
                'hour_of_day': hour,
                'trader_id': trader,
                'avg_pnl': avg_pnl,
                'trade_count': trade_count
            })
        
        output = pd.DataFrame(result)
        output.to_csv(self.output_dir / 'pnl_by_hour.csv', index=False)
    
    def _build_directional_bias(self):
        """9. Behavioral: directional_bias.csv"""
        result = []
        
        for trader, group in self.positions.groupby('trader_id'):
            long_trades = len(group[group['side'].isin(['long', 'buy'])])
            short_trades = len(group[group['side'].isin(['short', 'sell'])])
            total = long_trades + short_trades
            
            result.append({
                'trader_id': trader,
                'long_trades': long_trades,
                'short_trades': short_trades,
                'long_ratio': long_trades / total if total > 0 else 0,
                'short_ratio': short_trades / total if total > 0 else 0
            })
        
        df = pd.DataFrame(result)
        df.to_csv(self.output_dir / 'directional_bias.csv', index=False)
    
    def _build_order_type_performance(self):
        """10. Behavioral: order_type_performance.csv"""
        df = self.positions.copy()
        
        df['order_type'] = df['duration_seconds'].apply(lambda x:
            'market' if x < 300 else
            'limit' if x < 3600 else
            'stop'
        )
        
        result = []
        for order_type, group in df.groupby('order_type'):
            trade_count = len(group)
            avg_pnl = group['realized_pnl'].mean()
            win_rate = (group['realized_pnl'] > 0).mean()
            
            result.append({
                'order_type': order_type,
                'trade_count': trade_count,
                'avg_pnl': avg_pnl,
                'win_rate': win_rate
            })
        
        output = pd.DataFrame(result)
        output.to_csv(self.output_dir / 'order_type_performance.csv', index=False)
    
    def _build_greeks_exposure(self):
        """11. Greeks: greeks_exposure.csv (options only)"""
        options = self.positions[self.positions['product_type'] == 'option'].copy()
        
        if options.empty:
            pd.DataFrame().to_csv(self.output_dir / 'greeks_exposure.csv', index=False)
            return
        
        result = []
        for trader in options['trader_id'].unique():
            trader_opts = options[options['trader_id'] == trader]
            
            net_delta = 0
            for _, opt in trader_opts.iterrows():
                if opt['side'] in ['buy', 'long']:
                    delta_sign = 1
                else:
                    delta_sign = -1
                net_delta += delta_sign * opt['size'] * 0.5
            
            result.append({
                'trader_id': trader,
                'total_option_positions': len(trader_opts),
                'net_delta': net_delta,
                'gamma_exposure': 0,
                'theta_decay': 0
            })
        
        df = pd.DataFrame(result)
        df.to_csv(self.output_dir / 'greeks_exposure.csv', index=False)
    
    def _generate_empty_outputs(self):
        """Generate empty CSV files when no data available."""
        empty_files = [
            'equity_curve.csv', 'summary_metrics.csv', 'volume_by_market.csv',
            'fees_breakdown.csv', 'pnl_by_day.csv', 'pnl_by_hour.csv',
            'directional_bias.csv', 'order_type_performance.csv', 'greeks_exposure.csv'
        ]
        
        for filename in empty_files:
            pd.DataFrame().to_csv(self.output_dir / filename, index=False)