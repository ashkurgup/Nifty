import yfinance as yf
import json
import os
import time
from datetime import datetime
import pytz

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# --- CONFIGURATION DICTIONARIES (The missing part) ---
GLOBAL_MARKETS = {
    "DowF": {"symbol": "YM=F", "tz": "America/New_York", "is_futures": True, "weight": 0.4},
    "DAX": {"symbol": "^GDAXI", "tz": "Europe/Berlin", "is_futures": False, "weight": 0.2},
    "Nikkei": {"symbol": "^N225", "tz": "Asia/Tokyo", "is_futures": False, "weight": 0.2},
    "HSI": {"symbol": "^HSI", "tz": "Asia/Hong_Kong", "is_futures": False, "weight": 0.2}
}

SECTORS = {
    "BNK": {"symbol": "^NSEBANK", "weight": 0.4},
    "IT": {"symbol": "^CNXIT", "weight": 0.2},
    "MET": {"symbol": "^CNXMETAL", "weight": 0.15},
    "FIN": {"symbol": "NIFTY_FIN_SERVICE.NS", "weight": 0.15},
    "FM": {"symbol": "^CNXFMCG", "weight": 0.1}
}

def is_market_open(tz_name, is_futures):
    now = datetime.now(pytz.timezone(tz_name))
    if is_futures: 
        # Futures: Open Sun 6pm - Fri 5pm ET (approx)
        return "OPEN" if now.weekday() < 5 or (now.weekday() == 6 and now.hour >= 18) else "CLOSED"
    return "OPEN" if (now.weekday() < 5 and 9 <= now.hour < 17) else "CLOSED"

def fetch_data(symbol, period="5d", interval="5m"):
    try:
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        if df.empty: return []
        c = df["Close"]
        # Handle multi-index columns if they exist
        data = c.iloc[:, 0].dropna().tolist() if hasattr(c, "columns") else c.dropna().tolist()
        return data
    except: return []

def write_json(name, obj):
    with open(f"{DATA_DIR}/{name}.json", "w") as f:
        json.dump(obj, f, indent=2)

def update_nifty():
    # Fetching 1d data specifically to get today's accurate High and Low
    ticker = yf.Ticker("^NSEI")
    info = ticker.history(period="1d")
    
    cl = fetch_data("^NSEI")
    
    # Logic for Market Status (IST)
    ist = datetime.now(pytz.timezone("Asia/Kolkata"))
    is_live = "LIVE" if (ist.weekday() < 5 and (9*60+15) <= (ist.hour*60+ist.minute) <= (15*60+30)) else "CLOSED"

    return {
        "price": round(cl[-1], 2) if cl else 0,
        "high": round(info['High'].iloc[-1], 2) if not info.empty else 0,
        "low": round(info['Low'].iloc[-1], 2) if not info.empty else 0,
        "change": round(cl[-1] - cl[-2], 2) if len(cl) > 1 else 0,
        "percent": round(((cl[-1] - cl[-2]) / cl[-2]) * 100, 2) if len(cl) > 1 else 0,
        "market": is_live,
        "updated_ts": int(time.time())
    }

def update_global():
    total_score = 0
    indices = {}
    for k, cfg in GLOBAL_MARKETS.items():
        cl = fetch_data(cfg["symbol"])
        if not cl: continue
        pct = round(((cl[-1]-cl[-6])/cl[-6])*100, 2) if len(cl)>=6 else 0
        status = is_market_open(cfg["tz"], cfg["is_futures"])
        indices[k] = {"change_30m": pct, "status": status}
        mult = 1.0 if status == "OPEN" else 0.40 
        total_score += (1 if pct > 0 else -1 if pct < 0 else 0) * cfg["weight"] * mult
    return {"meter": max(0, min(10, round(5 + (total_score * 5)))), "indices": indices}

def update_breadth():
    total_score = 0
    sects = {}
    for name, cfg in SECTORS.items():
        cl = fetch_data(cfg["symbol"])
        if not cl: continue
        pct = round(((cl[-1]-cl[-6])/cl[-6])*100, 2) if len(cl)>=6 else 0
        sects[name] = pct
        total_score += (1 if pct > 0 else -1 if pct < 0 else 0) * cfg["weight"]
    return {"meter": max(0, min(10, round(5 + (total_score * 5)))), "sectors": sects}

def update_bias():
    cl = fetch_data("^NSEI", period="10d", interval="1h")
    # Bias needs enough data points for 240 period (approx 10 trading days of 1H)
    if len(cl) < 50: return {"bias": {"4H": "--", "1H": "--", "15M": "--"}, "message": "Updating..."}
    
    # Logic: compare price to moving average of n periods
    b15, b1h, b4h = ("BULLISH" if cl[-1] > sum(cl[-n:])/n else "BEARISH" for n in (6, 24, 48))
    
    if b4h == b1h == b15: msg = "Strong trend"
    elif b4h == b1h: msg = f"Healthy {b4h.lower()}"
    else: msg = "Consolidation"
    
    return {"bias": {"4H": b4h, "1H": b1h, "15M": b15}, "message": msg}

def update_strategy():
    cl = fetch_data("^NSEI", period="10d", interval="1h")
    if not cl: return {"sup": 0, "res": 0}
    return {
        "sup": int(min(cl[-50:])),
        "res": int(max(cl[-50:]))
    }

if __name__ == "__main__":
    write_json("nifty", update_nifty())
    write_json("global_meter", update_global())
    write_json("nifty_breadth", update_breadth())
    write_json("nifty_bias", update_bias())
    write_json("strategy", update_strategy())
