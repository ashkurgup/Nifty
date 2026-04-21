import yfinance as yf
import json
import os
import time
from datetime import datetime
import pytz

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Configuration with locked weights
GLOBAL_MARKETS = {
    "DowF":   {"symbol": "YM=F",    "weight": 0.35, "tz": "America/New_York"},
    "DAX":    {"symbol": "^GDAXI",  "weight": 0.25, "tz": "Europe/Berlin"},
    "Nikkei": {"symbol": "^N225",   "weight": 0.25, "tz": "Asia/Tokyo"},
    "HSI":    {"symbol": "^HSI",    "weight": 0.15, "tz": "Asia/Hong_Kong"},
}

SECTORS = {
    "BANK": {"symbol": "^NSEBANK",  "weight": 0.35},
    "FIN":  {"symbol": "^CNXFIN",   "weight": 0.25},
    "IT":   {"symbol": "^CNXIT",    "weight": 0.15},
    "METAL":{"symbol": "^CNXMETAL", "weight": 0.15},
    "FMCG": {"symbol": "^CNXFMCG",  "weight": 0.10}
}

def get_market_status(tz_name):
    """Determines if a market is OPEN based on timezone."""
    now = datetime.now(pytz.timezone(tz_name))
    if now.weekday() >= 5: return "CLOSED"
    # Simplified logic: Standard market hours 9:30-16:00
    if 9 <= now.hour < 17: return "OPEN"
    return "CLOSED"

def load_old_data(name):
    path = f"{DATA_DIR}/{name}.json"
    if os.path.exists(path):
        with open(path, "r") as f: return json.load(f)
    return None

def write_data(name, obj):
    with open(f"{DATA_DIR}/{name}.json", "w") as f: json.dump(obj, f, indent=2)

def fetch_closes(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        if df.empty: return []
        c = df["Close"]
        return c.iloc[:, 0].dropna().tolist() if hasattr(c, "columns") else c.dropna().tolist()
    except: return []

def rolling_30m_pct(cl):
    if len(cl) < 6: return None
    return round(((cl[-1] - cl[-6]) / cl[-6]) * 100, 2)

# --- Components ---
def update_nifty():
    old = load_old_data("nifty")
    cl = fetch_closes("^NSEI")
    if not cl and old: return old
    last, prev = cl[-1], cl[-2]
    return {
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round(((last - prev) / prev) * 100, 2),
        "market": "LIVE" if (9 <= datetime.now(pytz.timezone("Asia/Kolkata")).hour < 16) else "CLOSED",
        "updated_ts": int(time.time())
    }

def update_global():
    old = load_old_data("global_meter")
    indices = old["indices"] if old else {}
    total_weighted_score = 0
    
    for k, cfg in GLOBAL_MARKETS.items():
        cl = fetch_closes(cfg["symbol"])
        pct = rolling_30m_pct(cl)
        status = get_market_status(cfg["tz"])
        
        current_pct = pct if pct is not None else indices.get(k, {}).get("change_30m", 0)
        indices[k] = {"change_30m": current_pct, "status": status}
        
        # Apply Activity Multipliers [cite: 203]
        mult = 1.0 if status == "OPEN" else 0.40
        score = (1 if current_pct > 0 else -1 if current_pct < 0 else 0)
        total_weighted_score += (score * cfg["weight"] * mult)

    return {"meter": max(0, min(10, round(5 + (total_weighted_score * 5)))), "indices": indices}

def update_breadth():
    old = load_old_data("nifty_breadth")
    sectors_data = old["sectors"] if old else {}
    total_score = 0
    for name, cfg in SECTORS.items():
        cl = fetch_closes(cfg["symbol"])
        pct = rolling_30m_pct(cl)
        current_pct = pct if pct is not None else sectors_data.get(name, 0)
        sectors_data[name] = current_pct
        total_score += (1 if current_pct > 0 else -1 if current_pct < 0 else 0) * cfg["weight"]
    return {"meter": max(0, min(10, round(5 + (total_score * 5)))), "sectors": sectors_data}

def update_bias():
    cl = fetch_closes("^NSEI")
    if len(cl) < 240: return load_old_data("nifty_bias")
    b15, b1h, b4h = ("BULLISH" if cl[-1] > sum(cl[-n:])/n else "BEARISH" for n in (6, 48, 240))
    msg = f"{b4h.capitalize()} continuation" if b4h == b1h == b15 else f"Pullback within {b4h.lower()} structure" if b4h == b1h else "Structural conflict"
    return {"bias": {"4H": b4h, "1H": b1h, "15M": b15}, "message": msg}

if __name__ == "__main__":
    write_data("nifty", update_nifty()); write_data("global_meter", update_global())
    write_data("nifty_breadth", update_breadth()); write_data("nifty_bias", update_bias())
