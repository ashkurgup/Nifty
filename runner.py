import yfinance as yf
import json
import time
import os
from datetime import datetime
import pytz
import numpy as np

# ---------------- CONFIG & WEIGHTS ---------------- #

SECTOR_WEIGHTS = {'BANK': 0.35, 'FIN': 0.25, 'IT': 0.15, 'METAL': 0.15, 'FMCG': 0.10}
GLOBAL_WEIGHTS = {'DOW': 0.35, 'DAX': 0.25, 'NIKKEI': 0.25, 'HSI': 0.15}
ACTIVITY_MULTIPLIERS = {'OPEN': 1.00, 'RECENTLY_CLOSED': 0.75, 'CLOSED': 0.40}

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------------- UTILITIES ---------------- #

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

# ---------------- ANALYTICS ENGINE LOGIC ---------------- #

def get_candle_type(open_p, high, low, close):
    body = abs(close - open_p)
    full_range = high - low if high != low else 1
    upper_wick = high - max(open_p, close)
    lower_wick = min(open_p, close) - low
    is_green = close >= open_p
    color = "Green" if is_green else "Red"
    
    if body / full_range > 0.8: return f"Marubozu ({color})"
    if lower_wick > (body * 2) and upper_wick < (body * 0.5): return f"Hammer ({color})"
    if upper_wick > (body * 2) and lower_wick < (body * 0.5): return f"Inverted Hammer ({color})"
    if body < (full_range * 0.1): return f"Doji ({color})"
    if upper_wick > body and lower_wick > body: return f"Spinning Top ({color})"
    return f"Standard ({color})"

def build_analytics(df_1h):
    """Processes last 12 candles for Persistence Analytics Box"""
    if len(df_1h) < 12:
        return {"major": "--", "stats": "Awaiting Session Data...", "event": "Standby"}
    
    # 1. Major Candle Analysis
    bodies = (df_1h['Close'] - df_1h['Open']).abs()
    major_idx = bodies.idxmax()
    major_row = df_1h.loc[major_idx]
    major_size = round(bodies.max(), 2)
    major_type = get_candle_type(major_row['Open'], major_row['High'], major_row['Low'], major_row['Close'])
    major_time = major_idx.strftime('%I:%M %p')

    # 2. Next Candle logic (Support/Opposing)
    try:
        next_idx_pos = df_1h.index.get_loc(major_idx) + 1
        next_row = df_1h.iloc[next_idx_pos]
        next_color = "Green" if next_row['Close'] >= next_row['Open'] else "Red"
        major_dir = major_row['Close'] >= major_row['Open']
        next_dir = next_row['Close'] >= next_row['Open']
        relationship = "Supporting" if major_dir == next_dir else "Opposing"
        next_logic = f"{relationship} ({next_color})"
    except:
        next_logic = "Developing"

    # 3. Last 30 Mins Stats (6 candles)
    last_30 = df_1h.tail(6)
    dist = round(last_30['Close'].iloc[-1] - last_30['Open'].iloc[0], 2)
    
    overlaps = 0
    small_candles = 0
    for i in range(1, len(last_30)):
        curr, prev = last_30.iloc[i], last_30.iloc[i-1]
        # Overlap: 75% of body within previous range
        if max(curr['Open'], curr['Close']) <= prev['High'] and min(curr['Open'], curr['Close']) >= prev['Low']:
            overlaps += 1
        if abs(curr['Close'] - curr['Open']) < 10:
            small_candles += 1

    return {
        "major": f"Major Candle: {major_size} pts | {major_type} at {major_time} || Next: {next_logic}",
        "stats": f"Last 30 min | Dist: {dist} pts | Overlaps: {overlaps} | Small: {small_candles}",
        "event": "Expansion" if abs(dist) > 50 else "Range Bound"
    }

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

def get_30m_change(data):
    try:
        if len(data) < 6: return None
        start = data['Open'].iloc[-6]
        end = data['Close'].iloc[-1]
        return float(((end - start) / start) * 100)
    except:
        return None

# ---------------- BUILDING PAYLOADS ---------------- #

def build_nifty():
    prev = load_json("nifty")
    try:
        data = yf.download("^NSEI", period="1d", interval="5m", progress=False)
        if data.empty: return prev
        
        last_candle_time = data.index[-1].timestamp()
        if time.time() - last_candle_time > 86400: return prev # Keep persistent for 24h
        
        price = float(data['Close'].iloc[-1])
        prev_close = float(data['Close'].iloc[0])

        return {
            "price": round(price, 2),
            "change": round(price - prev_close, 2),
            "percent": round(((price - prev_close) / prev_close) * 100, 2),
            "high": round(float(data['High'].max()), 2),
            "low": round(float(data['Low'].min()), 2),
            "market": "OPEN" if is_nse_open() else "CLOSED",
            "updated_ts": int(time.time())
        }
    except:
        return prev

def build_global():
    prev = load_json("global_meter")
    tickers = {'DOW': 'YM=F', 'DAX': '^GDAXI', 'NIKKEI': '^N225', 'HSI': '^HSI'}
    indices, score, valid_weight = {}, 0, 0

    for name, ticker in tickers.items():
        last_val = prev.get("indices", {}).get(name, {}).get("change_30m")
        try:
            data = yf.download(ticker, period="1d", interval="5m", progress=False)
            pct = get_30m_change(data)
            state = get_market_state(data)
            if not is_valid(pct): pct = last_val
        except:
            pct, state = last_val, "CLOSED"

        if is_valid(pct):
            score += (1 if pct > 0 else -1 if pct < 0 else 0) * GLOBAL_WEIGHTS[name] * ACTIVITY_MULTIPLIERS[state]
            valid_weight += GLOBAL_WEIGHTS[name]
        indices[name] = {"change_30m": round(pct, 2) if is_valid(pct) else 0, "status": state}

    meter = round(5 + (score * 5), 1) if valid_weight > 0 else prev.get("meter", 5)
    return {"meter": meter, "indices": indices}

def build_breadth():
    prev = load_json("nifty_breadth")
    tickers = {'BANK': '^NSEBANK', 'FIN': 'NIFTY_FIN_SERVICE.NS', 'IT': '^CNXIT', 'METAL': '^CNXMETAL', 'FMCG': '^CNXFMCG'}
    sectors, score, valid_weight = {}, 0, 0

    for name, ticker in tickers.items():
        last_val = prev.get("sectors", {}).get(name)
        try:
            data = yf.download(ticker, period="1d", interval="5m", progress=False)
            pct = get_30m_change(data)
            if not is_valid(pct): pct = last_val
        except:
            pct = last_val

        if is_valid(pct):
            score += (1 if pct > 0 else -1 if pct < 0 else 0) * SECTOR_WEIGHTS[name]
            valid_weight += SECTOR_WEIGHTS[name]
        sectors[name] = round(pct, 2) if is_valid(pct) else 0

    meter = round(5 + ((score/valid_weight) * 5), 1) if valid_weight > 0 else prev.get("meter", 5)
    return {"meter": meter, "sectors": sectors}

def update_dashboard():
    # Fetch 1 day of data for main calcs and analytics
    nifty_df = yf.download("^NSEI", period="1d", interval="5m", progress=False)
    
    nifty = build_nifty()
    global_data = build_global()
    breadth = build_breadth()
    analytics = build_analytics(nifty_df)

    save_json("nifty", nifty)
    save_json("global_meter", global_data)
    save_json("nifty_breadth", breadth)
    save_json("analytics", analytics)

    print(f"Updated Dashboard & Analytics at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    update_dashboard()
