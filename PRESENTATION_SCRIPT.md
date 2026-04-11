# B1/B2 Trading Strategy Visualization — Implementation Script
# DS4200 Final Project — 5 Minutes
# Ruiyang Zhang & Alan | Northeastern University | Spring 2026

---

## [0:00] INTRODUCTION (30 seconds)

**[Slide: Title Page]**

**Speaker:** Hi everyone. Today we're presenting our DS4200 final project: an interactive visualization dashboard for technical trading strategy backtesting.

**[Slide: Project Overview]**

**Speaker:** We're analyzing two mean-reversion trading strategies—B1 and B2—across US and Chinese stock markets. But the focus of this project is **how we visualize** this complex multi-dimensional data to make it interpretable and actionable.

We used **three different visualization libraries**—D3.js, Altair, and TradingView Lightweight Charts—each chosen for specific strengths in handling different data types and interaction patterns.

---

## [1:00] DATA PIPELINE (30 seconds)

**[Slide: Data & Technical Indicators]**

**Speaker:** First, let's talk about the data pipeline. We start with raw OHLCV data from Kaggle and Tushare Pro. The key challenge is computing derived variables:

- **KDJ oscillator** (9,3,3) — generates 3 time series: K, D, and J lines
- **MACD** (12,26,9) — generates MACD line, signal line, and histogram
- **Zhixing trend lines** — custom exponential moving averages
- **Market regime** — binary classification (bull/bear) based on 200-day MA

For the dashboard, all pre-computed indicators are serialized as JSON—this allows the browser to render charts instantly without server-side processing.

---

## [1:30] WALKTHROUGH OF VISUALIZATIONS (3 minutes)

**[Slide: Viz 1 - D3.js Equity Curve]**

**Speaker:** Let's start with Visualization 1—the equity curve using **D3.js v7**.

**[Demonstrate interaction]**

**Speaker:** Why D3? Because we needed full control over the multi-layer layout. This chart combines:
- A main focus area with line charts
- A mini navigation chart below it for brush-based zooming
- A shaded background showing market regime (bull/bear)
- A synchronized crosshair showing portfolio value and drawdown

The key technical challenge here was **coordinate mapping** across multiple scales—portfolio value (linear), drawdown percentage (linear), and time (temporal). D3's `scaleLinear` and `scaleTime` let us create reusable coordinate systems.

**[Demonstrate brushing]**

**Speaker:** The brush-and-zoom interaction is implemented using D3's brush behavior. When you drag on the mini-chart, it updates the domain of the main chart's x-scale. This is a classic **focus + context** pattern from the D3 gallery.

We also added **regime bands**—green for bull, red for bear—rendered as background rectangles with opacity. This lets viewers correlate strategy performance with market conditions.

---

**[Slide: Viz 2 - Altair Heatmap]**

**Speaker:** Visualization 2 uses **Altair**—a Python declarative visualization library built on Vega-Lite.

**[Demonstrate interaction]**

**Speaker:** Why Altair here? Because we have a **3-dimensional categorical problem**: stop-loss × observation period × fly trigger. That's 81 combinations, each with multiple metrics (Sharpe, win rate, max drawdown).

Altair's `facet` operator lets us create small multiples effortlessly. We specify: "show me a heatmap faceted by fly trigger, with x-axis as stop-loss and y-axis as observation period"—and Altair generates the grid layout.

The key design decision is **color encoding**:
- For Sharpe and Win Rate: blue sequential (darker = better)
- For Max Drawdown: red sequential (darker = worse)

This uses **pre-attentive processing**—users instantly spot the optimal parameter region without reading individual values.

**[Demonstrate radio buttons]**

**Speaker:** We also use **parameter binding**—radio buttons dynamically re-encode the same data structure. The underlying data doesn't change, only the color scale and field mapping. This demonstrates Altair's strength in rapid prototyping of comparative views.

---

**[Slide: Viz 3 - Static Cross-Market]**

**Speaker:** Visualization 3 is a static image—but it's generated programmatically using Matplotlib.

We chose static here because the comparison is straightforward: two markets, two strategies, four metrics. A static image with clean typography and aligned axes is actually **more effective** than an interactive chart for this specific comparison.

The key is **consistent scales** across subplots—same y-axis range for Sharpe ratios, same color coding for strategies. This allows valid visual comparison.

---

**[Slide: Viz 4 - D3.js Scatter Plot]**

**Speaker:** Back to **D3.js** for Visualization 4—the trade outcome scatter.

**[Demonstrate filtering]**

**Speaker:** This is a classic **filterable scatter plot**. Each dot is one trade:
- X-axis: holding period (days)
- Y-axis: return percentage
- Color: exit reason
- White ring: whether the "fly" mechanism triggered

The interaction pattern here is **dynamic filtering**. When you uncheck an exit reason, D3's data join efficiently updates the DOM—only the affected circles transition. We use `attr("r", 0)` on exit and animate radius on enter for smooth transitions.

The tooltip is implemented using D3's mouse events—`mouseover` to show, `mousemove` to follow cursor, `mouseout` to hide. We also add a temporary radius enlargement on hover for **visual feedback**.

A key design choice: we filter by **exit reason** rather than return range or holding period. This is because exit reason has categorical semantic meaning—users want to compare "stop-loss exits" vs "S1 exits"—not arbitrary numeric ranges.

---

**[Slide: Viz 5 - TradingView Lightweight Charts]**

**Speaker:** Finally, Visualization 5 uses **TradingView Lightweight Charts v4**—a specialized library for financial time series.

**[Demonstrate interaction]**

**Speaker:** Why a specialized library here? Because candlestick charts with volume and indicators have unique requirements:
- Date/time handling with market hours
- Price axis with automatic scaling
- Synchronized crosshair across multiple sub-charts
- Efficient rendering of thousands of candles

Lightweight Charts handles all of this out of the box. We're essentially using it as a **canvas rendering engine**.

The challenge was **overlaid markers**—buy/sell signals from our backtest. We computed marker positions from our trade data and used the library's `addCandlestickSeries()` and `setMarkers()` APIs.

**[Demonstrate KDJ sub-chart]**

**Speaker:** Below the main chart, we have a KDJ indicator panel. This is a separate chart instance, but we **synchronize their time scales** using the `timeScale()` method. When you pan or zoom on the main chart, the KDJ chart automatically follows.

We also added a custom **OHLCV data panel** that updates on crosshair hover. This mimics professional trading terminals—showing open, high, low, close, and volume for the selected date.

---

## [4:30] DESIGN DECISIONS (30 seconds)

**[Slide: Technical Stack Summary]**

**Speaker:** To summarize our library choices:

| Library | Used For | Why |
|---------|----------|-----|
| **D3.js** | Viz 1, 4 | Full control, custom interactions, complex layouts |
| **Altair** | Viz 2 | Rapid prototyping, declarative syntax, small multiples |
| **TradingView** | Viz 5 | Domain-specific, efficient rendering, built-in interactions |

Each library was chosen for its **comparative advantage**—we didn't try to force everything into one tool.

---

## [5:00] CONCLUSION (30 seconds)

**[Slide: Key Takeaways]**

**Speaker:** Our visualization approach demonstrates several key principles:

1. **Tool selection matters**—matching the library to the problem
2. **Interaction patterns should be purposeful**—brush for zoom, filters for exploration, crosshairs for inspection
3. **Data preprocessing is critical**—JSON serialization enables instant rendering
4. **Responsive design**—all charts adapt to container width
5. **Accessibility**—semantic HTML, ARIA labels, keyboard navigation

The dashboard is live at the URL in the README. Thank you!

---

## APPENDIX: Technical Details for Q&A

**If asked about data size:**
- S&P 500: ~125K daily records × 505 stocks
- After aggregation: ~3,800 trades, 1,259 equity curve points
- All visualizations load under 2 seconds on typical broadband

**If asked about D3 learning curve:**
- Steep initial curve, but powerful once mastered
- Key concepts: selections, joins, scales, transitions
- We reused patterns from D3 Gallery and adapted them

**If asked about Altair vs D3:**
- Altair is faster to prototype (declarative)
- D3 gives more control (imperative)
- We used both where each shines

**If asked about mobile support:**
- Charts are responsive (resize observers)
- Touch gestures work on TradingView charts
- D3 charts could add touch support with additional event handlers

**If asked about color choices:**
- Used ColorBrewer schemes for colorblind safety
- High contrast for text (WCAG AA compliant)
- Consistent color coding across charts (B1=green, B2=blue, stop-loss=red)

---

## PRESENTATION TIPS

1. **Focus on HOW not WHAT**—emphasize implementation over results
2. **Demonstrate live**—spend ~30 seconds per chart showing interactions
3. **Use technical terms**—this is a visualization course audience
4. **Prepare for questions**—have the code open for reference
5. **Time management**—each section is timed, practice to stay within 5 minutes
