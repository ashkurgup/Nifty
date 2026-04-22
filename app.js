const colorDir = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#94a3b8"; 

function renderNifty(d) {
    if (!d) return; 
    document.getElementById("marketStatus").innerText = d.market === "OPEN" ? "● LIVE" : "○ CLOSED";
    document.getElementById("marketStatus").style.color = d.market === "OPEN" ? "#16a34a" : "#94a3b8";
    document.getElementById("niftyPrice").innerText = d.price.toLocaleString('en-IN', {minimumFractionDigits: 2});
    const chg = document.getElementById("niftyChange");
    chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
    chg.style.color = colorDir(d.change);
    document.getElementById("niftyHigh").innerText = d.high.toFixed(2);
    document.getElementById("niftyLow").innerText = d.low.toFixed(2);
    if (d.updated_ts) {
        const timeStr = new Date(d.updated_ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        document.getElementById("niftyUpdated").innerText = `Last Updated: ${timeStr}`;
    }
}

function renderBreadth(d) {
    if (!d) return; 
    const fill = document.getElementById("breadthFill");
    fill.style.width = (d.meter * 10) + "%";
    fill.style.backgroundColor = d.meter >= 7 ? "#16a34a" : d.meter <= 4 ? "#dc2626" : "#94a3b8";
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);
    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors).map(([s, p]) => `
        <span style="font-weight: 800; font-size: 11px;">
            ${s} <span style="color:${colorDir(p)};">${p > 0 ? '+' : ''}${p}%</span>
        </span>`).join('');
}

function renderGlobal(d) {
    if (!d) return; 
    const fill = document.getElementById("globalMeterFill");
    fill.style.width = (d.meter * 10) + "%";
    fill.style.backgroundColor = d.meter >= 7.5 ? "#16a34a" : d.meter <= 2.5 ? "#dc2626" : "#94a3b8";
    document.getElementById("globalMeterValue").innerText = Math.round(d.meter);
    document.getElementById("globalMarkets").innerHTML = Object.entries(d.indices).map(([k, v]) => `
        <span style="display: flex; align-items: center; font-weight: 800; font-size: 11px;">
            <span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}" style="width:6px; height:6px;"></span>
            ${k} <span style="color:${colorDir(v.change_30m)};">${v.change_30m}%</span>
        </span>`).join('');
}

function renderBias(d) {
    if (!d) return;
    const map = { BULLISH: "green", BEARISH: "red" };
    document.getElementById("bias4H").className = `sq ${map[d.bias["4H"]] || "grey"}`;
    document.getElementById("bias1H").className = `sq ${map[d.bias["1H"]] || "grey"}`;
    document.getElementById("bias15M").className = `sq ${map[d.bias["15M"]] || "grey"}`;
    document.getElementById("biasMessage").innerText = d.message; 
}

const load = (p, fn) => fetch(`data/${p}.json?t=${Date.now()}`).then(r => r.json()).then(fn).catch(() => {});
const run = () => {
    load("nifty", renderNifty);
    load("global_meter", renderGlobal);
    load("nifty_breadth", renderBreadth);
    load("nifty_bias", renderBias);
};

setInterval(run, 60000); 
run();
