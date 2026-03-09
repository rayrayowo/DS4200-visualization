# Trade Wizards MVP (Node-Based + Neural Network)

This folder is a standalone MVP for your `Trade Wizards` concept:

- Node-based strategy composition (`indicator`, `compare`, `logic`, `math`, `neural_net` nodes)
- Neural-network decision node (rolling walk-forward MLP)
- Backtesting with portfolio metrics:
  - cumulative return
  - max drawdown
  - daily win rate
  - trade-level win rate and holding days
- Chart annotations with entry/exit markers
- Config-driven ingestion + feature caching for reproducible runs

## Structure

```text
trade_wizards_mvp/
  config/default_graph.json
  run_demo.py
  tw_mvp/
    backtesting.py
    config_loader.py
    data_pipeline.py
    features.py
    nodes.py
    pipeline.py
    reporting.py
  cache/
  outputs/
```

## Run

From repo root:

```bash
./.venv/bin/python trade_wizards_mvp/run_demo.py
```

Use a custom config:

```bash
./.venv/bin/python trade_wizards_mvp/run_demo.py --config trade_wizards_mvp/config/default_graph.json
```

## Config Notes

Main sections in `default_graph.json`:

- `data`: source path, date range, ticker cap, cache dir
- `features`: feature windows and lookahead target horizon
- `graph`: node definitions and entry/exit signal refs
- `backtest`: fee and slippage assumptions
- `output`: artifact folder and chart ticker

## Artifacts

Each run writes to:

`trade_wizards_mvp/outputs/<run_name>/`

Files include:

- `metrics.json` and `metrics.csv`
- `signal_frame.csv`
- `daily_returns.csv`
- `trades.csv`
- `node_outputs_preview.csv`
- `trade_annotations_<ticker>.png`
- `resume_snapshot.md`
- `used_config.json`

## Important

- This is built as an educational strategy sandbox and not investment advice.
- It does not place real trades.

