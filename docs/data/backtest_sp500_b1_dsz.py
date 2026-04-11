"""
S&P 500 B1 + DSZ(N-type) 回测 v3 — 优化版
调整: fly 阈值, DSZ 更宽松
"""

import json, warnings
from collections import defaultdict
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RAW_CSV = "/Users/rayzhang/Downloads/stock-visualization/data/raw/all_stocks_5yr.csv"
OUT_B1  = "/Users/rayzhang/Downloads/stock-visualization/docs/data/b1_sp500_results.json"
OUT_DSZ = "/Users/rayzhang/Downloads/stock-visualization/docs/data/dsz_sp500_results.json"

# ── 指标 ──────────────────────────────────────────────────────────
def ema(s, n):    return s.ewm(span=n, adjust=False).mean()
def ma(s, n):     return s.rolling(n, min_periods=n).mean()
def td_sma(x, n): return x.ewm(alpha=1.0/n, adjust=False).mean()

def calc_kdj(high, low, close, n=9, ks=3, ds=3):
    ln = low.rolling(n, min_periods=n).min()
    hx = high.rolling(n, min_periods=n).max()
    den = (hx - ln).replace(0, np.nan)
    rsv = ((close - ln) / den * 100).fillna(50)
    k = rsv.ewm(alpha=1/ks, adjust=False).mean()
    d = k.ewm(alpha=1/ds, adjust=False).mean()
    return k, d, 3*k - 2*d

def calc_macd(close, f=12, s=26, sig=9):
    dif = ema(close, f) - ema(close, s)
    return dif, ema(dif, sig)

def zhixing(df):
    inner = ema(df["close"], 10)
    white = ema(inner, 10)
    yellow = (ma(df["close"],14)+ma(df["close"],28)+ma(df["close"],57)+ma(df["close"],114))/4
    return white, yellow

def calc_brick(high, low, close):
    hhv4 = high.rolling(4, min_periods=4).max()
    llv4 = low.rolling(4, min_periods=4).min()
    den  = hhv4 - llv4
    v1a  = pd.Series(np.where(den==0, 0, (hhv4-close)/den*100 - 90), index=close.index)
    v2a  = td_sma(v1a, 4) + 100
    v3a  = pd.Series(np.where(den==0, 0, (close-llv4)/den*100), index=close.index)
    v4a  = td_sma(v3a, 6)
    v5a  = td_sma(v4a, 6) + 100
    brick = pd.Series(np.where(v5a-v2a > 4, v5a-v2a-4, 0), index=close.index)
    pre   = brick.shift(1); pre2 = brick.shift(2)
    today_red   = brick > pre
    today_green = pre > brick
    white = today_red & (pre2 > pre) & ((brick-pre) > (pre2-pre)*2/3)
    return brick, white, today_red, today_green

def shadow_le(high, low, close):
    body = (close - close.shift(1)).abs()
    upper = (high - pd.concat([close, close.shift(1)], axis=1).max(axis=1)).clip(lower=0)
    lower = (pd.concat([close, close.shift(1)], axis=1).min(axis=1) - low).clip(lower=0)
    ratio = (upper+lower) / body.replace(0, np.nan)
    return ratio.fillna(999) <= 0.3

# ── B1 v2: 飞镖改成 3%, 止损 2%, 持10天 ─────────────────────────
def backtest_b1_v2(df):
    """
    B1 美股版: 飞镖 3%, 止损 2%, 持 10 天
    加入 S1 exit (J>80 after fly)
    """
    k, d, j = calc_kdj(df["high"], df["low"], df["close"])
    dif, dea = calc_macd(df["close"])
    white, yellow = zhixing(df)

    df = df.copy()
    df["j"]    = j.values; df["dea"]  = dea.values
    df["white"] = white.values; df["yellow"] = yellow.values
    df["kdj_k"] = k.values; df["kdj_d"] = d.values
    df["j_prev"] = df["j"].shift(1)

    df["b1"] = (
        (df["j"] < 13) & (df["j_prev"] >= 13) &
        (df["dea"] > 0) & (df["white"] > df["yellow"])
    )

    SL = -0.02; FLY = 0.03; MAX_HOLD = 10

    trades = []
    pos = None

    for i in range(1, len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1]

        if prev["b1"] and pos is None:
            pos = {"entry_idx": i, "entry_price": row["open"],
                   "fly": False, "fly_price": 0.0}

        if pos is not None:
            entry_px = pos["entry_price"]
            ret = (row["close"] - entry_px) / entry_px
            hold = i - pos["entry_idx"]
            exited = False

            if not pos["fly"]:
                # 止损
                if row["low"] <= entry_px * (1 + SL):
                    trades.append({
                        "ticker": row["Name"], "entry_date": prev["date"],
                        "exit_date": row["date"],
                        "entry_price": round(entry_px,2),
                        "exit_price": round(entry_px*(1+SL),2),
                        "return": round(SL*100, 2),
                        "exit_reason": "stop_loss",
                        "holding_days": hold, "flew": False
                    })
                    pos = None; exited = True

                # Fly stop (3%)
                elif row["close"] >= entry_px * (1 + FLY):
                    pos["fly"] = True
                    pos["fly_price"] = row["close"]

                # 10天强制走
                elif hold >= MAX_HOLD:
                    trades.append({
                        "ticker": row["Name"], "entry_date": prev["date"],
                        "exit_date": row["date"],
                        "entry_price": round(entry_px,2),
                        "exit_price": round(row["close"],2),
                        "return": round(ret*100, 2),
                        "exit_reason": "max_hold",
                        "holding_days": hold, "flew": False
                    })
                    pos = None; exited = True

            else:
                # Fly 后 S1 exit
                if row["kdj_k"] > row["kdj_d"] and row["j"] > 80:
                    trades.append({
                        "ticker": row["Name"], "entry_date": prev["date"],
                        "exit_date": row["date"],
                        "entry_price": round(entry_px,2),
                        "exit_price": round(row["close"],2),
                        "return": round(ret*100, 2),
                        "exit_reason": "s1_sell",
                        "holding_days": hold, "flew": True
                    })
                    pos = None; exited = True
                elif hold >= MAX_HOLD + 5:
                    trades.append({
                        "ticker": row["Name"], "entry_date": prev["date"],
                        "exit_date": row["date"],
                        "entry_price": round(entry_px,2),
                        "exit_price": round(row["close"],2),
                        "return": round(ret*100, 2),
                        "exit_reason": "max_hold",
                        "holding_days": hold, "flew": True
                    })
                    pos = None; exited = True

    return trades

# ── DSZ N-type v2: 更宽松条件 ────────────────────────────────────
def backtest_dsz_v2(df):
    """
    DSZ N-type 美股版:
    - 不要求 EMA8 择时过滤
    - 不要求量比 >= 1.0（改为宽松）
    - 保留: 白砖 + 知行多头 + DEA>0 + 涨幅>=4% + 影体比
    - 不要求 stroke (s1>=2, s2>=2)，改为只要白砖+突破
    """
    k, d, j = calc_kdj(df["high"], df["low"], df["close"])
    dif, dea = calc_macd(df["close"])
    white, yellow = zhixing(df)
    brick, white_sig, today_red, today_green = calc_brick(df["high"], df["low"], df["close"])

    df = df.copy()
    df["j"] = j.values; df["dea"] = dea.values
    df["white"] = white.values; df["yellow"] = yellow.values
    df["brick"] = brick.values; df["white_sig"] = white_sig.values
    df["today_red"] = today_red.values; df["today_green"] = today_green.values
    df["kdj_k"] = k.values; df["kdj_d"] = d.values
    df["close_prev"] = df["close"].shift(1)
    df["tight_shadow"] = shadow_le(df["high"], df["low"], df["close"]).values

    SL = -0.02; RISE = 0.04

    trades = []
    pos = None

    for i in range(3, len(df)):
        row = df.iloc[i]

        # DSZ 信号: 白砖 + 知行多头 + DEA>0 + 涨幅>=4% + 影体比
        if not row["white_sig"]: continue
        if not (row["dea"] > 0 and row["white"] > row["yellow"]): continue
        if not row["tight_shadow"]: continue
        rise = (row["close"] - row["close_prev"]) / row["close_prev"] if row["close_prev"] > 0 else 0
        if rise < RISE: continue

        if pos is None:
            pos = {"entry_idx": i, "entry_price": row["open"]}

        if pos is not None:
            entry_px = pos["entry_price"]
            ret = (row["close"] - entry_px) / entry_px
            hold = i - pos["entry_idx"]
            exited = False

            # 止损
            if row["low"] <= entry_px * (1 + SL):
                trades.append({
                    "ticker": row["Name"], "entry_date": df.iloc[pos["entry_idx"]]["date"],
                    "exit_date": row["date"],
                    "entry_price": round(entry_px,2),
                    "exit_price": round(entry_px*(1+SL),2),
                    "return": round(SL*100, 2),
                    "exit_reason": "stop_loss",
                    "holding_days": hold, "flew": False,
                    "pattern": "dsz_n", "level": 0
                })
                pos = None; exited = True

            # 砖绿清仓
            elif row["today_green"]:
                trades.append({
                    "ticker": row["Name"], "entry_date": df.iloc[pos["entry_idx"]]["date"],
                    "exit_date": row["date"],
                    "entry_price": round(entry_px,2),
                    "exit_price": round(row["close"],2),
                    "return": round(ret*100, 2),
                    "exit_reason": "brick_green",
                    "holding_days": hold, "flew": False,
                    "pattern": "dsz_n", "level": 0
                })
                pos = None; exited = True

            # 4连阴
            elif i >= 3 and all(df.iloc[i-3:i+1]["today_green"]):
                trades.append({
                    "ticker": row["Name"], "entry_date": df.iloc[pos["entry_idx"]]["date"],
                    "exit_date": row["date"],
                    "entry_price": round(entry_px,2),
                    "exit_price": round(row["close"],2),
                    "return": round(ret*100, 2),
                    "exit_reason": "4day_red",
                    "holding_days": hold, "flew": False,
                    "pattern": "dsz_n", "level": 0
                })
                pos = None; exited = True

            # 数据结束
            if not exited and i == len(df) - 1:
                trades.append({
                    "ticker": row["Name"], "entry_date": df.iloc[pos["entry_idx"]]["date"],
                    "exit_date": row["date"],
                    "entry_price": round(entry_px,2),
                    "exit_price": round(row["close"],2),
                    "return": round(ret*100, 2),
                    "exit_reason": "end_of_data",
                    "holding_days": hold, "flew": False,
                    "pattern": "dsz_n", "level": 0
                })
                pos = None

    return trades

# ── 主循环 ────────────────────────────────────────────────────────
print("Loading data ...")
raw = pd.read_csv(RAW_CSV)
tickers = raw["Name"].unique()
print(f"Total tickers: {len(tickers)}")

all_b1 = []
all_dsz = []

for idx, ticker in enumerate(tickers):
    if idx % 100 == 0:
        print(f"  [{idx}/{len(tickers)}] ...")

    dt = (raw[raw["Name"] == ticker]
          .copy().sort_values("date").reset_index(drop=True))
    dt["date"] = pd.to_datetime(dt["date"]).dt.strftime("%Y-%m-%d")
    if len(dt) < 60:
        continue

    try:
        all_b1.extend(backtest_b1_v2(dt))
    except Exception as e:
        pass

    try:
        all_dsz.extend(backtest_dsz_v2(dt))
    except Exception as e:
        pass

print(f"\nB1: {len(all_b1)} trades | DSZ: {len(all_dsz)} trades")

# ── 权益曲线 ──────────────────────────────────────────────────────
def build_equity(trades, start=1_000_000):
    """逐日累加权益曲线"""
    if not trades:
        return []
    date_set = set()
    for t in trades:
        date_set.add(t["entry_date"]); date_set.add(t["exit_date"])
    dates = sorted(date_set)
    if not dates: return []

    # 按 entry_date 收集仓位
    from collections import defaultdict
    entries_by_date = defaultdict(list)
    exits_by_date = defaultdict(list)
    for t in trades:
        entries_by_date[t["entry_date"]].append(t)
        exits_by_date[t["exit_date"]].append(t)

    # 简化: 按等权组合，每天加总收益
    daily_ret = defaultdict(float)
    for t in trades:
        ed = t["entry_date"]
        xd = t["exit_date"]
        n = max(1, (pd.to_datetime(xd) - pd.to_datetime(ed)).days)
        daily_ret[ed] += 0  # entry当天收益为0
        daily_ret[xd] += t["return"] / 100 / n  # exit当天

    cur = start
    rows = [{"date": dates[0], "value": round(cur, 2)}]
    for d in dates[1:]:
        cur *= (1 + daily_ret[d])
        rows.append({"date": d, "value": round(cur, 2)})
    return rows

b1_eq = build_equity(all_b1)
dsz_eq = build_equity(all_dsz)

# ── 指标 ──────────────────────────────────────────────────────────
def summarize(trades):
    if not trades: return {}
    rets = [t["return"] for t in trades]
    wins = [r for r in rets if r > 0]
    loss = [r for r in rets if r <= 0]
    exits = defaultdict(int)
    for t in trades: exits[t["exit_reason"]] += 1

    n = len(rets)
    return {
        "total_trades": n,
        "win_rate": round(len(wins)/n*100, 1),
        "avg_return": round(float(sum(rets)/n), 2),
        "avg_win": round(float(sum(wins)/len(wins)), 2) if wins else 0,
        "avg_loss": round(float(sum(loss)/len(loss)), 2) if loss else 0,
        "best": round(float(max(rets)), 2),
        "worst": round(float(min(rets)), 2),
        "total_return_pct": round(float(sum(rets)), 1),
        "exit_distribution": dict(exits),
    }

b1_m = summarize(all_b1)
dsz_m = summarize(all_dsz)

# ── 写出 ──────────────────────────────────────────────────────────
with open(OUT_B1, "w") as f:
    json.dump({
        "strategy": "B1 (S&P 500 v2)", "universe": "505 stocks, 2013-2018",
        "params": {"stop_loss": "2%", "fly": "3%", "max_hold": "10d"},
        "equity": b1_eq, "trades": all_b1, "metrics": b1_m
    }, f, indent=2, ensure_ascii=False)

with open(OUT_DSZ, "w") as f:
    json.dump({
        "strategy": "DSZ N-type (S&P 500 v2)", "universe": "505 stocks, 2013-2018",
        "params": {"stop_loss": "2%", "rise_min": "4%", "ema8_filter": False},
        "equity": dsz_eq, "trades": all_dsz, "metrics": dsz_m
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Results:")
print(f"  B1: {b1_m}")
print(f"  DSZ: {dsz_m}")
print(f"  B1 equity: {len(b1_eq)} days | DSZ equity: {len(dsz_eq)} days")
