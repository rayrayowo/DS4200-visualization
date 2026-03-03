# Stock Visualization

Data-driven analysis of U.S. equity market behavior using historical S&P 500 data.
This project focuses on interpretable signal analysis and strategy evaluation instead of black-box price prediction.

## What This Project Does

- Cleans and standardizes large-scale OHLCV data
- Computes technical indicators (MA, MACD, KDJ, volatility, regime labels)
- Builds a reusable backtesting pipeline
- Evaluates strategy behavior by:
  - overall market
  - bull/bear regime
  - sector
  - liquidity leaders
- Exports portfolio metrics and visualization-ready outputs

## Dataset

- Source: Kaggle S&P 500 historical stock data
- Coverage: ~5 years daily OHLCV
- Scale: ~619k rows (raw)

## Repository Structure

```text
data/
  raw/
  processed/
outputs/
src/
README.md
```

Key scripts:
- `src/clean_merge01.py` - build master table with features and labels
- `src/strategies.py` - strategy signal logic and templates
- `src/backtest.py` - backtest engine and performance metrics
- `src/evaluate.py` - run multi-strategy evaluation and export reports
- `src/plot_violin_regime.py` - regime return distribution chart
- `src/plot_effectiveness_bars_lowN.py` - signal effectiveness bars with uncertainty markers

## Quick Start

Run from repo root:

```bash
.venv/bin/python src/clean_merge01.py
.venv/bin/python src/evaluate.py
```

Optional visualization scripts:

```bash
.venv/bin/python src/plot_violin_regime.py
.venv/bin/python src/plot_effectiveness_bars_lowN.py
```

## Main Outputs

Generated under `data/processed/`:
- `master.parquet` / `master.csv`
- `market_proxy_daily.csv`
- `strategy_summary.csv`
- `strategy_daily_returns.csv`
- `strategy_trades.csv`

Generated under `outputs/`:
- `fig_violin_regime_fwd20.png`
- `fig_effectiveness_bars_5d_20d.png`
- `fig_signal_regime_compare.png`

## Customize a Strategy

Edit `strategy_custom_template()` in `src/strategies.py`, then run:

```bash
.venv/bin/python src/evaluate.py --strategies custom_template
```

## Signal Export (v2)

```bash
python src/strategy_signals_v2.py
python src/strategy_signals_v2.py --skip-csv
```
