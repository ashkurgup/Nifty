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
    "Dow":    {"symbol": "YM=F",    "weight": 0.35},
    "DAX":    {"symbol": "^GDAXI",  "weight": 0.25},
    "Nikkei": {"symbol": "^N225",   "weight": 0.25},
    "HSI":    {"symbol": "^HSI",    "weight": 0.15},
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

def closes_5m(symbol, days=25):
    df = yf.download(symbol, period=f"{days}d", interval="5m", progress=False)
    if df.empty:
        return []
    c = df["Close"]
    if hasattr(c, "columns"):
        c = c.iloc[:, 0]
    return c.dropna().tolist()

def rolling_30m_pct(cl):
    if len(cl) < 6:
        return None
    return round((cl[-1] - cl[-6]) / cl[-6] * 100, 2)

def market_state(name):
    utc = datetime.utcnow()
    m = utc.hour * 60 + utc.minute
    wd = utc.weekday()
    sessions = {
        "Dow": (810, 1200),
        "DAX": (420, 930),
        "Nikkei": (0, 360),
        "HSI": (90, 480)
    }
    if wd >= 5:
        return "CLOSED"
    s, e = sessions[name]
    if s <= m <= e:
        return "OPEN"
    if e < m <= e + 120:
        return "RECENT"
    return "CLOSED"

# ---------- NIFTY LIVE ----------
def fetch_nifty():
    cl = closes_5m(NIFTY, 3)
    ts = now_ts()
    if len(cl) < 2:
        return {"price": 0, "change": 0, "percent": 0, "market": "CLOSED", "ts": ts}
    last, prev = cl[-1], cl[-2]
    return {
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round((last - prev) / prev * 100, 2),
        "market": "LIVE",
        "ts": ts
    }

# ---------- GLOBAL ----------
def fetch_global():
    total = 0
    out = {}
    ts = now_ts()

    for k, v in GLOBAL_MARKETS.items():
        cl = closes_5m(v["symbol"], 3)
        pct = rolling_30m_pct(cl)
        if pct is None:
            continue
        state = market_state(k)
        mult = 1.0 if state == "OPEN" else 0.75 if state == "RECENT" else 0.4
        score = 1 if pct > 0 else -1 if pct < 0 else 0
        total += score * v["weight"] * mult
        out[k] = {"pct": pct, "state": state}

    meter = max(0, min(10, round(5 + total * 5)))
    return {"meter": meter, "markets": out, "ts": ts}

# ---------- BREADTH ----------
def fetch_breadth():
    total = 0
    out = {}
    ts = now_ts()

    for k, w in SECTORS.items():
        cl = closes_5m(SECTOR_SYMBOLS[k], 3)
        pct = rolling_30m_pct(cl)
        if pct is None:
            continue
        score = 1 if pct > 0 else -1 if pct < 0 else 0
        total += score * w
        out[k] = pct

    meter = max(0, min(10, round(5 + total * 5)))
    return {"meter": meter, "sectors": out, "ts": ts}

# ---------- BIAS ----------
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
    cl = closes_5m(NIFTY, 25)
    ts = now_ts()
    if len(cl) < 240:
        return {"msg": "Unavailable", "bias": {}, "ts": ts}

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

    return {"bias": {"4H": b4h, "1H": b1h, "15M": b15}, "msg": msg, "ts": ts}

# ---------- MAIN ----------
if __name__ == "__main__":
    write("nifty", fetch_nifty())
    write("global", fetch_global())
    write("breadth", fetch_breadth())
    write("bias", fetch_bias())
