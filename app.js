function colorFor(v) {
  return v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#374151";
}

function isDowFuturesOpen() {
  const d = new Date().getUTCDay();
  return d !== 0; // Dow futures open Sun–Fri
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

  niftyUpdated.innerText = "Updated " + Math.floor((Date.now()/1000 - d.updated_ts)/60) + " min ago";
  marketSphere.className = "sphere " + (d.market === "LIVE" ? "green" : "grey");
}

// -------- GLOBAL --------
function renderGlobal(d) {
  globalMeterFill.style.width = (d.meter * 10) + "%";
  globalMeterFill.className = "meter-fill " + (d.meter > 6 ? "green" : d.meter < 4 ? "red" : "");
  globalMeterValue.innerText = d.meter;

  const rows = [];
  Object.entries(d.indices).forEach(([key, v]) => {
    const label = key === "DowF" ? "Dow" : key;
    const open = key === "DowF" ? isDowFuturesOpen() : false;

    rows.push(
      `<span>
        <span class="sq ${open ? "green":"grey"}"></span>
        ${label} <span style="color:${colorFor(v.change_30m)}">${v.change_30m}%</span>
      </span>`
    );
  });
  globalMarkets.innerHTML = rows.join(" | ");
}

// -------- BREADTH --------
function renderBreadth(d) {
  breadthFill.style.width = (d.meter * 10) + "%";
  breadthFill.className = "meter-fill " + (d.meter > 6 ? "green" : d.meter < 4 ? "red" : "");
  breadthMeterValue.innerText = d.meter;

  const rows = [];
  Object.entries(d.sectors).forEach(([sector, pct]) => {
    rows.push(
      `<span>
        ${sector} <span style="color:${colorFor(pct)}">${pct >= 0 ? "+" : ""}${pct}%</span>
      </span>`
    );
  });

  breadthSectors.innerHTML = rows.join(" | ");
}

// -------- BIAS --------
function renderBias(d) {
  ["4H","1H","15M"].forEach(tf => {
    bias4H.className = "sq green";
  });
  biasMessage.innerText = d.message;
}

// -------- FETCH --------
fetch("data/nifty.json").then(r=>r.json()).then(renderNifty);
fetch("data/global_meter.json").then(r=>r.json()).then(renderGlobal);
fetch("data/nifty_breadth.json").then(r=>r.json()).then(renderBreadth);
fetch("data/nifty_bias.json").then(r=>r.json()).then(renderBias);
