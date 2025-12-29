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
    """Get or create blockchain data orchestrator with all data sources.

    Returns:
        MultiSourceOrchestrator: Orchestrator instance.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiSourceOrchestrator(
            dune_api_key=os.getenv("DUNE_API_KEY"),
            etherscan_api_keys={
                'ethereum': os.getenv("ETHERSCAN_API_KEY"),
            },
            cryptopanic_api_token=os.getenv("CRYPTOPANIC_API_TOKEN"),
            github_api_token=os.getenv("GITHUB_API_TOKEN")
        )
    return _orchestrator


# Define the Scout Agent with explicit types
scout_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Scout Agent responsible for gathering fundamental market data. "
        "You analyze macro indicators (SPX, DXY) and provide real on-chain insights "
        "using multiple free blockchain and alternative data sources.\n\n"
        "You have access to:\n"
        "- DeFiLlama for TVL and protocol metrics\n"
        "- CoinGecko for token prices and market data\n"
        "- Blockchain explorers for on-chain activity\n"
        "- CryptoPanic for news sentiment analysis\n"
        "- Reddit for social media sentiment\n"
        "- Google Trends for search interest correlation\n"
        "- GitHub for development activity metrics\n"
        "- Deribit for options market data (P/C ratios, IV)\n\n"
        "Use these tools to gather REAL data instead of simulating it. "
        "Provide specific numbers and cite your sources. "
        "Alternative data sources can provide early signals before price action."
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


# ============================================
# Alternative Data Source Tools
# ============================================

@scout_agent.tool
async def fetch_news_sentiment(
    ctx: RunContext[CryptoDependencies],
    currencies: List[str] = ['BTC', 'ETH']
) -> Dict[str, Any]:
    """Fetch cryptocurrency news sentiment from CryptoPanic.

    Provides aggregated news sentiment with positive/negative/neutral breakdown.
    News sentiment can provide early signals before price action.

    Args:
        ctx: PydanticAI context.
        currencies: List of currency codes (default: ['BTC', 'ETH']).

    Returns:
        dict: News sentiment analysis with sentiment score and distribution.

    Example:
        fetch_news_sentiment(ctx, ['BTC', 'ETH'])
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='news_sentiment',
            parameters={'currencies': currencies, 'kind': 'news'}
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {"error": result.data.get('error', 'Unknown error')}

        sentiment_summary = result.data.get('sentiment_summary', {})

        return {
            'currencies': currencies,
            'sentiment_score': sentiment_summary.get('sentiment_score', 0.0),
            'positive_pct': sentiment_summary.get('positive_pct', 0.0),
            'negative_pct': sentiment_summary.get('negative_pct', 0.0),
            'total_posts': sentiment_summary.get('total_posts', 0),
            'source': result.source,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch news sentiment: {str(e)}"}


@scout_agent.tool
async def fetch_social_media_sentiment(
    ctx: RunContext[CryptoDependencies],
    subreddit: str = 'cryptocurrency'
) -> Dict[str, Any]:
    """Fetch social media sentiment from Reddit cryptocurrency communities.

    Monitors subreddits like r/cryptocurrency, r/bitcoin for community sentiment.
    Social media can capture market narrative shifts.

    Args:
        ctx: PydanticAI context.
        subreddit: Subreddit name without 'r/' (default: 'cryptocurrency').

    Returns:
        dict: Reddit sentiment analysis with engagement metrics.

    Example:
        fetch_social_media_sentiment(ctx, 'bitcoin')
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='reddit_sentiment',
            parameters={'subreddit': subreddit, 'limit': 100}
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {"error": result.data.get('error', 'Unknown error')}

        sentiment_analysis = result.data.get('sentiment_analysis', {})

        return {
            'subreddit': subreddit,
            'sentiment_score': sentiment_analysis.get('sentiment_score', 0.0),
            'engagement_score': sentiment_analysis.get('engagement_score', 0.0),
            'posts_analyzed': result.data.get('posts_analyzed', 0),
            'source': result.source,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch social sentiment: {str(e)}"}


@scout_agent.tool
async def fetch_google_trends(
    ctx: RunContext[CryptoDependencies],
    keywords: List[str] = ['Bitcoin', 'Ethereum']
) -> Dict[str, Any]:
    """Fetch Google Trends search interest data.

    Correlates search interest with price movements.
    Rising search interest often precedes price moves.

    Args:
        ctx: PydanticAI context.
        keywords: Search keywords (default: ['Bitcoin', 'Ethereum']).

    Returns:
        dict: Google Trends analysis with momentum and direction.

    Example:
        fetch_google_trends(ctx, ['Bitcoin', 'Ethereum', 'Crypto'])
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='google_trends',
            parameters={'keywords': keywords, 'timeframe': 'now 7-d'}
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {"error": result.data.get('error', 'Unknown error')}

        trend_analysis = result.data.get('trend_analysis', {})

        return {
            'keywords': keywords,
            'trend_analysis': trend_analysis,
            'source': result.source,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch Google Trends: {str(e)}"}


@scout_agent.tool
async def fetch_github_activity(
    ctx: RunContext[CryptoDependencies],
    repositories: List[Dict[str, str]] = [
        {'owner': 'bitcoin', 'repo': 'bitcoin'},
        {'owner': 'ethereum', 'repo': 'go-ethereum'}
    ]
) -> Dict[str, Any]:
    """Fetch GitHub development activity for crypto projects.

    Monitors commit frequency, contributor activity, and repository health.
    Strong development activity indicates fundamental project strength.

    Args:
        ctx: PydanticAI context.
        repositories: List of repos as dicts with 'owner' and 'repo' keys.

    Returns:
        dict: GitHub activity metrics for requested repositories.

    Example:
        fetch_github_activity(ctx, [{'owner': 'bitcoin', 'repo': 'bitcoin'}])
    """
    orchestrator = get_orchestrator()
    results = {}

    try:
        for repo_info in repositories:
            request = BlockchainQueryRequest(
                query_type='github_activity',
                parameters={
                    'owner': repo_info['owner'],
                    'repo': repo_info['repo']
                }
            )

            result = await orchestrator.execute_query(request)

            if 'error' not in result.data:
                repo_key = f"{repo_info['owner']}/{repo_info['repo']}"
                activity_analysis = result.data.get('activity_analysis', {})

                results[repo_key] = {
                    'activity_score': activity_analysis.get('activity_score', 0.0),
                    'trend': activity_analysis.get('trend', 'unknown'),
                    'recent_commits': activity_analysis.get('recent_commits', 0),
                    'stars': result.data.get('stars', 0)
                }

        return {
            'repositories': results,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch GitHub activity: {str(e)}"}


@scout_agent.tool
async def fetch_options_market_data(
    ctx: RunContext[CryptoDependencies],
    currency: str = 'BTC'
) -> Dict[str, Any]:
    """Fetch options market data from Deribit.

    Provides put/call ratios, implied volatility, and options flow.
    Options data reveals sophisticated trader positioning and expectations.

    Args:
        ctx: PydanticAI context.
        currency: Currency code (default: 'BTC', can be 'ETH').

    Returns:
        dict: Options market metrics including P/C ratio and IV.

    Example:
        fetch_options_market_data(ctx, 'BTC')
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='options_data',
            parameters={'currency': currency}
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {"error": result.data.get('error', 'Unknown error')}

        options_analysis = result.data.get('options_analysis', {})

        return {
            'currency': currency,
            'put_call_ratio': options_analysis.get('put_call_ratio', 0.0),
            'avg_implied_volatility': options_analysis.get('avg_implied_volatility', 0.0),
            'market_sentiment': options_analysis.get('market_sentiment', 'neutral'),
            'total_volume': options_analysis.get('total_volume', 0.0),
            'source': result.source,
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": f"Failed to fetch options data: {str(e)}"}


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
