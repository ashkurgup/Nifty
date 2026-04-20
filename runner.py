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
# YFINANCE SAFE FETCH (CRITICAL)
# =========================================================

def fetch_hist(symbol, interval="1m"):
    """
    Forced-fresh Yahoo Finance fetch.
    Works best for intraday NSE context dashboards.
    """
    ticker = yf.Ticker(symbol)
    hist = ticker.history(
        period="1d",
        interval=interval,
        auto_adjust=True,
        prepost=True,
    )

    if hist is None or hist.empty:
        return None

    # Yahoo sometimes returns unsorted candles
    hist = hist.sort_index()
    return hist

# =========================================================
# ROLLING 30-MIN CHANGE (CANONICAL)
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
# NIFTY LIVE (LAST PRICE)
# =========================================================

def fetch_nifty():
    hist = fetch_hist("^NSEI", "1m")

    if hist is None or len(hist) < 2:
        raise RuntimeError("NIFTY data unavailable")

    last_price = round(float(hist["Close"].iloc[-1]), 2)

    # Use rolling change instead of prev close
    change_pct = rolling_30m_change(hist)
    change_pct = change_pct if change_pct is not None else 0.0

    now = now_ist()

    return {
        "symbol": "NIFTY",
        "price": last_price,
        "change": round(last_price - hist["Close"].iloc[-2], 2),
        "percent": change_pct,
        "market_status": "LIVE" if time(9, 15) <= now.time() <= time(15, 30) else "CLOSED",
        "updated": now.strftime("%d %b %Y, %H:%M:%S IST")
    }

# =========================================================
# STRUCTURAL BIAS (EMA-BASED, STABLE)
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
# GLOBAL METER (STRIP + METER)
# =========================================================

GLOBAL_INDICES = {
    "DowF": "^DJI",
    "DAX": "^GDAXI",
    "Nikkei": "^N225",
    "HSI": "^HSI"
}

def fetch_global_meter():
    indices = {}
    total_score = 0
    count = 0

    for name, symbol in GLOBAL_INDICES.items():
        hist = fetch_hist(symbol, "1m")
        pct = rolling_30m_change(hist)
        pct = pct if pct is not None else 0.0

        score = 1 if pct > 0 else -1 if pct < 0 else 0
        total_score += score
        count += 1

        indices[name] = {
            "change_30m": pct
        }

    meter = round(5 + (total_score / max(count, 1)) * 5, 2)
    meter = max(0, min(10, meter))

    return {
        "updated": now_ist().strftime("%d %b %Y, %H:%M IST"),
        "meter": meter,
        "indices": indices
    }

# =========================================================
# NIFTY BREADTH METER (WEIGHTED)
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
    json.dump(fetch_nifty(), open(f"{DATA_DIR}/nifty.json", "w"), indent=2)
    json.dump(fetch_bias(), open(f"{DATA_DIR}/nifty_bias.json", "w"), indent=2)
    json.dump(fetch_global_meter(), open(f"{DATA_DIR}/global_meter.json", "w"), indent=2)
    json.dump(fetch_nifty_breadth(), open(f"{DATA_DIR}/nifty_breadth.json", "w"), indent=2)

    print("✅ Live dashboard data updated (yfinance)")
