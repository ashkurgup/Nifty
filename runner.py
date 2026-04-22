import json
import time
import os

# --- WEIGHTS & MULTIPLIERS ---
SECTOR_WEIGHTS = {'BANK': 0.35, 'FIN': 0.25, 'IT': 0.15, 'METAL': 0.15, 'FMCG': 0.10}
GLOBAL_WEIGHTS = {'DOW': 0.35, 'DAX': 0.25, 'NIKKEI': 0.25, 'HSI': 0.15}
ACTIVITY_MULTIPLIERS = {'OPEN': 1.0, 'RECENTLY_CLOSED': 0.75, 'CLOSED': 0.40}

def get_bias_message(b4h, b1h, b15m):
    if b4h != b1h: return "Higher timeframes disagree — the market is transitioning."
    if b4h == "BULLISH":
        return "The trend is intact and aligned across all timeframes." if b15m == "BULLISH" else "The broader trend is up, but price is digesting gains."
    if b4h == "BEARISH":
        return "Downtrend is structured and orderly." if b15m == "BEARISH" else "A bounce is occurring inside a broader downtrend."
    return "Insufficient data for reliable structure."

def update_dashboard():
    # 1. NIFTY LIVE
    nifty_data = {
        "price": 22450.20, "change": 45.10, "percent": 0.20,
        "high": 22510.50, "low": 22420.00,
        "market": "OPEN", "updated_ts": int(time.time())
    }

    # 2. BREADTH (Weighted 30m Rolling)
    # Using unique values per sector to ensure the meter calculates correctly
    sector_values = {'BANK': 0.45, 'FIN': 0.30, 'IT': -0.10, 'METAL': 0.05, 'FMCG': 0.12}
    weighted_p = sum((1 if v > 0 else -1 if v < 0 else 0) * SECTOR_WEIGHTS[s] for s, v in sector_values.items())
    
    # Breadth Meter scale 0-10 (5 is balanced)
    breadth_meter = 5 + (weighted_p * 5)

    # 3. GLOBAL (Activity Adjusted)
    g_vals = {'DOW': -0.05, 'DAX': 0.10, 'NIKKEI': -0.30, 'HSI': 0.05}
    g_states = {'DOW': 'CLOSED', 'DAX': 'OPEN', 'NIKKEI': 'CLOSED', 'HSI': 'OPEN'}
    
    g_score = 0
    g_indices = {}
    for m, w in GLOBAL_WEIGHTS.items():
        mult = ACTIVITY_MULTIPLIERS[g_states[m]]
        g_score += (1 if g_vals[m] > 0 else -1 if g_vals[m] < 0 else 0) * w * mult
        g_indices[m] = {"change_30m": g_vals[m], "status": g_states[m]}
    
    global_meter = 5 + (g_score * 5)

    # 4. BIAS
    bias_data = {
        "bias": {"4H": "BULLISH", "1H": "BULLISH", "15M": "BEARISH"},
        "message": get_bias_message("BULLISH", "BULLISH", "BEARISH")
    }

    # Save Files
    if not os.path.exists('data'): os.makedirs('data')
    files = [("nifty", nifty_data), ("nifty_breadth", {"meter": breadth_meter, "sectors": sector_values}), 
             ("global_meter", {"meter": global_meter, "indices": g_indices}), ("nifty_bias", bias_data)]
    
    for name, data in files:
        with open(f'data/{name}.json', 'w') as f:
            json.dump(data, f)

if __name__ == "__main__":
    update_dashboard()
