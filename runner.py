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

GLOBAL_SYMBOLS = {
    "DowF": {"symbol": "YM=F", "weight": 0.35},
    "DAX": {"symbol": "^GDAXI", "weight": 0.25},
    "Nikkei": {"symbol": "^N225", "weight": 0.25},
    "HSI": {"symbol": "^HSI", "weight": 0.15},
}

# ================= HELPERS =================

def now_ist():
    return datetime.now(IST)

def safe_write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def get_closes(symbol, period="1d", interval="5m"):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df.empty:
        return []
    close = df["Close"]
    if hasattr(close, "columns"):
        close = close.iloc[:, 0]
    return close.dropna().tolist()

def rolling_30m_change(closes):
    if len(closes) < 6:
        return 0.0
    start = closes[-6]
    end = closes[-1]
    if start == 0:
        return 0.0
    return round((end - start) / start * 100, 2)

# ================= NIFTY =================

def fetch_nifty():
    closes = get_closes(NIFTY, period="1d", interval="1m")
    now = now_ist()
    ts = int(time.time())

    if len(closes) < 2:
        return {
            "symbol": "NIFTY",
            "price": 0,
            "change": 0,
            "percent": 0,
            "market_status": "CLOSED",
            "updated": now.strftime("%d %b %Y, %H:%M:%S IST"),
            "updated_ts": ts
        }

    last = closes[-1]
    prev = closes[-2]

    return {
        "symbol": "NIFTY",
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round((last - prev) / prev * 100, 2),
        "market_status": "LIVE",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST"),
        "updated_ts": ts
    }

# ================= STRUCTURAL BIAS =================

def ema_bias(closes, period):
    if len(closes) < period:
        return None
    k = 2 / (period + 1)
    ema = closes[0]
    for p in closes[1:]:
        ema = p * k + ema * (1 - k)
    return "BULLISH" if closes[-1] > ema else "BEARISH"

def fetch_bias():
    closes = get_closes(NIFTY, period="15d", interval="15m")
    now = now_ist()
    ts = int(time.time())

    if len(closes) < 60:
        return {
            "bias": {},
            "phase": "Unavailable",
            "updated": now.strftime("%d %b %Y, %H:%M IST"),
            "updated_ts": ts
        }

    bias = {
        "4H": ema_bias(closes[-160:], 50),
        "1H": ema_bias(closes[-48:], 20),
        "15M": ema_bias(closes[-20:], 10)
    }

    if bias["4H"] == bias["1H"] == bias["15M"]:
        phase = f"{bias['4H'].capitalize()} continuation"
    elif bias["4H"] == bias["1H"]:
        phase = f"Pullback within {bias['4H'].lower()} structure"
    elif bias["4H"] != bias["1H"]:
        phase = "Structural conflict"
    else:
        phase = "Intraday bias forming"

    return {
        "bias": bias,
        "phase": phase,
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "updated_ts": ts
    }

# ================= GLOBAL METER =================

def fetch_global_meter():
    now = now_ist()
    ts = int(time.time())

    total_weighted_score = 0.0
    indices = {}

    for key, cfg in GLOBAL_SYMBOLS.items():
        closes = get_closes(cfg["symbol"], period="1d", interval="5m")
        pct = rolling_30m_change(closes)
        indices[key] = {"change_30m": pct}

        if pct > 0:
            total_weighted_score += cfg["weight"]
        elif pct < 0:
            total_weighted_score -= cfg["weight"]

    meter = max(0, min(10, 5 + total_weighted_score * 5))

    return {
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "updated_ts": ts,
        "meter": round(meter, 2),
        "indices": indices
    }

# ================= NIFTY BREADTH (stub for now) =================

def fetch_nifty_breadth():
    now = now_ist()
    ts = int(time.time())

    return {
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "updated_ts": ts,
        "meter": 5,
        "sectors": ["BANK", "FIN", "IT", "METAL", "FMCG"]
    }

# ================= MAIN =================

if __name__ == "__main__":
    safe_write("data/nifty.json", fetch_nifty())
    safe_write("data/nifty_bias.json", fetch_bias())
    safe_write("data/global_meter.json", fetch_global_meter())
    safe_write("data/nifty_breadth.json", fetch_nifty_breadth())
``
