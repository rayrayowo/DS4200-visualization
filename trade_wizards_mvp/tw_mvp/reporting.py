from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_CACHE_ROOT = (Path(__file__).resolve().parents[1] / "outputs" / "mplcache").resolve()
_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .backtesting import BacktestResult


def _choose_chart_ticker(
    signal_frame: pd.DataFrame,
    trades: pd.DataFrame,
    preferred_ticker: str | None,
) -> str:
    all_tickers = signal_frame["ticker"].dropna().astype(str).unique().tolist()
    if not all_tickers:
        raise ValueError("No ticker found in signal frame.")

    if preferred_ticker and preferred_ticker in all_tickers:
        return preferred_ticker

    if not trades.empty:
        return str(trades["ticker"].value_counts().index[0])
    return str(all_tickers[0])


def _plot_trade_annotations(result: BacktestResult, out_path: Path, ticker: str) -> None:
    frame = result.signal_frame[result.signal_frame["ticker"] == ticker].copy()
    if frame.empty:
        return
    frame = frame.sort_values("date")

    entries = frame[frame["entry_signal"].astype(bool)]
    exits = frame[frame["exit_signal"].astype(bool)]

    plt.figure(figsize=(12, 6))
    plt.plot(frame["date"], frame["close"], label=f"{ticker} close", linewidth=1.4)
    if not entries.empty:
        plt.scatter(entries["date"], entries["close"], marker="^", s=45, label="Entry", color="#1b9e77", zorder=3)
    if not exits.empty:
        plt.scatter(exits["date"], exits["close"], marker="v", s=45, label="Exit", color="#d95f02", zorder=3)
    plt.title(f"Trade Annotations ({ticker})")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def _build_resume_snapshot(
    metrics: dict[str, float],
    signal_frame: pd.DataFrame,
    cache_path: Path,
    run_name: str,
) -> str:
    n_tickers = int(signal_frame["ticker"].nunique())
    n_rows = int(len(signal_frame))
    cumulative = metrics.get("cumulative_return", float("nan"))
    max_dd = metrics.get("max_drawdown", float("nan"))
    win_trade = metrics.get("win_rate_trade", float("nan"))

    def pct(x: float) -> str:
        if pd.isna(x):
            return "N/A"
        return f"{x * 100:.2f}%"

    lines = [
        f"Trade Wizards — {run_name}",
        "",
        "- Built a node-based strategy sandbox with neural-network decision nodes for stock signal generation.",
        f"- Processed {n_rows:,} OHLCV rows across {n_tickers} tickers with config-driven cleaning and cached features ({cache_path.name}).",
        (
            "- Ran a backtesting workflow with cumulative return "
            f"{pct(cumulative)}, max drawdown {pct(max_dd)}, and trade win rate {pct(win_trade)}."
        ),
        "- Exported trade-level summaries and chart annotations (entry/exit markers) for explainable strategy review.",
        "- Positioned the product as an educational, non-advisory sandbox with reproducible experiment settings.",
    ]
    return "\n".join(lines)


def save_run_artifacts(
    result: BacktestResult,
    node_outputs: dict[str, pd.Series],
    used_config: dict[str, Any],
    out_root: Path,
    run_name: str,
    cache_path: Path,
) -> Path:
    out_dir = out_root / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = out_dir / "metrics.json"
    metrics_csv_path = out_dir / "metrics.csv"
    signal_path = out_dir / "signal_frame.csv"
    daily_path = out_dir / "daily_returns.csv"
    trades_path = out_dir / "trades.csv"
    config_path = out_dir / "used_config.json"
    node_path = out_dir / "node_outputs_preview.csv"
    resume_snapshot_path = out_dir / "resume_snapshot.md"

    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(result.metrics, f, indent=2)

    pd.DataFrame([result.metrics]).to_csv(metrics_csv_path, index=False)
    result.signal_frame.to_csv(signal_path, index=False)
    result.daily.to_csv(daily_path, index=False)
    result.trades.to_csv(trades_path, index=False)

    with config_path.open("w", encoding="utf-8") as f:
        json.dump(used_config, f, indent=2)

    preview = result.signal_frame[["date", "ticker", "close", "entry_signal", "exit_signal"]].copy()
    for node_name, values in node_outputs.items():
        if values.dtype == "bool":
            preview[node_name] = values.astype("int8")
        else:
            preview[node_name] = pd.to_numeric(values, errors="coerce")
    preview.tail(2000).to_csv(node_path, index=False)

    resume_snapshot = _build_resume_snapshot(
        metrics=result.metrics,
        signal_frame=result.signal_frame,
        cache_path=cache_path,
        run_name=run_name,
    )
    with resume_snapshot_path.open("w", encoding="utf-8") as f:
        f.write(resume_snapshot + "\n")

    chart_ticker = used_config.get("output", {}).get("chart_ticker")
    selected_ticker = _choose_chart_ticker(result.signal_frame, result.trades, preferred_ticker=chart_ticker)
    chart_path = out_dir / f"trade_annotations_{selected_ticker}.png"
    try:
        _plot_trade_annotations(result=result, out_path=chart_path, ticker=selected_ticker)
    except Exception as exc:
        chart_path = out_dir / "trade_annotations_error.txt"
        chart_path.write_text(f"Plotting failed: {exc}\n", encoding="utf-8")

    print(f"[saved] {metrics_path}")
    print(f"[saved] {metrics_csv_path}")
    print(f"[saved] {signal_path}")
    print(f"[saved] {daily_path}")
    print(f"[saved] {trades_path}")
    print(f"[saved] {config_path}")
    print(f"[saved] {node_path}")
    print(f"[saved] {chart_path}")
    print(f"[saved] {resume_snapshot_path}")
    return out_dir
