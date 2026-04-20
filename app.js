let lastPrice = null;
let refreshTimer = null;

function pulse(el) {
  el.classList.remove("pulse");
  void el.offsetWidth;
  el.classList.add("pulse");
}

function ageSeconds(ts) {
  return Math.floor(Date.now()/1000 - ts);
}

function adaptiveRefresh(age) {
  if (refreshTimer) clearTimeout(refreshTimer);

  let next = 60000;
  if (age > 180) next = 10000;
  else if (age > 60) next = 30000;

  refreshTimer = setTimeout(fetchAll, next);
}

function renderNifty(d) {
  const price = document.getElementById("niftyPrice");
  const change = document.getElementById("niftyChange");
  const time = document.getElementById("niftyTime");
  const badge = document.getElementById("dataStatus");

  price.innerText = d.price.toFixed(2);
  change.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
  change.style.color = d.change >= 0 ? "green" : "red";

  const age = ageSeconds(d.updated_ts);
  time.innerText = `Updated: ${d.updated}`;
  time.title = `Exact age: ${age} seconds`;

  badge.className = "status " + (age < 60 ? "live" : age < 180 ? "delayed" : "stale");
  badge.innerText = badge.classList.contains("live") ? "LIVE" : "STALE";

  if (lastPrice !== null && lastPrice !== d.price) pulse(price);
  lastPrice = d.price;

  adaptiveRefresh(age);
}

function renderBias(d) {
  ["4H","1H","15M"].forEach(t => {
    const el = document.getElementById("bias"+t.replace("M","M"));
    el.className = "sq " + (d.bias[t] === "BULLISH" ? "green" : "red");
  });
  document.getElementById("biasPhase").innerText = d.phase;
}

function renderGlobal(d) {
  const fill = document.getElementById("globalMeterFill");
  fill.style.width = (d.meter * 10) + "%";
  fill.className = "meter-fill " + (d.meter > 6 ? "green" : d.meter < 4 ? "red" : "neutral");

  pulse(fill);

  dowVal.innerText = d.indices.DowF.change_30m;
  daxVal.innerText = d.indices.DAX.change_30m;
  nikkeiVal.innerText = d.indices.Nikkei.change_30m;
  hangVal.innerText = d.indices.HSI.change_30m;
}

function renderBreadth(d) {
  const fill = document.getElementById("niftyBreadthFill");
  fill.style.width = (d.meter * 10) + "%";
  fill.className = "meter-fill neutral";
  pulse(fill);
}

function fetchAll() {
  fetch("data/nifty.json").then(r=>r.json()).then(renderNifty);
  fetch("data/nifty_bias.json").then(r=>r.json()).then(renderBias);
  fetch("data/global_meter.json").then(r=>r.json()).then(renderGlobal);
  fetch("data/nifty_breadth.json").then(r=>r.json()).then(renderBreadth);
}

fetchAll();
