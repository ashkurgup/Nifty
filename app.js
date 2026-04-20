/* =====================================================
   UTILITIES
===================================================== */
const nowSec = () => Math.floor(Date.now() / 1000);

function ago(ts) {
  if (!ts || isNaN(ts)) return "";
  const s = nowSec() - ts;
  if (s < 60) return `Updated ${s} sec ago`;
  if (s < 3600) return `Updated ${Math.floor(s/60)} min ago`;
  return `Updated ${Math.floor(s/3600)} hr ago`;
}

/* =====================================================
   MARKET SESSION (NSE)
===================================================== */
function isMarketOpenIST() {
  const now = new Date();
  const ist = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Kolkata" }));
  const h = ist.getHours(), m = ist.getMinutes();
  const day = ist.getDay();
  if (day === 0 || day === 6) return false;
  if (h < 9 || h > 15) return false;
  if (h === 9 && m < 15) return false;
  if (h === 15 && m > 30) return false;
  return true;
}

/* =====================================================
   NIFTY
===================================================== */
let lastNifty = null;

function renderNifty(d) {
  if (d.price && d.price !== 0) lastNifty = d;

  if (lastNifty) {
    niftyPrice.innerText = lastNifty.price.toFixed(2);
    const sign = lastNifty.change >= 0 ? "+" : "";
    niftyChange.innerText =
      `${sign}${lastNifty.change} (${lastNifty.percent}%)`;
    niftyChange.style.color =
      lastNifty.change >= 0 ? "#16a34a" : "#dc2626";
  }

  niftyUpdated.innerText = ago(d.updated_ts || d.ts);
  marketSphere.className =
    "sphere " + (isMarketOpenIST() ? "green" : "grey");
}

/* =====================================================
   STRUCTURAL BIAS
===================================================== */
function biasColor(v) {
  if (v === "BULLISH") return "green";
  if (v === "BEARISH") return "red";
  return "";
}

function renderBias(d) {
  ["4H","1H","15M"].forEach(tf => {
    document.getElementById("bias"+tf).className =
      "sq " + biasColor(d.bias?.[tf]);
  });
  biasMessage.innerText = d.message || "Unavailable";
}

/* =====================================================
   GLOBAL MARKET (FIXED)
===================================================== */
function marketStateGlobal(market) {
  const utc = new Date();
  const min = utc.getUTCHours() * 60 + utc.getUTCMinutes();
  const wd = utc.getUTCDay();
  if (wd === 0 || wd === 6) return "CLOSED";

  const sessions = {
    Dow: [810,1200],
    DAX: [420,930],
    Nikkei: [0,360],
    HSI: [90,480]
  };
  if (!sessions[market]) return "CLOSED";
  return (min >= sessions[market][0] && min <= sessions[market][1])
    ? "OPEN" : "CLOSED";
}

function renderGlobal(d) {
  const meter = d.meter;
  globalMeterFill.style.width = (meter * 10) + "%";
  globalMeterValue.innerText = meter;

  globalMeterFill.className =
    "meter-fill " +
    (meter > 6 ? "green" : meter < 4 ? "red" : "neutral");

  const rows = [];

  Object.entries(d.indices).forEach(([rawKey, obj]) => {
    const key = rawKey === "DowF" ? "Dow" : rawKey;
    const pct = obj.change_30m;

    const color =
      pct > 0 ? "#16a34a" :
      pct < 0 ? "#dc2626" :
      "#374151";

    const sq =
      marketStateGlobal(key) === "OPEN" ? "green" : "grey";

    rows.push(
      `<span>
        <span class="sq ${sq}"></span>
        ${key} <span style="color:${color}">${pct}%</span>
      </span>`
    );
  });

  globalMarkets.innerHTML = rows.join(" | ");
}

/* =====================================================
   NIFTY BREADTH (FIXED)
===================================================== */
function renderBreadth(d) {
  const meter = d.meter;
  breadthFill.style.width = (meter * 10) + "%";
  breadthMeterValue.innerText = meter;

  breadthFill.className =
    "meter-fill " +
    (meter > 6 ? "green" : meter < 4 ? "red" : "neutral");

  const rows = [];
  Object.entries(d.sectors).forEach(([sector, pct]) => {
    const color =
      pct > 0 ? "#16a34a" :
      pct < 0 ? "#dc2626" :
      "#374151";
    rows.push(`<span style="color:${color}">${sector}</span>`);
  });

  breadthSectors.innerHTML = rows.join(" | ");
}

/* =====================================================
   FETCH LOOP
===================================================== */
function fetchAll() {
  fetch("data/nifty.json").then(r=>r.json()).then(renderNifty);
  fetch("data/nifty_bias.json").then(r=>r.json()).then(renderBias);
  fetch("data/global_meter.json").then(r=>r.json()).then(renderGlobal);
  fetch("data/nifty_breadth.json").then(r=>r.json()).then(renderBreadth);
}

fetchAll();
setInterval(fetchAll, 60000);
``
