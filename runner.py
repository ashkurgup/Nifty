import requests
import json
from datetime import datetime, timedelta
import pytz
import os

# ================= CONFIG =================

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com"
IST = pytz.timezone("Asia/Kolkata")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def now_ist():
    return datetime.now(IST)

# ================= SAFE HELPERS =================

def safe_write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def fetch_ohlc(symbol, interval="1min", bars=60):
    """
    Fetch intraday OHLC from Twelve Data
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": bars,
        "apikey": API_KEY
    }
    r = requests.get(f"{BASE_URL}/time_series", params=params, timeout=15)
    data = r.json()

    if "values" not in data:
        return None

    values = sorted(data["values"], key=lambda x: x["datetime"])
    return values

def rolling_30m_change(values):
    if not values or len(values) < 2:
        return None
    start = float(values[0]["close"])
    end = float(values[-1]["close"])
    if start == 0:
        return None
    return round((end - start) / start * 100, 2)

# ================= NIFTY LIVE =================

def fetch_nifty():
    values = fetch_ohlc("NIFTY_50", "1min", 60)
    now = now_ist()

    if not values:
        return {
            "symbol": "NIFTY",
            "price": 0,
            "change": 0,
            "percent": 0,
            "market_status": "CLOSED",
            "updated": now.strftime("%d %b %Y, %H:%M:%S IST")
        }

    last = float(values[-1]["close"])
    prev = float(values[-2]["close"])
    pct = rolling_30m_change(values)

    return {
        "symbol": "NIFTY",
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": pct if pct is not None else 0.0,
        "market_status": "LIVE",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST")
    }

# ================= STRUCTURAL BIAS =================

def bias_from_ema(values, ema_period):
    close = [float(v["close"]) for v in values]
    if len(close) < ema_period:
        return "PULLBACK"
    multiplier = 2 / (ema_period + 1)
    ema = close[0]
    for price in close[1:]:
        ema = price * multiplier + ema * (1 - multiplier)
    return "BULLISH" if close[-1] > ema else "BEARISH"

def fetch_bias():
    values = fetch_ohlc("NIFTY_50", "15min", 80)
    now = now_ist()

    if not values:
        return {"symbol": "NIFTY", "bias": {}, "phase": "Unavailable", "updated": now.strftime("%d %b %Y, %H:%M IST")}

    bias = {
        "4H": bias_from_ema(values, 50),
        "1H": bias_from_ema(values, 20),
        "15M": bias_from_ema(values, 20)
    }

    if bias["4H"] == bias["1H"] == "BULLISH" and bias["15M"] != "BULLISH":
        phase = "Pullback phase"
    elif bias["4H"] == bias["1H"] == bias["15M"]:
        phase = f"{bias['4H'].capitalize()} continuation"
    else:
        phase = "Trend consolidation"

    return {
        "symbol": "NIFTY",
        "bias": bias,
        "phase": phase,
        "updated": now.strftime("%d %b %Y, %H:%M IST")
    }

# ================= GLOBAL METER =================

GLOBAL_SYMBOLS = {
    "DowF": "DJI",
    "DAX": "DAX",
    "Nikkei": "NIKKEI",
    "HSI": "HSI"
}

def fetch_global_meter():
    total, count = 0, 0
    indices = {}
    now = now_ist()

    for name, sym in GLOBAL_SYMBOLS.items():
        values = fetch_ohlc(sym, "1min", 30)
        pct = rolling_30m_change(values)
        pct = pct if pct is not None else 0.0
        score = 1 if pct > 0 else -1 if pct < 0 else 0
        total += score
        count += 1
        indices[name] = {"change_30m": pct}

    meter = max(0, min(10, 5 + (total / count) * 5))

    return {
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "meter": round(meter, 2),
        "indices": indices
    }

# ================= NIFTY BREADTH =================

NIFTY_SECTORS = {
    "BANK": {"symbol": "NIFTY_BANK", "weight": 0.35},
    "FIN": {"symbol": "NIFTY_FIN_SERVICE", "weight": 0.25},
    "IT": {"symbol": "NIFTY_IT", "weight": 0.15},
    "METAL": {"symbol": "NIFTY_METAL", "weight": 0.15},
    "FMCG": {"symbol": "NIFTY_FMCG", "weight": 0.10}
}

def fetch_nifty_breadth():
    total = 0.0
    sectors = []
    now = now_ist()

    for name, cfg in NIFTY_SECTORS.items():
        values = fetch_ohlc(cfg["symbol"], "1min", 30)
        pct = rolling_30m_change(values)
        pct = pct if pct is not None else 0.0

        if pct > 0.15:
            score = 1
        elif pct < -0.15:
            score = -1
        else:
            score = 0

        total += score * cfg["weight"]

        sectors.append({
            "key": name,
            "change_30m": pct,
            "weight": cfg["weight"]
        })

    meter = max(0, min(10, 5 + total * 5))

    return {
        "updated": now.strftime("%d %b %Y, %H:%M IST"),
        "meter": round(meter, 2),
        "sectors": sectors
    }

# ================= MAIN =================

if __name__ == "__main__":
    safe_write(f"{DATA_DIR}/nifty.json", fetch_nifty())
    safe_write(f"{DATA_DIR}/nifty_bias.json", fetch_bias())
    safe_write(f"{DATA_DIR}/global_meter.json", fetch_global_meter())
    safe_write(f"{DATA_DIR}/nifty_breadth.json", fetch_nifty_breadth())

    print("✅ Dashboard updated via Twelve Data")
``
