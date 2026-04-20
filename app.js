/* ================= NIFTY ================= */
fetch("data/nifty.json?ts=" + Date.now())
  .then(r => r.json())
  .then(data => {
    document.getElementById("niftyPrice").innerText = data.price.toFixed(2);

    const sign = data.change >= 0 ? "+" : "";
    document.getElementById("niftyChange").innerText =
      `${sign}${data.change} (${data.percent}%)`;

    document.getElementById("niftyChange").style.color =
      data.change >= 0 ? "#16a34a" : "#dc2626";

    document.getElementById("niftyTime").innerText =
      "Updated: " + data.updated;
  });


/* ================= STRUCTURAL BIAS ================= */
fetch("data/nifty_bias.json?ts=" + Date.now())
  .then(r => r.json())
  .then(d => {
    document.getElementById("bias4H").className =
      "sq " + (d.bias["4H"] === "BULLISH" ? "green" : "red");

    document.getElementById("bias1H").className =
      "sq " + (d.bias["1H"] === "BULLISH" ? "green" : "red");

    document.getElementById("bias15M").className =
      "sq " + (d.bias["15M"] === "BULLISH" ? "green" : "red");

    document.getElementById("biasPhase").innerText = d.phase;
  });


/* ================= GLOBAL METER ================= */
fetch("data/global_meter.json?ts=" + Date.now())
  .then(r => r.json())
  .then(d => {
    const pct = Math.round(d.meter * 10);
    const fill = document.getElementById("globalMeterFill");

    fill.style.width = pct + "%";
    fill.className =
      "meter-fill " +
      (d.meter > 6 ? "green" : d.meter < 4 ? "red" : "neutral");

    document.getElementById("dowVal").innerText = d.indices.DowF.change_30m + "%";
    document.getElementById("daxVal").innerText = d.indices.DAX.change_30m + "%";
    document.getElementById("nikkeiVal").innerText = d.indices.Nikkei.change_30m + "%";
    document.getElementById("hangVal").innerText = d.indices.HSI.change_30m + "%";
  });


/* ================= NIFTY BREADTH ================= */
fetch("data/nifty_breadth.json?ts=" + Date.now())
  .then(r => r.json())
  .then(d => {
    const pct = Math.round(d.meter * 10);
    const fill = document.getElementById("niftyBreadthFill");

    fill.style.width = pct + "%";
    fill.className =
      "meter-fill " +
      (d.meter > 6 ? "green" : d.meter < 4 ? "red" : "neutral");
  });
