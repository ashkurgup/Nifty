const colorDir = (v) => v > 0 ? "#16a34a" : v < 0 ? "#dc2626" : "#94a3b8";

// ---------------- CACHE ---------------- //

const cache = {
    nifty: null,
    global: null,
    breadth: null,
    bias: null
};

const isValid = (v) => v !== null && v !== undefined && !Number.isNaN(v);

// ---------------- STALE CHECK ---------------- //

const isStale = (ts) => {
    if (!ts) return false;
    const diff = (Date.now() / 1000) - ts;
    return diff > 600; // >10 minutes
};

const applyStaleEffect = (isStaleData) => {
    const container = document.getElementById("dashboardContainer");
    if (!container) return;

    container.style.opacity = isStaleData ? "0.6" : "1";
};

// ---------------- NIFTY ---------------- //

function renderNifty(d) {
    if (!d) return;

    applyStaleEffect(isStale(d.updated_ts));

    const statusEl = document.getElementById("marketStatus");
    statusEl.innerText = d.market === "OPEN" ? "● LIVE" : "○ CLOSED";
    statusEl.style.color = d.market === "OPEN" ? "#16a34a" : "#94a3b8";

    if (isValid(d.price))
        document.getElementById("niftyPrice").innerText = d.price.toLocaleString('en-IN');

    if (isValid(d.change) && isValid(d.percent)) {
        const chg = document.getElementById("niftyChange");
        chg.innerText = `${d.change >= 0 ? "+" : ""}${d.change} (${d.percent}%)`;
        chg.style.color = colorDir(d.change);
    }

    if (isValid(d.high))
        document.getElementById("niftyHigh").innerText = d.high.toFixed(2);

    if (isValid(d.low))
        document.getElementById("niftyLow").innerText = d.low.toFixed(2);

    if (d.updated_ts) {
        const timeStr = new Date(d.updated_ts * 1000)
            .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        document.getElementById("niftyUpdated").innerText = `Last Updated: ${timeStr}`;
    }
}

// ---------------- BREADTH ---------------- //

function renderBreadth(d) {
    if (!d) return;

    const fill = document.getElementById("breadthFill");

    if (isValid(d.meter)) {
        fill.style.width = (d.meter * 10) + "%";
        fill.style.backgroundColor =
            d.meter >= 7 ? "#16a34a" :
            d.meter <= 4 ? "#dc2626" : "#94a3b8";

        document.getElementById("breadthMeterValue").innerText = Math.round(d.meter);
    }

    if (d.sectors) {
        document.getElementById("breadthSectors").innerHTML =
            Object.entries(d.sectors).map(([s, p]) => `
                <span style="font-weight: 800; font-size: 11px;">
                    ${s} <span style="color:${colorDir(p)};">
                        ${p > 0 ? '+' : ''}${isValid(p) ? p : '--'}%
                    </span>
                </span>
            `).join('');
    }
}

// ---------------- GLOBAL ---------------- //

function renderGlobal(d) {
    if (!d) return;

    const fill = document.getElementById("globalMeterFill");

    if (isValid(d.meter)) {
        fill.style.width = (d.meter * 10) + "%";
        fill.style.backgroundColor =
            d.meter >= 7.5 ? "#16a34a" :
            d.meter <= 2.5 ? "#dc2626" : "#94a3b8";

        document.getElementById("globalMeterValue").innerText = Math.round(d.meter);
    }

    if (d.indices) {
        document.getElementById("globalMarkets").innerHTML =
            Object.entries(d.indices).map(([k, v]) => `
                <span style="display:flex;align-items:center;font-weight:800;font-size:11px;">
                    <span class="sq ${v.status === 'OPEN' ? 'green' : 'grey'}"
                          style="width:6px;height:6px;"></span>
                    ${k}
                    <span style="color:${colorDir(v.change_30m)}; margin-left:4px;">
                        ${isValid(v.change_30m) ? v.change_30m : '--'}%
                    </span>
                </span>
            `).join('');
    }
}

// ---------------- BIAS ---------------- //

function renderBias(d) {
    if (!d || !d.bias) return;

    const map = { BULLISH: "green", BEARISH: "red" };

    document.getElementById("bias4H").className =
        `sq ${map[d.bias["4H"]] || "grey"}`;

    document.getElementById("bias1H").className =
        `sq ${map[d.bias["1H"]] || "grey"}`;

    document.getElementById("bias15M").className =
        `sq ${map[d.bias["15M"]] || "grey"}`;

    if (d.message)
        document.getElementById("biasMessage").innerText = d.message;
}

// ---------------- SAFE LOADER ---------------- //

const load = async (key, path, renderer) => {
    try {
        const res = await fetch(`data/${path}.json?t=${Date.now()}`);
        const data = await res.json();

        if (data && Object.keys(data).length > 0) {
            cache[key] = data;
            renderer(data);
        } else if (cache[key]) {
            renderer(cache[key]);
        }
    } catch {
        if (cache[key]) {
            renderer(cache[key]);
        }
    }
};

// ---------------- RUNNER ---------------- //

const run = () => {
    load("nifty", "nifty", renderNifty);
    load("global", "global_meter", renderGlobal);
    load("breadth", "nifty_breadth", renderBreadth);
    load("bias", "nifty_bias", renderBias);
};

// 🔁 Sync with backend candle cycle (5 min)
setInterval(run, 300000);

// Initial load
run();
