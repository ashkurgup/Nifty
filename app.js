const colorFor = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#374151";
const meterCtx = (v) => v >= 7 ? "green" : v <= 4 ? "red" : ""; 

function renderNifty(d) {
   function renderNifty(d) {
    if (!d) return;

    // 1. UPDATE HEADER: Only "LIVE" or "CLOSED" with space
    const isOpen = d.market === "LIVE";
    const statusEl = document.getElementById("marketStatus");
    if (statusEl) {
        // Space added between NIFTY and bullet is handled in HTML/CSS spacing
        statusEl.innerText = isOpen ? "● LIVE" : "○ CLOSED";
        statusEl.style.color = isOpen ? "#16a34a" : "#9ca3af";
    }

    // 2. UPDATE FOOTER: Remove "Live", make text darker
    // Using a darker grey like #6b7280 instead of #cbd5e1
    const timeStr = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    const updatedEl = document.getElementById("niftyUpdated");
    updatedEl.innerText = timeStr;
    updatedEl.style.color = "#6b7280"; // Darker grey
    updatedEl.style.fontWeight = "700";

    // ... (keep price and high/low logic same)
}

    // 2. Update Price
    document.getElementById("niftyPrice").innerText = d.price.toFixed(2);

    // 3. Update Change and Day High/Low
    const chg = document.getElementById("niftyChange");
    chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
    chg.style.color = colorFor(d.change);

    // NEW: Populate High and Low (Assuming your JSON has 'high' and 'low' keys)
    if(d.high) document.getElementById("niftyHigh").innerText = d.high.toFixed(2);
    if(d.low) document.getElementById("niftyLow").innerText = d.low.toFixed(2);

    // 4. Update Timestamp
    document.getElementById("niftyUpdated").innerText = `Live • ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
}

function renderGlobal(d) {
    if (!d) return;
    const fill = document.getElementById("globalMeterFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("globalMeterValue").innerText = Math.round(d.meter);

    document.getElementById("globalMarkets").innerHTML = Object.entries(d.indices).map(([k, v]) => `
        <span style="display: flex; align-items: center; font-weight: 800; font-size: 13px; margin-right: 20px; white-space: nowrap;">
            <span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}" style="width:7px; height:7px; margin-right:6px;"></span> 
            ${k} 
            <span style="color:${colorFor(v.change_30m)}; margin-left: 5px;">
                ${v.change_30m >= 0 ? '+' : ''}${v.change_30m}%
            </span>
        </span>`).join('<span style="color:#e5e7eb; margin-right: 20px;">|</span>');
}

function renderBreadth(d) {
    if (!d) return;
    const fill = document.getElementById("breadthFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);

    // Using the same format as Global Markets for consistency
    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors).map(([s, p]) => `
        <span style="display: flex; align-items: center; font-weight: 800; font-size: 13px; margin-right: 20px; white-space: nowrap;">
            <span class="sq green" style="width:7px; height:7px; margin-right:6px;"></span> 
            ${s} 
            <span style="color:${colorFor(p)}; margin-left: 5px;">
                ${p >= 0 ? '+' : ''}${p}%
            </span>
        </span>`).join('<span style="color:#e5e7eb; margin-right: 20px;">|</span>');
}

function renderBreadth(d) {
    if (!d) return;
    const fill = document.getElementById("breadthFill");
    fill.className = `meter-fill ${meterCtx(d.meter)}`;
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);

    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors).map(([s, p]) => `
        <span style="white-space: nowrap;">
            ${s} <span style="color:${colorFor(p)}">${p >= 0 ? '+' : ''}${p}%</span>
        </span>`).join('<span style="color:#e5e7eb; margin: 0 4px;">|</span>');
}

function renderBias(d) {
    if (!d) return;
    const map = { BULLISH: "green", BEARISH: "red" };
    document.getElementById("bias4H").className = `sq ${map[d.bias["4H"]] || ""}`;
    document.getElementById("bias1H").className = `sq ${map[d.bias["1H"]] || ""}`;
    document.getElementById("bias15M").className = `sq ${map[d.bias["15M"]] || ""}`;
    document.getElementById("biasMessage").innerText = d.message;
}

function renderStrategy(d) {
    if (!d) return;
    const stratBox = document.querySelector(".box-side:nth-child(3)"); 
    stratBox.innerHTML = `
        <div class="side-title">STRATEGY</div>
        <div class="side-val">Active</div>
        <div class="sr-levels">S: <span class="pos">${d.sup}</span> | R: <span class="neg">${d.res}</span></div>
        <div class="small">SMC Protocol</div>
    `;
}

const load = (p, fn) => fetch(`data/${p}.json?t=${Date.now()}`).then(r => r.json()).then(fn).catch(() => {});
load("nifty", renderNifty); 
load("global_meter", renderGlobal);
load("nifty_breadth", renderBreadth); 
load("nifty_bias", renderBias);
load("strategy", renderStrategy);
