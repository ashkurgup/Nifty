import yfinance as yf
import json
import time
import os
from datetime import datetime
import pytz
import numpy as np

# ---------------- CONFIG ---------------- #

SECTOR_WEIGHTS = {'BANK': 0.35, 'FIN': 0.25, 'IT': 0.15, 'METAL': 0.15, 'FMCG': 0.10}
GLOBAL_WEIGHTS = {'DOW': 0.35, 'DAX': 0.25, 'NIKKEI': 0.25, 'HSI': 0.15}
ACTIVITY_MULTIPLIERS = {'OPEN': 1.00, 'RECENTLY_CLOSED': 0.75, 'CLOSED': 0.40}

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------------- UTIL ---------------- #

def load_json(name):
    try:
        with open(f"{DATA_DIR}/{name}.json") as f:
            return json.load(f)
    except:
        return {}

def save_json(name, payload):
    with open(f"{DATA_DIR}/{name}.json", "w") as f:
        json.dump(payload, f)

def is_valid(x):
    return x is not None and not (isinstance(x, float) and np.isnan(x))

# ---------------- MARKET STATE ---------------- #

def is_nse_open():
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return now.weekday() < 5 and start <= now <= end

def get_market_state(data):
    try:
        last_ts = data.index[-1].timestamp()
        diff = time.time() - last_ts
        if diff < 900: return "OPEN"
        elif diff < 7200: return "RECENTLY_CLOSED"
        return "CLOSED"
    except:
        return "CLOSED"

# ---------------- CORE CALC ---------------- #

def get_30m_change(data):
    try:
        if len(data) < 6:
            return None
        start = data['Open'].iloc[-6]
        end = data['Close'].iloc[-1]
        return float(((end - start) / start) * 100)
    except:
        return None

# ---------------- NIFTY LIVE ---------------- #

def build_nifty():
    prev = load_json("nifty")

    try:
        data = yf.download("^NSEI", period="1d", interval="5m", progress=False)

        if data.empty:
            return prev

        last_candle_time = data.index[-1].timestamp()
        if time.time() - last_candle_time > 600:
            return prev  # stale → persist

        price = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[0])

        payload = {
            "price": round(price, 2),
            "change": round(price - prev_close, 2),
            "percent": round(((price - prev_close) / prev_close) * 100, 2),
            "high": round(float(data['High'].max()), 2),
            "low": round(float(data['Low'].min()), 2),
            "market": "OPEN" if is_nse_open() else "CLOSED",
            "updated_ts": int(time.time())
        }

        return payload

    except:
        return prev

# ---------------- GLOBAL ---------------- #

def build_global():
    prev = load_json("global_meter")

    tickers = {'DOW': 'YM=F', 'DAX': '^GDAXI', 'NIKKEI': '^N225', 'HSI': '^HSI'}

    indices = {}
    score = 0
    valid_weight = 0

    for name, ticker in tickers.items():
        last_val = prev.get("indices", {}).get(name, {}).get("change_30m")

        try:
            data = yf.download(ticker, period="1d", interval="5m", progress=False)

            pct = get_30m_change(data)
            state = get_market_state(data)

            if not is_valid(pct):
                pct = last_val

        except:
            pct = last_val
            state = "CLOSED"

        if is_valid(pct):
            direction = 1 if pct > 0 else -1 if pct < 0 else 0
            weight = GLOBAL_WEIGHTS[name]
            mult = ACTIVITY_MULTIPLIERS[state]

            score += direction * weight * mult
            valid_weight += weight

        indices[name] = {
            "change_30m": round(pct, 2) if is_valid(pct) else 0,
            "status": state
        }

    if valid_weight > 0:
        meter = round(5 + (score * 5), 1)
    else:
        meter = prev.get("meter", 5)

    return {"meter": meter, "indices": indices}

# ---------------- BREADTH ---------------- #

def build_breadth():
    prev = load_json("nifty_breadth")

    tickers = {
        'BANK': '^NSEBANK',
        'FIN': 'NIFTY_FIN_SERVICE.NS',
        'IT': '^CNXIT',
        'METAL': '^CNXMETAL',
        'FMCG': '^CNXFMCG'
    }

    sectors = {}
    score = 0
    valid_weight = 0

    for name, ticker in tickers.items():
        last_val = prev.get("sectors", {}).get(name)

        try:
            data = yf.download(ticker, period="1d", interval="5m", progress=False)
            pct = get_30m_change(data)

            if not is_valid(pct):
                pct = last_val

        except:
            pct = last_val

        if is_valid(pct):
            direction = 1 if pct > 0 else -1 if pct < 0 else 0
            weight = SECTOR_WEIGHTS[name]

            score += direction * weight
            valid_weight += weight

        sectors[name] = round(pct, 2) if is_valid(pct) else 0

    if valid_weight > 0:
        normalized = score / valid_weight
        meter = round(5 + (normalized * 5), 1)
    else:
        meter = prev.get("meter", 5)

    return {"meter": meter, "sectors": sectors}

# ---------------- BIAS ---------------- #

def get_bias(df):
    if len(df) < 2:
        return None
    if df['Close'].iloc[-1] > df['Close'].iloc[0]:
        return "BULLISH"
    elif df['Close'].iloc[-1] < df['Close'].iloc[0]:
        return "BEARISH"
    return None

def get_bias_message(b4h, b1h, b15m):
    if b4h != b1h:
        return "Higher timeframes disagree — the market is transitioning."
    if b4h == "BULLISH":
        return "The trend is intact and aligned across all timeframes." if b15m == "BULLISH" else "The broader trend is up, but price is digesting gains."
    if b4h == "BEARISH":
        return "Downtrend is structured and orderly." if b15m == "BEARISH" else "A bounce is occurring inside a broader downtrend."
    return "There isn’t enough information to form a structural view."

def build_bias():
    prev = load_json("nifty_bias")

    try:
        data = yf.download("^NSEI", period="10d", interval="5m", progress=False)

        b15 = get_bias(data.tail(3))
        b1h = get_bias(data.tail(12))
        b4h = get_bias(data.tail(48))

        if not all([b15, b1h, b4h]):
            return prev

        return {
            "bias": {"4H": b4h, "1H": b1h, "15M": b15},
            "message": get_bias_message(b4h, b1h, b15)
        }

    except:
        return prev

# ---------------- MAIN ---------------- #

def update_dashboard():
    nifty = build_nifty()
    global_data = build_global()
    breadth = build_breadth()
    bias = build_bias()

    save_json("nifty", nifty)
    save_json("global_meter", global_data)
    save_json("nifty_breadth", breadth)
    save_json("nifty_bias", bias)

    print(f"Updated at {datetime.now().strftime('%H:%M:%S')}")

# ---------------- RUN ---------------- #

if __name__ == "__main__":
    update_dashboard()
