const colorFor = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#374151";

/* Locked Scale Logic: 7+ Green, 4- Red  */
function meterContextClass(v) {
  if (v >= 7) return "green"; 
  if (v <= 4) return "red";
  return ""; 
}

// -------- NIFTY --------
function renderNifty(d) {
  if (!d) return;
  document.getElementById("niftyPrice").innerText = d.price.toFixed(2);
  const changeEl = document.getElementById("niftyChange");
  changeEl.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
  changeEl.style.color = colorFor(d.change);
  
  document.getElementById("marketSphere").className = `sphere ${d.market === "LIVE" ? "green" : "grey"}`;
  
  if (d.updated_ts) {
    const mins = Math.floor((Date.now() / 1000 - d.updated_ts) / 60);
    document.getElementById("niftyUpdated").innerText = `Updated ${mins} min ago`;
  }
}

// -------- GLOBAL --------
function renderGlobal(d) {
  if (!d) return;
  const fill = document.getElementById("globalMeterFill");
  fill.style.width = (d.meter * 10) + "%";
  fill.className = "meter-fill " + meterContextClass(d.meter);
  document.getElementById("globalMeterValue").innerText = Math.round(d.meter);

  const html = Object.entries(d.indices).map(([key, v]) => `
    <span class="market-item">
      <span class="sq grey"></span>
      <span class="market-name">${key === "DowF" ? "Dow" : key}</span>
      <span style="color:${colorFor(v.change_30m)}">${v.change_30m >= 0 ? "+" : ""}${v.change_30m}%</span>
    </span>`).join(" | ");
  document.getElementById("globalMarkets").innerHTML = html;
}

// -------- BREADTH --------
function renderBreadth(d) {
  if (!d) return;
  const fill = document.getElementById("breadthFill");
  fill.style.width = (d.meter * 10) + "%";
  fill.className = "meter-fill " + meterContextClass(d.meter);
  document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);

  const html = Object.entries(d.sectors).map(([s, pct]) => `
    <span class="sector-item">
      <span>${s}</span>
      <span style="color:${colorFor(pct)}">${pct >= 0 ? "+" : ""}${pct}%</span>
    </span>`).join(" | ");
  document.getElementById("breadthSectors").innerHTML = html;
}

// -------- BIAS --------
function renderBias(d) {
  if (!d) return;
  const map = { BULLISH: "green", BEARISH: "red" };
  document.getElementById("bias4H").className = `sq ${map[d.bias["4H"]] || ""}`;
  document.getElementById("bias1H").className = `sq ${map[d.bias["1H"]] || ""}`;
  document.getElementById("bias15M").className = `sq ${map[d.bias["15M"]] || ""}`;
  document.getElementById("biasMessage").innerText = d.message;
}

// Fetch all data
const f = (path, fn) => fetch(`data/${path}.json?t=${Date.now()}`).then(r => r.json()).then(fn).catch(e => console.log(path, e));
f("nifty", renderNifty);
f("global_meter", renderGlobal);
f("nifty_breadth", renderBreadth);
f("nifty_bias", renderBias);
