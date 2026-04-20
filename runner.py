import yfinance as yf
import json
from datetime import datetime, timedelta, time
import pytz
import os

# =========================================================
# CONFIGURATION (PLUGGABLE LOGIC)
# =========================================================

GLOBAL_CONFIG = {
    "indices": {
        "dow": {"symbol": "YM=F", "weight": 0.40, "region": "US"},
        "dax": {"symbol": "^GDAXI", "weight": 0.25, "region": "EU"},
        "nikkei": {"symbol": "^N225", "weight": 0.20, "region": "ASIA"},
        "hang": {
            "symbol": "^HSI",
            "weight": 0.15,
            "region": "ASIA",
            "risk_proxy": True
        }
    },
    "direction_thresholds": {"positive": 0.20, "negative": -0.20},
    "market_state_multiplier": {
        "OPEN": 1.00,
        "RECENTLY_CLOSED": 0.75,
        "LONG_CLOSED": 0.50
    },
    "risk_proxy_boost": {"threshold": 0.15, "multiplier": 1.25}
}

# =========================================================
# TIME / PATH
# =========================================================

IST = pytz.timezone("Asia/Kolkata")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def now_ist():
    return datetime.now(IST)

# =========================================================
# MARKET STATE
# =========================================================

def market_state(region, now):
    h = now.hour
    if region == "ASIA":
        if 6 <= h < 12: return "OPEN"
        if 12 <= h < 14: return "RECENTLY_CLOSED"
    if region == "EU":
        if 12 <= h < 18: return "OPEN"
        if 18 <= h < 20: return "RECENTLY_CLOSED"
    if region == "US":
        if h >= 18 or h < 3: return "OPEN"
        if 3 <= h < 5: return "RECENTLY_CLOSED"
    return "LONG_CLOSED"

# =========================================================
# SAFE HELPERS
# =========================================================

def last_30min_change(hist):
    if hist is None or hist.empty or len(hist) < 2:
        return None
    try:
        end = hist.iloc[-1]["Close"]
        cutoff = hist.index[-1] - timedelta(minutes=30)
        earlier = hist[hist.index <= cutoff]
        start = earlier.iloc[-1]["Close"] if not earlier.empty else hist.iloc[0]["Close"]
        if start == 0:
            return None
        return round((end - start) / start * 100, 2)
    except Exception:
        return None

def direction_score(pct):
    if pct is None:
        return 0
    if pct > GLOBAL_CONFIG["direction_thresholds"]["positive"]:
        return 1
    if pct < GLOBAL_CONFIG["direction_thresholds"]["negative"]:
        return -1
    return 0

# =========================================================
# NIFTY
# =========================================================

def fetch_nifty():
    t = yf.Ticker("^NSEI")
    hist = t.history(period="2d", interval="1m")
    if hist.empty or len(hist) < 2:
        raise RuntimeError("NIFTY data unavailable")

    last, prev = hist.iloc[-1], hist.iloc[-2]
    price = round(float(last["Close"]), 2)
    change = round(price - float(prev["Close"]), 2)
    percent = round(change / float(prev["Close"]) * 100, 2)
    now = now_ist()

    return {
        "symbol": "NIFTY",
        "price": price,
        "change": change,
        "percent": percent,
        "market_status": "LIVE" if time(9, 15) <= now.time() <= time(15, 30) else "CLOSED",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST")
    }

# =========================================================
# STRUCTURAL BIAS
# =========================================================

def bias_tf(symbol, interval, ema):
    hist = yf.Ticker(symbol).history(period="5d", interval=interval)
    if hist.empty:
        return "PULLBACK"
    close = hist["Close"]
    ema_val = close.ewm(span=ema).mean()
    return "BULLISH" if close.iloc[-1] > ema_val.iloc[-1] else "BEARISH"

def fetch_bias():
    bias = {
        "4H": bias_tf("^NSEI", "60m", 50),
        "1H": bias_tf("^NSEI", "30m", 20),
        "15M": bias_tf("^NSEI", "15m", 20)
    }
    if bias["4H"] == bias["1H"] == "BULLISH":
        phase = "Pullback phase" if bias["15M"] != "BULLISH" else "Bullish continuation"
    else:
        phase = "Trend consolidation"

    return {
        "symbol": "NIFTY",
        "bias": bias,
        "phase": phase,
        "updated": now_ist().strftime("%d %b %Y, %H:%M IST")
    }

# =========================================================
# GLOBAL METER (SAFE + PLUGGABLE)
# =========================================================

def fetch_global_meter():
    now = now_ist()
    total = 0.0
    indices_out = {}

    for key, cfg in GLOBAL_CONFIG["indices"].items():
        try:
            hist = yf.Ticker(cfg["symbol"]).history(period="1d", interval="5m")
            change = last_30min_change(hist)

            if change is None:
                indices_out[key] = {"change": 0.0, "state": "NO_DATA", "multiplier": 0.0}
                continue

            d_score = direction_score(change)
            state = market_state(cfg["region"], now)
            multiplier = GLOBAL_CONFIG["market_state_multiplier"][state]

            if cfg.get("risk_proxy") and abs(change) >= GLOBAL_CONFIG["risk_proxy_boost"]["threshold"]:
                multiplier *= GLOBAL_CONFIG["risk_proxy_boost"]["multiplier"]

            total += d_score * cfg["weight"] * multiplier

            indices_out[key] = {
                "change": change,
                "state": state,
                "multiplier": round(multiplier, 2)
            }

        except Exception:
            indices_out[key] = {"change": 0.0, "state": "ERROR", "multiplier": 0.0}

    score = round(max(1, min(10, 5 + total * 5)), 2)

    return {
        "score": score,
        "indices": indices_out,
        "updated": now.strftime("%d %b %Y, %H:%M IST")
    }

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    json.dump(fetch_nifty(), open(f"{DATA_DIR}/nifty.json", "w"), indent=2)
    json.dump(fetch_bias(), open(f"{DATA_DIR}/nifty_bias.json", "w"), indent=2)
    json.dump(fetch_global_meter(), open(f"{DATA_DIR}/global_meter.json", "w"), indent=2)
    print("✅ All dashboard data updated safely")
