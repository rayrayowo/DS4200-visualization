from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _rsi(close: pd.Series, window: int) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0.0)
    loss = -diff.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def _zscore(series: pd.Series, window: int) -> pd.Series:
    mean = series.rolling(window=window, min_periods=window).mean()
    std = series.rolling(window=window, min_periods=window).std(ddof=0)
    z = (series - mean) / std.replace(0.0, np.nan)
    return z.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def add_features(df: pd.DataFrame, feature_cfg: dict[str, Any]) -> pd.DataFrame:
    sma_fast = int(feature_cfg.get("sma_fast", 20))
    sma_slow = int(feature_cfg.get("sma_slow", 60))
    rsi_window = int(feature_cfg.get("rsi_window", 14))
    volume_z_window = int(feature_cfg.get("volume_z_window", 20))
    lookahead_days = int(feature_cfg.get("lookahead_days", 5))

    if sma_fast <= 0 or sma_slow <= 0:
        raise ValueError("sma_fast and sma_slow must be positive.")
    if rsi_window <= 1:
        raise ValueError("rsi_window must be > 1.")
    if lookahead_days <= 0:
        raise ValueError("lookahead_days must be positive.")

    def per_ticker(g: pd.DataFrame) -> pd.DataFrame:
        out = g.sort_values("date").copy()
        close = out["close"]

        out["ret_1d"] = close.pct_change()
        out["ret_5d"] = close.pct_change(5)
        out["ret_20d"] = close.pct_change(20)

        out[f"sma_{sma_fast}"] = close.rolling(window=sma_fast, min_periods=sma_fast).mean()
        out[f"sma_{sma_slow}"] = close.rolling(window=sma_slow, min_periods=sma_slow).mean()

        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()
        out["macd_line"] = ema_fast - ema_slow
        out["macd_signal"] = out["macd_line"].ewm(span=9, adjust=False).mean()
        out["macd_hist"] = out["macd_line"] - out["macd_signal"]

        out[f"rsi_{rsi_window}"] = _rsi(close=close, window=rsi_window)
        out[f"volume_z{volume_z_window}"] = _zscore(out["volume"], window=volume_z_window)

        fwd = close.shift(-lookahead_days) / close - 1.0
        out[f"fwd_ret_{lookahead_days}d"] = fwd
        out[f"target_up_{lookahead_days}d"] = (fwd > 0).astype("float64")
        out.loc[fwd.isna(), f"target_up_{lookahead_days}d"] = np.nan
        return out

    chunks = []
    for _, ticker_frame in df.groupby("ticker", sort=False):
        chunks.append(per_ticker(ticker_frame))

    out = pd.concat(chunks, ignore_index=True)
    out = out.sort_values(["date", "ticker"]).reset_index(drop=True)
    return out

