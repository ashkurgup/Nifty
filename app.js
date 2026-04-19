function renderNifty(data) {
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
  document.getElementById("niftyUpdated").innerText =
    "Updated: " + data.updated;
}

fetch("data/nifty.json")
  .then(res => res.json())
  .then(renderNifty)
  .catch(err => console.error("NIFTY data load failed", err));
