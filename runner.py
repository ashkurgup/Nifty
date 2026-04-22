import json
import time
import os

# --- LOCKED SPECIFICATIONS ---
# Sector weights reflect index relevance [cite: 39, 40]
SECTOR_WEIGHTS = {'BANK': 0.35, 'FIN': 0.25, 'IT': 0.15, 'METAL': 0.15, 'FMCG': 0.10} 
GLOBAL_WEIGHTS = {'DOW': 0.35, 'DAX': 0.25, 'NIKKEI': 0.25, 'HSI': 0.15}
ACTIVITY_MULTIPLIERS = {'OPEN': 1.0, 'RECENTLY_CLOSED': 0.75, 'CLOSED': 0.40}

def get_bias_message(b4h, b1h, b15m):
    """Maps structure states to Human Interactive Messages [cite: 80, 90]"""
    if b4h != b1h: 
        return "Higher timeframes disagree — the market is transitioning."
    if b4h == "BULLISH":
        return "The trend is intact and aligned across all timeframes." if b15m == "BULLISH" else "The broader trend is up, but price is digesting gains."
    if b4h == "BEARISH":
        return "Downtrend is structured and orderly." if b15m == "BEARISH" else "A bounce is occurring inside a broader downtrend."
    return "There isn’t enough information to form a structural view."

def update_dashboard():
    # 1. NIFTY LIVE (5m Basis) [cite: 251, 257]
    nifty_data = {
        "price": 22450.20, "change": 45.10, "percent": 0.20,
        "market": "OPEN", "updated_ts": int(time.time())
    }

    # 2. BREADTH (30m Rolling, Weighted) [cite: 3, 16, 30]
    sector_data = {}
    weighted_participation = 0
    for s, w in SECTOR_WEIGHTS.items():
        pct = 0.50 # Placeholder for 30m rolling change based on 5m candles [cite: 10, 18]
        sector_data[s] = round(pct, 2)
        if pct > 0: weighted_participation += w
        elif pct < 0: weighted_participation -= w
    
    breadth_meter = 5 + (weighted_participation * 5)

    # 3. GLOBAL (Activity Adjusted) [cite: 165, 183, 202]
    global_indices = {}
    global_weighted_score = 0
    for m, w in GLOBAL_WEIGHTS.items():
        pct = -0.15 # Placeholder for 30m rolling value [cite: 170, 184]
        state = "OPEN" 
        global_weighted_score += (1 if pct > 0 else -1 if pct < 0 else 0) * w * ACTIVITY_MULTIPLIERS[state]
        global_indices[m] = {"change_30m": pct, "status": state}
    
    global_meter = 5 + (global_weighted_score * 5)

    # 4. BIAS (Structural Frame) [cite: 85, 86]
    bias_data = {
        "bias": {"4H": "BULLISH", "1H": "BULLISH", "15M": "BEARISH"},
        "message": get_bias_message("BULLISH", "BULLISH", "BEARISH")
    }

    # Save to JSON
    if not os.path.exists('data'): os.makedirs('data')
    for name, payload in [("nifty", nifty_data), ("nifty_breadth", {"meter": breadth_meter, "sectors": sector_data}), 
                         ("global_meter", {"meter": global_meter, "indices": global_indices}), ("nifty_bias", bias_data)]:
        with open(f'data/{name}.json', 'w') as f:
            json.dump(payload, f)

if __name__ == "__main__":
    update_dashboard()
