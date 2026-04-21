import yfinance as yf
import json
import os
import time
from datetime import datetime
import pytz

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Configuration with locked weights and shorthands [cite: 41, 195]
GLOBAL_MARKETS = {
    "DowF":   {"symbol": "YM=F",    "weight": 0.35, "tz": "America/New_York", "is_futures": True},
    "DAX":    {"symbol": "^GDAXI",  "weight": 0.25, "tz": "Europe/Berlin",    "is_futures": False},
    "Nikkei": {"symbol": "^N225",   "weight": 0.25, "tz": "Asia/Tokyo",       "is_futures": False},
    "HSI":    {"symbol": "^HSI",    "weight": 0.15, "tz": "Asia/Hong_Kong",   "is_futures": False},
}

SECTORS = {
    "BNK": {"symbol": "^NSEBANK",  "weight": 0.35},
    "FIN": {"symbol": "^CNXFIN",   "weight": 0.25},
    "IT":  {"symbol": "^CNXIT",    "weight": 0.15},
    "MET": {"symbol": "^CNXMETAL", "weight": 0.15},
    "FM":  {"symbol": "^CNXFMCG",  "weight": 0.10}
}

def is_market_open(tz_name, is_futures):
    now = datetime.now(pytz.timezone(tz_name))
    # Dow Futures (YM=F) specific logic [cite: 203]
    if is_futures: 
        return "OPEN" if now.weekday() < 5 or (now.weekday() == 6 and now.hour >= 18) else "CLOSED"
    return "OPEN" if (now.weekday() < 5 and 9 <= now.hour < 17) else "CLOSED"

def fetch_data(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        c = df["Close"]
        return c.iloc[:, 0].dropna().tolist() if hasattr(c, "columns") else c.dropna().tolist()
    except: return []

def write_json(name, obj):
    with open(f"{DATA_DIR}/{name}.json", "w") as f:
        json.dump(obj, f, indent=2)

def update_nifty():
    cl = fetch_data("^NSEI")
    return {
        "price": round(cl[-1], 2) if cl else 0,
        "change": round(cl[-1] - cl[-2], 2) if len(cl) > 1 else 0,
        "percent": round(((cl[-1] - cl[-2]) / cl[-2]) * 100, 2) if len(cl) > 1 else 0,
        "market": "CLOSED", # Persistent Snapshot state [cite: 265, 276]
        "updated_ts": int(time.time())
    }

def update_global():
    total_score = 0
    indices = {}
    for k, cfg in GLOBAL_MARKETS.items():
        cl = fetch_data(cfg["symbol"])
        pct = round(((cl[-1]-cl[-6])/cl[-6])*100, 2) if len(cl)>=6 else 0
        status = is_market_open(cfg["tz"], cfg["is_futures"])
        indices[k] = {"change_30m": pct, "status": status}
        # Activity adjustment for meter only [cite: 201, 203]
        mult = 1.0 if status == "OPEN" else 0.40 
        total_score += (1 if pct > 0 else -1 if pct < 0 else 0) * cfg["weight"] * mult
    return {"meter": max(0, min(10, round(5 + (total_score * 5)))), "indices": indices}

def update_breadth():
    total_score = 0
    sects = {}
    for name, cfg in SECTORS.items():
        cl = fetch_data(cfg["symbol"])
        pct = round(((cl[-1]-cl[-6])/cl[-6])*100, 2) if len(cl)>=6 else 0
        sects[name] = pct
        total_score += (1 if pct > 0 else -1 if pct < 0 else 0) * cfg["weight"] # [cite: 30, 41]
    return {"meter": max(0, min(10, round(5 + (total_score * 5)))), "sectors": sects}

def update_bias():
    cl = fetch_data("^NSEI")
    if len(cl) < 240: return {"bias": {}, "message": "Insufficient Data"}
    # Standard technical definitions [cite: 87, 88, 89]
    b15, b1h, b4h = ("BULLISH" if cl[-1] > sum(cl[-n:])/n else "BEARISH" for n in (6, 48, 240))
    # Human interactive logic [cite: 91, 107, 125]
    if b4h == b1h == b15: msg = "Bullish continuation"
    elif b4h == b1h: msg = f"Pullback within {b4h.lower()} structure"
    else: msg = "Structural conflict"
    return {"bias": {"4H": b4h, "1H": b1h, "15M": b15}, "message": msg}

if __name__ == "__main__":
    write_json("nifty", update_nifty()); write_json("global_meter", update_global())
    write_json("nifty_breadth", update_breadth()); write_json("nifty_bias", update_bias())
