/* ================= NIFTY ================= */
function renderNifty(data) {
  document.getElementById("niftyPrice").innerText = data.price.toFixed(2);
  const ch = document.getElementById("niftyChange");
  ch.innerText = `${data.change > 0 ? "+" : ""}${data.change} (${data.percent}%)`;
  ch.style.color = data.change >= 0 ? "#16a34a" : "#dc2626";
  document.getElementById("niftyTime").innerText = "Updated: " + data.updated;
}
fetch("data/nifty.json?ts=" + Date.now()).then(r=>r.json()).then(renderNifty);

/* ================= STRUCTURAL BIAS ================= */
fetch("data/nifty_bias.json?ts=" + Date.now())
  .then(r=>r.json())
  .then(d=>{
    document.getElementById("bias4H").className = "sq " + (d.bias["4H"]==="BULLISH"?"green":"red");
    document.getElementById("bias1H").className = "sq " + (d.bias["1H"]==="BULLISH"?"green":"red");
    document.getElementById("bias15M").className = "sq " + (d.bias["15M"]==="BULLISH"?"green":"red");
    document.getElementById("biasPhase").innerText = d.phase;
  });

/* ================= GLOBAL METER ================= */
fetch("data/global_meter.json?ts=" + Date.now())
  .then(r=>r.json())
  .then(d=>{
    const mapSq = (v,id)=>{
      document.getElementById(id).className = "sq " + (v>0?"green":"red");
    };

    mapSq(d.indices.dow.change,"sqDow");
    mapSq(d.indices.dax.change,"sqDax");
    mapSq(d.indices.nikkei.change,"sqNikkei");
    mapSq(d.indices.hang.change,"sqHang");

    dowVal.innerText = `${d.indices.dow.change}%`;
    daxVal.innerText = `${d.indices.dax.change}%`;
    nikkeiVal.innerText = `${d.indices.nikkei.change}%`;
    hangVal.innerText = `${d.indices.hang.change}%`;

    const score=d.score;
    const fill=document.getElementById("meterFill");
    fill.style.width=`${score*10}%`;
    fill.className="meter-fill "+(score<5?"red":score>5?"green":"neutral");
  });
