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

def fetch_ohlc(symbol, interval="1min", bars=60):
    r = requests.get(
        f"{BASE_URL}/time_series",
        params={
            "symbol": symbol,
            "interval": interval,
            "outputsize": bars,
            "apikey": API_KEY
        },
        timeout=15
    )
    data = r.json()
    if "values" not in data:
        return None
    return sorted(data["values"], key=lambda x: x["datetime"])

def rolling_change(values):
    if not values or len(values) < 2:
        return None
    start = float(values[0]["close"])
    end = float(values[-1]["close"])
    return round((end - start) / start * 100, 2) if start else None

def fetch_nifty():
    values = fetch_ohlc("NIFTY_50")
    now = now_ist()
    ts = int(time.time())

    if not values:
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
        "percent": rolling_change(values) or 0,
        "market_status": "LIVE",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST"),
        "updated_ts": ts
    }

def fetch_bias():
    values = fetch_ohlc("NIFTY_50", "15min", 80)
    now = now_ist()
    ts = int(time.time())

    if not values:
        return {
            "bias": {},
            "phase": "Unavailable",
            "updated": now.strftime("%d %b %Y, %H:%M IST"),
            "updated_ts": ts
        }

    def ema_bias(period):
        closes = [float(v["close"]) for v in values]
        if len(closes) < period:
            return "NEUTRAL"
        k = 2 / (period + 1)
        ema = closes[0]
        for p in closes[1:]:
            ema = p * k + ema * (1 - k)
        return "BULLISH" if closes[-1] > ema else "BEARISH"

    bias = {
        "4H": ema_bias(50),
        "1H": ema_bias(20),
        "15M": ema_bias(10)
    }

    phase = "Trend consolidation"
    if bias["4H"] == bias["1H"] == bias["15M"]:
        phase = f"{bias['4H'].capitalize()} continuation"

    return {
        "bias": bias,
        "phase": phase,
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "updated_ts": ts
    }

def fetch_global_meter():
    now = now_ist()
    ts = int(time.time())
    meter = 5

    return {
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "updated_ts": ts,
        "meter": meter,
        "indices": {
            "DowF": {"change_30m": 0},
            "DAX": {"change_30m": 0},
            "Nikkei": {"change_30m": 0},
            "HSI": {"change_30m": 0}
        }
    }

def fetch_nifty_breadth():
    now = now_ist()
    ts = int(time.time())

    return {
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "updated_ts": ts,
        "meter": 5,
        "sectors": ["BANK","FIN","IT","METAL","FMCG"]
    }

if __name__ == "__main__":
    safe_write("data/nifty.json", fetch_nifty())
    safe_write("data/nifty_bias.json", fetch_bias())
    safe_write("data/global_meter.json", fetch_global_meter())
    safe_write("data/nifty_breadth.json", fetch_nifty_breadth())
