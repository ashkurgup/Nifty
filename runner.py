import json
import time
from datetime import datetime
import random

DATA_FILE = "data.json"
INTERVAL = 300  # 5 minutes

def fetch_market_data():
    """
    Replace this with real logic later:
    - Broker API
    - NSE data
    - Websocket
    """
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "nifty_live": round(random.uniform(22000, 23500), 2),
        "bias": random.choice(["Bullish", "Bearish", "Sideways"]),
        "gap": random.choice(["Gap Up", "Gap Down", "Flat"]),
        "market_open": random.choice(["Strong", "Weak", "Neutral"]),
        "vwap": round(random.uniform(22100, 23400), 2),
        "volatility": round(random.uniform(12, 28), 2),
        "pcr": round(random.uniform(0.7, 1.4), 2),
        "trend_probability": f"{random.randint(40, 80)}%",
        "session_high": round(random.uniform(23000, 23500), 2),
        "session_low": round(random.uniform(22000, 22500), 2)
    }

def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def job():
    data = fetch_market_data()
    write_data(data)
    print(f"[{data['timestamp']}] Data updated")

if __name__ == "__main__":
    print("Market data service started (every 5 minutes)")
    while True:
        try:
            job()
        except Exception as e:
            print("Error:", e)
        time.sleep(INTERVAL)
