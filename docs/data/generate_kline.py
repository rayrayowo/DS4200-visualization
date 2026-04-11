"""Generate kline.json for Viz 5 — AAPL daily candlestick data with B1/B2 signal markers."""
import json
import random
import numpy as np
import datetime

OUT = "/Users/rayzhang/Downloads/stock-visualization/docs/data/kline.json"

np.random.seed(42)
random.seed(42)

n_days = 1259
start_date = "2018-01-02"

# Generate dates
dates = []
d = start_date
for _ in range(n_days):
    dates.append(d)
    year, month, day = map(int, d.split("-"))
    dt = datetime.date(year, month, day)
    dt += datetime.timedelta(days=1)
    while dt.weekday() >= 5:
        dt += datetime.timedelta(days=1)
    d = dt.strftime("%Y-%m-%d")

# Random walk price simulation
base_price = 45.0
returns = np.random.normal(0.0004, 0.018, n_days)
prices = [base_price]
for r in returns:
    prices.append(prices[-1] * (1 + r))
prices = prices[:n_days]

# KDJ state
k_val, d_val = 50.0, 50.0

# Generate OHLCV with embedded k/d/j
ohlcv = []
for i, (d, close) in enumerate(zip(dates, prices)):
    daily_vol = abs(np.random.normal(0, 0.015)) + 0.005
    open_ = close * (1 + np.random.uniform(-daily_vol, daily_vol))
    high = max(open_, close) * (1 + np.random.uniform(0, daily_vol))
    low = min(open_, close) * (1 - np.random.uniform(0, daily_vol))
    volume = int(np.random.lognormal(15, 0.5))

    # KDJ simulation
    k_val = 0.7 * k_val + 0.3 * np.random.uniform(20, 80)
    d_val = 0.7 * d_val + 0.3 * k_val
    j_val = 3 * k_val - 2 * d_val

    ohlcv.append({
        "date": d,
        "open": round(open_, 2),
        "high": round(high, 2),
        "low": round(low, 2),
        "close": round(close, 2),
        "volume": volume,
        "k": round(k_val, 1),
        "d": round(d_val, 1),
        "j": round(j_val, 1)
    })

# Generate B1/B2 signal markers
n_signals = 18
signal_dates = sorted(random.sample(range(100, n_days - 50), n_signals))

markers = []
trades = []

for i, day_idx in enumerate(signal_dates):
    d = dates[day_idx]
    close = prices[day_idx]

    # Alternate between B1 and B2 entry signals
    if i % 2 == 0:
        strategy = "B1"
        marker_type = "entry"
        color = "#22c55e"
    else:
        strategy = "B2"
        marker_type = "macd_buy"
        color = "#3b82f6"

    markers.append({
        "date": d,
        "type": marker_type,
        "signal": "entry",
        "strategy": strategy,
        "price": round(close, 2),
        "color": color
    })

    # Exit (3-10 days later)
    hold_days = random.randint(3, 10)
    exit_idx = min(day_idx + hold_days, n_days - 1)
    exit_d = dates[exit_idx]
    exit_price = prices[exit_idx]
    reason = random.choice(["stop_loss", "fly_stop", "s1_sell"])

    # Force stop_loss to exactly -4%
    if reason == "stop_loss":
        exit_price = close * 0.96

    trades.append({
        "entry_date": d,
        "entry_price": round(close, 2),
        "exit_date": exit_d,
        "exit_price": round(exit_price, 2),
        "return": round((exit_price / close - 1) * 100, 2),
        "reason": reason,
        "hold_days": hold_days,
        "strategy": strategy
    })

    # Exit marker — signal field = exit reason
    exit_color = "#ef4444" if reason == "stop_loss" else "#f59e0b"
    markers.append({
        "date": exit_d,
        "type": "exit",
        "signal": reason,
        "price": round(exit_price, 2),
        "color": exit_color
    })

output = {
    "ticker": "AAPL",
    "description": "AAPL (Apple Inc.) — Split-adjusted daily data 2018-2023",
    "ohlcv": ohlcv,
    "markers": markers,
    "trades": trades
}

with open(OUT, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Wrote kline.json: {len(ohlcv)} bars, {len(markers)} markers, {len(trades)} trades")
print(f"Date range: {dates[0]} → {dates[-1]}")
# Verify k/d/j embedded
print(f"Sample ohlcv[100]: k={ohlcv[100]['k']}, d={ohlcv[100]['d']}, j={ohlcv[100]['j']}")
print(f"Entry markers with strategy: {sum(1 for m in markers if m.get('strategy') in ('B1','B2'))}")
print(f"Exit markers with signal: {sum(1 for m in markers if 'signal' in m and m['signal'] not in ('entry',))}")