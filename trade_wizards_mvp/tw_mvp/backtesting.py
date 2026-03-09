from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


TRADING_DAYS_PER_YEAR = 252


@dataclass
class BacktestResult:
    signal_frame: pd.DataFrame
    daily: pd.DataFrame
    trades: pd.DataFrame
    metrics: dict[str, float]


def _compute_drawdown(equity: pd.Series) -> pd.Series:
    peak = equity.cummax()
    return equity / peak - 1.0


def build_position_frame(signal_frame: pd.DataFrame) -> pd.DataFrame:
    required = {"date", "ticker", "close", "ret_1d", "entry_signal", "exit_signal"}
    missing = sorted(required.difference(signal_frame.columns))
    if missing:
        raise ValueError(f"Signal frame missing required columns: {missing}")

    frame = signal_frame.copy().sort_values(["ticker", "date"]).reset_index(drop=True)

    position_chunks: list[pd.DataFrame] = []
    for _, g in frame.groupby("ticker", sort=False):
        g = g.copy()
        state = 0.0
        pos: list[float] = []
        for enter, exit_ in zip(g["entry_signal"].astype(bool), g["exit_signal"].astype(bool), strict=True):
            if exit_:
                state = 0.0
            if enter:
                state = 1.0
            pos.append(state)
        g["position"] = pd.Series(pos, index=g.index, dtype="float64")
        position_chunks.append(g)

    out = pd.concat(position_chunks, ignore_index=True).sort_values(["date", "ticker"]).reset_index(drop=True)
    return out


def build_daily_returns(position_frame: pd.DataFrame, fee_bps: float, slippage_bps: float) -> pd.DataFrame:
    frame = position_frame.copy().sort_values(["ticker", "date"]).reset_index(drop=True)
    frame["ret_1d"] = pd.to_numeric(frame["ret_1d"], errors="coerce").fillna(0.0)
    frame["position"] = pd.to_numeric(frame["position"], errors="coerce").fillna(0.0).clip(0.0, 1.0)
    frame["position_prev"] = frame.groupby("ticker", sort=False)["position"].shift(1).fillna(0.0)
    frame["turnover"] = (frame["position"] - frame["position_prev"]).abs()

    cost_rate = (fee_bps + slippage_bps) / 10_000.0
    frame["gross_ret"] = frame["position_prev"] * frame["ret_1d"]
    frame["cost_ret"] = frame["turnover"] * cost_rate
    frame["strategy_ret"] = frame["gross_ret"] - frame["cost_ret"]
    frame["is_active"] = (frame["position_prev"] > 0).astype("int8")

    daily = (
        frame.groupby("date", as_index=False)
        .agg(
            strategy_ret=("strategy_ret", "mean"),
            gross_ret=("gross_ret", "mean"),
            cost_ret=("cost_ret", "mean"),
            turnover=("turnover", "mean"),
            exposure=("is_active", "mean"),
            active_positions=("is_active", "sum"),
            universe_size=("ticker", "size"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    daily["equity"] = (1.0 + daily["strategy_ret"]).cumprod()
    daily["drawdown"] = _compute_drawdown(daily["equity"])
    return daily


def extract_trades(position_frame: pd.DataFrame) -> pd.DataFrame:
    frame = position_frame.copy().sort_values(["ticker", "date"]).reset_index(drop=True)
    rows: list[dict[str, object]] = []

    for ticker, g in frame.groupby("ticker", sort=False):
        g = g.copy().reset_index(drop=True)
        g["active"] = g["position"].shift(1).fillna(0.0) > 0
        starts = g.index[g["active"] & ~g["active"].shift(1, fill_value=False)]
        ends = g.index[g["active"] & ~g["active"].shift(-1, fill_value=False)]

        for start_idx, end_idx in zip(starts.to_list(), ends.to_list(), strict=True):
            ret_slice = pd.to_numeric(g.loc[start_idx:end_idx, "ret_1d"], errors="coerce").fillna(0.0)
            trade_return = float(np.prod(1.0 + ret_slice.to_numpy()) - 1.0)
            rows.append(
                {
                    "ticker": ticker,
                    "entry_date": g.loc[start_idx, "date"],
                    "exit_date": g.loc[end_idx, "date"],
                    "entry_price": float(g.loc[start_idx, "close"]),
                    "exit_price": float(g.loc[end_idx, "close"]),
                    "holding_days": int(end_idx - start_idx + 1),
                    "trade_return": trade_return,
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=["ticker", "entry_date", "exit_date", "entry_price", "exit_price", "holding_days", "trade_return"]
        )
    return pd.DataFrame(rows).sort_values(["entry_date", "ticker"]).reset_index(drop=True)


def compute_metrics(daily: pd.DataFrame, trades: pd.DataFrame) -> dict[str, float]:
    if daily.empty:
        return {
            "n_days": 0.0,
            "cumulative_return": np.nan,
            "cagr": np.nan,
            "annual_volatility": np.nan,
            "sharpe": np.nan,
            "max_drawdown": np.nan,
            "win_rate_daily": np.nan,
            "total_trades": np.nan,
            "win_rate_trade": np.nan,
            "avg_trade_return": np.nan,
            "avg_holding_days": np.nan,
        }

    ret = pd.to_numeric(daily["strategy_ret"], errors="coerce").fillna(0.0)
    n_days = len(ret)
    cumulative_return = float((1.0 + ret).prod() - 1.0)
    cagr = float((1.0 + cumulative_return) ** (TRADING_DAYS_PER_YEAR / n_days) - 1.0) if n_days > 0 else np.nan

    annual_vol = float(ret.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR))
    sharpe = float(ret.mean() / ret.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR)) if annual_vol > 0 else np.nan
    max_drawdown = float(pd.to_numeric(daily["drawdown"], errors="coerce").min())
    win_rate_daily = float((ret > 0).mean())

    metrics = {
        "n_days": float(n_days),
        "cumulative_return": cumulative_return,
        "cagr": cagr,
        "annual_volatility": annual_vol,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "win_rate_daily": win_rate_daily,
        "total_trades": float(len(trades)) if not trades.empty else 0.0,
        "win_rate_trade": float((trades["trade_return"] > 0).mean()) if not trades.empty else np.nan,
        "avg_trade_return": float(trades["trade_return"].mean()) if not trades.empty else np.nan,
        "avg_holding_days": float(trades["holding_days"].mean()) if not trades.empty else np.nan,
    }
    return metrics


def run_backtest(signal_frame: pd.DataFrame, fee_bps: float, slippage_bps: float) -> BacktestResult:
    position_frame = build_position_frame(signal_frame=signal_frame)
    daily = build_daily_returns(position_frame=position_frame, fee_bps=fee_bps, slippage_bps=slippage_bps)
    trades = extract_trades(position_frame=position_frame)
    metrics = compute_metrics(daily=daily, trades=trades)
    return BacktestResult(signal_frame=position_frame, daily=daily, trades=trades, metrics=metrics)

