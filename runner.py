import yfinance as yf
import json
import os
import time
from datetime import datetime
import pytz

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Locked Weights and Timezones [cite: 41, 195]
GLOBAL_MARKETS = {
    "DowF":   {"symbol": "YM=F",    "weight": 0.35, "tz": "America/New_York"},
    "DAX":    {"symbol": "^GDAXI",  "weight": 0.25, "tz": "Europe/Berlin"},
    "Nikkei": {"symbol": "^N225",   "weight": 0.25, "tz": "Asia/Tokyo"},
    "HSI":    {"symbol": "^HSI",    "weight": 0.15, "tz": "Asia/Hong_Kong"},
}

SECTORS = {
    "BANK": "^NSEBANK", "FIN": "^CNXFIN", "IT": "^CNXIT", "METAL": "^CNXMETAL", "FMCG": "^CNXFMCG"
}

def is_market_open(tz_name):
    now = datetime.now(pytz.timezone(tz_name))
    # Open Mon-Fri, approx 9:00 to 17:00 local time
    return "OPEN" if (now.weekday() < 5 and 9 <= now.hour < 17) else "CLOSED"

def load_json(name):
    try:
        with open(f"{DATA_DIR}/{name}.json", "r") as f: return json.load(f)
    except: return None

def write_json(name, obj):
    with open(f"{DATA_DIR}/{name}.json", "w") as f: json.dump(obj, f, indent=2)

def fetch_data(symbol):
    try:
        df = yf.download(symbol, period="5d", interval="5m", progress=False)
        if df.empty: return []
        c = df["Close"]
        return c.iloc[:, 0].dropna().tolist() if hasattr(c, "columns") else c.dropna().tolist()
    except: return []

# --- 1. NIFTY LIVE [cite: 251] ---
def get_nifty():
    cl = fetch_data("^NSEI")
    if not cl: return load_json("nifty")
    last, prev = cl[-1], cl[-2]
    return {
        "price": round(last, 2),
        "change": round(last - prev, 2),
        "percent": round(((last - prev) / prev) * 100, 2),
        "market": "LIVE" if (9 <= datetime.now(pytz.timezone("Asia/Kolkata")).hour < 16) else "CLOSED",
        "updated_ts": int(time.time())
    }

# --- 2. GLOBAL [cite: 165, 203] ---
def get_global():
    old = load_json("global_meter")
    indices = old["indices"] if old else {}
    total_score = 0
    for k, cfg in GLOBAL_MARKETS.items():
        cl = fetch_data(cfg["symbol"])
        pct = (round(((cl[-1]-cl[-6])/cl[-6])*100, 2)) if len(cl)>=6 else indices.get(k,{}).get("change_30m", 0)
        status = is_market_open(cfg["tz"])
        indices[k] = {"change_30m": pct, "status": status}
        mult = 1.0 if status == "OPEN" else 0.40 # Activity Multiplier [cite: 203]
        total_score += (1 if pct > 0 else -1 if pct < 0 else 0) * cfg["weight"] * mult
    return {"meter": max(0, min(10, round(5 + (total_score * 5)))), "indices": indices}

# --- 3. BREADTH [cite: 3, 41] ---
def get_breadth():
    weights = {"BANK": 0.35, "FIN": 0.25, "IT": 0.15, "METAL": 0.15, "FMCG": 0.10}
    old = load_json("nifty_breadth")
    sects = old["sectors"] if old else {}
    total = 0
    for s, w in weights.items():
        cl = fetch_data(SECTORS[s])
        pct = (round(((cl[-1]-cl[-6])/cl[-6])*100, 2)) if len(cl)>=6 else sects.get(s, 0)
        sects[s] = pct
        total += (1 if pct > 0 else -1 if pct < 0 else 0) * w
    return {"meter": max(0, min(10, round(5 + (total * 5)))), "sectors": sects}

# --- 4. BIAS [cite: 80, 90] ---
def get_bias():
    cl = fetch_data("^NSEI")
    if len(cl) < 240: return load_json("nifty_bias")
    b15, b1h, b4h = ("BULLISH" if cl[-1] > sum(cl[-n:])/n else "BEARISH" for n in (6, 48, 240))
    if b4h == b1h == b15: msg = f"{b4h.capitalize()} continuation"
    elif b4h == b1h: msg = f"Pullback within {b4h.lower()} structure"
    else: msg = "Structural conflict"
    return {"bias": {"4H": b4h, "1H": b1h, "15M": b15}, "message": msg}

if __name__ == "__main__":
    write_json("nifty", get_nifty()); write_json("global_meter", get_global())
    write_json("nifty_breadth", get_breadth()); write_json("nifty_bias", get_bias())
