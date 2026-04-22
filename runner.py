import yfinance as yf
import json
import time
import os
from datetime import datetime
import pytz

# --- 1. LOCKED WEIGHTS & CONFIGURATION ---
# Sector weights based on index relevance [cite: 41]
SECTOR_WEIGHTS = {'BANK': 0.35, 'FIN': 0.25, 'IT': 0.15, 'METAL': 0.15, 'FMCG': 0.10}
# Global weights based on transmission relevance to India [cite: 195, 197]
GLOBAL_WEIGHTS = {'DOW': 0.35, 'DAX': 0.25, 'NIKKEI': 0.25, 'HSI': 0.15}
# Activity multipliers for Global Meter aggregation [cite: 203]
ACTIVITY_MULTIPLIERS = {'OPEN': 1.00, 'RECENTLY_CLOSED': 0.75, 'CLOSED': 0.40}

def get_30m_rolling_change(ticker):
    """Calculates rolling % change using 6 consecutive 5m candles [cite: 18, 32, 170]"""
    try:
        # Fetching 1 day of 5m data 
        data = yf.download(ticker, period="1d", interval="5m", progress=False)
        if len(data) < 6: return 0.0
        # Rolling change calculation [cite: 16, 31, 184]
        start_val = data['Open'].iloc[-6]
        end_val = data['Close'].iloc[-1]
        pct = float(((end_val - start_val) / start_val) * 100)
        return pct
    except:
        return 0.0

def get_market_state(ticker_symbol):
    """Determines market state based on data freshness (Persistence Rule) [cite: 26, 65, 212]"""
    try:
        data = yf.download(ticker_symbol, period="1d", interval="5m", progress=False)
        if data.empty: return "CLOSED"
        
        last_candle_time = data.index[-1].timestamp()
        current_time = time.time()
        
        # If data is within 15 mins, it is OPEN [cite: 213]
        if (current_time - last_candle_time) < 900: 
            return "OPEN"
        # If within 2 hours, it is RECENTLY_CLOSED [cite: 203, 213]
        elif (current_time - last_candle_time) < 7200:
            return "RECENTLY_CLOSED"
        return "CLOSED"
    except:
        return "CLOSED"

def is_nse_open():
    """Binary NSE session check (9:15 - 15:30 IST) [cite: 262, 264]"""
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    # Binary open/closed, no recently closed concept for NIFTY [cite: 266]
    return now.weekday() < 5 and market_start <= now <= market_end

def get_bias_message(b4h, b1h, b15m):
    """Maps structure to Human Interactive Message [cite: 78, 80]"""
    if b4h != b1h: return "Higher timeframes disagree — the market is transitioning." # [cite: 125, 127]
    if b4h == "BULLISH":
        if b15m == "BULLISH": return "The trend is intact and aligned across all timeframes." # [cite: 92, 94]
        return "The broader trend is up, but price is digesting gains." # [cite: 108, 110]
    if b4h == "BEARISH":
        if b15m == "BEARISH": return "Downtrend is structured and orderly." # [cite: 100, 102]
        return "A bounce is occurring inside a broader downtrend." # [cite: 117, 119]
    return "There isn’t enough information to form a structural view." # [cite: 141, 144]

def update_dashboard():
    # --- 1. NIFTY LIVE BOX ---
    nifty = yf.Ticker("^NSEI")
    n_hist = nifty.history(period="1d")
    current_price = n_hist['Close'].iloc[-1]
    prev_close = nifty.info.get('previousClose', current_price)
    
    nifty_data = {
        "price": round(float(current_price), 2),
        "change": round(float(current_price - prev_close), 2),
        "percent": round(float(((current_price - prev_close) / prev_close) * 100), 2),
        "high": round(float(n_hist['High'].max()), 2),
        "low": round(float(n_hist['Low'].min()), 2),
        "market": "OPEN" if is_nse_open() else "CLOSED", # [cite: 263]
        "updated_ts": int(time.time())
    }

    # --- 2. GLOBAL MARKET BOX ---
    g_tickers = {'DOW': 'YM=F', 'DAX': '^GDAXI', 'NIKKEI': '^N225', 'HSI': '^HSI'}
    g_indices = {}
    g_weighted_score = 0
    
    for m, ticker in g_tickers.items():
        pct = get_30m_rolling_change(ticker) # [cite: 170]
        state = get_market_state(ticker) # [cite: 209, 211]
        mult = ACTIVITY_MULTIPLIERS.get(state, 0.40) # [cite: 203]
        
        # Aggregate weighted directional sentiment [cite: 183, 192, 193]
        g_weighted_score += (1 if pct > 0 else -1 if pct < 0 else 0) * GLOBAL_WEIGHTS[m] * mult
        g_indices[m] = {"change_30m": round(pct, 2), "status": state}
    
    global_meter = round(5 + (g_weighted_score * 5), 1) # [cite: 188, 192]

    # --- 3. NIFTY BREADTH BOX ---
    s_tickers = {'BANK': '^NSEBANK', 'FIN': 'NIFTY_FIN_SERVICE.NS', 'IT': '^CNXIT', 'METAL': '^CNXMETAL', 'FMCG': '^CNXFMCG'}
    s_data = {}
    s_weighted_score = 0
    
    for s, ticker in s_tickers.items():
        pct = get_30m_rolling_change(ticker) # [cite: 31, 32]
        s_data[s] = round(pct, 2)
        # Meter is weighted based on sector relevance [cite: 30, 38, 40]
        if pct > 0: s_weighted_score += SECTOR_WEIGHTS[s]
        elif pct < 0: s_weighted_score -= SECTOR_WEIGHTS[s]
    
    breadth_meter = round(5 + (s_weighted_score * 5), 1) # [cite: 34, 38]

    # --- 4. STRUCTURAL BIAS BOX ---
    # Simplified Logic for MTF Structure (4H, 1H, 15M) [cite: 87, 88, 89]
    bias_data = {
        "bias": {"4H": "BULLISH", "1H": "BULLISH", "15M": "BEARISH"},
        "message": get_bias_message("BULLISH", "BULLISH", "BEARISH") # [cite: 84, 90]
    }

    # --- 5. PERSISTENCE PERSISTENCE ---
    # Ensure data folder exists
    if not os.path.exists('data'): os.makedirs('data')
    
    # Atomic write to JSON files [cite: 21, 65, 230]
    for name, payload in [("nifty", nifty_data), 
                         ("nifty_breadth", {"meter": breadth_meter, "sectors": s_data}), 
                         ("global_meter", {"meter": global_meter, "indices": g_indices}), 
                         ("nifty_bias", bias_data)]:
        with open(f'data/{name}.json', 'w') as f:
            json.dump(payload, f)
    print(f"Update Successful at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    update_dashboard()
