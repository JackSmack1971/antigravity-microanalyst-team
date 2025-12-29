"""
Quant Agent module for technical market analysis.

This module defines the Quant Analyst Agent, which uses yfinance data to derive
technical indicators and market regime classifications.
"""
import yfinance as yf
import pandas as pd
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import TechnicalData, PriceStructure, PriceMetrics, RiskProfile
from deps.dependencies import CryptoDependencies

# Define the Quant Agent with explicit types
quant_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Quantitative Analyst Agent. Your task is to interpret "
        "technical market data for a given crypto symbol and provide a "
        "structured analysis including price structure and microstructure proxies."
    ),
    deps_type=CryptoDependencies,
    result_type=TechnicalData
)

@quant_agent.tool
def fetch_market_data(ctx: RunContext[CryptoDependencies]) -> dict:
    """Fetches raw market data and calculates technical indicators.

    Uses yfinance to retrieve hourly historical data for the last 5 days,
    calculates EMA 200, RSI (14), and basic microstructure proxies like
    volume and price volatility.

    Args:
        ctx: PydanticAI context containing dependencies, specifically the asset symbol.

    Returns:
        dict: A dictionary containing technical metrics:
            - symbol (str): The asset ticker.
            - current_price (float): Latest close price.
            - ema_200 (float): 200-period Exponential Moving Average.
            - rsi (float): 14-period Relative Strength Index.
            - avg_vol (float): Average volume over the period.
            - last_vol (float): Volume of the most recent candle.
            - price_std (float): Standard deviation of price.
            - avg_price (float): Mean price over the period.

    Raises:
        ModelRetry: If no data is found for the symbol or if an error occurs.
    """
    symbol = ctx.deps.symbol
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5d", interval="1h")
        if df.empty:
            raise ModelRetry(f"No data found for symbol {symbol}. Please verify the ticker.")
            
        current_price = df['Close'].iloc[-1]
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        ema_200 = df['EMA_200'].iloc[-1]
        
        # Simple RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Microstructure Proxies
        vol_std = df['Volume'].std()
        price_std = df['Close'].std()
        
        return {
            "symbol": symbol,
            "current_price": float(current_price),
            "ema_200": float(ema_200),
            "rsi": float(current_rsi),
            "avg_vol": float(df['Volume'].mean()),
            "last_vol": float(df['Volume'].iloc[-1]),
            "price_std": float(price_std),
            "avg_price": float(df['Close'].mean())
        }
    except Exception as e:
        if isinstance(e, ModelRetry):
            raise
        return {"error": f"Failed to fetch data: {str(e)}"}

async def run_quant_agent(symbol: str = "BTC-USD") -> TechnicalData:
    """Runs the PydanticAI Quant Agent for a specific crypto symbol.

    Initializes dependencies, triggers the agent run, and persists the 
    resulting technical analysis to local storage.

    Args:
        symbol: The cryptocurrency ticker (e.g., 'BTC-USD'). Defaults to "BTC-USD".

    Returns:
        TechnicalData: Structured Pydantic model containing the technical analysis.

    Raises:
        Exception: If the agent run fails or data cannot be saved.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "quant-001"},
            symbol=symbol
        )
        
        try:
            result = await quant_agent.run(
                f"Analyze the technical structure for {symbol}. "
                "Use the fetch_market_data tool to get raw metrics. "
                "Map the tool's 'current_price', 'rsi', and 'ema_200' to the PriceMetrics model. "
                "Classify the market regime based on price vs EMA_200. "
                "Populate market microstructure using tool provided proxies.",
                deps=deps
            )
            
            output = result.data.model_dump()
            
            # Save artifact
            os.makedirs("data", exist_ok=True)
            with open("data/technical_data.json", "w") as f:
                json.dump(output, f, indent=2, default=str)
                
            return result.data
            
        except Exception as e:
            print(f"Error in quant_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    import sys
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    
    async def main():
        data = await run_quant_agent(symbol)
        print(data.model_dump_json(indent=2))
        
    asyncio.run(main())
