import yfinance as yf
import json
from datetime import datetime
import pytz
import os
import time

IST = pytz.timezone("Asia/Kolkata")
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

NIFTY_SYMBOL = "^NSEI"

def now_ist():
    return datetime.now(IST)

def safe_write(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ================= HELPER =================

def close_series(df):
    """
    Returns a clean list of close prices from yfinance,
    handling both Series and MultiIndex formats.
    """
    if df.empty:
        return []
    close = df["Close"]
    if isinstance(close, dict) or hasattr(close, "columns"):
        close = close.iloc[:, 0]   # flatten MultiIndex
    return close.dropna().tolist()

# ================= EMA =================

def ema_bias(closes, period):
    if len(closes) < period:
        return None
    k = 2 / (period + 1)
    ema = closes[0]
    for p in closes[1:]:
        ema = p * k + ema * (1 - k)
    return "BULLISH" if closes[-1] > ema else "BEARISH"

# ================= NIFTY PRICE =================

def fetch_nifty():
    now = now_ist()
    ts = int(time.time())

    df = yf.download(
        NIFTY_SYMBOL,
        period="1d",
        interval="1m",
        progress=False,
        auto_adjust=False
    )

    closes = close_series(df)

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

    last = float(closes[-1])
    prev = float(closes[-2])

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

def fetch_bias():
    now = now_ist()
    ts = int(time.time())

    df = yf.download(
        NIFTY_SYMBOL,
        period="15d",
        interval="15m",
        progress=False,
        auto_adjust=False
    )

    closes = close_series(df)

    if len(closes) < 60:
        return {
            "bias": {},
            "phase": "Unavailable",
            "updated": now.strftime("%d %b %Y, %H:%M IST"),
            "updated_ts": ts
        }

    bias_4h = ema_bias(closes[-160:], 50)   # ~10 trading days
    bias_1h = ema_bias(closes[-48:], 20)    # ~3 trading days
    bias_15m = ema_bias(closes[-20:], 10)   # intraday

    bias = {
        "4H": bias_4h,
        "1H": bias_1h,
        "15M": bias_15m
    }

    if bias_4h == bias_1h == bias_15m and bias_4h:
        phase = f"{bias_4h.capitalize()} continuation"
    elif bias_4h == bias_1h and bias_15m:
        phase = f"Pullback within {bias_4h.lower()} structure"
    elif bias_4h != bias_1h:
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
