"""Generate kline.json — Unix timestamps for timezone-safe TradingView display."""
import json, numpy as np, pandas as pd
from datetime import datetime, timezone

RAW_CSV = "/Users/rayzhang/Downloads/stock-visualization/data/raw/all_stocks_5yr.csv"
OUT     = "/Users/rayzhang/Downloads/stock-visualization/docs/data/kline.json"

def date_to_ts(date_str):
    """Convert YYYY-MM-DD string to Unix timestamp (UTC midnight)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

# ── Load AAPL ──────────────────────────────────────────────────────
df = pd.read_csv(RAW_CSV)
df = df[df["Name"] == "AAPL"].copy().sort_values("date").reset_index(drop=True)

# ── Indicators ──────────────────────────────────────────────────────
def ema_alpha1(s, n):
    return s.ewm(alpha=1.0/n, adjust=False).mean()

def calc_kdj(high, low, close, n=9):
    ln = low.rolling(n, min_periods=n).min()
    hx = high.rolling(n, min_periods=n).max()
    den = (hx - ln).replace(0, np.nan)
    rsv = ((close - ln) / den * 100).fillna(50)
    k = ema_alpha1(rsv, 3); d = ema_alpha1(k, 3)
    return k, d, 3*k - 2*d

def calc_macd(close, f=12, s=26, sig=9):
    dif = close.ewm(span=f, adjust=False).mean() - close.ewm(span=s, adjust=False).mean()
    return dif, dif.ewm(span=sig, adjust=False).mean()

k, d, j = calc_kdj(df["high"], df["low"], df["close"])
dif, dea = calc_macd(df["close"])
ema1 = df["close"].ewm(span=10, adjust=False).mean()
white = ema1.ewm(span=10, adjust=False).mean()
yellow = df["close"].ewm(span=20, adjust=False).mean()

df["kdj_k"] = k.values; df["kdj_d"] = d.values; df["kdj_j"] = j.values
df["macd_dea"] = dea.values
df["zhixing_white"] = white.values; df["zhixing_yellow"] = yellow.values

# ── B1 signals ──────────────────────────────────────────────────────
df["j_prev"] = df["kdj_j"].shift(1)
df["b1_signal"] = (
    (df["kdj_j"] < 13) & (df["j_prev"] >= 13) &
    (df["macd_dea"] > 0) &
    (df["zhixing_white"] > df["zhixing_yellow"])
)
b1_indices = df[df["b1_signal"]].index.tolist()
print(f"B1 signals: {len(b1_indices)}")

# ── B1 backtest (params matching backtest_sp500_b1_dsz.py v2) ──────
STOP_LOSS = -0.02
FLY_PCT   =  0.03
MAX_HOLD  = 10

trades  = []
markers = []

for idx in b1_indices:
    entry_date_str = df.loc[idx, "date"]
    entry_price    = float(df.loc[idx, "open"])
    entry_ts       = date_to_ts(entry_date_str)

    fly_triggered  = False
    remaining_sl   = entry_price * (1 + STOP_LOSS)

    for offset in range(1, min(MAX_HOLD, len(df) - idx)):
        i   = idx + offset
        day = df.iloc[i]
        date_str = day["date"]
        price    = float(day["close"])

        if not fly_triggered:
            ret = (price - entry_price) / entry_price

            if float(day["low"]) <= entry_price * (1 + STOP_LOSS):
                trades.append({
                    "entry_date": entry_date_str, "entry_ts": entry_ts,
                    "entry_price": round(entry_price, 2),
                    "exit_date": date_str, "exit_ts": date_to_ts(date_str),
                    "exit_price": round(entry_price * (1 + STOP_LOSS), 2),
                    "return": round(STOP_LOSS * 100, 2),
                    "reason": "stop_loss", "hold_days": offset, "flew": False
                })
                markers.append({
                    "date": date_str, "ts": date_to_ts(date_str),
                    "type": "exit", "signal": "stop_loss",
                    "strategy": "B1", "price": round(price, 2), "color": "#ef4444"
                })
                break

            if price >= entry_price * (1 + FLY_PCT):
                fly_triggered = True
                remaining_sl   = price * (1 + STOP_LOSS)
                markers.append({
                    "date": date_str, "ts": date_to_ts(date_str),
                    "type": "exit", "signal": "fly_stop",
                    "strategy": "B1", "price": round(price, 2), "color": "#f59e0b"
                })
                continue

            if offset >= MAX_HOLD:
                trades.append({
                    "entry_date": entry_date_str, "entry_ts": entry_ts,
                    "entry_price": round(entry_price, 2),
                    "exit_date": date_str, "exit_ts": date_to_ts(date_str),
                    "exit_price": round(price, 2),
                    "return": round(ret * 100, 2),
                    "reason": "max_hold", "hold_days": offset, "flew": False
                })
                markers.append({
                    "date": date_str, "ts": date_to_ts(date_str),
                    "type": "exit", "signal": "max_hold",
                    "strategy": "B1", "price": round(price, 2), "color": "#a855f7"
                })
                break

        else:
            if float(day["kdj_j"]) > 80 and float(day["kdj_k"]) > float(day["kdj_d"]):
                trades.append({
                    "entry_date": entry_date_str, "entry_ts": entry_ts,
                    "entry_price": round(entry_price, 2),
                    "exit_date": date_str, "exit_ts": date_to_ts(date_str),
                    "exit_price": round(price, 2),
                    "return": round((price - entry_price) / entry_price * 100, 2),
                    "reason": "s1_sell", "hold_days": offset, "flew": True
                })
                markers.append({
                    "date": date_str, "ts": date_to_ts(date_str),
                    "type": "exit", "signal": "s1_sell",
                    "strategy": "B1", "price": round(price, 2), "color": "#3b82f6"
                })
                break

            if float(day["low"]) <= remaining_sl:
                trades.append({
                    "entry_date": entry_date_str, "entry_ts": entry_ts,
                    "entry_price": round(entry_price, 2),
                    "exit_date": date_str, "exit_ts": date_to_ts(date_str),
                    "exit_price": round(price, 2),
                    "return": round((price - entry_price) / entry_price * 100, 2),
                    "reason": "fly_stop", "hold_days": offset, "flew": True
                })
                markers.append({
                    "date": date_str, "ts": date_to_ts(date_str),
                    "type": "exit", "signal": "fly_stop",
                    "strategy": "B1", "price": round(price, 2), "color": "#f59e0b"
                })
                break

            if offset >= MAX_HOLD + 5:
                trades.append({
                    "entry_date": entry_date_str, "entry_ts": entry_ts,
                    "entry_price": round(entry_price, 2),
                    "exit_date": date_str, "exit_ts": date_to_ts(date_str),
                    "exit_price": round(price, 2),
                    "return": round((price - entry_price) / entry_price * 100, 2),
                    "reason": "max_hold", "hold_days": offset, "flew": True
                })
                markers.append({
                    "date": date_str, "ts": date_to_ts(date_str),
                    "type": "exit", "signal": "max_hold",
                    "strategy": "B1", "price": round(price, 2), "color": "#a855f7"
                })
                break
    else:
        last = df.iloc[-1]
        trades.append({
            "entry_date": entry_date_str, "entry_ts": entry_ts,
            "entry_price": round(entry_price, 2),
            "exit_date": last["date"], "exit_ts": date_to_ts(last["date"]),
            "exit_price": round(float(last["close"]), 2),
            "return": round((float(last["close"]) - entry_price) / entry_price * 100, 2),
            "reason": "end_of_data", "hold_days": len(df) - idx, "flew": fly_triggered
        })

    # Entry marker
    markers.append({
        "date": entry_date_str, "ts": entry_ts,
        "type": "entry", "signal": "entry",
        "strategy": "B1", "price": round(entry_price, 2), "color": "#22c55e"
    })

# ── OHLCV (timestamps) ──────────────────────────────────────────────
ohlcv = []
for _, row in df.iterrows():
    ohlcv.append({
        "ts":    date_to_ts(row["date"]),
        "date":  row["date"],
        "open":  round(float(row["open"]), 2),
        "high":  round(float(row["high"]), 2),
        "low":   round(float(row["low"]), 2),
        "close": round(float(row["close"]), 2),
        "volume": int(row["volume"]),
        "k": round(float(row["kdj_k"]), 1),
        "d": round(float(row["kdj_d"]), 1),
        "j": round(float(row["kdj_j"]), 1)
    })

output = {
    "ticker": "AAPL",
    "description": "AAPL (Apple Inc.) — Real B1 backtest data 2013-2018",
    "ohlcv": ohlcv,
    "markers": sorted(markers, key=lambda m: m["ts"]),
    "trades": trades
}

with open(OUT, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Written: {len(ohlcv)} bars, {len(markers)} markers, {len(trades)} trades")
print(f"Time range: {ohlcv[0]['date']} → {ohlcv[-1]['date']}")
ret_dist = {}
for t in trades:
    r = t["reason"]
    ret_dist[r] = ret_dist.get(r, 0) + 1
print(f"Exit distribution: {ret_dist}")
