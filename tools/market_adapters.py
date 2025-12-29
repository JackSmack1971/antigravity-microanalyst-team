"""
Market Adapters module for raw data fetching and synchronization.

This module provides legacy adapters and utility functions for fetching
comprehensive market states, including crypto, macro, and technicals.
"""
import yfinance as yf
import pandas as pd
import json
import sys
from datetime import datetime

def get_full_market_state(symbol="BTC-USD"):
    """Master Adapter: Fetches Price, Macro, and derived Microstructure data.

    Retrieves synchronous data for the specified symbol, calculates RSI and
    EMA 200, and fetches macro context (S&P 500 and Gold prices).

    Args:
        symbol: The asset ticker symbol. Defaults to "BTC-USD".

    Returns:
        str: A JSON-formatted string containing the full market state or 
            an error message.
    """
    try:
        # 1. Fetch Crypto Data
        btc = yf.Ticker(symbol)
        df = btc.history(period="1mo", interval="1h")
        current_price = df['Close'].iloc[-1]
        
        # 2. Fetch Macro Data (S&P 500, Gold, DXY)
        spx = yf.Ticker("^GSPC").history(period="5d")['Close'].iloc[-1]
        gold = yf.Ticker("GC=F").history(period="5d")['Close'].iloc[-1]
        
        # 3. Calculate Technicals
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        ema_200 = df['EMA_200'].iloc[-1]
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # 4. Construct JSON Output
        output = {
            "module_1_price": {
                "asset": symbol,
                "price": round(current_price, 2),
                "rsi_1h": round(current_rsi, 2),
                "regime": "Trending_Up" if current_price > ema_200 else "Trending_Down"
            },
            "module_2_macro": {
                "spx_level": round(spx, 2),
                "gold_price": round(gold, 2),
                "risk_environment": "Risk_On" if spx > 4000 else "Risk_Off" # Simplified logic
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        return json.dumps(output, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    print(get_full_market_state(target))