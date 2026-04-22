const colorDir = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#94a3b8";

// ---------------- STATE ---------------- //
const tradeState = {
    1: { active: false, startTime: null, interval: null },
    2: { active: false, startTime: null, interval: null }
};

// ---------------- RENDERERS (HAZE REMOVED) ---------------- //
function renderNifty(d) {
    if (!d) return;
    // applyStaleEffect removed to fix haziness
    const statusEl = document.getElementById("marketStatus");
    statusEl.innerText = d.market === "OPEN" ? "● LIVE" : "○ CLOSED";
    statusEl.style.color = d.market === "OPEN" ? "#16a34a" : "#94a3b8";

    document.getElementById("niftyPrice").innerText = d.price?.toLocaleString('en-IN') || "--";
    const chg = document.getElementById("niftyChange");
    if(d.change) {
        chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
        chg.style.color = colorDir(d.change);
    }
    document.getElementById("niftyHigh").innerText = d.high?.toFixed(2) || "--";
    document.getElementById("niftyLow").innerText = d.low?.toFixed(2) || "--";
    if (d.updated_ts) {
        const timeStr = new Date(d.updated_ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        document.getElementById("niftyUpdated").innerText = `Last Updated: ${timeStr}`;
    }
}

// ... Keep your renderGlobal and renderBreadth as they were ...

// ---------------- DUAL TIMER & SELECTIVE SELL ---------------- //
function formatTime(ms) {
    let s = Math.floor(ms / 1000);
    return new Date(s * 1000).toISOString().substr(11, 8);
}

function startTrade(id) {
    const t = tradeState[id];
    t.active = true;
    t.startTime = Date.now();
    const note = document.getElementById(`note${id}`);
    note.innerText = "Position Active";
    note.style.color = "#16a34a";
    t.interval = setInterval(() => {
        document.getElementById(`timer${id}`).innerText = formatTime(Date.now() - t.startTime);
    }, 1000);
}

function stopTrade(id) {
    const t = tradeState[id];
    clearInterval(t.interval);
    t.active = false;
    const note = document.getElementById(`note${id}`);
    note.innerText = "Trade Closed";
    note.style.color = "#94a3b8";
}

function handleBuy() {
    if (!tradeState[1].active) startTrade(1);
    else if (!tradeState[2].active) startTrade(2);
}

function handleSell() {
    const t1 = tradeState[1].active;
    const t2 = tradeState[2].active;

    if (t1 && t2) {
        const choice = prompt("Select trade to close: 1 or 2?");
        if (choice === "1") stopTrade(1);
        else if (choice === "2") stopTrade(2);
    } else if (t2) {
        stopTrade(2);
    } else if (t1) {
        stopTrade(1);
    }
}

// ---------------- LOADERS ---------------- //
const run = async () => {
    // Standard fetch logic for your data/ files...
    // fetch('data/nifty.json').then(r => r.json()).then(renderNifty);
};
setInterval(run, 60000);
run();
