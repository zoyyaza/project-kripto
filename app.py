import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin,ethereum,litecoin&vs_currencies=usd"
)

COINS = {
    "bitcoin":  {"name": "Bitcoin",  "symbol": "BTC", "color": "#F7931A"},
    "ethereum": {"name": "Ethereum", "symbol": "ETH", "color": "#627EEA"},
    "litecoin": {"name": "Litecoin", "symbol": "LTC", "color": "#BFBBBB"},
}


def fetch_prices():
    try:
        response = requests.get(COINGECKO_URL, timeout=8)
        response.raise_for_status()
        data = response.json()
        return {coin_id: data[coin_id]["usd"] for coin_id in COINS if coin_id in data}
    except Exception:
        return {}


def build_card(coin_id, price):
    meta = COINS[coin_id]
    price_str = f"${price:,.2f}" if price is not None else "Unavailable"
    return f"""
        <div class="card">
            <div class="coin-dot" style="background:{meta['color']}"></div>
            <div class="coin-info">
                <span class="coin-name">{meta['name']}</span>
                <span class="coin-symbol">{meta['symbol']}</span>
            </div>
            <div class="coin-price">{price_str}</div>
        </div>"""


@app.route("/")
def index():
    prices = fetch_prices()
    cards_html = "".join(
        build_card(coin_id, prices.get(coin_id)) for coin_id in COINS
    )
    api_status = "Live" if prices else "Unavailable — showing cached data"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Kripto — Crypto Price Tracker</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }}

    header {{
      text-align: center;
      margin-bottom: 2.5rem;
    }}

    header h1 {{
      font-size: 2.4rem;
      font-weight: 700;
      letter-spacing: -0.5px;
      color: #f8fafc;
    }}

    header p {{
      margin-top: 0.4rem;
      font-size: 0.95rem;
      color: #94a3b8;
    }}

    .cards {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
      width: 100%;
      max-width: 480px;
    }}

    .card {{
      background: #1e2130;
      border: 1px solid #2d3148;
      border-radius: 14px;
      padding: 1.25rem 1.5rem;
      display: flex;
      align-items: center;
      gap: 1rem;
      transition: border-color 0.2s;
    }}

    .card:hover {{ border-color: #4f5882; }}

    .coin-dot {{
      width: 14px;
      height: 14px;
      border-radius: 50%;
      flex-shrink: 0;
    }}

    .coin-info {{
      display: flex;
      flex-direction: column;
      flex: 1;
    }}

    .coin-name {{
      font-size: 1rem;
      font-weight: 600;
      color: #f1f5f9;
    }}

    .coin-symbol {{
      font-size: 0.78rem;
      color: #64748b;
      margin-top: 2px;
    }}

    .coin-price {{
      font-size: 1.15rem;
      font-weight: 700;
      color: #a5f3c0;
      white-space: nowrap;
    }}

    footer {{
      margin-top: 2.5rem;
      font-size: 0.8rem;
      color: #475569;
      text-align: center;
    }}

    .status-dot {{
      display: inline-block;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: {"#22c55e" if prices else "#ef4444"};
      margin-right: 5px;
      vertical-align: middle;
    }}
  </style>
</head>
<body>
  <header>
    <h1>&#9889; Kripto</h1>
    <p>Real-time cryptocurrency prices</p>
  </header>

  <div class="cards">
    {cards_html}
  </div>

  <footer>
    <span class="status-dot"></span>API: {api_status} &nbsp;&middot;&nbsp; Data: CoinGecko
    <br/>Refresh the page for the latest prices.
  </footer>
</body>
</html>"""
    return html


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
