function colorFor(v) {
  return v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#374151";
}

/* ✅ NORMALIZED CONTEXT COLOR (ENVIRONMENT, NOT DIRECTION) */
function meterContextClass(v) {
  if (v >= 6.5) return "green";   // supportive context
  if (v < 4) return "red";        // fragile context
  return "";                      // neutral / mixed (grey)
}

function isDowFuturesOpen() {
  const d = new Date().getUTCDay();
  return d !== 0;
}

// -------- NIFTY --------
let lastNifty = null;

function renderNifty(d) {
  if (d.price && d.price !== 0) lastNifty = d;

  if (lastNifty) {
    niftyPrice.innerText = lastNifty.price.toFixed(2);
    niftyChange.innerText =
      `${lastNifty.change >= 0 ? "+" : ""}${lastNifty.change} (${lastNifty.percent}%)`;
    niftyChange.style.color = colorFor(lastNifty.change);
  }

  const ts = d.updated_ts || d.ts;
  if (ts) {
    const mins = Math.floor((Date.now() / 1000 - ts) / 60);
    niftyUpdated.innerText = `Updated ${mins} min ago`;
  } else {
    niftyUpdated.innerText = "";
  }

  marketSphere.className =
    "sphere " + (d.market === "LIVE" ? "green" : "grey");
}

// -------- GLOBAL --------
function renderGlobal(d) {
  globalMeterFill.style.width = (d.meter * 10) + "%";
  globalMeterFill.className =
    "meter-fill " + meterContextClass(d.meter);
  globalMeterValue.innerText = d.meter;

  const rows = [];

  Object.entries(d.indices).forEach(([key, v]) => {
    const label = key === "DowF" ? "Dow" : key;
    const open = key === "DowF" ? isDowFuturesOpen() : false;
    const color = colorFor(v.change_30m);

    rows.push(`
      <span class="market-item">
        <span class="sq ${open ? "green" : "grey"}"></span>
        <span class="market-name">${label}</span>
        <span class="market-pct" style="color:${color}">
          ${v.change_30m >= 0 ? "+" : ""}${v.change_30m}%
        </span>
      </span>
    `);
  });

  globalMarkets.innerHTML = rows.join(" | ");
}

// -------- BREADTH --------
function renderBreadth(d) {
  breadthFill.style.width = (d.meter * 10) + "%";
  breadthFill.className =
    "meter-fill " + meterContextClass(d.meter);
  breadthMeterValue.innerText = d.meter;

  const rows = [];

  Object.entries(d.sectors).forEach(([sector, pct]) => {
    const color = colorFor(pct);

    rows.push(`
      <span class="sector-item">
        <span class="sector-name">${sector}</span>
        <span class="sector-pct" style="color:${color}">
          ${pct >= 0 ? "+" : ""}${pct}%
        </span>
      </span>
    `);
  });

  breadthSectors.innerHTML = rows.join(" | ");
}

// -------- BIAS --------
function renderBias(d) {
  const map = { BULLISH: "green", BEARISH: "red" };

  bias4H.className = `sq ${map[d.bias?.["4H"]] || ""}`;
  bias1H.className = `sq ${map[d.bias?.["1H"]] || ""}`;
  bias15M.className = `sq ${map[d.bias?.["15M"]] || ""}`;

  biasMessage.innerText = d.message || "";
}

// -------- FETCH --------
fetch("data/nifty.json").then(r => r.json()).then(renderNifty);
fetch("data/global_meter.json").then(r => r.json()).then(renderGlobal);
fetch("data/nifty_breadth.json").then(r => r.json()).then(renderBreadth);
fetch("data/nifty_bias.json").then(r => r.json()).then(renderBias);
``
