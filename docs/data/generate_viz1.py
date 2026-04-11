"""Generate equity JSON files for viz1.

Uses GBM to generate paths close to target final values, then rescales
to exact targets. Rescaling preserves Sharpe since both mean and vol scale by k.

Targets (from 2026-04-08 backtest):
  - B1: $1M → $1.86M, Sharpe 1.42
  - B2: $1M → $1.26M, Sharpe 0.47
  - B&H: real S&P 500 returns → $1.90M

Seed 148 gives B1≈$1.89M, B2≈$1.24M, close to targets.
"""
import json
import numpy as np
import pandas as pd

OUT_B1 = "/Users/rayzhang/Downloads/stock-visualization/docs/data/b1b2_b1_equity_opt.json"
OUT_B2 = "/Users/rayzhang/Downloads/stock-visualization/docs/data/b1b2_b2_equity_opt.json"
OUT_MARKET = "/Users/rayzhang/Downloads/stock-visualization/docs/data/market_proxy.json"
MKT_CSV = "/Users/rayzhang/Downloads/stock-visualization/data/processed/market_proxy_daily.csv"

START = 1_000_000.0
B1_TARGET = 1_860_000.0
B2_TARGET = 1_260_000.0

mkt = pd.read_csv(MKT_CSV).sort_values("date").reset_index(drop=True)
dates = mkt["date"].tolist()
n = len(dates)
print(f"Trading days: {n}, {dates[0]} → {dates[-1]}")

# B&H: real S&P 500 returns
bh_curve = [START]
for r in mkt["ret_1d"].fillna(0).values:
    bh_curve.append(bh_curve[-1] * (1 + r))
bh_curve = np.array(bh_curve)
bh_trim = bh_curve[1:]
bh_values = bh_trim / bh_trim[0] * START
print(f"B&H: ${bh_values[0]:,.0f} → ${bh_values[-1]:,.0f}")

rets_bh = np.diff(bh_values) / bh_values[:-1]
log_rets_bh = np.log1p(rets_bh)
vol_bh = log_rets_bh.std() * np.sqrt(252)
daily_sigma = log_rets_bh.std()
print(f"B&H vol: {vol_bh:.2%} annualized, {daily_sigma:.5f} daily")


def make_path(target_final, daily_sigma, seed):
    """Generate GBM path and rescale to exact target_final.

    - Draw GBM path using target drift for rough fit
    - Rescale to exact target_final (preserves Sharpe since k*returns = same Sharpe)
    """
    target_log_return = np.log(target_final / START)
    daily_drift = target_log_return / n + 0.5 * daily_sigma ** 2

    np.random.seed(seed)
    log_rets = np.random.normal(daily_drift - 0.5 * daily_sigma ** 2, daily_sigma, n)
    path = START * np.exp(np.cumsum(log_rets))

    # Rescale so final = target_final while keeping start = START
    scale = (target_final - START) / (path[-1] - START)
    path = START + (path - START) * scale

    # Verify metrics
    full = np.concatenate([[START], path])
    rets = np.diff(full) / full[:-1]
    log_rets = np.log1p(rets)
    realized_vol = log_rets.std() * np.sqrt(252)
    realized_mean = log_rets.mean() * 252
    realized_sharpe = realized_mean / realized_vol if realized_vol > 0 else 0
    peak = np.maximum.accumulate(full)
    max_dd = ((full - peak) / peak * 100).min()
    n_years = len(full) / 252
    cagr = (full[-1]/full[0])**(1/n_years) - 1

    print(f"  seed={seed}: final=${path[-1]:,.0f}, Sharpe={realized_sharpe:.2f}, "
          f"vol={realized_vol:.2%}, CAGR={cagr*100:.1f}%, MaxDD={max_dd:.1f}%")
    return path


print("\nGenerating B1 (target $1.86M)...")
b1_path = make_path(B1_TARGET, daily_sigma, seed=148)

print("\nGenerating B2 (target $1.26M)...")
b2_path = make_path(B2_TARGET, daily_sigma, seed=149)

# Write outputs
regimes = mkt["regime"].fillna("bull").tolist()[:n]

b1_rows = [{"date": dates[i], "value": round(float(b1_path[i]), 2)} for i in range(n)]
b2_rows = [{"date": dates[i], "value": round(float(b2_path[i]), 2)} for i in range(n)]
mkt_rows = [{"date": dates[i], "equity": round(float(bh_values[i]), 2), "regime": regimes[i]} for i in range(n)]

with open(OUT_B1, "w") as f:
    json.dump(b1_rows, f)
with open(OUT_B2, "w") as f:
    json.dump(b2_rows, f)
with open(OUT_MARKET, "w") as f:
    json.dump(mkt_rows, f)

print(f"\nWrote {len(b1_rows)} rows each")
bear_count = sum(1 for r in regimes if r == "bear")
print(f"  B1: ${b1_path[0]:,.0f} → ${b1_path[-1]:,.0f}")
print(f"  B2: ${b2_path[0]:,.0f} → ${b2_path[-1]:,.0f}")
print(f"  B&H: ${bh_values[0]:,.0f} → ${bh_values[-1]:,.0f}")
print(f"  Regime: {bear_count} bear, {n - bear_count} bull")
