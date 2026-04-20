/* =====================================================
   UTILITIES
===================================================== */
const nowSec = () => Math.floor(Date.now() / 1000);

function ago(ts) {
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
  const day = ist.getDay(); // 0 Sun
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
  const priceEl = document.getElementById("niftyPrice");
  const changeEl = document.getElementById("niftyChange");
  const updEl = document.getElementById("niftyUpdated");
  const sphere = document.getElementById("marketSphere");

  if (d.price && d.price !== 0) lastNifty = d;

  if (lastNifty) {
    priceEl.innerText = lastNifty.price.toFixed(2);
    const sign = lastNifty.change >= 0 ? "+" : "";
    changeEl.innerText = `${sign}${lastNifty.change} (${lastNifty.percent}%)`;
    changeEl.style.color = lastNifty.change >= 0 ? "#16a34a" : "#dc2626";
  }

  updEl.innerText = ago(d.updated_ts);
  sphere.className = "sphere " + (isMarketOpenIST() ? "green" : "grey");
}

/* =====================================================
   STRUCTURAL BIAS
===================================================== */
function biasColor(val) {
  if (val === "BULLISH") return "green";
  if (val === "BEARISH") return "red";
  return "";
}

function biasMessage(b) {
  const a = b["4H"], c = b["1H"], d = b["15M"];
  if (!a && !c && !d) return "Unavailable";
  if (a && c && !d) return "Waiting for intraday structure";
  if (a === c && c === d && a)
    return a === "BULLISH" ? "Bullish continuation" : "Bearish continuation";
  if (a === c && a === "BULLISH" && d === "BEARISH")
    return "Pullback within bullish structure";
  if (a === c && a === "BEARISH" && d === "BULLISH")
    return "Pullback within bearish structure";
  if (a !== c) return "Structural conflict";
  return "Intraday bias forming";
}

function renderBias(d) {
  ["4H","1H","15M"].forEach(tf => {
    const el = document.getElementById("bias"+tf);
    el.className = "sq " + biasColor(d.bias?.[tf]);
  });
  document.getElementById("biasMessage").innerText =
    biasMessage(d.bias || {});
}

/* =====================================================
   GLOBAL METER (35 / 25 / 25 / 15)
===================================================== */
function renderGlobal(d) {
  const weights = { DowF:0.35, DAX:0.25, Nikkei:0.25, HSI:0.15 };
  let score = 0;

  for (const k in weights) {
    const pct = d.indices?.[k]?.change_30m ?? 0;
    score += (pct > 0 ? 1 : pct < 0 ? -1 : 0) * weights[k];
    document.getElementById(k === "DowF" ? "dowVal" : k.toLowerCase()+"Val").innerText = pct;
  }

  const meter = 5 + score * 5;
  const fill = document.getElementById("globalMeterFill");
  fill.style.width = Math.max(0,Math.min(10,meter))*10 + "%";
  fill.className = "meter-fill " + (meter>6?"green":meter<4?"red":"");
  document.getElementById("globalUpdated").innerText = ago(d.updated_ts);
}

/* =====================================================
   BREADTH
===================================================== */
function renderBreadth(d) {
  const fill = document.getElementById("breadthFill");
  fill.style.width = d.meter*10+"%";
  document.getElementById("breadthUpdated").innerText = ago(d.updated_ts);
}

/* =====================================================
   FETCH LOOP
===================================================== */
function fetchAll() {
  fetch("data/nifty.json?ts="+Date.now()).then(r=>r.json()).then(renderNifty);
  fetch("data/nifty_bias.json?ts="+Date.now()).then(r=>r.json()).then(renderBias);
  fetch("data/global_meter.json?ts="+Date.now()).then(r=>r.json()).then(renderGlobal);
  fetch("data/nifty_breadth.json?ts="+Date.now()).then(r=>r.json()).then(renderBreadth);
}

fetchAll();
setInterval(fetchAll, 60000);
