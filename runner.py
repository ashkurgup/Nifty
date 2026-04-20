import yfinance as yf
import json
from datetime import datetime, timedelta
import pytz
import os

IST = pytz.timezone("Asia/Kolkata")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# =========================================================
# UTILITIES
# =========================================================

def now_ist():
    return datetime.now(IST)

def nse_market_live(now):
    if now.weekday() >= 5:
        return False
    return now.replace(hour=9, minute=15) <= now <= now.replace(hour=15, minute=30)

def last_30min_change(hist):
    """Return % change between now and ~30 minutes ago"""
    if hist.empty:
        return 0.0

    end = hist.iloc[-1]["Close"]
    start_time = hist.index[-1] - timedelta(minutes=30)
    start_rows = hist[hist.index <= start_time]

    if start_rows.empty:
        start = hist.iloc[0]["Close"]
    else:
        start = start_rows.iloc[-1]["Close"]

    return round((end - start) / start * 100, 2)

# =========================================================
# 1️⃣ NIFTY PRICE
# =========================================================

def fetch_nifty():
    t = yf.Ticker("^NSEI")
    hist = t.history(period="2d", interval="1m")

    last = hist.iloc[-1]
    prev = hist.iloc[-2]

    price = round(float(last["Close"]), 2)
    change = round(price - float(prev["Close"]), 2)
    percent = round(change / float(prev["Close"]) * 100, 2)

    now = now_ist()

    return {
        "symbol": "NIFTY",
        "price": price,
        "change": change,
        "percent": percent,
        "market_status": "LIVE" if nse_market_live(now) else "CLOSED",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST")
    }

# =========================================================
# 2️⃣ STRUCTURAL BIAS (EMA‑BASED, STABLE)
# =========================================================

def timeframe_bias(symbol, interval, ema_period):
    t = yf.Ticker(symbol)
    hist = t.history(period="5d", interval=interval)

    if hist.empty:
        return "PULLBACK"

    close = hist["Close"]
    ema = close.ewm(span=ema_period).mean()

    if close.iloc[-1] > ema.iloc[-1]:
        return "BULLISH"
    elif close.iloc[-1] < ema.iloc[-1]:
        return "BEARISH"
    else:
        return "PULLBACK"

def fetch_structural_bias():
    bias = {
        "4H": timeframe_bias("^NSEI", "60m", 50),
        "1H": timeframe_bias("^NSEI", "30m", 20),
        "15M": timeframe_bias("^NSEI", "15m", 20)
    }

    # Phase logic (simple & dashboard‑friendly)
    if bias["4H"] == bias["1H"] == "BULLISH" and bias["15M"] == "PULLBACK":
        phase = "Pullback phase"
    elif bias["4H"] == bias["1H"] == bias["15M"]:
        phase = f"{bias['4H'].capitalize()} continuation"
    else:
        phase = "Trend consolidation"

    return {
        "symbol": "NIFTY",
        "bias": bias,
        "phase": phase,
        "updated": now_ist().strftime("%d %b %Y, %H:%M IST")
    }

# =========================================================
# 3️⃣ GLOBAL METER
# =========================================================

GLOBAL_INDICES = {
    "dow":   {"symbol": "YM=F",   "weight": 0.40},
    "dax":   {"symbol": "^GDAXI", "weight": 0.25},
    "nikkei":{"symbol": "^N225",  "weight": 0.20},
    "hang":  {"symbol": "^HSI",   "weight": 0.15},
}

def direction_score(pct):
    if pct > 0.20:
        return 1
    if pct < -0.20:
        return -1
    return 0

def market_multiplier(symbol):
    now = now_ist()

    # Simple heuristic (dashboard use)
    if symbol in ["YM=F"]:
        return 1.0           # Futures always relevant
    if now.hour < 12:
        return 0.5           # Asia closed
    return 1.0               # Europe / US active

def fetch_global_meter():
    total = 0.0
    indices_out = {}

    for key, cfg in GLOBAL_INDICES.items():
        t = yf.Ticker(cfg["symbol"])
        hist = t.history(period="1d", interval="5m")

        change30 = last_30min_change(hist)
        ds = direction_score(change30)
        mult = market_multiplier(cfg["symbol"])

        total += ds * cfg["weight"] * mult

        indices_out[key] = {
            "change": change30,
            "multiplier": mult
        }

    # Normalize sum → 1–10
    score = round(5 + total * 5, 2)
    score = max(1, min(10, score))

    return {
        "score": score,
        "indices": indices_out,
        "updated": now_ist().strftime("%d %b %Y, %H:%M IST")
    }

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    try:
        json.dump(fetch_nifty(), open(f"{DATA_DIR}/nifty.json", "w"), indent=2)
        json.dump(fetch_structural_bias(), open(f"{DATA_DIR}/nifty_bias.json", "w"), indent=2)
        json.dump(fetch_global_meter(), open(f"{DATA_DIR}/global_meter.json", "w"), indent=2)

        print("✅ Dashboard data updated")

    except Exception as e:
        print("❌ Update failed:", e)
