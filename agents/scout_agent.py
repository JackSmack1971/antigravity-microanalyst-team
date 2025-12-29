"""
Scout Agent module for fundamental and macro market analysis.

This module defines the Scout Agent, which gathers macro indicators (SPX, DXY)
and on-chain data from multiple free blockchain data sources including
DeFiLlama, CoinGecko, and Dune Analytics.
"""
import yfinance as yf
import json
import os
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import FundamentalData
from deps.dependencies import CryptoDependencies
from tools.blockchain_orchestrator import (
    MultiSourceOrchestrator,
    BlockchainQueryRequest,
    get_protocol_tvl,
    get_token_price,
)

# Initialize blockchain data orchestrator
_orchestrator: Optional[MultiSourceOrchestrator] = None


def get_orchestrator() -> MultiSourceOrchestrator:
    """Get or create blockchain data orchestrator.

    Returns:
        MultiSourceOrchestrator: Orchestrator instance.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiSourceOrchestrator(
            dune_api_key=os.getenv("DUNE_API_KEY"),
            etherscan_api_keys={
                'ethereum': os.getenv("ETHERSCAN_API_KEY"),
            }
        )
    return _orchestrator


# Define the Scout Agent with explicit types
scout_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Scout Agent responsible for gathering fundamental market data. "
        "You analyze macro indicators (SPX, DXY) and provide real on-chain insights "
        "using multiple free blockchain data sources.\n\n"
        "You have access to:\n"
        "- DeFiLlama for TVL and protocol metrics\n"
        "- CoinGecko for token prices and market data\n"
        "- Blockchain explorers for on-chain activity\n\n"
        "Use these tools to gather REAL data instead of simulating it. "
        "Provide specific numbers and cite your sources."
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


@scout_agent.tool
async def fetch_defi_tvl_data(
    ctx: RunContext[CryptoDependencies],
    protocols: List[str]
) -> Dict[str, Any]:
    """Fetch Total Value Locked (TVL) for DeFi protocols.

    Uses DeFiLlama free API to get real TVL data for major protocols.
    This provides insight into capital flows and DeFi health.

    Args:
        ctx: PydanticAI context.
        protocols: List of protocol slugs (e.g., ['aave', 'uniswap', 'curve']).

    Returns:
        dict: TVL data for requested protocols.

    Example:
        fetch_defi_tvl_data(ctx, ['aave', 'compound'])
    """
    orchestrator = get_orchestrator()
    results = {}

    try:
        for protocol in protocols:
            result = await get_protocol_tvl(orchestrator, protocol)
            if 'error' not in result.get('data', {}):
                results[protocol] = {
                    'tvl_usd': result['data'].get('tvl', 0),
                    'chains': result['data'].get('chainTvls', {}),
                    'source': result['source']
                }

        return {
            'protocols': results,
            'total_tvl': sum(p.get('tvl_usd', 0) for p in results.values()),
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch TVL data: {str(e)}"}


@scout_agent.tool
async def fetch_crypto_market_data(
    ctx: RunContext[CryptoDependencies],
    token_ids: List[str]
) -> Dict[str, Any]:
    """Fetch real-time crypto market data.

    Uses CoinGecko free API to get prices, volume, market cap,
    and 24h changes for crypto assets.

    Args:
        ctx: PydanticAI context.
        token_ids: List of CoinGecko token IDs (e.g., ['bitcoin', 'ethereum']).

    Returns:
        dict: Market data including prices and volumes.

    Example:
        fetch_crypto_market_data(ctx, ['bitcoin', 'ethereum'])
    """
    orchestrator = get_orchestrator()

    try:
        result = await get_token_price(orchestrator, token_ids)

        if 'error' in result.get('data', {}):
            return {"error": result['data']['error']}

        return {
            'tokens': result['data'],
            'source': result['source'],
            'real_time': True,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch market data: {str(e)}"}


@scout_agent.tool
async def fetch_stablecoin_supply(
    ctx: RunContext[CryptoDependencies]
) -> Dict[str, Any]:
    """Fetch stablecoin supply metrics.

    Uses DeFiLlama to get stablecoin market cap data.
    Stablecoin supply is a key indicator of market liquidity and sentiment.

    Args:
        ctx: PydanticAI context.

    Returns:
        dict: Stablecoin supply and market cap data.
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='stablecoin_data',
            parameters={}
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {"error": result.data['error']}

        return {
            'stablecoin_data': result.data,
            'source': result.source,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch stablecoin data: {str(e)}"}


@scout_agent.tool
async def fetch_chain_ecosystem_health(
    ctx: RunContext[CryptoDependencies],
    chain: str = "Ethereum"
) -> Dict[str, Any]:
    """Fetch blockchain ecosystem health metrics.

    Uses DeFiLlama to get TVL trends for a specific blockchain.
    Shows ecosystem growth and capital flows.

    Args:
        ctx: PydanticAI context.
        chain: Chain name (default: Ethereum).

    Returns:
        dict: Chain ecosystem metrics.
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='chain_metrics',
            parameters={'chain': chain}
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {"error": result.data['error']}

        # Extract recent TVL if available
        tvl_history = result.data
        recent_tvl = None
        if isinstance(tvl_history, list) and len(tvl_history) > 0:
            recent_tvl = tvl_history[-1].get('tvl')

        return {
            'chain': chain,
            'recent_tvl': recent_tvl,
            'tvl_history': tvl_history[-7:] if isinstance(tvl_history, list) else None,  # Last 7 data points
            'source': result.source,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch chain health: {str(e)}"}

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
                "Perform a comprehensive fundamental market scan:\n\n"
                "1. Fetch macro data (SPX, DXY) using fetch_macro_data\n"
                "2. Fetch DeFi TVL data for major protocols like ['aave', 'uniswap', 'curve'] using fetch_defi_tvl_data\n"
                "3. Fetch crypto market data for ['bitcoin', 'ethereum'] using fetch_crypto_market_data\n"
                "4. Fetch stablecoin supply metrics using fetch_stablecoin_supply\n"
                "5. Fetch Ethereum ecosystem health using fetch_chain_ecosystem_health\n\n"
                "Analyze this REAL on-chain data to determine:\n"
                "- Exchange net flows (inflow to exchanges = bearish, outflow = bullish)\n"
                "- Active address trends (from DeFi and chain activity)\n"
                "- Whale accumulation signals (from TVL changes and large cap movements)\n"
                "- Sentiment signals from stablecoin supply and market data\n\n"
                "Provide specific numbers from the data you gathered.",
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
