/* --- UTILITIES --- */
// Directional color reflects what last happened [cite: 56, 223]
const colorDir = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#9ca3af"; 

/* --- RENDER FUNCTIONS --- */
function renderNifty(d) {
    if (!d) return; 
    const statusEl = document.getElementById("marketStatus");
    statusEl.innerText = d.market === "OPEN" ? "● OPEN" : "○ CLOSED";
    statusEl.style.color = d.market === "OPEN" ? "#16a34a" : "#9ca3af";
    
    document.getElementById("niftyPrice").innerText = d.price.toFixed(2);
    const chg = document.getElementById("niftyChange");
    chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
    chg.style.color = colorDir(d.change);
}

function renderBreadth(d) {
    if (!d) return; 
    const fill = document.getElementById("breadthFill");
    fill.style.width = (d.meter * 10) + "%"; // 0-10 scale [cite: 34]
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);

    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors).map(([s, p]) => `
        <span style="font-weight: 800; font-size: 12px;">
            ${s} <span style="color:${colorDir(p)}; margin-left: 2px;">${p > 0 ? '+' : ''}${p}%</span>
        </span>`).join('<span style="color:#f1f5f9; margin: 0 6px;">|</span>');
}

function renderGlobal(d) {
    if (!d) return; 
    const fill = document.getElementById("globalMeterFill");
    fill.style.width = (d.meter * 10) + "%"; 
    document.getElementById("globalMeterValue").innerText = Math.round(d.meter);

    document.getElementById("globalMarkets").innerHTML = Object.entries(d.indices).map(([k, v]) => `
        <span style="display: flex; align-items: center; font-weight: 800; font-size: 11px;">
            <span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}" style="width:7px; height:7px; margin-right:4px;"></span>
            ${k} <span style="color:${colorDir(v.change_30m)}; margin-left: 3px;">${v.change_30m}%</span>
        </span>`).join('<span style="color:#f1f5f9; margin: 0 6px;">|</span>');
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
const run = () => {
    load("nifty", renderNifty);
    load("global_meter", renderGlobal);
    load("nifty_breadth", renderBreadth);
    load("nifty_bias", renderBias);
};

setInterval(run, 60000); 
run();
