/* =====================================================
   CONFIG
===================================================== */

const REFRESH_INTERVAL = 60 * 1000; // 60 sec

/* =====================================================
   NIFTY
===================================================== */

function renderNifty(data) {
  const priceEl = document.getElementById("niftyPrice");
  const changeEl = document.getElementById("niftyChange");
  const timeEl = document.getElementById("niftyTime");
  const badge = document.getElementById("dataStatus");

  if (!priceEl || !changeEl || !timeEl) return;

  priceEl.innerText = data.price.toFixed(2);

  const sign = data.change >= 0 ? "+" : "";
  changeEl.innerText = `${sign}${data.change} (${data.percent}%)`;
  changeEl.style.color = data.change >= 0 ? "#16a34a" : "#dc2626";

  timeEl.innerText = "Updated: " + data.updated;

  // ---- stale data logic ----
  const updatedTime = new Date(data.updated.replace(" IST", ""));
  const now = new Date();
  const ageMin = (now - updatedTime) / 60000;

  if (badge) {
    badge.classList.remove("hidden", "stale-ok", "stale-warn", "stale-bad");

    if (ageMin <= 2) {
      badge.classList.add("stale-ok");
      badge.innerText = "Live";
    } else if (ageMin <= 5) {
      badge.classList.add("stale-warn");
      badge.innerText = "Delayed";
    } else {
      badge.classList.add("stale-bad");
      badge.innerText = "Stale";
    }
  }
}

function fetchNifty() {
  fetch("data/nifty.json?ts=" + Date.now())
    .then(r => r.json())
    .then(renderNifty)
    .catch(() => {});
}

/* =====================================================
   STRUCTURAL BIAS
===================================================== */

function renderBias(d) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "sq " + (val === "BULLISH" ? "green" : "red");
  };

  set("bias4H", d.bias["4H"]);
  set("bias1H", d.bias["1H"]);
  set("bias15M", d.bias["15M"]);

  const phase = document.getElementById("biasPhase");
  if (phase) phase.innerText = d.phase;
}

function fetchBias() {
  fetch("data/nifty_bias.json?ts=" + Date.now())
    .then(r => r.json())
    .then(renderBias)
    .catch(() => {});
}

/* =====================================================
   GLOBAL METER
===================================================== */

function renderGlobalMeter(d) {
  const fill = document.getElementById("globalMeterFill");
  if (!fill) return;

  const pct = Math.round(d.meter * 10);
  fill.style.width = pct + "%";

  fill.className =
    "meter-fill " +
    (d.meter > 6 ? "green" : d.meter < 4 ? "red" : "neutral");

  document.getElementById("dowVal").innerText =
    d.indices.DowF.change_30m + "%";
  document.getElementById("daxVal").innerText =
    d.indices.DAX.change_30m + "%";
  document.getElementById("nikkeiVal").innerText =
    d.indices.Nikkei.change_30m + "%";
  document.getElementById("hangVal").innerText =
    d.indices.HSI.change_30m + "%";
}

function fetchGlobalMeter() {
  fetch("data/global_meter.json?ts=" + Date.now())
    .then(r => r.json())
    .then(renderGlobalMeter)
    .catch(() => {});
}

/* =====================================================
   NIFTY BREADTH
===================================================== */

function renderNiftyBreadth(d) {
  const fill = document.getElementById("niftyBreadthFill");
  if (!fill) return;

  const pct = Math.round(d.meter * 10);
  fill.style.width = pct + "%";

  fill.className =
    "meter-fill " +
    (d.meter > 6 ? "green" : d.meter < 4 ? "red" : "neutral");
}

function fetchNiftyBreadth() {
  fetch("data/nifty_breadth.json?ts=" + Date.now())
    .then(r => r.json())
    .then(renderNiftyBreadth)
    .catch(() => {});
}

/* =====================================================
   INITIAL LOAD
===================================================== */

fetchNifty();
fetchBias();
fetchGlobalMeter();
fetchNiftyBreadth();

/* =====================================================
   AUTO REFRESH
===================================================== */

setInterval(() => {
  fetchNifty();
  fetchBias();
  fetchGlobalMeter();
  fetchNiftyBreadth();
}, REFRESH_INTERVAL);
