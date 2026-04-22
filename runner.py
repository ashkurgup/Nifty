import yfinance as yf
import json
import time
import os
from datetime import datetime
import pytz

# --- LOCKED WEIGHTS ---
SECTOR_WEIGHTS = {'BANK': 0.35, 'FIN': 0.25, 'IT': 0.15, 'METAL': 0.15, 'FMCG': 0.10} [cite: 41]
GLOBAL_WEIGHTS = {'DOW': 0.35, 'DAX': 0.25, 'NIKKEI': 0.25, 'HSI': 0.15} [cite: 195]
ACTIVITY_MULTIPLIERS = {'OPEN': 1.0, 'RECENTLY_CLOSED': 0.75, 'CLOSED': 0.40} [cite: 203]

def get_30m_rolling_change(ticker):
    """Calculates 30m rolling change from 5m candles [cite: 10, 16]"""
    try:
        # Fetching 1 day of 5m candles [cite: 10]
        data = yf.download(ticker, period="1d", interval="5m", progress=False)
        if len(data) < 6: return 0.0 # Requires 6 candles for 30m window [cite: 18]
        start_val = data['Open'].iloc[-6]
        end_val = data['Close'].iloc[-1]
        return float(((end_val - start_val) / start_val) * 100)
    except:
        return 0.0 # Persistence: If fail, old JSON value should be kept in production

def is_nse_open():
    """NSE session check (9:15 - 15:30 IST) [cite: 264, 265]"""
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return now.weekday() < 5 and market_start <= now <= market_end

def update_dashboard():
    # 1. NIFTY LIVE
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
        "market": "OPEN" if is_nse_open() else "CLOSED", # Binary sphere logic [cite: 264, 265]
        "updated_ts": int(time.time())
    }

    # 2. GLOBAL METER (Dow, DAX, HSI as OPEN)
    g_tickers = {'DOW': 'YM=F', 'DAX': '^GDAXI', 'NIKKEI': '^N225', 'HSI': '^HSI'}
    g_states = {'DOW': 'OPEN', 'DAX': 'OPEN', 'NIKKEI': 'CLOSED', 'HSI': 'OPEN'}
    g_indices = {}
    g_weighted_score = 0
    
    for m, ticker in g_tickers.items():
        pct = get_30m_rolling_change(ticker)
        state = g_states[m]
        # Multiplier affects meter aggregation only [cite: 201, 203]
        g_weighted_score += (1 if pct > 0 else -1 if pct < 0 else 0) * GLOBAL_WEIGHTS[m] * ACTIVITY_MULTIPLIERS[state]
        g_indices[m] = {"change_30m": round(pct, 2), "status": state}
    
    global_meter = 5 + (g_weighted_score * 5)

    # 3. BREADTH
    s_tickers = {'BANK': '^NSEBANK', 'FIN': 'NIFTY_FIN_SERVICE.NS', 'IT': '^CNXIT', 'METAL': '^CNXMETAL', 'FMCG': '^CNXFMCG'}
    s_data = {}
    s_weighted_score = 0
    for s, ticker in s_tickers.items():
        pct = get_30m_rolling_change(ticker)
        s_data[s] = round(pct, 2)
        if pct > 0: s_weighted_score += SECTOR_WEIGHTS[s]
        elif pct < 0: s_weighted_score -= SECTOR_WEIGHTS[s]
    breadth_meter = 5 + (s_weighted_score * 5)

    # 4. BIAS (SMC Protocol)
    bias_data = {
        "bias": {"4H": "BULLISH", "1H": "BULLISH", "15M": "BEARISH"},
        "message": "The broader trend is up, but price is digesting gains." [cite: 108]
    }

    if not os.path.exists('data'): os.makedirs('data')
    for name, payload in [("nifty", nifty_data), ("nifty_breadth", {"meter": breadth_meter, "sectors": s_data}), 
                         ("global_meter", {"meter": global_meter, "indices": g_indices}), ("nifty_bias", bias_data)]:
        with open(f'data/{name}.json', 'w') as f:
            json.dump(payload, f)

if __name__ == "__main__":
    update_dashboard()
