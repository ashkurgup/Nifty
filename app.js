function renderNifty(data) {
  document.getElementById("niftyPrice").innerText =
    data.price.toFixed(2);

  const changeEl = document.getElementById("niftyChange");
  const sign = data.change >= 0 ? "+" : "";

  changeEl.innerText =
    `${sign}${data.change} (${data.percent}%)`;

  changeEl.className =
    "nifty-change " + (data.change >= 0 ? "positive" : "negative");

  const statusDot = document.getElementById("niftyStatus");
  statusDot.className =
    "status-dot " + (data.market_status === "LIVE" ? "live" : "closed");

  document.getElementById("niftyTime").innerText =
    "Updated: " + data.updated;
}

fetch("data/nifty.json")
  .then(res => res.json())
  .then(renderNifty)
  .catch(err => console.error("NIFTY load failed", err));
