function isMarketLive() {
  const now = new Date();
  const day = now.getDay(); // 0 = Sunday
  const hour = now.getHours();
  const minute = now.getMinutes();

  const isWeekday = day >= 1 && day <= 5;
  const isMarketTime =
    (hour > 9 || (hour === 9 && minute >= 0)) &&
    (hour < 15 || (hour === 15 && minute <= 30));

  return isWeekday && isMarketTime;
}

function renderNifty(data) {
  const live = isMarketLive();
  const statusDot = document.getElementById("niftyStatus");

  statusDot.className = "status-dot " + (live ? "live" : "closed");

  document.getElementById("niftyPrice").innerText =
    Number(data.price).toFixed(2);

  const changeEl = document.getElementById("niftyChange");
  const sign = data.change >= 0 ? "+" : "";
  changeEl.innerText =
    sign + data.change + " (" + data.percent + "%)";

  changeEl.className =
    "nifty-change " + (data.change >= 0 ? "positive" : "negative");

  document.getElementById("niftyTime").innerText =
    "Updated: " + data.updated;
}

function loadNifty() {
  fetch("data/nifty.json")
    .then(res => res.json())
    .then(renderNifty)
    .catch(console.error);
}

loadNifty();
setInterval(loadNifty, 300000); // 5 min
