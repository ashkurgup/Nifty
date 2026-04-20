import yfinance as yf
import json
from datetime import datetime, timedelta, time
import pytz
import os

# =========================================================
# GLOBAL SETTINGS
# =========================================================

IST = pytz.timezone("Asia/Kolkata")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def now_ist():
    return datetime.now(IST)

# =========================================================
# SAFE FILE HELPERS
# =========================================================

def load_previous(path, fallback):
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return fallback

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# =========================================================
# YFINANCE SAFE FETCH
# =========================================================

def fetch_hist(symbol, interval="1m"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(
            period="1d",
            interval=interval,
            auto_adjust=True,
            prepost=True,
        )
        if hist is None or hist.empty:
            return None
        return hist.sort_index()
    except Exception:
        return None

# =========================================================
# ROLLING 30‑MIN CHANGE
# =========================================================

def rolling_30m_change(hist):
    if hist is None or len(hist) < 2:
        return None

    end_time = hist.index[-1]
    start_time = end_time - timedelta(minutes=30)
    window = hist[hist.index >= start_time]

    if len(window) < 2:
        return None

    start = window["Close"].iloc[0]
    end = window["Close"].iloc[-1]

    if start == 0:
        return None

    return round((end - start) / start * 100, 2)

# =========================================================
# NIFTY LIVE (FAIL‑SAFE)
# =========================================================

def fetch_nifty():
    path = f"{DATA_DIR}/nifty.json"
    now = now_ist()

    hist = fetch_hist("^NSEI", "1m")

    if hist is None or len(hist) < 2:
        prev = load_previous(path, {
            "symbol": "NIFTY",
            "price": 0,
            "change": 0,
            "percent": 0,
            "market_status": "CLOSED",
            "updated": ""
        })
        prev["updated"] = now.strftime("%d %b %Y, %H:%M:%S IST")
        return prev

    last_price = round(float(hist["Close"].iloc[-1]), 2)
    prev_price = float(hist["Close"].iloc[-2])
    change = round(last_price - prev_price, 2)

    pct = rolling_30m_change(hist)
    pct = pct if pct is not None else 0.0

    return {
        "symbol": "NIFTY",
        "price": last_price,
        "change": change,
        "percent": pct,
        "market_status": "LIVE" if time(9, 15) <= now.time() <= time(15, 30) else "CLOSED",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST")
    }

# =========================================================
# STRUCTURAL BIAS (FAIL‑SAFE)
# =========================================================

def bias_tf(symbol, interval, ema):
    hist = fetch_hist(symbol, interval)
    if hist is None or len(hist) < ema:
        return "PULLBACK"

    close = hist["Close"]
    ema_val = close.ewm(span=ema).mean()

    if close.iloc[-1] > ema_val.iloc[-1]:
        return "BULLISH"
    if close.iloc[-1] < ema_val.iloc[-1]:
        return "BEARISH"
    return "PULLBACK"

def fetch_bias():
    bias = {
        "4H": bias_tf("^NSEI", "60m", 50),
        "1H": bias_tf("^NSEI", "30m", 20),
        "15M": bias_tf("^NSEI", "15m", 20)
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
        "updated": now_ist().strftime("%d %b %Y, %H:%M IST")
    }

# =========================================================
# GLOBAL METER (FAIL‑SAFE)
# =========================================================

GLOBAL_INDICES = {
    "DowF": "^DJI",
    "DAX": "^GDAXI",
    "Nikkei": "^N225",
    "HSI": "^HSI"
}

def fetch_global_meter():
    indices = {}
    total = 0
    count = 0

    for name, symbol in GLOBAL_INDICES.items():
        hist = fetch_hist(symbol, "1m")
        pct = rolling_30m_change(hist)
        pct = pct if pct is not None else 0.0

        score = 1 if pct > 0 else -1 if pct < 0 else 0
        total += score
        count += 1

        indices[name] = {"change_30m": pct}

    meter = round(5 + (total / max(count, 1)) * 5, 2)
    meter = max(0, min(10, meter))

    return {
        "updated": now_ist().strftime("%d %b %Y, %H:%M IST"),
        "meter": meter,
        "indices": indices
    }

# =========================================================
# NIFTY BREADTH METER (FAIL‑SAFE)
# =========================================================

NIFTY_SECTORS = {
    "BANK": {"symbol": "^NSEBANK", "weight": 0.35},
    "FIN": {"symbol": "NIFTY_FIN_SERVICE.NS", "weight": 0.25},
    "IT": {"symbol": "^CNXIT", "weight": 0.15},
    "METAL": {"symbol": "^CNXMETAL", "weight": 0.15},
    "FMCG": {"symbol": "^CNXFMCG", "weight": 0.10},
}

def fetch_nifty_breadth():
    total = 0.0
    sectors = []

    for name, cfg in NIFTY_SECTORS.items():
        hist = fetch_hist(cfg["symbol"], "1m")
        pct = rolling_30m_change(hist)
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

    meter = round(5 + total * 5, 2)
    meter = max(0, min(10, meter))

    return {
        "updated": now_ist().strftime("%d %b %Y, %H:%M IST"),
        "meter": meter,
        "sectors": sectors
    }

# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    save_json(f"{DATA_DIR}/nifty.json", fetch_nifty())
    save_json(f"{DATA_DIR}/nifty_bias.json", fetch_bias())
    save_json(f"{DATA_DIR}/global_meter.json", fetch_global_meter())
    save_json(f"{DATA_DIR}/nifty_breadth.json", fetch_nifty_breadth())

    print("✅ Dashboard data updated safely (yfinance)")
