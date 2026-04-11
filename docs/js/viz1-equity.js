/**
 * Viz 1: B1 / B2 Strategy Equity Curve — D3 Area Chart with Brush Zoom
 * Shows B1 and B2 portfolio values over time with bull/bear regime shading
 * and a buy-and-hold S&P 500 baseline for comparison.
 *
 * Data: b1b2_b1_equity_opt.json  (date, value)
 *       b1b2_b2_equity_opt.json  (date, value)
 *       market_proxy.json        (date, equity, regime)
 */
(function () {
  const container = document.getElementById("viz1-container");
  if (!container) return;

  // ── Dimensions ──
  const margin = { top: 24, right: 30, bottom: 120, left: 72 };
  const fullWidth = Math.max(container.clientWidth, 800);
  const width = fullWidth - margin.left - margin.right;
  const totalHeight = 540;
  const contextHeight = 50;
  const gap = 40;
  const focusHeight = totalHeight - contextHeight - gap - margin.top - margin.bottom;

  // ── Colors ──
  const BULL_BG    = "rgba(34, 197, 94, 0.18)";
  const BEAR_BG    = "rgba(239, 68, 68, 0.22)";
  const B1_COLOR   = "#22c55e";
  const B1_FILL    = "rgba(34, 197, 94, 0.10)";
  const B2_COLOR   = "#3b82f6";
  const B2_FILL    = "rgba(59, 130, 246, 0.10)";
  const BH_COLOR   = "#6b7280";
  const ZERO_COLOR = "#d1d5db";

  // Use compact dollar format to avoid Y-axis label overlap
  const fmtDollar = function(d) {
    if (d >= 1e6) return (d / 1e6).toFixed(1) + "M";
    if (d >= 1e3) return (d / 1e3).toFixed(0) + "K";
    return "$" + d.toFixed(0);
  };
  const fmtPct    = d3.format("+.1f");
  const fmtDate   = d3.timeFormat("%Y-%m-%d");

  // ── SVG ──
  const svg = d3.select(container)
    .append("svg")
    .attr("width", fullWidth + 110)
    .attr("height", totalHeight)
    .attr("role", "img")
    .attr("aria-label", "Portfolio equity curve comparing B1 and B2 strategy performance against S&P 500 buy-and-hold from 2013 to 2018, with bull/bear market regime shading");

  const tooltip = d3.select("#tooltip");

  // ── Load both datasets ──
  Promise.all([
    d3.json("data/b1b2_b1_equity_opt.json"),
    d3.json("data/b1b2_b2_equity_opt.json"),
    d3.json("data/market_proxy.json"),
    d3.json("data/market_ma200.json")
  ]).then(function ([b1Raw, b2Raw, marketRaw, ma200Raw]) {

    // Parse equity data (B1 and B2 strategies)
    const b1Data = b1Raw.map(d => ({
      date: new Date(d.date),
      value: +d.value
    }));
    const b2Data = b2Raw.map(d => ({
      date: new Date(d.date),
      value: +d.value
    }));

    // Parse market data (regime + buy-and-hold baseline)
    const mktData = marketRaw.map(d => ({
      date: new Date(d.date),
      equity: +d.equity,
      regime: d.regime || "bull"
    }));

    // Scale market equity to $1M start for buy-and-hold comparison
    const startEquity = mktData[0].equity || 1;

    // Parse 200-day MA for the S&P proxy line
    const ma200Data = ma200Raw.map(d => ({
      date: new Date(d.date),
      ma200: d.ma200 ? (+d.ma200 / startEquity) * 1000000 : null
    }));

    const bhData = mktData.map(d => ({
      date: d.date,
      value: (d.equity / startEquity) * 1000000
    }));

    // Build regime lookup by aligning dates
    const regimeMap = new Map();
    mktData.forEach(d => regimeMap.set(fmtDate(d.date), d.regime));

    // ── Scales (focus) ──
    const xDomain = d3.extent(b1Data, d => d.date);
    const allValues = b1Data.map(d => d.value).concat(bhData.map(d => d.value), b2Data.map(d => d.value));
    const yMin = d3.min(allValues) * 0.97;
    const yMax = d3.max(allValues) * 1.03;

    const x = d3.scaleTime().domain(xDomain).range([0, width]);
    const y = d3.scaleLinear().domain([yMin, yMax]).range([focusHeight, 0]);

    // ── Scales (context) ──
    const x2 = d3.scaleTime().domain(xDomain).range([0, width]);
    const y2 = d3.scaleLinear().domain([yMin, yMax]).range([contextHeight, 0]);

    // ── Focus group ──
    const focus = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    svg.append("defs").append("clipPath")
      .attr("id", "clip-focus")
      .append("rect")
      .attr("width", width)
      .attr("height", focusHeight);

    const clipped = focus.append("g").attr("clip-path", "url(#clip-focus)");

    // ── Regime bands ──
    function drawRegimeBands(g, xScale, height) {
      g.selectAll(".regime-band").remove();
      let i = 0;
      while (i < mktData.length) {
        const regime = mktData[i].regime;
        const startDate = mktData[i].date;
        let j = i;
        while (j < mktData.length && mktData[j].regime === regime) j++;
        const endDate = mktData[j - 1].date;
        const rx = xScale(startDate);
        const rw = xScale(endDate) - rx;
        if (rw > 0) {
          g.append("rect")
            .attr("class", "regime-band")
            .attr("x", rx)
            .attr("y", 0)
            .attr("width", rw)
            .attr("height", height)
            .attr("fill", regime === "bear" ? BEAR_BG : BULL_BG);
        }
        i = j;
      }
    }
    drawRegimeBands(clipped, x, focusHeight);

    // ── $1M baseline ──
    clipped.append("line")
      .attr("class", "baseline")
      .attr("x1", 0).attr("x2", width)
      .attr("y1", y(1000000)).attr("y2", y(1000000))
      .attr("stroke", ZERO_COLOR)
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "4,4");
    // Label for baseline
    clipped.append("text")
      .attr("x", 4)
      .attr("y", y(1000000) - 6)
      .attr("font-size", "10px")
      .attr("fill", ZERO_COLOR)
      .attr("font-family", "var(--font-mono)")
      .text("$1M");


    // ── Buy & Hold area + line ──
    const bhAreaGen = d3.area()
      .x(d => x(d.date))
      .y0(focusHeight)
      .y1(d => y(d.value))
      .curve(d3.curveMonotoneX);

    const bhLineGen = d3.line()
      .x(d => x(d.date))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX);

    const bhArea = clipped.append("path")
      .datum(bhData)
      .attr("fill", "rgba(107, 114, 128, 0.06)")
      .attr("d", bhAreaGen);

    const bhLine = clipped.append("path")
      .datum(bhData)
      .attr("fill", "none")
      .attr("stroke", BH_COLOR)
      .attr("stroke-width", 1.2)
      .attr("stroke-dasharray", "6,3")
      .attr("d", bhLineGen);

    // ── 200-day MA line (S&P proxy threshold for regime) ──
    // Draw as a solid gray line — regime changes when B&H crosses this line
    const ma200LineGen = d3.line()
      .x(d => x(d.date))
      .y(d => y(d.ma200))
      .defined(d => d.ma200 !== null)
      .curve(d3.curveMonotoneX);
    clipped.append("path")
      .datum(ma200Data)
      .attr("class", "ma200-line")
      .attr("fill", "none")
      .attr("stroke", "#9ca3af")
      .attr("stroke-width", 1)
      .attr("stroke-dasharray", "3,2")
      .attr("opacity", 0.6)
      .attr("d", ma200LineGen);

    // ── B1 Strategy area + line ──
    const b1AreaGen = d3.area()
      .x(d => x(d.date))
      .y0(focusHeight)
      .y1(d => y(d.value))
      .curve(d3.curveMonotoneX);

    const b1LineGen = d3.line()
      .x(d => x(d.date))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX);

    const b1Area = clipped.append("path")
      .datum(b1Data)
      .attr("fill", B1_FILL)
      .attr("d", b1AreaGen);

    const b1Line = clipped.append("path")
      .datum(b1Data)
      .attr("fill", "none")
      .attr("stroke", B1_COLOR)
      .attr("stroke-width", 2)
      .attr("d", b1LineGen);

    // ── B2 Strategy area + line ──
    const b2AreaGen = d3.area()
      .x(d => x(d.date))
      .y0(focusHeight)
      .y1(d => y(d.value))
      .curve(d3.curveMonotoneX);

    const b2LineGen = d3.line()
      .x(d => x(d.date))
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX);

    const b2Area = clipped.append("path")
      .datum(b2Data)
      .attr("fill", B2_FILL)
      .attr("d", b2AreaGen);

    const b2Line = clipped.append("path")
      .datum(b2Data)
      .attr("fill", "none")
      .attr("stroke", B2_COLOR)
      .attr("stroke-width", 2)
      .attr("d", b2LineGen);

    // ── Axes (focus) ──
    const xAxis = d3.axisBottom(x).ticks(8).tickFormat(d3.timeFormat("%b %Y"));
    const gX = focus.append("g")
      .attr("transform", `translate(0,${focusHeight})`)
      .call(xAxis);

    focus.append("g")
      .call(d3.axisLeft(y).ticks(6).tickFormat(fmtDollar));

    // Y-axis label
    focus.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -58).attr("x", -focusHeight / 2)
      .attr("text-anchor", "middle")
      .attr("fill", "#6b7280").attr("font-size", "13px")
      .text("Portfolio Value ($)");

    // ── Legend (inside chart area, top left) ──
    const lgG = svg.append("g").attr("transform", `translate(${margin.left + 10}, ${margin.top + 5})`);
    let ly = 0;
    const lineSpacing = 18;
    function addLegendLine(x, y, stroke, sw, dash) {
      lgG.append("line").attr("x1", 0).attr("x2", x).attr("y1", y).attr("y2", y)
        .attr("stroke", stroke).attr("stroke-width", sw).attr("stroke-dasharray", dash || "");
    }
    function addLegendText(x, y, text, color) {
      lgG.append("text").attr("x", x).attr("y", y).text(text)
        .attr("font-size", "11px").attr("fill", color).attr("font-family", "'DM Sans', sans-serif");
    }
    addLegendLine(20, ly + 4, B1_COLOR, 2, "");
    addLegendText(24, ly + 8, "B1 Strategy", "#374151"); ly += lineSpacing;
    addLegendLine(20, ly + 4, B2_COLOR, 2, "");
    addLegendText(24, ly + 8, "B2 Strategy", "#374151"); ly += lineSpacing;
    addLegendLine(20, ly + 4, BH_COLOR, 1.2, "6,3");
    addLegendText(24, ly + 8, "Buy & Hold S&P 500", "#6b7280"); ly += lineSpacing;
    addLegendLine(20, ly + 4, "#9ca3af", 1, "3,2");
    addLegendText(24, ly + 8, "S&P Proxy 200-day MA", "#6b7280"); ly += lineSpacing;
    // Bull regime swatch
    lgG.append("rect").attr("x", 0).attr("y", ly).attr("width", 14).attr("height", 10)
      .attr("fill", BULL_BG).attr("stroke", "#22c55e").attr("stroke-width", 0.5);
    lgG.append("text").attr("x", 18).attr("y", ly + 9).text("Bull (B&H > MA200)")
      .attr("font-size", "11px").attr("fill", "#6b7280").attr("font-family", "'DM Sans', sans-serif");
    ly += lineSpacing + 2;
    // Bear regime swatch
    lgG.append("rect").attr("x", 0).attr("y", ly).attr("width", 14).attr("height", 10)
      .attr("fill", BEAR_BG).attr("stroke", "#ef4444").attr("stroke-width", 0.5);
    lgG.append("text").attr("x", 18).attr("y", ly + 9).text("Bear (B&H < MA200)")
      .attr("font-size", "11px").attr("fill", "#6b7280").attr("font-family", "'DM Sans', sans-serif");

    // ── Hover tooltip ──
    const bisect = d3.bisector(d => d.date).left;
    const bhBisect = d3.bisector(d => d.date).left;
    const b2Bisect = d3.bisector(d => d.date).left;

    const hoverLine = focus.append("line")
      .attr("stroke", "#999").attr("stroke-width", 1).attr("stroke-dasharray", "3,3")
      .style("opacity", 0);
    const hoverDotB1 = focus.append("circle")
      .attr("r", 4).attr("fill", B1_COLOR).attr("stroke", "#fff").attr("stroke-width", 1.5)
      .style("opacity", 0);
    const hoverDotB2 = focus.append("circle")
      .attr("r", 4).attr("fill", B2_COLOR).attr("stroke", "#fff").attr("stroke-width", 1.5)
      .style("opacity", 0);
    const hoverDotBH = focus.append("circle")
      .attr("r", 3.5).attr("fill", BH_COLOR).attr("stroke", "#fff").attr("stroke-width", 1)
      .style("opacity", 0);

    focus.append("rect")
      .attr("width", width).attr("height", focusHeight)
      .attr("fill", "none").attr("pointer-events", "all")
      .on("mousemove", function (event) {
        const [mx] = d3.pointer(event);
        const date = x.invert(mx);

        // Find closest B1 data point
        const idx = bisect(b1Data, date, 1);
        const d0 = b1Data[idx - 1], d1 = b1Data[idx] || d0;
        const d = date - d0.date > d1.date - date ? d1 : d0;

        // Find closest B2 data point
        const b2Idx = b2Bisect(b2Data, date, 1);
        const b20 = b2Data[b2Idx - 1], b21 = b2Data[b2Idx] || b20;
        const b2pt = date - b20.date > b21.date - date ? b21 : b20;

        // Find closest BH data point
        const bhIdx = bhBisect(bhData, date, 1);
        const bh0 = bhData[bhIdx - 1], bh1 = bhData[bhIdx] || bh0;
        const bh = date - bh0.date > bh1.date - date ? bh1 : bh0;

        // Regime lookup
        const regime = regimeMap.get(fmtDate(d.date)) || "bull";

        // Drawdown: peak-to-trough for B1
        let peak = d.value;
        for (let k = 0; k <= idx; k++) {
          if (b1Data[k].value > peak) peak = b1Data[k].value;
        }
        const dd = ((d.value - peak) / peak * 100);

        hoverLine.attr("x1", x(d.date)).attr("x2", x(d.date))
          .attr("y1", 0).attr("y2", focusHeight).style("opacity", 1);
        hoverDotB1.attr("cx", x(d.date)).attr("cy", y(d.value)).style("opacity", 1);
        hoverDotB2.attr("cx", x(b2pt.date)).attr("cy", y(b2pt.value)).style("opacity", 1);
        hoverDotBH.attr("cx", x(bh.date)).attr("cy", y(bh.value)).style("opacity", 1);

        const b1Ret = ((d.value / 1000000 - 1) * 100);
        const b2Ret = ((b2pt.value / 1000000 - 1) * 100);
        const bhRet = ((bh.value / 1000000 - 1) * 100);

        tooltip.style("opacity", 1)
          .html(
            `<div style="border-bottom:1px solid rgba(255,255,255,0.2);padding-bottom:4px;margin-bottom:4px;font-weight:600;">${fmtDate(d.date)}</div>` +
            `<div><span style="color:${B1_COLOR}">&#9632;</span> B1: ${fmtDollar(d.value)} <span style="color:#9ca3af">(${fmtPct(b1Ret)}%)</span></div>` +
            `<div><span style="color:${B2_COLOR}">&#9632;</span> B2: ${fmtDollar(b2pt.value)} <span style="color:#9ca3af">(${fmtPct(b2Ret)}%)</span></div>` +
            `<div><span style="color:${BH_COLOR}">&#9632;</span> B&amp;H: ${fmtDollar(bh.value)} <span style="color:#9ca3af">(${fmtPct(bhRet)}%)</span></div>` +
            `<div style="border-top:1px solid rgba(255,255,255,0.2);padding-top:4px;margin-top:4px;color:#9ca3af;">` +
            `DD: ${dd.toFixed(1)}% &nbsp;|&nbsp; <span style="color:${regime === 'bear' ? '#ef4444' : '#22c55e'}">${regime.toUpperCase()}</span>` +
            `</div>`
          )
          .style("left", (event.pageX + 15) + "px")
          .style("top", (event.pageY - 10) + "px")
          .style("line-height", "1.6");
      })
      .on("mouseleave", function () {
        hoverLine.style("opacity", 0);
        hoverDotB1.style("opacity", 0);
        hoverDotB2.style("opacity", 0);
        hoverDotBH.style("opacity", 0);
        tooltip.style("opacity", 0);
      });

    // ══════════════════════════════════════════════════════════
    // CONTEXT (mini chart with brush)
    // ══════════════════════════════════════════════════════════
    const contextTop = margin.top + focusHeight + gap;
    const context = svg.append("g")
      .attr("transform", `translate(${margin.left},${contextTop})`);

    // Regime bands on context (draw FIRST so they're behind data lines)
    drawRegimeBands(context, x2, contextHeight);

    // Context B1 area
    const ctxArea = d3.area()
      .x(d => x2(d.date))
      .y0(contextHeight)
      .y1(d => y2(d.value))
      .curve(d3.curveMonotoneX);

    context.append("path")
      .datum(b1Data)
      .attr("fill", "rgba(34, 197, 94, 0.25)")
      .attr("d", ctxArea);

    // Context B2 line
    const ctxB2Line = context.append("path")
      .datum(b2Data)
      .attr("fill", "none")
      .attr("stroke", B2_COLOR)
      .attr("stroke-width", 1)
      .attr("opacity", 0.6)
      .attr("d", d3.line()
        .x(d => x2(d.date))
        .y(d => y2(d.value))
        .curve(d3.curveMonotoneX));

    // Context x-axis
    context.append("g")
      .attr("transform", `translate(0,${contextHeight})`)
      .call(d3.axisBottom(x2).ticks(6).tickFormat(d3.timeFormat("%Y")));

    // Label
    context.append("text")
      .attr("x", width / 2).attr("y", -6)
      .attr("text-anchor", "middle")
      .attr("font-size", "11px").attr("fill", "#999")
      .text("Drag to select time range");

    // ── Brush ──
    function brushed(event) {
      if (!event.selection) {
        x.domain(xDomain);
      } else {
        const [s0, s1] = event.selection.map(x2.invert);
        x.domain([s0, s1]);
      }
      // Update focus chart
      b1Area.attr("d", b1AreaGen);
      b1Line.attr("d", b1LineGen);
      b2Area.attr("d", b2AreaGen);
      b2Line.attr("d", b2LineGen);
      bhArea.attr("d", bhAreaGen);
      bhLine.attr("d", bhLineGen);
      clipped.select(".ma200-line")
        .attr("d", ma200LineGen);
      clipped.select(".baseline")
        .attr("y1", y(1000000)).attr("y2", y(1000000));
      gX.call(xAxis);
      drawRegimeBands(clipped, x, focusHeight);
    }

    const brush = d3.brushX()
      .extent([[0, 0], [width, contextHeight]])
      .on("brush end", brushed);

    context.append("g")
      .attr("class", "brush")
      .call(brush)
      .call(brush.move, [0, width])
      // Style the selection rect (visible blue selection — user feedback for brush range)
      .select(".selection")
      .style("fill", "rgba(37,99,235,0.15)")
      .style("stroke", "rgba(37,99,235,0.5)")
      .style("stroke-width", "1");
    // Hide default D3 triangle handles — we use custom circle handles instead
    context.selectAll(".handle")
      .style("display", "none");

    // ── Brush handle circles (draggable indicators) ──
    // Left handle circle
    const handleLeft = context.append("circle")
      .attr("class", "brush-handle brush-handle-left")
      .attr("cx", 0)
      .attr("cy", contextHeight / 2)
      .attr("r", 6)
      .attr("fill", "var(--color-accent)")
      .attr("opacity", "0.8");

    // Right handle circle
    const handleRight = context.append("circle")
      .attr("class", "brush-handle brush-handle-right")
      .attr("cx", width)
      .attr("cy", contextHeight / 2)
      .attr("r", 6)
      .attr("fill", "var(--color-accent)")
      .attr("opacity", "0.8");

  }).catch(function (err) {
    container.innerHTML = '<p style="color:#E45756;text-align:center;">Error loading data. Check console for details.</p>';
    console.error("Viz1 error:", err);
  });
})();
