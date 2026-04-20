import yfinance as yf
import json
from datetime import datetime
import pytz
import os
import time

IST = pytz.timezone("Asia/Kolkata")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

NIFTY = "^NSEI"

GLOBAL_MARKETS = {
    "DowF":   {"symbol": "YM=F",   "weight": 0.35},
    "DAX":    {"symbol": "^GDAXI", "weight": 0.25},
    "Nikkei": {"symbol": "^N225",  "weight": 0.25},
    "HSI":    {"symbol": "^HSI",   "weight": 0.15},
}

SECTORS = {
    "BANK": 0.35,
    "FIN": 0.25,
    "IT": 0.15,
    "METAL": 0.15,
    "FMCG": 0.10
}

SECTOR_SYMBOLS = {
    "BANK": "^NSEBANK",
    "FIN": "^CNXFIN",
    "IT": "^CNXIT",
    "METAL": "^CNXMETAL",
    "FMCG": "^CNXFMCG"
}

def now_ts():
    return int(time.time())

def write(name, obj):
    with open(f"{DATA_DIR}/{name}.json", "w") as f:
        json.dump(obj, f, indent=2)

def closes_5m(symbol, days=3):
    df = yf.download(symbol, period=f"{days}d", interval="5m", progress=False)
    if df.empty:
        return []
    c = df["Close"]
    if hasattr(c, "columns"):
        c = c.iloc[:, 0]
    return c.dropna().tolist()

def rolling_30m_pct(cl):
    if len(cl) < 6 or cl[-6] == 0:
        return None
    return round((cl[-1] - cl[-6]) / cl[-6] * 100, 2)

# ---------------- NIFTY ----------------
def fetch_nifty():
    cl = closes_5m(NIFTY, 3)
    ts = now_ts()

    if len(cl) < 2:
        return {"price": 0, "change": 0, "percent": 0, "market": "CLOSED", "updated_ts": ts}

    last, prev = cl[-1], cl[-2]
    return {
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round((last - prev) / prev * 100, 2),
        "market": "LIVE",
        "updated_ts": ts
    }

# ---------------- GLOBAL ----------------
def fetch_global():
    total = 0
    indices = {}
    ts = now_ts()

    for k, cfg in GLOBAL_MARKETS.items():
        cl = closes_5m(cfg["symbol"])
        pct = rolling_30m_pct(cl)
        if pct is None:
            continue

        score = 1 if pct > 0 else -1 if pct < 0 else 0
        total += score * cfg["weight"]
        indices[k] = {"change_30m": pct}

    meter = max(0, min(10, round(5 + total * 5)))
    return {"meter": meter, "indices": indices, "updated_ts": ts}

# ---------------- BREADTH ----------------
def fetch_breadth():
    total = 0
    sectors = {}
    ts = now_ts()

    for sector, weight in SECTORS.items():
        cl = closes_5m(SECTOR_SYMBOLS[sector])
        pct = rolling_30m_pct(cl)
        if pct is None:
            continue

        sectors[sector] = pct
        total += (1 if pct > 0 else -1 if pct < 0 else 0) * weight

    meter = max(0, min(10, round(5 + total * 5)))
    return {"meter": meter, "sectors": sectors, "updated_ts": ts}

# ---------------- BIAS ----------------
def ema(cl, n):
    k = 2 / (n + 1)
    e = cl[0]
    for p in cl[1:]:
        e = p * k + e * (1 - k)
    return e

def bias_state(cl, size, ema_n):
    if len(cl) < size:
        return None
    return "BULLISH" if cl[-1] > ema(cl[-size:], ema_n) else "BEARISH"

def fetch_bias():
    cl = closes_5m(NIFTY, 15)
    ts = now_ts()

    if len(cl) < 240:
        return {"bias": {}, "message": "Unavailable", "updated_ts": ts}

    b15 = bias_state(cl, 6, 5)
    b1h = bias_state(cl, 48, 20)
    b4h = bias_state(cl, 240, 50)

    if b4h == b1h == b15:
        msg = f"{b4h.capitalize()} continuation"
    elif b4h == b1h:
        msg = f"Pullback within {b4h.lower()} structure"
    elif b4h != b1h:
        msg = "Structural conflict"
    else:
        msg = "Intraday bias forming"

    return {
        "bias": {"4H": b4h, "1H": b1h, "15M": b15},
        "message": msg,
        "updated_ts": ts
    }

# ---------------- MAIN ----------------
if __name__ == "__main__":
    write("nifty", fetch_nifty())
    write("global_meter", fetch_global())
    write("nifty_breadth", fetch_breadth())
    write("nifty_bias", fetch_bias())
