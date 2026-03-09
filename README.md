# Stock Visualization

Data-driven analysis of Chinese and U.S. equity markets using historical data.
This project focuses on **interpretable signal analysis**, **strategy evaluation**, and **backtesting**.

## 🆕 What's New (2026)

### B1/B2 Strategy Scanner v2.0
- Real-time stock screening with B1 (oversold bounce) and B2 (momentum) strategies
- Built-in technical indicators: KDJ, MACD, RSI, BOLL, Zhixing Trend Lines, Brick Chart
- Streamlit UI for single stock analysis and batch scanning
- Support for Tushare (China A-shares) and Yahoo Finance

### Neural Network Trading Strategy
- Node-based strategy composition
- Walk-forward MLP backtesting
- Portfolio metrics: cumulative return, max drawdown, win rate

## What This Project Does

- **Data Collection**: Tushare (China A-shares), Yahoo Finance (US/HK stocks)
- **Technical Analysis**: KDJ, MACD, RSI, BOLL, Moving Averages, Zhixing Trend Lines, Brick Chart
- **Strategy Signals**: B1 (KDJ J<13, MACD DEA>0), B2 (KDJ J<55, +4% price, volume ratio>1.1)
- **Backtesting**: Walk-forward analysis, portfolio metrics
- **Visualization**: K-line charts, profit curves, violin plots, monthly returns

## Strategies

### B1 Strategy (Oversold Bounce)
- Market: Shanghai/Shenzhen Main Board
- Weekly: MA30 > MA60 > MA120 > MA240
- Daily: KDJ J < 13, MACD DEA > 0
- Zhixing: White line > Yellow line

### B2 Strategy (Momentum)
- Market: Shanghai/Shenzhen Main Board
- Weekly: MA30 > MA60 > MA120 > MA240
- Daily: KDJ J < 55, Price change >= 4%, Volume ratio >= 1.1

### Brick Chart (ZX-ZHUAN)
- White brick = Buy signal (golden cross after green day)
- Red brick = Hold
- Green brick = Short/Empty

## Repository Structure

```
stock-visualization/
├── b1_scanner/           # B1/B2 Strategy Scanner v2.0
│   ├── app.py           # Streamlit UI
│   ├── scanner_core.py   # Strategy logic
│   ├── indicators.py     # Technical indicators
│   └── data_sources.py  # Tushare + Yahoo Finance
│
├── trade_wizards_mvp/   # Neural Network Trading
│   ├── run_demo.py      # Run backtest
│   ├── tw_mvp/          # Core modules
│   └── config/          # Strategy configs
│
├── src/                  # Legacy analysis scripts
├── data/                 # Raw and processed data
├── outputs/              # Charts and results
└── README.md
```

## Quick Start

### B1 Scanner (Recommended)

```bash
cd b1_scanner
pip install -r requirements.txt

# Set Tushare token (optional)
export TUSHARE_TOKEN="your_token_here"

# Run UI
streamlit run app.py
```

### Neural Network Strategy

```bash
cd trade_wizards_mvp
.venv/bin/python run_demo.py
```

## Data Sources

| Source | Coverage | API |
|--------|----------|-----|
| **Tushare** | China A-shares (600/601/603/000) | Requires token |
| **Yahoo Finance** | US/HK/China stocks | Free |

### Get Tushare Token
1. Register at https://tushare.pro
2. Get your token from profile
3. Set: `export TUSHARE_TOKEN="your_token"`

## Technical Indicators

- **KDJ** (9,3,3): Overbought/oversold
- **MACD** (12,26,9): Trend
- **RSI** (14): Relative strength
- **BOLL** (20,2): Bollinger Bands
- **Zhixing White**: EMA(EMA(C,10),10) - Short-term trend
- **Zhixing Yellow**: (MA14+MA28+MA57+MA114)/4 - Long-term trend
- **Brick Chart**: Volume-based momentum

## Main Outputs

Generated under `b1_scanner/`:
- Real-time screening results
- K-line charts with indicators
- Buy/sell signals

Generated under `trade_wizards_mvp/outputs/`:
- `metrics.json/csv`: Performance metrics
- `trades.csv`: Trade records
- `trade_annotations_*.png`: Charts with entry/exit markers

## Customize Strategies

### Add Custom Stock List
Edit the watchlist in `b1_scanner/app.py`:
```
600519.SH,贵州茅台
600276.SH,恒瑞医药
688235.SH,百济神州
```

### Modify B1/B2 Conditions
Edit `scanner_core.py`:
```python
@dataclass
class B1Config:
    strategy: str = "B1"  # or "B2"
    require_golden_cross: bool = False
    require_brick_white: bool = False
```

## Tech Stack

- **Python 3.12**
- **Data**: Pandas, NumPy, Tushare, yfinance
- **ML**: scikit-learn (Neural Networks)
- **Visualization**: Plotly, Matplotlib, Streamlit
- **Backtesting**: Custom pipeline

## License

MIT License - For educational purposes only. Not investment advice.

## Contact

- GitHub: [rayrayowo](https://github.com/rayrayowo)
- Email: zhang.ruiyang@northeastern.edu
