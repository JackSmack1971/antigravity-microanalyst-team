"""
Scout Agent module for fundamental and macro market analysis.

This module defines the Scout Agent, which gathers macro indicators (SPX, DXY)
and simulates fundamental signals such as on-chain whale behavior and sentiment.
"""
import yfinance as yf
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import FundamentalData
from deps.dependencies import CryptoDependencies

# Define the Scout Agent with explicit types
scout_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Scout Agent responsible for gathering fundamental market data. "
        "You analyze macro indicators (SPX, DXY) and provide on-chain and sentiment insights."
    ),
    deps_type=CryptoDependencies,
    result_type=FundamentalData
)

@scout_agent.tool
def fetch_macro_data(ctx: RunContext[CryptoDependencies]) -> dict:
    """Fetches macro-economic levels (S&P 500 and DXY).

    Uses yfinance to retrieve levels for the S&P 500 Index (^GSPC) and 
    the US Dollar Index (DX-Y.NYB).

    Args:
        ctx: PydanticAI context (unused in this specific tool but required for signature).

    Returns:
        dict: A dictionary containing macro levels:
            - spx_level (float): The current S&P 500 index level.
            - dxy_index (float): The current US Dollar Index level.
            - error (str, optional): Error message if fetching fails.
    """
    try:
        spx = yf.Ticker("^GSPC").history(period="5d")['Close'].iloc[-1]
        dxy = yf.Ticker("DX-Y.NYB").history(period="5d")['Close'].iloc[-1]
        return {
            "spx_level": float(spx),
            "dxy_index": float(dxy)
        }
    except Exception as e:
        return {"error": f"Failed to fetch macro data: {str(e)}"}

async def run_scout_agent() -> FundamentalData:
    """Runs the PydanticAI Scout Agent to perform a market scan.

    Initializes dependencies, executes the agent to synthesize macro, 
    on-chain, and sentiment data, and persists the result.

    Returns:
        FundamentalData: Structured Pydantic model containing fundamental analysis.

    Raises:
        Exception: If the agent run fails or data cannot be persistent.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "scout-001"}
        )
        
        try:
            result = await scout_agent.run(
                "Perform a fundamental market scan. Fetch macro data and interpret current "
                "on-chain and sentiment signals. "
                "Simulate and interpret on-chain and sentiment data (assume high whale accumulation and positive social volume).",
                deps=deps
            )
            
            output = result.data.model_dump()
            
            # Legacy compatibility
            os.makedirs("data", exist_ok=True)
            with open("data/fundamental_data.json", "w") as f:
                json.dump(output, f, indent=2, default=str)
                
            return result.data
            
        except Exception as e:
            print(f"Error in scout_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    import sys
    
    async def main():
        data = await run_scout_agent()
        print(data.model_dump_json(indent=2))
        
    asyncio.run(main())
