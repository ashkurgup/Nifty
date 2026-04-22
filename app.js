/* --- 1. UTILITY FORMULAS --- */
const colorFor = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#374151";
const meterCtx = (v) => v >= 7 ? "green" : v <= 4 ? "red" : ""; 

/* --- 2. RENDER NIFTY BOX --- */
function renderNifty(d) {
    if (!d) return;
    const isOpen = d.market === "LIVE";
    const statusEl = document.getElementById("marketStatus");
    if (statusEl) {
        statusEl.innerText = isOpen ? "● LIVE" : "○ CLOSED";
        statusEl.style.color = isOpen ? "#16a34a" : "#9ca3af";
    }
    document.getElementById("niftyPrice").innerText = d.price.toFixed(2);
    const chg = document.getElementById("niftyChange");
    chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
    chg.style.color = colorFor(d.change);
    if(d.high) document.getElementById("niftyHigh").innerText = d.high.toFixed(2);
    if(d.low) document.getElementById("niftyLow").innerText = d.low.toFixed(2);

    if (d.updated_ts) {
        const fetchTime = new Date(d.updated_ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const updatedEl = document.getElementById("niftyUpdated");
        if (updatedEl) {
            updatedEl.innerText = `Last Updated: ${fetchTime}`;
            updatedEl.style.fontStyle = "italic";   
            updatedEl.style.color = "#9ca3af";      
            updatedEl.style.fontWeight = "400";     
            updatedEl.style.fontSize = "10px";      
        }
    }
}

function renderGlobal(d) {
    if (!d) return;
    const fill = document.getElementById("globalMeterFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("globalMeterValue").innerText = Math.round(d.meter);

    document.getElementById("globalMarkets").innerHTML = Object.entries(d.indices).map(([k, v]) => `
        <span style="display: flex; align-items: center; font-weight: 800; font-size: 12px; white-space: nowrap;">
            <span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}" style="width:7px; height:7px; margin-right:4px; border-radius:50%;"></span> 
            ${k} <span style="color:${colorFor(v.change_30m)}; margin-left: 4px;">${v.change_30m >= 0 ? '+' : ''}${v.change_30m}%</span>
        </span>`).join('<span style="color:#f1f5f9; font-size:10px;">|</span>');
}

function renderBreadth(d) {
    if (!d) return;
    const fill = document.getElementById("breadthFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);

    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors).map(([s, p]) => `
        <span style="display: flex; align-items: center; font-weight: 800; font-size: 12px; white-space: nowrap;">
            ${s} <span style="color:${colorFor(p)}; margin-left: 4px;">${p >= 0 ? '+' : ''}${p}%</span>
        </span>`).join('<span style="color:#f1f5f9; font-size:10px;">|</span>');
}

/* --- 5. RENDER STRUCTURAL BIAS --- */
function renderBias(d) {
    if (!d) return;
    const map = { BULLISH: "green", BEARISH: "red" };
    document.getElementById("bias4H").className = `sq ${map[d.bias["4H"]] || ""}`;
    document.getElementById("bias1H").className = `sq ${map[d.bias["1H"]] || ""}`;
    document.getElementById("bias15M").className = `sq ${map[d.bias["15M"]] || ""}`;
    document.getElementById("biasMessage").innerText = d.message;
}

/* --- 6. RENDER STRATEGY BOX --- */
function renderStrategy(d) {
    if (!d) return;
    const stratBox = document.querySelector(".box-side:nth-child(4)"); 
    if(!stratBox) return;
    stratBox.innerHTML = `
        <div class="side-title">STRATEGY</div>
        <div class="side-val">Active</div>
        <div class="sr-levels" style="font-weight:800; font-size:12px; margin: 5px 0;">
            S: <span style="color:#16a34a">${d.sup}</span> | R: <span style="color:#dc2626">${d.res}</span>
        </div>
        <div class="small">SMC Protocol</div>
    `;
}

const load = (p, fn) => fetch(`data/${p}.json?t=${Date.now()}`).then(r => r.json()).then(fn).catch(() => {});
load("nifty", renderNifty); 
load("global_meter", renderGlobal);
load("nifty_breadth", renderBreadth); 
load("nifty_bias", renderBias);
load("strategy", renderStrategy);
