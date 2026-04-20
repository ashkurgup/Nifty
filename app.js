function renderNifty(data) {
  // Market status text (TOP)
  const statusText = document.getElementById("niftyStatusText");
  statusText.innerText = data.market_status;
  statusText.className =
    "market-status " +
    (data.market_status === "LIVE" ? "live" : "closed");

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
``
