function renderNifty(data) {

  // Status dot
  const statusDot = document.getElementById("niftyStatus");
  statusDot.className =
    "status-dot " +
    (data.market_status === "LIVE" ? "live" : "closed");

  // Price
  document.getElementById("niftyPrice").innerText =
    data.price.toFixed(2);

  // Change
  const changeEl = document.getElementById("niftyChange");
  const sign = data.change >= 0 ? "+" : "";
  changeEl.innerText =
    `${sign}${data.change} (${data.percent}%)`;

  changeEl.className =
    "nifty-change " + (data.change >= 0 ? "positive" : "negative");

  // Updated time
  document.getElementById("niftyTime").innerText =
    "Updated: " + data.updated;
}

function loadNifty() {
  fetch("data/nifty.json")
    .then(res => res.json())
    .then(renderNifty)
    .catch(err => console.error("NIFTY load failed", err));
}

loadNifty();
setInterval(loadNifty, 60000); // refresh every 60s

function renderBias(data) {
  const map = {
    "BULLISH": "bullish",
    "BEARISH": "bearish",
    "PULLBACK": "pullback"
  };

  document.getElementById("bias4H").className =
    "bias-dot " + map[data.bias["4H"]];

  document.getElementById("bias1H").className =
    "bias-dot " + map[data.bias["1H"]];

  document.getElementById("bias15M").className =
    "bias-dot " + map[data.bias["15M"]];

  document.getElementById("biasPhase").innerText =
    data.phase;

  document.getElementById("biasUpdated").innerText =
    "Updated: " + data.updated;
}

function loadBias() {
  fetch("data/nifty_bias.json?ts=" + Date.now())
    .then(r => r.json())
    .then(renderBias)
    .catch(e => console.error("Bias load failed", e));
}

loadBias();
setInterval(loadBias, 300000); // every 5 minutes
