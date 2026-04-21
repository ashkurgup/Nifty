const colorFor = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#374151";
const meterCtx = (v) => v >= 7.5 ? "green" : v <= 2.5 ? "red" : ""; [cite: 191]

function renderNifty(d) {
    if (!d) return;
    document.getElementById("niftyPrice").innerText = d.price.toFixed(2); [cite: 268]
    const chg = document.getElementById("niftyChange");
    chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`; [cite: 269]
    chg.style.color = colorFor(d.change);
    document.getElementById("marketSphere").className = `sphere ${d.market === "LIVE" ? "green" : "grey"}`; [cite: 264, 265]
    document.getElementById("niftyUpdated").innerText = `Updated ${Math.floor((Date.now()/1000 - d.updated_ts)/60)} min ago`; [cite: 14, 259]
}

function renderGlobal(d) {
    if (!d) return;
    const fill = document.getElementById("globalMeterFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%"; [cite: 187, 188]
    document.getElementById("globalMeterValue").innerText = Math.round(d.meter); [cite: 238]
    
    document.getElementById("globalMarkets").innerHTML = Object.entries(d.indices).map(([k, v]) => `
        <span style="white-space:nowrap;">
            <span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}"></span> 
            ${k === 'DowF' ? 'Dow' : k} 
            <span style="color:${colorFor(v.change_30m)}">${v.change_30m >= 0 ? '+' : ''}${v.change_30m}%</span>
        </span>`).join(" | "); [cite: 213, 219, 234]
}

function renderBreadth(d) {
    if (!d) return;
    const fill = document.getElementById("breadthFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%"; [cite: 33, 34]
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);
    
    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors).map(([s, p]) => `
        <span>${s} <span style="color:${colorFor(p)}">${p >= 0 ? '+' : ''}${p}%</span></span>`).join(" | "); [cite: 45, 52]
}

function renderBias(d) {
    if (!d) return;
    const map = { BULLISH: "green", BEARISH: "red" }; [cite: 86]
    document.getElementById("bias4H").className = `sq ${map[d.bias["4H"]] || ""}`;
    document.getElementById("bias1H").className = `sq ${map[d.bias["1H"]] || ""}`;
    document.getElementById("bias15M").className = `sq ${map[d.bias["15M"]] || ""}`;
    document.getElementById("biasMessage").innerText = d.message; [cite: 90, 155]
}

const load = (p, fn) => fetch(`data/${p}.json?t=${Date.now()}`).then(r => r.json()).then(fn).catch(() => {});
load("nifty", renderNifty); load("global_meter", renderGlobal);
load("nifty_breadth", renderBreadth); load("nifty_bias", renderBias);
