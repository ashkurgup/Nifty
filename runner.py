import yfinance as yf
import json
import datetime
import yaml

with open("config.yml") as f:
    config = yaml.safe_load(f)

nifty = yf.Ticker(config["symbol"])
data = nifty.history(period="1d", interval="1m")

last = data.iloc[-1]
prev_close = nifty.info["previousClose"]

price = round(last["Close"], 2)
change = round(price - prev_close, 2)
percent = round((change / prev_close) * 100, 2)

output = {
    "price": price,
    "change": change,
    "percent": percent,
    "updated": datetime.datetime.now().strftime("%H:%M:%S IST")
}

with open(config["output_file"], "w") as f:
    json.dump(output, f)
