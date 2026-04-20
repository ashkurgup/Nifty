import requests
import json
from datetime import datetime
import pytz
import os
import time

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com"
IST = pytz.timezone("Asia/Kolkata")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def now_ist():
    return datetime.now(IST)

def safe_write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def fetch_ohlc(symbol, interval, bars):
    r = requests.get(
        f"{BASE_URL}/time_series",
        params={
            "symbol": symbol,
            "interval": interval,
            "outputsize": bars,
            "apikey": API_KEY
        },
        timeout=20
    )
    data = r.json()
    if "values" not in data:
        return []
    return sorted(data["values"], key=lambda x: x["datetime"])

# ================= EMA =================

def ema_bias(values, period):
    closes = [float(v["close"]) for v in values]
    if len(closes) < period:
        return None
    k = 2 / (period + 1)
    ema = closes[0]
    for p in closes[1:]:
        ema = p * k + ema * (1 - k)
    return "BULLISH" if closes[-1] > ema else "BEARISH"

# ================= NIFTY PRICE =================

def fetch_nifty():
    values = fetch_ohlc("NIFTY_50", "1min", 10)
    now = now_ist()
    ts = int(time.time())

    if len(values) < 2:
        return {
            "symbol": "NIFTY",
            "price": 0,
            "change": 0,
            "percent": 0,
            "market_status": "CLOSED",
            "updated": now.strftime("%d %b %Y, %H:%M:%S IST"),
            "updated_ts": ts
        }

    last = float(values[-1]["close"])
    prev = float(values[-2]["close"])

    return {
        "symbol": "NIFTY",
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round((last - prev) / prev * 100, 2) if prev else 0,
        "market_status": "LIVE",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST"),
        "updated_ts": ts
    }

# ================= STRUCTURAL BIAS =================

def fetch_bias():
    now = now_ist()
    ts = int(time.time())

    # ✅ ONE reliable fetch
    # 15‑minute candles × 300 ≈ ~12 trading days
    values = fetch_ohlc("NIFTY_50", "15min", 300)

    if len(values) < 50:
        return {
            "bias": {},
            "phase": "Unavailable",
            "updated": now.strftime("%d %b %Y, %H:%M IST"),
            "updated_ts": ts
        }

    # ✅ Frame slicing
    values_4h = values[-160:]   # ~10 trading days
    values_1h = values[-48:]    # ~3 trading days
    values_15m = values[-20:]   # intraday

    bias = {
        "4H": ema_bias(values_4h, 50),
        "1H": ema_bias(values_1h, 20),
        "15M": ema_bias(values_15m, 10)
    }

    if not bias["4H"] and not bias["1H"] and not bias["15M"]:
        return {
            "bias": {},
            "phase": "Unavailable",
            "updated": now.strftime("%d %b %Y, %H:%M IST"),
            "updated_ts": ts
        }

    if bias["4H"] == bias["1H"] == bias["15M"]:
        phase = f"{bias['4H'].capitalize()} continuation"
    elif bias["4H"] == bias["1H"] and bias["15M"]:
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

    return {
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "updated_ts": ts,
        "meter": 5,
        "indices": {
            "DowF": {"change_30m": 0},
            "DAX": {"change_30m": 0},
            "Nikkei": {"change_30m": 0},
            "HSI": {"change_30m": 0}
        }
    }

# ================= NIFTY BREADTH =================

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
