import json
from datetime import datetime
import random

DATA_FILE = "data.json"

def fetch_market_data():
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

def main():
    data = fetch_market_data()
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print("Data updated:", data["timestamp"])

if __name__ == "__main__":
    main()
