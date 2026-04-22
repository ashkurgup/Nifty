import yfinance as yf
import pandas as pd
import json
import time
import os

# --- TICKER CONFIGURATION ---
# Nifty 50 and Sectoral Indices (NSE Symbols)
NIFTY_TICKER = "^NSEI"
SECTOR_TICKERS = {
    'BANK': '^NSEBANK', 
    'FIN': 'NIFTY_FIN_SERVICE.NS', 
    'IT': '^CNXIT', 
    'METAL': '^CNXMETAL', 
    'FMCG': '^CNXFMCG'
}

# Global Indices
GLOBAL_TICKERS = {
    'DOW': 'YM=F',    # Dow Futures
    'DAX': '^GDAXI',  # DAX Performance Index
    'NIKKEI': '^N225', # Nikkei 225
    'HSI': '^HSI'     # Hang Seng Index
}

# --- WEIGHTS & MULTIPLIERS ---
SECTOR_WEIGHTS = {'BANK': 0.35, 'FIN': 0.25, 'IT': 0.15, 'METAL': 0.15, 'FMCG': 0.10}
GLOBAL_WEIGHTS = {'DOW': 0.35, 'DAX': 0.25, 'NIKKEI': 0.25, 'HSI': 0.15}
ACTIVITY_MULTIPLIERS = {'OPEN': 1.0, 'RECENTLY_CLOSED': 0.75, 'CLOSED': 0.40}

def get_30m_rolling_change(ticker_symbol):
    """Fetches last 6 of 5m candles to calculate 30m rolling change"""
    try:
        data = yf.download(ticker_symbol, period="1d", interval="5m", progress=False)
        if len(data) < 6: return 0.0
        # Formula: ((Last Close - Open 6 candles ago) / Open 6 candles ago) * 100
        start_val = data['Open'].iloc[-6]
        end_val = data['Close'].iloc[-1]
        return float(((end_val - start_val) / start_val) * 100)
    except:
        return 0.0

def get_bias_message(b4h, b1h, b15m):
    if b4h != b1h: return "Higher timeframes disagree — the market is transitioning."
    if b4h == "BULLISH":
        return "The trend is intact and aligned across all timeframes." if b15m == "BULLISH" else "The broader trend is up, but price is digesting gains."
    if b4h == "BEARISH":
        return "Downtrend is structured and orderly." if b15m == "BEARISH" else "A bounce is occurring inside a broader downtrend."
    return "Insufficient data for reliable structure."

def update_dashboard():
    # 1. NIFTY LIVE DATA
    nifty = yf.Ticker(NIFTY_TICKER)
    n_hist = nifty.history(period="1d")
    current_price = n_hist['Close'].iloc[-1]
    prev_close = nifty.info.get('previousClose', current_price)
    
    nifty_data = {
        "price": round(float(current_price), 2),
        "change": round(float(current_price - prev_close), 2),
        "percent": round(float(((current_price - prev_close) / prev_close) * 100), 2),
        "high": round(float(n_hist['High'].max()), 2),
        "low": round(float(n_hist['Low'].min()), 2),
        "market": "OPEN" if time.strftime("%H%M") < "1530" and time.strftime("%H%M") > "0915" else "CLOSED",
        "updated_ts": int(time.time())
    }

    # 2. BREADTH (Weighted 30m Rolling)
    sector_data = {}
    weighted_p = 0
    for s, ticker in SECTOR_TICKERS.items():
        pct = get_30m_rolling_change(ticker)
        sector_data[s] = round(pct, 2)
        if pct > 0: weighted_p += SECTOR_WEIGHTS[s]
        elif pct < 0: weighted_p -= SECTOR_WEIGHTS[s]
    breadth_meter = 5 + (weighted_p * 5)

    # 3. GLOBAL (Activity Adjusted)
    g_indices = {}
    g_score = 0
    for m, ticker in GLOBAL_TICKERS.items():
        pct = get_30m_rolling_change(ticker)
        # Simplified state logic: Assume DAX/DOW open in afternoon IST
        state = "OPEN" if time.strftime("%H") >= "13" else "CLOSED"
        mult = ACTIVITY_MULTIPLIERS[state]
        g_score += (1 if pct > 0 else -1 if pct < 0 else 0) * GLOBAL_WEIGHTS[m] * mult
        g_indices[m] = {"change_30m": round(pct, 2), "status": state}
    global_meter = 5 + (g_score * 5)

    # 4. STRUCTURAL BIAS (Placeholder for logic)
    bias_data = {
        "bias": {"4H": "BULLISH", "1H": "BULLISH", "15M": "BEARISH"},
        "message": get_bias_message("BULLISH", "BULLISH", "BEARISH")
    }

    # Save Files
    if not os.path.exists('data'): os.makedirs('data')
    for name, payload in [("nifty", nifty_data), ("nifty_breadth", {"meter": breadth_meter, "sectors": sector_data}), 
                         ("global_meter", {"meter": global_meter, "indices": g_indices}), ("nifty_bias", bias_data)]:
        with open(f'data/{name}.json', 'w') as f:
            json.dump(payload, f)
    print(f"Update Successful at {time.strftime('%H:%M:%S')}")

if __name__ == "__main__":
    update_dashboard()
