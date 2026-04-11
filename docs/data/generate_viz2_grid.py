"""Generate viz2_grid_flat.json from Angel's A-share parameter sweep results."""
import json

ANGEL_GRID = "/Users/rayzhang/clawd/angel/scripts/cache/b1b2_a_shares_grid_full.json"
OUT = "/Users/rayzhang/Downloads/stock-visualization/docs/data/viz2_grid_flat.json"

with open(ANGEL_GRID) as f:
    data = json.load(f)

SL_MAP = {0.02: "2%", 0.03: "3%", 0.04: "4%"}
OBS_MAP = {1: "1 day", 2: "2 days", 3: "3 days"}
FLY_MAP = {0.05: "5%", 0.08: "8%", 0.10: "10%"}
BEAR_MAP = {"full": "full", "half": "half", "skip": "skip"}

rows = []

for strat_key, strat_name in [("b1_all", "B1"), ("b2_all", "B2")]:
    for entry in data.get(strat_key, []):
        p = entry.get("params", {})
        sl = SL_MAP.get(p.get("sl"))
        obs = OBS_MAP.get(p.get("obs"))
        fly = FLY_MAP.get(p.get("fly"))
        bear = BEAR_MAP.get(p.get("bear"))

        if not all([sl, obs, fly, bear]):
            continue

        rows.append({
            "stop_loss": sl,
            "obs_days": obs,
            "fly_pct": fly,
            "bear_mode": bear,
            "strategy": strat_name,
            "sharpe": round(float(entry.get("sharpe", 0)), 3),
            "win_rate": round(float(entry.get("win_rate", 0)), 1),
            "pnl_pct": round(float(entry.get("pnl_pct", 0)), 1),
            "max_dd": round(float(entry.get("max_dd", 0)), 1),
            "trades": int(entry.get("trades", 0))
        })

# Deduplicate - keep best (lowest max_dd for same combo)
seen = {}
for r in rows:
    key = (r["stop_loss"], r["obs_days"], r["fly_pct"], r["bear_mode"], r["strategy"])
    if key not in seen or r["sharpe"] > seen[key]["sharpe"]:
        seen[key] = r

out_rows = sorted(seen.values(), key=lambda x: (
    x["strategy"], x["stop_loss"], x["obs_days"], x["fly_pct"], x["bear_mode"]
))

with open(OUT, "w") as f:
    json.dump(out_rows, f, indent=2)

print(f"Wrote {len(out_rows)} rows to {OUT}")
# Stats
for s in ["B1", "B2"]:
    subset = [r for r in out_rows if r["strategy"] == s]
    print(f"  {s}: {len(subset)} combos, Sharpe range {min(r['sharpe'] for r in subset):.2f}–{max(r['sharpe'] for r in subset):.2f}")