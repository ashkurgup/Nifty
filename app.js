const colorDir = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#94a3b8";
const tradeState = {
    1: { active: false, startTime: null, interval: null },
    2: { active: false, startTime: null, interval: null }
};

// ---------------- RENDERERS ---------------- //
function renderNifty(d) {
    if (!d) return;
    document.getElementById("marketStatus").innerText = d.market === "OPEN" ? "● LIVE" : "○ CLOSED";
    document.getElementById("marketStatus").style.color = d.market === "OPEN" ? "#16a34a" : "#94a3b8";
    document.getElementById("niftyPrice").innerText = d.price?.toLocaleString('en-IN') || "--";
    const chg = document.getElementById("niftyChange");
    if (d.change) {
        chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
        chg.style.color = colorDir(d.change);
    }
}

function renderBreadth(d) {
    if (!d) return;
    document.getElementById("breadthMeterValue").innerText = Math.round(d.meter || 5);
    const fill = document.getElementById("breadthFill");
    fill.style.width = (d.meter * 10) + "%";
    fill.style.backgroundColor = d.meter >= 7 ? "#16a34a" : d.meter <= 4 ? "#dc2626" : "#94a3b8";
    document.getElementById("breadthSectors").innerHTML = Object.entries(d.sectors || {}).map(([s, p]) => `
        <span style="font-weight: 800; font-size: 11px;">${s} <span style="color:${colorDir(p)};">${p > 0 ? '+' : ''}${p}%</span></span>
    `).join('');
}

function renderGlobal(d) {
    if (!d) return;
    document.getElementById("globalMeterValue").innerText = Math.round(d.meter || 5);
    const fill = document.getElementById("globalMeterFill");
    fill.style.width = (d.meter * 10) + "%";
    document.getElementById("globalMarkets").innerHTML = Object.entries(d.indices || {}).map(([k, v]) => `
        <span style="font-weight:800; font-size:11px;"><span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}"></span> ${k} <span style="color:${colorDir(v.change_30m)};">${v.change_30m}%</span></span>
    `).join('');
}

// ---------------- TIMER LOGIC ---------------- //
function formatTime(ms) {
    let s = Math.floor(ms / 1000);
    return new Date(s * 1000).toISOString().substr(11, 8);
}

function startTrade(id) {
    tradeState[id].active = true;
    tradeState[id].startTime = Date.now();
    document.getElementById(`note${id}`).innerText = "ACTIVE";
    document.getElementById(`note${id}`).style.color = "#16a34a";
    tradeState[id].interval = setInterval(() => {
        document.getElementById(`timer${id}`).innerText = formatTime(Date.now() - tradeState[id].startTime);
    }, 1000);
}

function stopTrade(id) {
    clearInterval(tradeState[id].interval);
    tradeState[id].active = false;
    document.getElementById(`note${id}`).innerText = "CLOSED";
    document.getElementById(`note${id}`).style.color = "#94a3b8";
}

function handleBuy() {
    if (!tradeState[1].active) startTrade(1);
    else if (!tradeState[2].active) startTrade(2);
}

function handleSell() {
    const t1 = tradeState[1].active;
    const t2 = tradeState[2].active;
    if (t1 && t2) {
        const choice = prompt("Close Trade 1 or 2?");
        if (choice === "1") stopTrade(1);
        else if (choice === "2") stopTrade(2);
    } else if (t2) stopTrade(2);
    else if (t1) stopTrade(1);
}

// ---------------- LOADER ---------------- //
const run = () => {
    fetch('data/nifty.json').then(r => r.json()).then(renderNifty).catch(() => {});
    fetch('data/global_meter.json').then(r => r.json()).then(renderGlobal).catch(() => {});
    fetch('data/nifty_breadth.json').then(r => r.json()).then(renderBreadth).catch(() => {});
};

setInterval(run, 60000);
run();
