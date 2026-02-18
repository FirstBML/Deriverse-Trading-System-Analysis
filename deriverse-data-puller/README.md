# Deriverse Trading Analytics

Derivatives protocol simulation with spot, perp, and options markets. Includes an adaptive Streamlit dashboard with PnL tracking, Greeks exposure, liquidation monitoring, and personal trade journaling.
The data used are mock to mimick real solana ecosystem data format.


## quick setup

```bash
git clone https://github.com/FirstBML/Deriverse-Trading-System-Analysis.git
cd deriverse-data-puller
cp .env.example .env                # Set ADMIN_PASSWORD=yourpassword
uv sync
python run.py                       # Select option 1
---

##  or Setup

```bash
git clone https://github.com/FirstBML/Deriverse-Trading-System-Analysis.git
cd deriverse-data-puller or cd your directory
uv venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate         # macOS / Linux
uv pip install -e .
cp .env.example .env                # Set ADMIN_PASSWORD=yourpassword
python run.py                       # Select option 1
```

---

## Project Structure

```
deriverse-data-puller/
├── dashboards/
│   ├── app.py                   # Streamlit dashboard
│   └── .streamlit/
│       └── config.toml          # Dark theme (enforced across browsers)
├── scripts/
│   ├── generate_mock_data.py
│   ├── run_ingestion.py
│   ├── run_analytics.py
│   ├── diagnose_data.py
│   └── validate_analytics.py
├── src/
│   ├── analytics/               # PnL engine, metrics, Greeks
│   └── ingestion/               # Normalizer, pipeline, watermark
├── configs/
│   ├── ingestion.yaml           # Pipeline config (committed)
│   └── mock_data.json           # Generated mock events (gitignored)
├── data/                        # Auto-generated (gitignored)
├── tests/
├── run.py                       # Interactive runner
├── pyproject.toml
└── .env.example
```

---

## Interactive Runner (`python run.py`)

| Option | Action |
|--------|--------|
| 1 | Full pipeline + launch dashboard |
| 2 | Full pipeline, no dashboard |
| 3 | Launch dashboard only (data must exist) |
| 4 | Delete all generated data |
| 5 | Delete analytics only (keep raw events) |
| 6 | Delete trader notes only |
| 7 | Delete normalized events only |
| 8 | View data file counts and sizes |
| 9 | Advanced: run individual steps, validate, check deps |

**Manual steps** (if preferred):
```bash
python -m scripts.generate_mock_data
python -m scripts.run_ingestion
python -m scripts.run_analytics
streamlit run dashboards/app.py
```

---

## Admin Access

Add `?admin=1` to the URL, then enter your `.env` password:
```
http://localhost:8501/?admin=1
```
Unlocks: all-time data, custom date ranges, debug panel.

---

## Dashboard Tabs

| Tab | Content |
|-----|---------|
| Overview | KPIs, top performers, transaction history |
| Performance | Equity curve, drawdown |
| Time Analysis | Daily / hourly PnL patterns |
| Risk | Liquidation monitoring |
| Volume | Volume by symbol, fees, trade duration |
| Orders | Product type performance matrix |
| Greeks | Options delta exposure |
| Journal | Personal trade annotations (wallet-locked) |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | `uv pip install -e .` |
| No dashboard data | Run option 1 in `run.py` |
| Admin panel missing | Add `?admin=1` to URL |
| Admin password invalid | Check `.env` — no spaces or quotes around value |
| Wallet not found | Verify it exists in `configs/mock_data.json` |
| Fresh start | Option 4 in `run.py` |

```bash
python -m scripts.diagnose_data      # Check event counts
python -m scripts.validate_analytics # Validate output correctness
python -m pytest tests/              # Run unit tests
```