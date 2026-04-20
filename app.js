/* =====================================================
   UTILITIES
===================================================== */
function nowSec() {
  return Math.floor(Date.now() / 1000);
}

function ago(ts) {
  if (!ts || isNaN(ts)) return "";
  const s = nowSec() - ts;
  if (s < 60) return `Updated ${s} sec ago`;
  if (s < 3600) return `Updated ${Math.floor(s/60)} min ago`;
  return `Updated ${Math.floor(s/3600)} hr ago`;
}

/* =====================================================
   NIFTY
===================================================== */
let lastNifty = null;

function isMarketOpenIST() {
  const now = new Date();
  const ist = new Date(now.toLocaleString("en-US",{timeZone:"Asia/Kolkata"}));
  const h = ist.getHours(), m = ist.getMinutes(), d = ist.getDay();
  if (d === 0 || d === 6) return false;
  if (h < 9 || h > 15) return false;
  if (h === 9 && m < 15) return false;
  if (h === 15 && m > 30) return false;
  return true;
}

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
   GLOBAL MARKET (FIXED: Dow Futures LIVE ✅)
===================================================== */
function marketStateGlobal(name) {
  const wd = new Date().getUTCDay();

  // ✅ Dow Futures trade almost 24x5
  if (name === "Dow") return wd !== 0 ? "OPEN" : "CLOSED";

  const utc = new Date();
  const min = utc.getUTCHours()*60 + utc.getUTCMinutes();

  const sessions = {
    DAX: [420,930],
    Nikkei: [0,360],
    HSI: [90,480]
  };

  if (!sessions[name] || wd === 0 || wd === 6) return "CLOSED";
  return (min >= sessions[name][0] && min <= sessions[name][1])
    ? "OPEN" : "CLOSED";
}

function renderGlobal(d) {
  const meter = d.meter;

  globalMeterValue.innerText = meter;
  globalMeterFill.style.width = (meter * 10) + "%";
  globalMeterFill.className =
    "meter-fill " + (meter > 6 ? "green" : meter < 4 ? "red" : "neutral");

  const rows = [];

  Object.entries(d.indices || {}).forEach(([key,obj]) => {
    const name = key === "DowF" ? "Dow" : key;
    const pct = obj.change_30m ?? 0;

    const color =
      pct > 0 ? "#16a34a" : pct < 0 ? "#dc2626" : "#374151";

    const sq =
      marketStateGlobal(name) === "OPEN" ? "green" : "grey";

    rows.push(
      `<span>
        <span class="sq ${sq}"></span>
        ${name} <span style="color:${color}">${pct}%</span>
      </span>`
    );
  });

  globalMarkets.innerHTML = rows.join(" | ");
}

/* =====================================================
   NIFTY BREADTH (FIXED: BANK | FIN … ✅)
===================================================== */
function renderBreadth(d) {
  const meter = d.meter;
  breadthMeterValue.innerText = meter;
  breadthFill.style.width = (meter * 10) + "%";
  breadthFill.className =
    "meter-fill " + (meter > 6 ? "green" : meter < 4 ? "red" : "neutral");

  const rows = [];

  // ✅ support BOTH formats
  if (Array.isArray(d.sectors)) {
    d.sectors.forEach(s => rows.push(s));
  } else {
    Object.entries(d.sectors || {}).forEach(([s,pct]) => {
      const color =
        pct > 0 ? "#16a34a" : pct < 0 ? "#dc2626" : "#374151";
      rows.push(`<span style="color:${color}">${s}</span>`);
    });
  }

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
