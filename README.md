# B1/B2 Trading Strategy — Backtest & Visualization

**DS4200 Final Project** | Northeastern University | Spring 2026

Interactive dashboard exploring whether technical analysis-based strategies can generate consistent returns across US and Chinese stock markets.

---

## 🎯 Project Overview

This project backtests two mean-reversion strategies (**B1** and **B2**) on:
- **S&P 500**: 505 stocks (2013–2018)
- **Chinese A-shares**: 3,066 stocks (2015–2026)

Through a 81-combination parameter sweep, we identify optimal settings for stop-loss, observation period, and profit-taking thresholds.

### Live Dashboard
👉 **[View Interactive Dashboard](https://rayrayowo.github.io/DS4200-visualization/docs/index.html)**

---

## 📊 Strategies

### B1 — Oversold Rebound
- **Entry**: KDJ J < 13 + MACD DEA > 0 + Uptrend (white line > yellow line)
- **Logic**: Buy when extremely oversold but macro trend remains intact
- **Optimal**: 3% stop-loss, 3-day observation, 10% fly trigger

### B2 — Momentum Confirmation
- **Entry**: After B1 appears → daily gain ≥ 4% + volume surge ≥ 1.1x
- **Logic**: Wait for breakout confirmation before entering
- **Optimal**: 3% stop-loss, 2-day observation, 5% fly trigger

---

## 📈 Visualizations

| Viz | Description | Tech |
|-----|-------------|------|
| **1. Equity Curve** | Portfolio value over time with regime shading | D3.js |
| **2. Parameter Sensitivity** | Heatmap of 81 parameter combinations | Altair |
| **3. Cross-Market Comparison** | US vs China performance side-by-side | Static |
| **4. Trade Outcomes** | Scatter plot of individual trades | D3.js |
| **5. K-line with Signals** | AAPL candlestick with buy/sell markers | TradingView Lightweight Charts |

---

## 🔑 Key Findings

1. **Stop-loss is the most critical parameter** — Tight stops (2-3%) dramatically improve risk-adjusted returns
2. **B1 is cross-market robust** — Similar Sharpe ratios in US (1.11) and China (1.77) with identical optimal parameters
3. **B2 is market-dependent** — Exceptional in A-shares but modest in S&P 500, reflecting different momentum patterns
4. **Asymmetric returns drive profitability** — ~50% win rate, but winners generate outsized returns through the "fly" mechanism

---

## 🛠️ Tech Stack

- **Data**: Kaggle (S&P 500), Tushare Pro (A-shares)
- **Backtesting**: Python (Pandas, NumPy)
- **Visualization**: D3.js v7, Altair, TradingView Lightweight Charts v4
- **Deployment**: GitHub Pages (gh-pages branch)

---

## 📂 Project Structure

```
DS4200-visualization/
├── docs/
│   ├── index.html          # Main dashboard
│   ├── css/style.css       # Styles
│   ├── js/                 # Visualization scripts
│   ├── data/               # JSON data files
│   └── img/                # Static images
├── DS4200_Project_Description.docx  # Design document for submission
└── README.md
```

---

## 👥 Authors

- **Ruiyang Zhang** (@rayrayowo)
- **Alan**

---

## 📄 Course

DS4200 — Information Presentation and Data Visualization | Northeastern University

---

## 📜 License

MIT License — For educational purposes only. Not investment advice.
