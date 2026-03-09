from __future__ import annotations

from pathlib import Path

import pandas as pd

from .backtesting import run_backtest
from .config_loader import load_config
from .data_pipeline import build_feature_dataset
from .nodes import NodeGraphEngine
from .reporting import save_run_artifacts


def run_pipeline(config_path: str | Path) -> Path:
    config = load_config(config_path)
    run_name = config.run_name
    print(f"[run] {run_name}")

    dataset, cache_path = build_feature_dataset(config)
    print(
        f"[data] rows={len(dataset):,}, tickers={dataset['ticker'].nunique()}, "
        f"date_range={dataset['date'].min().date()}~{dataset['date'].max().date()}"
    )

    graph_cfg = config.section("graph")
    engine = NodeGraphEngine(graph_cfg=graph_cfg)
    graph_result = engine.evaluate(dataset)
    entry_count = int(graph_result.entry_signal.sum())
    exit_count = int(graph_result.exit_signal.sum())
    print(f"[graph] entry_events={entry_count:,}, exit_events={exit_count:,}")

    signal_frame = dataset[
        [
            "date",
            "ticker",
            "close",
            "ret_1d",
        ]
    ].copy()
    signal_frame["entry_signal"] = graph_result.entry_signal.astype(bool)
    signal_frame["exit_signal"] = graph_result.exit_signal.astype(bool)

    backtest_cfg = config.section("backtest")
    fee_bps = float(backtest_cfg.get("fee_bps", 0.0))
    slippage_bps = float(backtest_cfg.get("slippage_bps", 0.0))
    bt_result = run_backtest(signal_frame=signal_frame, fee_bps=fee_bps, slippage_bps=slippage_bps)
    print(
        "[metrics] "
        f"cum_return={bt_result.metrics['cumulative_return']:.4f}, "
        f"max_dd={bt_result.metrics['max_drawdown']:.4f}, "
        f"win_rate_daily={bt_result.metrics['win_rate_daily']:.4f}, "
        f"total_trades={int(bt_result.metrics['total_trades'])}"
    )

    # Keep useful node outputs on the position frame for downstream inspection.
    for node_id, values in graph_result.node_outputs.items():
        bt_result.signal_frame[node_id] = values.values

    output_cfg = config.section("output")
    out_root = config.resolve_path(
        path_value=output_cfg.get("out_dir"),
        default=config.project_root / "trade_wizards_mvp" / "outputs",
    )
    out_root.mkdir(parents=True, exist_ok=True)

    out_dir = save_run_artifacts(
        result=bt_result,
        node_outputs=graph_result.node_outputs,
        used_config=config.raw,
        out_root=out_root,
        run_name=run_name,
        cache_path=cache_path,
    )
    return out_dir

