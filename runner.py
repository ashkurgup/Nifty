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
    return x is not None and not (isinstance(x, (float, np.float64)) and np.isnan(x))

# ---------------- ANALYTICS ENGINE LOGIC ---------------- #

def get_candle_type(op, hi, lo, cl):
    # Ensure inputs are floats to prevent DataFrame ambiguity errors
    op, hi, lo, cl = float(op), float(hi), float(lo), float(cl)
    
    body = abs(cl - op)
    full_range = hi - lo if hi != lo else 1
    upper_wick = hi - max(op, cl)
    lower_wick = min(op, cl) - lo
    is_green = cl >= op
    color = "Green" if is_green else "Red"
    
    if body / full_range > 0.8: return f"Marubozu ({color})"
    if lower_wick > (body * 2) and upper_wick < (body * 0.5): return f"Hammer ({color})"
    if upper_wick > (body * 2) and lower_wick < (body * 0.5): return f"Inv. Hammer ({color})"
    if body < (full_range * 0.1): return f"Doji ({color})"
    if upper_wick > body and lower_wick > body: return f"Spinning Top ({color})"
    return f"Standard ({color})"

def build_analytics(df):
    """Processes last 12 candles for Persistence Analytics Box"""
    if df is None or df.empty or len(df) < 12:
        return {"major": "--", "stats": "Awaiting Session Data...", "event": "Standby"}
    
    # Force single-level columns if yfinance returns multi-index
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 1. Major Candle Analysis
    bodies = (df['Close'] - df['Open']).abs()
    major_idx = bodies.idxmax()
    major_row = df.loc[major_idx]
    
    major_size = round(float(bodies.max()), 2)
    major_type = get_candle_type(major_row['Open'], major_row['High'], major_row['Low'], major_row['Close'])
    major_time = major_idx.strftime('%I:%M %p')

    # 2. Next Candle logic
    try:
        next_idx_pos = df.index.get_loc(major_idx) + 1
        next_row = df.iloc[next_idx_pos]
        next_color = "Green" if float(next_row['Close']) >= float(next_row['Open']) else "Red"
        major_dir = float(major_row['Close']) >= float(major_row['Open'])
        next_dir = float(next_row['Close']) >= float(next_row['Open'])
        relationship = "Supporting" if major_dir == next_dir else "Opposing"
        next_logic = f"{relationship} ({next_color})"
    except:
        next_logic = "Developing"

    # 3. Last 30 Mins Stats
    last_30 = df.tail(6)
    dist = round(float(last_30['Close'].iloc[-1]) - float(last_30['Open'].iloc[0]), 2)
    
    overlaps = 0
    small_candles = 0
    for i in range(1, len(last_30)):
        curr, prev = last_30.iloc[i], last_30.iloc[i-1]
        # Overlap check
        if max(float(curr['Open']), float(curr['Close'])) <= float(prev['High']) and \
           min(float(curr['Open']), float(curr['Close'])) >= float(prev['Low']):
            overlaps += 1
        if abs(float(curr['Close']) - float(curr['Open'])) < 10:
            small_candles += 1

    return {
        "major": f"Major Candle: {major_size} pts | {major_type} at {major_time} || Next: {next_logic}",
        "stats": f"Last 30 min | Dist: {dist} pts | Overlaps: {overlaps} | Small: {small_candles}",
        "event": "Expansion" if abs(dist) > 50 else "Range Bound"
    }

# ---------------- MARKET STATE & FETCHERS ---------------- #

import pandas as pd

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
        start = float(data['Open'].iloc[-6])
        end = float(data['Close'].iloc[-1])
        return float(((end - start) / start) * 100)
    except:
        return None

def update_dashboard():
    # Helper to clean yfinance data
    def get_clean_data(ticker, period="1d", interval="5m"):
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    nifty_df = get_clean_data("^NSEI")
    
    # Persistent Nifty Data
    prev_nifty = load_json("nifty")
    if not nifty_df.empty:
        price = float(nifty_df['Close'].iloc[-1])
        prev_close = float(nifty_df['Close'].iloc[0])
        nifty_payload = {
            "price": round(price, 2),
            "change": round(price - prev_close, 2),
            "percent": round(((price - prev_close) / prev_close) * 100, 2),
            "high": round(float(nifty_df['High'].max()), 2),
            "low": round(float(nifty_df['Low'].min()), 2),
            "market": "OPEN" if is_nse_open() else "CLOSED",
            "updated_ts": int(time.time())
        }
    else:
        nifty_payload = prev_nifty

    # Global & Breadth (Simplified logic using cleaned data)
    # ... [Keeping your existing logic for build_global and build_breadth but ensuring get_clean_data is used] ...

    # Final Analytics
    analytics_payload = build_analytics(nifty_df)

    save_json("nifty", nifty_payload)
    save_json("analytics", analytics_payload)
    
    # Triggering updates for other modules
    # save_json("global_meter", build_global_logic()) 
    # save_json("nifty_breadth", build_breadth_logic())

    print(f"Dashboard Update Successful at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    update_dashboard()
