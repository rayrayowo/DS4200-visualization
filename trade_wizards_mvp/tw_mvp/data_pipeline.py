from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from .config_loader import RunConfig
from .features import add_features


def _to_snake(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", str(name)).strip("_").lower()


def _read_prices_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Raw prices file not found: {path}")

    df = pd.read_csv(path)
    df = df.rename(columns={c: _to_snake(c) for c in df.columns})
    if "name" in df.columns and "ticker" not in df.columns:
        df = df.rename(columns={"name": "ticker"})

    required = {"date", "ticker", "open", "high", "low", "close", "volume"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Raw prices file missing required columns: {missing}")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["ticker"] = df["ticker"].astype(str).str.strip()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["date", "ticker", "high", "low", "close"]).copy()
    df["volume"] = df["volume"].fillna(0.0)
    df = df[(df["close"] > 0) & (df["high"] > 0) & (df["low"] > 0)]

    before = len(df)
    df = df.drop_duplicates(subset=["date", "ticker"], keep="last")
    dropped_dup = before - len(df)
    if dropped_dup > 0:
        print(f"[data] dropped duplicated rows: {dropped_dup:,}")

    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    df["dollar_volume"] = df["close"] * df["volume"]
    return df


def _apply_dataset_filters(df: pd.DataFrame, data_cfg: dict[str, Any]) -> pd.DataFrame:
    frame = df.copy()

    start_date = data_cfg.get("start_date")
    end_date = data_cfg.get("end_date")
    if start_date:
        frame = frame[frame["date"] >= pd.to_datetime(start_date)]
    if end_date:
        frame = frame[frame["date"] <= pd.to_datetime(end_date)]

    min_history_days = int(data_cfg.get("min_history_days", 252))
    per_ticker_counts = frame.groupby("ticker")["date"].count()
    keep_tickers = per_ticker_counts[per_ticker_counts >= min_history_days].index
    frame = frame[frame["ticker"].isin(keep_tickers)]

    max_tickers = data_cfg.get("max_tickers")
    if max_tickers is not None:
        max_tickers = int(max_tickers)
        if max_tickers > 0:
            top_tickers = (
                frame.groupby("ticker", as_index=False)["dollar_volume"]
                .mean()
                .sort_values("dollar_volume", ascending=False)
                .head(max_tickers)["ticker"]
                .tolist()
            )
            frame = frame[frame["ticker"].isin(top_tickers)]

    frame = frame.sort_values(["date", "ticker"]).reset_index(drop=True)
    return frame


def _cache_key(config: RunConfig) -> str:
    raw_data_cfg = config.section("data")
    raw_feature_cfg = config.section("features")

    price_path = config.resolve_path(
        path_value=raw_data_cfg.get("prices_path"),
        default=config.project_root / "data" / "raw" / "all_stocks_5yr.csv",
    )
    payload = {
        "prices_path": str(price_path),
        "prices_mtime_ns": price_path.stat().st_mtime_ns if price_path.exists() else None,
        "data_cfg": raw_data_cfg,
        "features_cfg": raw_feature_cfg,
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.md5(encoded).hexdigest()[:12]


def build_feature_dataset(config: RunConfig) -> tuple[pd.DataFrame, Path]:
    data_cfg = config.section("data")
    feature_cfg = config.section("features")

    raw_prices_path = config.resolve_path(
        path_value=data_cfg.get("prices_path"),
        default=config.project_root / "data" / "raw" / "all_stocks_5yr.csv",
    )
    cache_dir = config.resolve_path(
        path_value=data_cfg.get("cache_dir"),
        default=config.project_root / "trade_wizards_mvp" / "cache",
    )
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_key = _cache_key(config)
    cache_path = cache_dir / f"features_{cache_key}.parquet"
    if cache_path.exists():
        cached = pd.read_parquet(cache_path)
        cached["date"] = pd.to_datetime(cached["date"], errors="coerce")
        print(f"[cache] loaded dataset: {cache_path}")
        return cached, cache_path

    base = _read_prices_csv(raw_prices_path)
    filtered = _apply_dataset_filters(base, data_cfg=data_cfg)
    featured = add_features(filtered, feature_cfg=feature_cfg)
    featured.to_parquet(cache_path, index=False)
    print(f"[cache] built dataset: {cache_path}")
    return featured, cache_path

