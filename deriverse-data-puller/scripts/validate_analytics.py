# scripts/validate_analytics.py
"""
Validation script to verify analytics output quality and correctness.
Run after python -m scripts.run_analytics
"""

import pandas as pd
from pathlib import Path
import sys

OUTPUT_DIR = Path("data/analytics_output")

class bcolors:
    OK = '\033[92m'
    FAIL = '\033[91m'
    WARN = '\033[93m'
    END = '\033[0m'

def validate_file_exists(filename):
    """Check if required file exists."""
    path = OUTPUT_DIR / filename
    if path.exists():
        print(f"{bcolors.OK}✓{bcolors.END} {filename} exists")
        return True
    else:
        print(f"{bcolors.FAIL}✗{bcolors.END} {filename} missing")
        return False

def validate_positions():
    """Validate positions.csv structure and data quality."""
    df = pd.read_csv(OUTPUT_DIR / "positions.csv")
    
    required_cols = [
        'position_id', 'trader_id', 'market_id', 'product_type', 'side',
        'open_time', 'close_time', 'duration_seconds',
        'entry_price', 'exit_price', 'size', 'gross_pnl', 'fees', 'realized_pnl'
    ]
    
    issues = []
    
    # Check columns
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        issues.append(f"Missing columns: {missing_cols}")
    
    # Check data quality
    if not df.empty:
        if (df['duration_seconds'] < 0).any():
            issues.append("Negative duration_seconds found")
        
        if (df['fees'] < 0).any():
            issues.append("Negative fees found")
        
        # PnL consistency check
        expected_pnl = df['gross_pnl'] - df['fees']
        if not expected_pnl.equals(df['realized_pnl']):
            max_diff = abs(expected_pnl - df['realized_pnl']).max()
            if max_diff > 0.01:  # Allow for rounding
                issues.append(f"PnL inconsistency detected (max diff: {max_diff:.4f})")
    
    if issues:
        print(f"{bcolors.WARN}⚠{bcolors.END} positions.csv has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"{bcolors.OK}✓{bcolors.END} positions.csv is valid ({len(df)} rows)")
        return True

def validate_summary_metrics():
    """Validate summary_metrics.csv calculations."""
    positions = pd.read_csv(OUTPUT_DIR / "positions.csv")
    summary = pd.read_csv(OUTPUT_DIR / "summary_metrics.csv")
    
    issues = []
    
    for _, row in summary.iterrows():
        trader = row['trader_id']
        trader_pos = positions[positions['trader_id'] == trader]
        
        # Validate win rate
        actual_wins = (trader_pos['realized_pnl'] > 0).sum()
        actual_total = len(trader_pos)
        expected_win_rate = actual_wins / actual_total if actual_total > 0 else 0
        
        if abs(row['win_rate'] - expected_win_rate) > 0.01:
            issues.append(f"{trader}: win_rate mismatch ({row['win_rate']:.2f} vs {expected_win_rate:.2f})")
        
        # Validate long/short ratio
        if abs(row['long_ratio'] + row['short_ratio'] - 1.0) > 0.01:
            issues.append(f"{trader}: long_ratio + short_ratio != 1.0")
        
        # Validate total_pnl
        expected_total = trader_pos['realized_pnl'].sum()
        if abs(row['total_pnl'] - expected_total) > 0.01:
            issues.append(f"{trader}: total_pnl mismatch")
    
    if issues:
        print(f"{bcolors.WARN}⚠{bcolors.END} summary_metrics.csv has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"{bcolors.OK}✓{bcolors.END} summary_metrics.csv is valid")
        return True

def validate_equity_curve():
    """Validate equity_curve.csv drawdown calculations."""
    df = pd.read_csv(OUTPUT_DIR / "equity_curve.csv")
    
    issues = []
    
    for trader in df['trader_id'].unique():
        trader_data = df[df['trader_id'] == trader].sort_values('timestamp')
        
        # Validate drawdown is always <= 0
        if (trader_data['drawdown'] > 0.01).any():
            issues.append(f"{trader}: Positive drawdown found")
        
        # Validate cumulative PnL is monotonic sum
        if not trader_data['cumulative_pnl'].is_monotonic_increasing and not trader_data['cumulative_pnl'].is_monotonic_decreasing:
            # This is actually OK - cumulative can go up and down
            pass
    
    if issues:
        print(f"{bcolors.WARN}⚠{bcolors.END} equity_curve.csv has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"{bcolors.OK}✓{bcolors.END} equity_curve.csv is valid")
        return True

def validate_directional_bias():
    """Validate directional_bias.csv calculations."""
    df = pd.read_csv(OUTPUT_DIR / "directional_bias.csv")
    
    issues = []
    
    for _, row in df.iterrows():
        total = row['long_trades'] + row['short_trades']
        
        if total == 0:
            issues.append(f"{row['trader_id']}: No trades")
            continue
        
        expected_long_ratio = row['long_trades'] / total
        expected_short_ratio = row['short_trades'] / total
        
        if abs(row['long_ratio'] - expected_long_ratio) > 0.01:
            issues.append(f"{row['trader_id']}: long_ratio calculation error")
        
        if abs(row['short_ratio'] - expected_short_ratio) > 0.01:
            issues.append(f"{row['trader_id']}: short_ratio calculation error")
        
        if abs(row['long_ratio'] + row['short_ratio'] - 1.0) > 0.01:
            issues.append(f"{row['trader_id']}: ratios don't sum to 1.0")
    
    if issues:
        print(f"{bcolors.WARN}⚠{bcolors.END} directional_bias.csv has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"{bcolors.OK}✓{bcolors.END} directional_bias.csv is valid")
        return True

def main():
    print("\n" + "=" * 60)
    print("DERIVERSE ANALYTICS VALIDATION")
    print("=" * 60 + "\n")
    
    if not OUTPUT_DIR.exists():
        print(f"{bcolors.FAIL}✗{bcolors.END} Output directory not found: {OUTPUT_DIR}")
        print("Run: python -m scripts.run_analytics")
        sys.exit(1)
    
    # Check file existence
    print("Checking required files...")
    required_files = [
        'positions.csv',
        'realized_pnl.csv',
        'equity_curve.csv',
        'summary_metrics.csv',
        'volume_by_market.csv',
        'fees_breakdown.csv',
        'pnl_by_day.csv',
        'pnl_by_hour.csv',
        'directional_bias.csv',
        'order_type_performance.csv'
    ]
    
    all_exist = all(validate_file_exists(f) for f in required_files)
    
    if not all_exist:
        print(f"\n{bcolors.FAIL}✗ Some files are missing{bcolors.END}")
        sys.exit(1)
    
    print("\nValidating data quality...")
    
    validations = [
        validate_positions(),
        validate_summary_metrics(),
        validate_equity_curve(),
        validate_directional_bias()
    ]
    
    print("\n" + "=" * 60)
    if all(validations):
        print(f"{bcolors.OK}✓ ALL VALIDATIONS PASSED{bcolors.END}")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print(f"{bcolors.WARN}⚠ SOME VALIDATIONS FAILED{bcolors.END}")
        print("=" * 60 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()