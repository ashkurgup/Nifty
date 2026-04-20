import yfinance as yf
import json
from datetime import datetime
import pytz
import os
import time

IST = pytz.timezone("Asia/Kolkata")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ================= CONFIG =================

NIFTY = "^NSEI"

GLOBAL_MARKETS = {
    "Dow": {"symbol": "YM=F", "weight": 0.35},
    "DAX": {"symbol": "^GDAXI", "weight": 0.25},
    "Nikkei": {"symbol": "^N225", "weight": 0.25},
    "HSI": {"symbol": "^HSI", "weight": 0.15},
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

# ================= HELPERS =================

def now_ist():
    return datetime.now(IST)

def safe_write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def closes_5m(symbol, days=20):
    df = yf.download(
        symbol,
        period=f"{days}d",
        interval="5m",
        progress=False
    )
    if df.empty:
        return []
    close = df["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    return close.dropna().tolist()

def rolling_30m_pct(closes):
    if len(closes) < 6:
        return None
    start = closes[-6]
    end = closes[-1]
    if start == 0:
        return None
    return round((end - start) / start * 100, 2)

# ================= MARKET STATE (UTC) =================

def market_state(name):
    utc = datetime.utcnow()
    mins = utc.hour * 60 + utc.minute
    wd = utc.weekday()

    sessions = {
        "Dow": (810, 1200),
        "DAX": (420, 930),
        "Nikkei": (0, 360),
        "HSI": (90, 480)
    }

    if wd >= 5:
        return "CLOSED"

    start, end = sessions[name]
    if start <= mins <= end:
        return "OPEN"
    if end < mins <= end + 120:
        return "RECENT"
    return "CLOSED"

# ================= NIFTY LIVE =================

def fetch_nifty():
    closes = closes_5m(NIFTY, 2)
    now = now_ist()
    ts = int(time.time())

    if len(closes) < 2:
        return {
            "price": 0,
            "change": 0,
            "percent": 0,
            "market_status": "CLOSED",
            "updated_ts": ts
        }

    last = closes[-1]
    prev = closes[-2]

    return {
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round((last - prev) / prev * 100, 2),
        "market_status": "LIVE",
        "updated_ts": ts
    }

# ================= GLOBAL MARKET =================

def fetch_global():
    total = 0
    indices = {}
    now = now_ist()
    ts = int(time.time())

    for name, cfg in GLOBAL_MARKETS.items():
        closes = closes_5m(cfg["symbol"], 2)
        pct = rolling_30m_pct(closes)
        if pct is None:
            continue

        state = market_state(name)
        mult = 1.0 if state == "OPEN" else 0.75 if state == "RECENT" else 0.4
        score = (1 if pct > 0 else -1 if pct < 0 else 0)

        total += score * cfg["weight"] * mult
        indices[name] = pct

    meter = max(0, min(10, round(5 + total * 5)))

    return {
        "meter": meter,
        "indices": indices,
        "updated_ts": ts
    }

# ================= BREADTH =================

def fetch_breadth():
    total = 0
    sectors = {}
    ts = int(time.time())

    for name, weight in SECTORS.items():
        closes = closes_5m(SECTOR_SYMBOLS[name], 2)
        pct = rolling_30m_pct(closes)
        if pct is None:
            continue
        total += (1 if pct > 0 else -1 if pct < 0 else 0) * weight
        sectors[name] = pct

    meter = max(0, min(10, round(5 + total * 5)))

    return {
        "meter": meter,
        "sectors": sectors,
        "updated_ts": ts
    }

# ================= BIAS =================

def ema(closes, n):
    if len(closes) < n:
        return None
    k = 2 / (n + 1)
    e = closes[0]
    for p in closes[1:]:
        e = p * k + e * (1 - k)
    return e

def bias_state(closes, period):
    e = ema(closes, period)
    if e is None:
        return None
    return "BULLISH" if closes[-1] > e else "BEARISH"

def fetch_bias():
    closes = closes_5m(NIFTY, 25)
    ts = int(time.time())

    if len(closes) < 240:
        return {"bias": {}, "message": "Unavailable", "updated_ts": ts}

    b15 = bias_state(closes[-6:], 5)
    b1h = bias_state(closes[-48:], 20)
    b4h = bias_state(closes[-240:], 50)

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

# ================= MAIN =================

if __name__ == "__main__":
    safe_write("data/nifty.json", fetch_nifty())
    safe_write("data/global.json", fetch_global())
    safe_write("data/breadth.json", fetch_breadth())
    safe_write("data/bias.json", fetch_bias())
