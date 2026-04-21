const colorFor = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#374151";
const meterCtx = (v) => v >= 7 ? "green" : v <= 4 ? "red" : ""; 

function renderGlobal(d) {
    if (!d) return;
    const fill = document.getElementById("globalMeterFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`; // Restored color
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("globalMeterValue").innerText = Math.round(d.meter);

    document.getElementById("globalMarkets").innerHTML = Object.entries(d.indices).map(([k, v]) => `
        <span class="item-wrap">
            <span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}"></span> 
            ${k} <span style="color:${colorFor(v.change_30m)}">&nbsp;${v.change_30m >= 0 ? '+' : ''}${v.change_30m}%</span>
        </span>`).join('<span class="gap">|</span>');
}

function renderBreadth(d) {
    if (!d) return;
    const fill = document.getElementById("breadthFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);

    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors).map(([s, p]) => `
        <span class="item-wrap">${s}<span style="color:${colorFor(p)}">&nbsp;${p >= 0 ? '+' : ''}${p}%</span></span>
    `).join('<span class="gap">|</span>');
}

function renderNifty(d) {
    if (!d) return;
    document.getElementById("niftyPrice").innerText = d.price.toFixed(2);
    const chg = document.getElementById("niftyChange");
    chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
    chg.style.color = colorFor(d.change);
    document.getElementById("marketSphere").className = `sphere grey`; // Market Closed
    document.getElementById("niftyUpdated").innerText = `Updated ${Math.floor((Date.now()/1000 - d.updated_ts)/60)} min ago`;
}

function renderBias(d) {
    if (!d) return;
    const map = { BULLISH: "green", BEARISH: "red" };
    document.getElementById("bias4H").className = `sq ${map[d.bias["4H"]] || ""}`;
    document.getElementById("bias1H").className = `sq ${map[d.bias["1H"]] || ""}`;
    document.getElementById("bias15M").className = `sq ${map[d.bias["15M"]] || ""}`;
    document.getElementById("biasMessage").innerText = d.message;
}

const load = (p, fn) => fetch(`data/${p}.json?t=${Date.now()}`).then(r => r.json()).then(fn).catch(() => {});
load("nifty", renderNifty); load("global_meter", renderGlobal);
load("nifty_breadth", renderBreadth); load("nifty_bias", renderBias);
