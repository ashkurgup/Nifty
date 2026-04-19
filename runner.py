import yfinance as yf
import json
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def is_market_live(now):
    if now.weekday() >= 5:  # Saturday, Sunday
        return False
    market_open = now.replace(hour=9, minute=0, second=0)
    market_close = now.replace(hour=15, minute=30, second=0)
    return market_open <= now <= market_close

def fetch_nifty():
    ticker = yf.Ticker("^NSEI")
    hist = ticker.history(period="2d", interval="1m")

    last = hist.iloc[-1]
    prev_close = hist.iloc[-2]["Close"]

    price = round(last["Close"], 2)
    change = round(price - prev_close, 2)
    percent = round((change / prev_close) * 100, 2)

    now = datetime.now(IST)

    return {
        "symbol": "NIFTY",
        "price": price,
        "change": change,
        "percent": percent,
        "market_status": "LIVE" if is_market_live(now) else "CLOSED",
        "updated": now.strftime("%H:%M:%S IST")
    }

if __name__ == "__main__":
    data = fetch_nifty()
    with open("data/nifty.json", "w") as f:
        json.dump(data, f, indent=2)

    print("✅ NIFTY data updated")
