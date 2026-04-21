import yfinance as yf
import json
import os
import time

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# --- CONFIGURATION (LOCKED WEIGHTS) ---
GLOBAL_MARKETS = {
    "DowF":   {"symbol": "YM=F",    "weight": 0.35},
    "DAX":    {"symbol": "^GDAXI",  "weight": 0.25},
    "Nikkei": {"symbol": "^N225",   "weight": 0.25},
    "HSI":    {"symbol": "^HSI",    "weight": 0.15},
}

SECTORS = {
    "BANK": {"symbol": "^NSEBANK",  "weight": 0.35},
    "FIN":  {"symbol": "^CNXFIN",   "weight": 0.25},
    "IT":   {"symbol": "^CNXIT",    "weight": 0.15},
    "METAL":{"symbol": "^CNXMETAL", "weight": 0.15},
    "FMCG": {"symbol": "^CNXFMCG",  "weight": 0.10}
}

def get_now():
    return int(time.time())

def load_old_data(name):
    path = f"{DATA_DIR}/{name}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def write_data(name, obj):
    with open(f"{DATA_DIR}/{name}.json", "w") as f:
        json.dump(obj, f, indent=2)

def fetch_closes(symbol, interval="5m", period="5d"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty: return []
        c = df["Close"]
        if hasattr(c, "columns"): c = c.iloc[:, 0]
        return c.dropna().tolist()
    except:
        return []

def rolling_30m_pct(cl):
    if len(cl) < 6: return None
    return round(((cl[-1] - cl[-6]) / cl[-6]) * 100, 2)

# --- 1. NIFTY LIVE ---
def update_nifty():
    old = load_old_data("nifty")
    cl = fetch_closes("^NSEI")
    
    if not cl and old: return old
    
    ts = get_now()
    last, prev = cl[-1], cl[-2]
    # Simple market open check (Friday 3:30 PM IST is roughly 10:00 UTC)
    market_state = "LIVE" if (1 <= time.gmtime().tm_wday <= 5) else "CLOSED"

    return {
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round(((last - prev) / prev) * 100, 2),
        "market": market_state,
        "updated_ts": ts
    }

# --- 2. GLOBAL METER (ACTIVITY ADJUSTED) ---
def update_global():
    old = load_old_data("global_meter")
    indices = old["indices"] if old else {}
    total_weighted_score = 0
    
    for k, cfg in GLOBAL_MARKETS.items():
        cl = fetch_closes(cfg["symbol"])
        pct = rolling_30m_pct(cl)
        
        # Use persistence if fetch fails
        current_pct = pct if pct is not None else indices.get(k, {}).get("change_30m", 0)
        indices[k] = {"change_30m": current_pct}
        
        # Activity Adjustment (Simulated: Defaulting to OPEN for this logic) [cite: 203]
        multiplier = 1.0 
        score = (1 if current_pct > 0 else -1 if current_pct < 0 else 0)
        total_weighted_score += (score * cfg["weight"] * multiplier)

    meter = max(0, min(10, round(5 + (total_weighted_score * 5))))
    return {"meter": meter, "indices": indices, "updated_ts": get_now()}

# --- 3. BREADTH (SECTOR WEIGHTED) ---
def update_breadth():
    old = load_old_data("nifty_breadth")
    sectors_data = old["sectors"] if old else {}
    total_weighted_score = 0

    for name, cfg in SECTORS.items():
        cl = fetch_closes(cfg["symbol"])
        pct = rolling_30m_pct(cl)
        
        current_pct = pct if pct is not None else sectors_data.get(name, 0)
        sectors_data[name] = current_pct
        
        score = (1 if current_pct > 0 else -1 if current_pct < 0 else 0)
        total_weighted_score += (score * cfg["weight"])

    meter = max(0, min(10, round(5 + (total_weighted_score * 5))))
    return {"meter": meter, "sectors": sectors_data, "updated_ts": get_now()}

# --- 4. BIAS (MESSAGING LAYER) ---
def update_bias():
    cl = fetch_closes("^NSEI", interval="5m", period="30d")
    if len(cl) < 240: # Need enough for 4H
        old = load_old_data("nifty_bias")
        return old if old else {"bias": {}, "message": "Initializing...", "updated_ts": get_now()}

    # Bias Logic [cite: 86, 87, 88, 89]
    b15m = "BULLISH" if cl[-1] > sum(cl[-6:])/6 else "BEARISH"
    b1h = "BULLISH" if cl[-1] > sum(cl[-48:])/48 else "BEARISH"
    b4h = "BULLISH" if cl[-1] > sum(cl[-240:])/240 else "BEARISH"

    if b4h == b1h == b15m:
        msg = f"{b4h.capitalize()} continuation" [cite: 91, 99]
    elif b4h == b1h:
        msg = f"Pullback within {b4h.lower()} structure" [cite: 107, 116]
    else:
        msg = "Structural conflict" [cite: 124]

    return {
        "bias": {"4H": b4h, "1H": b1h, "15M": b15m},
        "message": msg,
        "updated_ts": get_now()
    }

if __name__ == "__main__":
    write_data("nifty", update_nifty())
    write_data("global_meter", update_global())
    write_data("nifty_breadth", update_breadth())
    write_data("nifty_bias", update_bias())
