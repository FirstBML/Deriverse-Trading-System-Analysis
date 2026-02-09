# Deriverse Trading System Analysis

## Overview
Real-time trading analytics pipeline for derivatives protocol simulation.

“The mock dataset intentionally includes realistic inconsistencies such as duplicate opens and closes without corresponding opens.

The analytics pipeline enforces a strict validation layer that logs and skips invalid events while continuing to process valid ones.

This mirrors production trading systems, where data is not guaranteed to be clean and analytics must be resilient, deterministic, and autonomous.”

## 🔍 Data Integrity & Validation Philosophy

This project intentionally uses realistic mock trading data, including edge cases commonly observed in production systems:

- Close events without a corresponding open
- Duplicate open events
- Partial closes
- Fee inconsistencies

Rather than manually cleaning data, the analytics pipeline is designed to:

- Validate all events at runtime
- Skip invalid events deterministically
- Log integrity issues without breaking execution
- Produce canonical, reproducible PnL outputs

Example validation handling:

```python
if key not in open_positions:
    # Close without open → logged & skipped

## Architecture

### Phase 1: Event Ingestion ✅ COMPLETE
- Normalized event schema validation
- Watermark-based incremental processing
- Event deduplication

### Phase 2: Canonical PnL Engine ✅ COMPLETE
- Position tracking with partial close support
- Realized PnL calculation
- Deterministic position IDs
- **Outputs:** `positions.csv`, `realized_pnl.csv`

### Phase 3: Derived Metrics 📋 DESIGNED (Not Implemented)

**Design Principle:** All Phase 3 metrics are derived from Phase 2 outputs only. They never access raw events or modify the PnL engine.

#### Planned Metrics

**Trading Performance**
- Win Rate: `wins / total_trades` from positions_df
- Average Trade Duration: `mean(close_time - open_time)`
- Profit Factor: `sum(winning_pnl) / abs(sum(losing_pnl))`

**Risk Metrics**
- Max Drawdown: Peak-to-trough decline in cumulative PnL
- Sharpe Ratio: `mean(daily_returns) / std(daily_returns) * sqrt(252)`
- Sortino Ratio: Sharpe using only downside volatility

**Cost Analysis**
- Fee Drag: `sum(fees) / sum(abs(gross_pnl))`
- Net vs Gross Return comparison

**Position Management**
- Liquidation Ratio: `liquidations / total_closes`
- Partial vs Full Close Ratio: Distribution of close sizes
- Average Position Size: By trader, market, product type

**Why Not Implemented Yet:**
1. Core PnL engine validation takes priority
2. Metric requirements may evolve from dashboard feedback
3. Premature optimization wastes effort
4. Current focus: canonical data quality