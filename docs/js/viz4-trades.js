/**
 * Viz 4: Individual Trade Outcomes — D3 Scatter Plot
 * Each dot = one trade. X = holding days, Y = return %.
 * Color = exit reason. White ring = flew (sold half at fly trigger).
 */
(function () {
  const container = document.getElementById("viz4-container");
  const statsDiv = document.getElementById("viz4-stats");
  const filtersDiv = document.getElementById("viz4-filters");
  if (!container) return;

  // ── Dimensions ──
  const margin = { top: 20, right: 30, bottom: 50, left: 60 };
  const fullWidth = Math.max(container.clientWidth, 700);
  const fullHeight = 440;
  const width = fullWidth - margin.left - margin.right;
  const height = fullHeight - margin.top - margin.bottom;

  // ── Exit reason colors ──
  const EXIT_COLORS = {
    stop_loss: "#ef4444",
    fly_stop: "#f59e0b",
    s1_sell: "#22c55e",
    end: "#6b7280",
    "4day_half": "#8b5cf6",
    "8day_full": "#a855f7",
    end_of_data: "#6b7280"
  };
  const EXIT_LABELS = {
    stop_loss: "Stop-Loss",
    fly_stop: "Fly (Sold Half)",
    s1_sell: "S1 Sell",
    end: "End of Data",
    "4day_half": "4-Day Half",
    "8day_full": "8-Day Full",
    end_of_data: "End of Data"
  };

  const tooltip = d3.select("#tooltip");

  d3.json("data/b1b2_b1_trades_opt.json").then(function (raw) {
    const activePositions = raw && !Array.isArray(raw) ? (raw.active_positions || {}) : {};

    const sourceTrades = Array.isArray(raw)
      ? raw
      : Array.isArray(raw && raw.trades)
        ? raw.trades
        : [];

    const trades = sourceTrades.map(d => ({
      ticker: d.ticker,
      entry: d.entry_date || d.entry,
      exit: d.exit_date || d.exit,
      entryPrice: +(d.entry_price ?? d.entryPrice),
      exitPrice: +(d.exit_price ?? d.exitPrice),
      ret: d.total_return !== undefined ? +d.total_return * 100 : +d.ret,
      days: +(d.holding_days ?? d.days),
      reason: d.exit_reason || d.reason,
      flew: Boolean(d.flew)
    }));

    // ── Summary stats ──
    const total = trades.length;
    const wins = trades.filter(t => t.ret > 0).length;
    const winRate = ((wins / total) * 100).toFixed(1);
    const avgRet = (trades.reduce((s, t) => s + t.ret, 0) / total).toFixed(2);
    const avgDays = (trades.reduce((s, t) => s + t.days, 0) / total).toFixed(1);

    if (statsDiv) {
      statsDiv.innerHTML = `
        <div class="stat-grid">
          <div class="stat-item"><span class="stat-val">${total}</span><span class="stat-label">Total Trades</span></div>
          <div class="stat-item"><span class="stat-val">${winRate}%</span><span class="stat-label">Win Rate</span></div>
          <div class="stat-item"><span class="stat-val">${avgRet}%</span><span class="stat-label">Avg Return</span></div>
          <div class="stat-item"><span class="stat-val">${avgDays}d</span><span class="stat-label">Avg Hold</span></div>
        </div>`;
    }

    // ── Filter checkboxes ──
    const activeReasons = new Set(
      Object.keys(EXIT_COLORS).filter(k => trades.some(t => t.reason === k))
    );

    function buildFilters() {
      let html = '<strong class="filter-label">Exit Reason:</strong>';
      for (const [key, label] of Object.entries(EXIT_LABELS)) {
        const color = EXIT_COLORS[key];
        const count = trades.filter(t => t.reason === key).length;
        if (count === 0) continue;  // skip exit reasons not in data
        html += `<label class="filter-cb">
          <input type="checkbox" data-reason="${key}" checked>
          <span style="color:${color}">${label}</span> (${count})
        </label>`;
      }
      if (filtersDiv) filtersDiv.innerHTML = html;

      // Bind events
      filtersDiv.querySelectorAll('input[data-reason]').forEach(cb => {
        cb.addEventListener('change', function () {
          if (this.checked) activeReasons.add(this.dataset.reason);
          else activeReasons.delete(this.dataset.reason);
          updateDots();
        });
      });

      // Safety: if no reason checkboxes are selected, re-select all
      filtersDiv.querySelectorAll('input[data-reason]').forEach(function (cb) {
        cb.addEventListener('change', function () {
          if (activeReasons.size === 0) {
            filtersDiv.querySelectorAll('input[data-reason]').forEach(function (c) { c.checked = true; });
            Object.keys(EXIT_COLORS).forEach(function (k) {
              if (trades.some(function (t) { return t.reason === k; })) activeReasons.add(k);
            });
          }
        });
      });
    }
    buildFilters();

    // ── SVG ──
    const svg = d3.select(container)
      .append("svg")
      .attr("width", fullWidth)
      .attr("height", fullHeight)
      .attr("role", "img")
      .attr("aria-label", "Scatter plot of 3,852 individual B1 trades on S&P 500, showing holding period (days) on x-axis and return (percent) on y-axis, colored by exit reason");

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // ── Scales ──
    const x = d3.scaleLinear()
      .domain([0, d3.max(trades, t => t.days) * 1.05])
      .range([0, width]);

    const yExtent = d3.extent(trades, t => t.ret);
    const yPad = Math.max(Math.abs(yExtent[0]), Math.abs(yExtent[1])) * 0.1;
    const y = d3.scaleLinear()
      .domain([yExtent[0] - yPad, yExtent[1] + yPad])
      .range([height, 0]);

    // ── Zero line ──
    g.append("line")
      .attr("x1", 0).attr("x2", width)
      .attr("y1", y(0)).attr("y2", y(0))
      .attr("stroke", "#d1d5db").attr("stroke-width", 1).attr("stroke-dasharray", "4,3");

    // Shade loss region
    g.append("rect")
      .attr("x", 0).attr("y", y(0))
      .attr("width", width).attr("height", height - y(0))
      .attr("fill", "rgba(239, 68, 68, 0.04)");

    // ── Axes ──
    g.append("g")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(x).ticks(8));

    g.append("g")
      .call(d3.axisLeft(y).ticks(8).tickFormat(d => d.toFixed(0) + "%"));

    // Axis labels
    g.append("text")
      .attr("x", width / 2).attr("y", height + 40)
      .attr("text-anchor", "middle")
      .attr("fill", "#6b7280").attr("font-size", "13px")
      .text("Holding Period (days)");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -45).attr("x", -height / 2)
      .attr("text-anchor", "middle")
      .attr("fill", "#6b7280").attr("font-size", "13px")
      .text("Trade Return (%)");

    // ── Dots ──
    const dotsG = g.append("g");

    function updateDots() {
      const filtered = trades.filter(t => {
        if (activeReasons.size > 0 && !activeReasons.has(t.reason)) return false;
        return true;
      });

      const dots = dotsG.selectAll("circle.trade-dot")
        .data(filtered, t => t.entry + t.ticker);

      dots.exit().transition().duration(200).attr("r", 0).remove();

      const enter = dots.enter().append("circle")
        .attr("class", "trade-dot")
        .attr("cx", t => x(t.days))
        .attr("cy", t => y(t.ret))
        .attr("r", 0)
        .attr("fill", t => EXIT_COLORS[t.reason] || "#999")
        .attr("fill-opacity", 0.65)
        .attr("stroke", t => t.flew ? "#fff" : "none")
        .attr("stroke-width", t => t.flew ? 2 : 0);

      enter.transition().duration(300).attr("r", t => t.flew ? 6 : 4.5);

      enter
        .on("mouseover", function (event, t) {
          d3.select(this).attr("r", 8).attr("fill-opacity", 1);
          tooltip.style("opacity", 1)
            .html(
              `<strong>${t.ticker}</strong><br>` +
              `Entry: ${t.entry} @ $${t.entryPrice.toFixed(2)}<br>` +
              `Exit: ${t.exit} @ $${t.exitPrice.toFixed(2)}<br>` +
              `Return: <span style="color:${t.ret >= 0 ? '#22c55e' : '#ef4444'}">${t.ret.toFixed(2)}%</span><br>` +
              `Hold: ${t.days} days<br>` +
              `Exit: ${EXIT_LABELS[t.reason] || t.reason}<br>` +
              (t.flew ? '<span style="color:#8b5cf6">Flew (sold half)</span>' : '')
            )
            .style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 10) + "px");
        })
        .on("mousemove", function (event) {
          tooltip.style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", function (event, t) {
          d3.select(this).attr("r", t.flew ? 6 : 4.5).attr("fill-opacity", 0.65);
          tooltip.style("opacity", 0);
        });

      // Merge update
      dots.transition().duration(300)
        .attr("cx", t => x(t.days))
        .attr("cy", t => y(t.ret))
        .attr("fill", t => EXIT_COLORS[t.reason] || "#999");
    }
    updateDots();

  }).catch(function (err) {
    container.innerHTML = '<p style="color:#E45756;text-align:center;">Error loading trade data.</p>';
    console.error("Viz4 error:", err);
  });
})();
