"""
Blockchain Data Agent module for on-chain analysis.

This module defines a specialized Pydantic AI agent for gathering
on-chain blockchain data using multiple free data sources.
"""
import os
import json
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, ModelRetry

from config.agent_factory import create_agent
from deps.dependencies import CryptoDependencies
from tools.blockchain_orchestrator import (
    MultiSourceOrchestrator,
    BlockchainQueryRequest,
    get_protocol_tvl,
    get_token_price,
    get_whale_activity,
)


class OnChainMetricsDetailed(BaseModel):
    """Detailed on-chain metrics data model."""

    # Exchange flows
    exchange_net_flow: str = Field(..., description="Net flow to/from exchanges")
    exchange_inflow_24h: Optional[float] = Field(None, description="24h exchange inflow in USD")
    exchange_outflow_24h: Optional[float] = Field(None, description="24h exchange outflow in USD")

    # Address activity
    active_addresses_trend: str = Field(..., description="Trend in active addresses")
    active_addresses_24h: Optional[int] = Field(None, description="Active addresses in 24h")
    new_addresses_24h: Optional[int] = Field(None, description="New addresses in 24h")

    # Whale activity
    whale_accumulation: str = Field(..., description="Whale accumulation signal")
    whale_transactions_24h: Optional[int] = Field(None, description="Large transactions in 24h")
    whale_net_flow: Optional[str] = Field(None, description="Net whale flow direction")

    # DeFi metrics
    total_value_locked: Optional[float] = Field(None, description="Total Value Locked in USD")
    tvl_change_24h: Optional[float] = Field(None, description="24h TVL change percentage")
    dominant_protocols: Optional[List[str]] = Field(None, description="Top protocols by TVL")

    # Token metrics
    token_holder_count: Optional[int] = Field(None, description="Number of token holders")
    token_concentration: Optional[str] = Field(None, description="Token distribution concentration")

    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)


class BlockchainAnalysisResult(BaseModel):
    """Complete blockchain analysis result."""

    onchain_metrics: OnChainMetricsDetailed
    market_sentiment: str = Field(..., description="Overall market sentiment from on-chain data")
    key_insights: List[str] = Field(..., description="List of key insights from analysis")
    confidence_score: float = Field(..., ge=0, le=1, description="Analysis confidence (0-1)")
    data_sources_used: List[str] = Field(..., description="Data sources used in analysis")


# Create global orchestrator instance
_orchestrator: Optional[MultiSourceOrchestrator] = None


def get_orchestrator() -> MultiSourceOrchestrator:
    """Get or create the global orchestrator instance.

    Returns:
        MultiSourceOrchestrator: Global orchestrator instance.
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiSourceOrchestrator(
            dune_api_key=os.getenv("DUNE_API_KEY"),
            etherscan_api_keys={
                'ethereum': os.getenv("ETHERSCAN_API_KEY"),
                'bsc': os.getenv("BSCSCAN_API_KEY"),
                'polygon': os.getenv("POLYGONSCAN_API_KEY"),
            }
        )
    return _orchestrator


# Define the Blockchain Data Agent
blockchain_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Blockchain Data Analyst Agent specialized in on-chain analysis. "
        "Your role is to gather and interpret on-chain metrics from multiple free data sources "
        "including DeFiLlama, CoinGecko, Dune Analytics, and blockchain explorers.\n\n"
        "You have access to tools that provide:\n"
        "- Protocol TVL and DeFi metrics (DeFiLlama)\n"
        "- Token prices and market data (CoinGecko)\n"
        "- Whale activity and complex analytics (Dune Analytics)\n"
        "- Transaction data and balances (Etherscan family)\n\n"
        "Your goal is to synthesize this data into actionable insights about:\n"
        "1. Exchange flows and accumulation patterns\n"
        "2. Whale behavior and large transactions\n"
        "3. DeFi protocol health and TVL trends\n"
        "4. Network activity and adoption metrics\n\n"
        "Always provide specific numbers and cite your data sources. "
        "Be honest about data limitations and confidence levels."
    ),
    deps_type=CryptoDependencies,
    result_type=BlockchainAnalysisResult
)


@blockchain_agent.tool
async def get_defi_protocol_metrics(
    ctx: RunContext[CryptoDependencies],
    protocol: str,
) -> Dict[str, Any]:
    """Get DeFi protocol metrics including TVL.

    Fetches comprehensive protocol data from DeFiLlama including
    total value locked, chain breakdown, and historical trends.

    Args:
        ctx: PydanticAI context.
        protocol: Protocol slug (e.g., 'aave', 'uniswap', 'curve').

    Returns:
        dict: Protocol metrics including TVL, chains, and trends.

    Example:
        To analyze Aave, call: get_defi_protocol_metrics(ctx, 'aave')
    """
    orchestrator = get_orchestrator()

    try:
        result = await get_protocol_tvl(orchestrator, protocol)

        if 'error' in result.get('data', {}):
            return {
                "error": result['data']['error'],
                "source": result['source']
            }

        return {
            "protocol": protocol,
            "tvl_usd": result['data'].get('tvl'),
            "chain_tvls": result['data'].get('chainTvls', {}),
            "source": result['source'],
            "confidence": result['confidence_score'],
        }

    except Exception as e:
        return {"error": f"Failed to fetch protocol metrics: {str(e)}"}


@blockchain_agent.tool
async def get_token_market_data(
    ctx: RunContext[CryptoDependencies],
    token_ids: List[str],
) -> Dict[str, Any]:
    """Get real-time token market data.

    Fetches current prices, 24h volume, market cap, and price changes
    from CoinGecko for multiple tokens simultaneously.

    Args:
        ctx: PydanticAI context.
        token_ids: List of CoinGecko token IDs (e.g., ['bitcoin', 'ethereum']).

    Returns:
        dict: Market data for requested tokens.

    Example:
        To get BTC and ETH prices: get_token_market_data(ctx, ['bitcoin', 'ethereum'])
    """
    orchestrator = get_orchestrator()

    try:
        result = await get_token_price(orchestrator, token_ids)

        if 'error' in result.get('data', {}):
            return {
                "error": result['data']['error'],
                "source": result['source']
            }

        return {
            "tokens": result['data'],
            "source": result['source'],
            "confidence": result['confidence_score'],
            "real_time": True,
        }

    except Exception as e:
        return {"error": f"Failed to fetch token data: {str(e)}"}


@blockchain_agent.tool
async def get_chain_ecosystem_metrics(
    ctx: RunContext[CryptoDependencies],
    chain: str,
) -> Dict[str, Any]:
    """Get blockchain ecosystem metrics.

    Fetches TVL, active protocols, and growth metrics for a
    specific blockchain from DeFiLlama.

    Args:
        ctx: PydanticAI context.
        chain: Chain name (e.g., 'Ethereum', 'BSC', 'Polygon', 'Arbitrum').

    Returns:
        dict: Chain ecosystem metrics.

    Example:
        To analyze Ethereum DeFi: get_chain_ecosystem_metrics(ctx, 'Ethereum')
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='chain_metrics',
            parameters={'chain': chain},
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {
                "error": result.data['error'],
                "source": result.source
            }

        return {
            "chain": chain,
            "tvl_history": result.data,
            "source": result.source,
            "confidence": result.confidence_score,
        }

    except Exception as e:
        return {"error": f"Failed to fetch chain metrics: {str(e)}"}


@blockchain_agent.tool
async def get_wallet_analysis(
    ctx: RunContext[CryptoDependencies],
    address: str,
    chain: str = "ethereum",
) -> Dict[str, Any]:
    """Analyze wallet transaction history.

    Fetches recent transaction history for a wallet address
    from blockchain explorers (Etherscan family).

    Args:
        ctx: PydanticAI context.
        address: Wallet address to analyze.
        chain: Blockchain network (default: ethereum).

    Returns:
        dict: Transaction history and analysis.

    Example:
        To analyze a whale wallet: get_wallet_analysis(ctx, '0x...', 'ethereum')
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='transaction_history',
            parameters={
                'address': address,
                'limit': 50,
            },
            chains=[chain],
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {
                "error": result.data['error'],
                "source": result.source
            }

        return {
            "address": address,
            "chain": chain,
            "transactions": result.data,
            "source": result.source,
            "confidence": result.confidence_score,
        }

    except Exception as e:
        return {"error": f"Failed to fetch wallet data: {str(e)}"}


@blockchain_agent.tool
async def get_stablecoin_metrics(
    ctx: RunContext[CryptoDependencies],
    stablecoin: Optional[str] = None,
) -> Dict[str, Any]:
    """Get stablecoin market metrics.

    Fetches stablecoin market cap, dominance, and trend data
    from DeFiLlama. Can get aggregate data or specific stablecoin.

    Args:
        ctx: PydanticAI context.
        stablecoin: Optional specific stablecoin (e.g., 'USDT', 'USDC').

    Returns:
        dict: Stablecoin metrics.

    Example:
        For all stablecoins: get_stablecoin_metrics(ctx)
        For USDC only: get_stablecoin_metrics(ctx, 'USDC')
    """
    orchestrator = get_orchestrator()

    try:
        request = BlockchainQueryRequest(
            query_type='stablecoin_data',
            parameters={'stablecoin': stablecoin},
        )

        result = await orchestrator.execute_query(request)

        if 'error' in result.data:
            return {
                "error": result.data['error'],
                "source": result.source
            }

        return {
            "stablecoin": stablecoin or "all",
            "metrics": result.data,
            "source": result.source,
            "confidence": result.confidence_score,
        }

    except Exception as e:
        return {"error": f"Failed to fetch stablecoin data: {str(e)}"}


@blockchain_agent.output_validator
async def validate_blockchain_output(
    ctx: RunContext[CryptoDependencies],
    output: BlockchainAnalysisResult,
) -> BlockchainAnalysisResult:
    """Validate blockchain analysis output.

    Ensures the analysis includes meaningful insights and
    cites data sources properly.

    Args:
        ctx: PydanticAI run context.
        output: Analysis result to validate.

    Returns:
        BlockchainAnalysisResult: Validated output.

    Raises:
        ModelRetry: If validation fails.
    """
    if len(output.key_insights) < 2:
        raise ModelRetry(
            "Please provide at least 2 key insights from the on-chain data. "
            "Analyze the metrics you gathered and draw meaningful conclusions."
        )

    if len(output.data_sources_used) == 0:
        raise ModelRetry(
            "Please cite which data sources you used (e.g., DeFiLlama, CoinGecko). "
            "Use the tools to gather actual on-chain data."
        )

    return output


async def run_blockchain_agent(
    analysis_type: str = "comprehensive",
    focus_tokens: Optional[List[str]] = None,
    focus_protocols: Optional[List[str]] = None,
) -> BlockchainAnalysisResult:
    """Run the Blockchain Data Agent.

    Args:
        analysis_type: Type of analysis ('comprehensive', 'defi', 'whale', 'token').
        focus_tokens: Optional list of tokens to focus on.
        focus_protocols: Optional list of protocols to analyze.

    Returns:
        BlockchainAnalysisResult: Complete on-chain analysis.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "blockchain-001"}
        )

        # Build prompt based on analysis type
        if analysis_type == "comprehensive":
            prompt = (
                "Perform a comprehensive on-chain analysis. "
                "Gather data on: 1) Top DeFi protocols and TVL trends, "
                "2) Major token prices and market data, "
                "3) Stablecoin metrics, "
                "4) Blockchain ecosystem health. "
                "Synthesize this into actionable insights."
            )
        elif analysis_type == "defi":
            protocols = focus_protocols or ['aave', 'uniswap', 'curve']
            prompt = (
                f"Analyze DeFi protocols: {', '.join(protocols)}. "
                "Get TVL data, trends, and provide insights on protocol health. "
                "Include stablecoin metrics as they relate to DeFi."
            )
        elif analysis_type == "token":
            tokens = focus_tokens or ['bitcoin', 'ethereum']
            prompt = (
                f"Analyze tokens: {', '.join(tokens)}. "
                "Get market data, prices, volumes. "
                "Provide insights on market sentiment and trends."
            )
        else:
            prompt = (
                "Perform on-chain analysis and provide insights on "
                "current blockchain market conditions."
            )

        try:
            result = await blockchain_agent.run(prompt, deps=deps)

            # Save to file
            os.makedirs("data", exist_ok=True)
            with open("data/blockchain_analysis.json", "w") as f:
                json.dump(result.data.model_dump(), f, indent=2, default=str)

            return result.data

        except Exception as e:
            print(f"Error in blockchain_agent: {e}")
            raise


if __name__ == "__main__":
    import asyncio

    async def main():
        """Example usage of blockchain agent."""

        # Comprehensive analysis
        print("Running comprehensive blockchain analysis...")
        result = await run_blockchain_agent(analysis_type="comprehensive")

        print("\n=== BLOCKCHAIN ANALYSIS RESULTS ===")
        print(f"Market Sentiment: {result.market_sentiment}")
        print(f"Confidence Score: {result.confidence_score:.2f}")
        print(f"\nData Sources Used: {', '.join(result.data_sources_used)}")

        print("\nKey Insights:")
        for i, insight in enumerate(result.key_insights, 1):
            print(f"{i}. {insight}")

        print("\nOn-Chain Metrics:")
        print(f"  Exchange Flow: {result.onchain_metrics.exchange_net_flow}")
        print(f"  Active Addresses Trend: {result.onchain_metrics.active_addresses_trend}")
        print(f"  Whale Accumulation: {result.onchain_metrics.whale_accumulation}")
        if result.onchain_metrics.total_value_locked:
            print(f"  Total Value Locked: ${result.onchain_metrics.total_value_locked:,.0f}")

        # DeFi-focused analysis
        print("\n\nRunning DeFi protocol analysis...")
        defi_result = await run_blockchain_agent(
            analysis_type="defi",
            focus_protocols=['aave', 'compound', 'uniswap']
        )

        print(f"\nDeFi Insights:")
        for insight in defi_result.key_insights:
            print(f"  • {insight}")

    asyncio.run(main())
