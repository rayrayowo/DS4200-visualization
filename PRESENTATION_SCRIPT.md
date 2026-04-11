# B1/B2 Trading Strategy Backtest Presentation Script
# DS4200 Final Project — 5 Minutes
# Ruiyang Zhang & Alan | Northeastern University | Spring 2026

---

## [0:00] INTRODUCTION (45 seconds)

**[Slide: Title Page]**

**Speaker:** Hi everyone. Today we're presenting our DS4200 final project: a backtest analysis of two technical analysis-based trading strategies—B1 and B2—across US and Chinese stock markets.

**[Slide: Introduction]**

**Speaker:** Technical indicators like KDJ and MACD are widely used by traders worldwide. But do they actually generate consistent returns? And more importantly, which parameters matter most?

We designed two strategies based on mean-reversion principles:
- **B1** buys when a stock is extremely oversold but the macro trend remains intact
- **B2** adds a momentum confirmation filter—waiting for a volume surge before entering

We backtested these across S&P 500 (505 stocks, 2013-2018) and Chinese A-shares (over 3,000 stocks, 2015-2026), running 81 parameter combinations to find optimal settings.

---

## [1:00] STRATEGY DEFINITION (45 seconds)

**[Slide: Strategy Cards]**

**Speaker:** Let me explain the entry conditions:

**B1** triggers when three conditions align:
1. KDJ J-line drops below 13—indicating extreme oversold conditions
2. MACD DEA remains positive—confirming the broader uptrend is intact
3. The "white line" stays above the "yellow line"—our custom trend filter

The logic is simple: buy the panic dip in an otherwise healthy uptrend.

**B2** is more conservative. It waits for a B1 signal to appear first, then requires:
- A daily gain of at least 4%
- Volume surge of 1.1x or higher
- KDJ J still below 55—not yet overbought

This additional momentum filter significantly improves win rates, as we'll see.

**[Slide: Position Management]**

**Speaker:** Both strategies use identical exit rules:
- **Hard stop-loss** at 2-4% below entry
- **Observation period**—if we're not profitable within 2-3 days, we exit
- **Fly trigger**—when we gain 5-10%, we sell half and let the rest ride
- **S1 exit**—we close remaining positions on heavy volume selling

We manage 10 concurrent positions for B1 and 4 for B2, with dynamic sizing based on portfolio value.

---

## [1:45] DATA & METHODOLOGY (30 seconds)

**[Slide: Data Sources]**

**Speaker:** Our data comes from two sources:
- **S&P 500**: Kaggle dataset supplemented with Yahoo Finance, 505 stocks spanning 2013-2018
- **A-shares**: Tushare Pro API with qfq adjustment, covering over 3,000 stocks from 2015-2026

We computed KDJ, MACD, and trend indicators for each stock, then categorized each day as bull or bear market regime based on whether the S&P proxy traded above its 200-day moving average.

**[Slide: Parameter Sweep]**

**Speaker:** We ran a full parameter sweep: 3 stop-loss levels × 3 observation periods × 3 fly thresholds × 3 bear-market modes. That's 81 combinations per strategy, resulting in over 11,000 trades analyzed.

---

## [2:15] WALKTHROUGH OF VISUALIZATIONS (2 minutes)

**[Slide: Viz 1 - Equity Curve]**

**Speaker:** Let's look at the results. Visualization 1 shows the equity curve for our optimized B1 strategy on S&P 500.

**[Demonstrate interaction]**

The green line is B1, the blue dashed line is B2, and gray is buy-and-hold baseline. You can drag on the mini-chart to zoom into any time period.

Key result: B1 achieved a Sharpe ratio of 1.42 with only -7.6% maximum drawdown, turning $1 million into $1.86 million over 5 years. That's a 13.3% compound annual growth rate.

Notice how the strategy performs consistently in both bull and bear regimes—the shaded green and red backgrounds.

**[Slide: Viz 2 - Parameter Sensitivity]**

**Speaker:** Visualization 2 reveals which parameters matter most.

**[Demonstrate interaction]**

Each cell shows a performance metric for a parameter combination. Darker blue means better Sharpe ratio.

The finding is clear: **stop-loss is the most critical parameter**. A 2% stop-loss consistently outperforms 3% and 4% across all combinations.

This makes sense for mean-reversion strategies: if the oversold bounce doesn't happen immediately, the thesis is wrong—cut losses fast.

**[Slide: Viz 3 - Cross-Market Comparison]**

**Speaker:** Visualization 3 compares performance across markets.

B1 is remarkably consistent—Sharpe 1.42 in the US, 1.59 in China. Similar optimal parameters, similar risk profiles. This suggests the oversold-rebound pattern is a fundamental market behavior, not a market-specific anomaly.

B2 shows market divergence—exceptional in A-shares but modest in S&P 500. This likely reflects differences in momentum patterns between the two markets.

**[Slide: Viz 4 - Trade Outcomes]**

**Speaker:** Visualization 4 breaks down every individual trade.

**[Demonstrate interaction]**

You can filter by exit reason. The scatter plot shows holding period versus return.

Our data shows 54% of trades are profitable with an average return of 2%. Stop-loss exits cluster tightly at -2%, demonstrating effective downside protection. The most profitable trades come from S1 exits and fly stops.

**[Slide: Viz 5 - AAPL K-line]**

**Speaker:** Finally, Visualization 5 shows how these signals look on actual price action.

**[Demonstrate interaction]**

This is Apple's candlestick chart with B1 signals marked. Green circles are buy signals, red squares are stop-loss exits, blue arrows are S1 sells.

You can see how B1 signals consistently appear near local bottoms—not every signal leads to a rally, but the ones that do often precede significant moves.

---

## [4:15] KEY FINDINGS (45 seconds)

**[Slide: Conclusion]**

**Speaker:** To summarize our key findings:

**First, stop-loss is the most important parameter.** A tight 2% stop improved Sharpe ratio by 38% compared to 4%. When trading mean-reversion, wrong entries must be cut immediately.

**Second, B1 is cross-market robust.** Nearly identical performance in US and China with the same optimal parameters. The oversold-rebound pattern transcends market structure.

**Third, B2 is market-dependent.** It works spectacularly in A-shares but underperforms in S&P 500, likely due to different volatility and momentum patterns.

**Fourth, asymmetric returns drive profitability.** Win rates around 50%, but profitable trades generate outsized returns through the fly mechanism. The key is preserving capital on losers while letting winners run.

---

## [5:00] CLOSING (15 seconds)

**Speaker:** Our full backtest engine, signal generation code, and data pipeline are available on GitHub.

Thank you for your attention. We're happy to take questions.

---

## APPENDIX: Technical Notes for Q&A

**If asked about data quality:**
- S&P 500 data from Kaggle is widely used in academic research
- A-share data from Tushare Pro is the industry standard for Chinese market research
- We applied qfq (forward-adjusted) prices to account for dividends and splits

**If asked about overfitting:**
- We used identical parameters across both markets
- The 2% stop-loss finding is consistent across all 81 combinations
- A-shares validation was done after S&P 500 optimization

**If asked about transaction costs:**
- We acknowledge slippage and commissions aren't modeled
- However, our 2-4% stop-loss thresholds provide significant buffer
- Real-world implementation would likely require wider stops

**If asked about future performance:**
- Past results don't guarantee future returns
- Market regimes evolve; strategies require continuous monitoring
- This project demonstrates methodology, not investment advice

---

## PRESENTATION TIPS

1. **Pacing**: Each section has time estimates. Practice to stay within 5 minutes.
2. **Interaction**: Spend ~15 seconds demonstrating each visualization live.
3. **Emphasis**: Highlight the 2% stop-loss finding—that's your key insight.
4. **Transitions**: Use the visualization scroll-spy navigation to move between sections.
5. **Backup**: Keep the Q&A notes handy in case of technical questions.
