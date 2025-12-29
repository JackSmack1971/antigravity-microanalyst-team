"""
Multi-Source Blockchain Data Orchestrator.

This module implements intelligent query routing, fallback chains, and
distributed query execution across multiple blockchain data sources.
Based on research for cost-effective, high-performance data access.
"""
import asyncio
from typing import Dict, List, Optional, Any, Literal
from datetime import datetime
from enum import Enum

from tools.blockchain_adapters import (
    BlockchainDataCache,
    DeFiLlamaAdapter,
    DuneAnalyticsAdapter,
    CoinGeckoAdapter,
    EtherscanAdapter,
    RateLimitError,
)

from tools.alternative_data_adapters import (
    CryptoPanicAdapter,
    RedditSentimentAdapter,
    GoogleTrendsAdapter,
    GitHubActivityAdapter,
    DeribitOptionsAdapter,
)


class QueryComplexity(Enum):
    """Query complexity levels for intelligent routing."""
    SIMPLE = 0.3      # Simple RPC or cached queries
    MEDIUM = 0.6      # Multi-source queries
    COMPLEX = 0.9     # Complex analytical queries


class DataSourceType(str, Enum):
    """Available blockchain and alternative data sources."""
    DEFILLAMA = "defillama"
    DUNE = "dune"
    COINGECKO = "coingecko"
    ETHERSCAN = "etherscan"
    # Alternative data sources
    CRYPTOPANIC = "cryptopanic"
    REDDIT = "reddit"
    GOOGLE_TRENDS = "google_trends"
    GITHUB = "github"
    DERIBIT = "deribit"


class BlockchainQueryRequest:
    """Structured request for blockchain data.

    Attributes:
        query_type: Type of query (tvl, price, transactions, etc.)
        parameters: Query-specific parameters
        chains: List of blockchain networks
        priority: Query priority (affects timeout and retries)
        real_time: Whether real-time data is required
    """

    def __init__(
        self,
        query_type: str,
        parameters: Dict[str, Any],
        chains: Optional[List[str]] = None,
        priority: str = "normal",
        real_time: bool = False,
    ):
        self.query_type = query_type
        self.parameters = parameters
        self.chains = chains or ["ethereum"]
        self.priority = priority
        self.real_time = real_time
        self.timestamp = datetime.utcnow()


class BlockchainQueryResponse:
    """Structured response with validation and metadata.

    Attributes:
        data: Query result data
        source: Data source used
        timestamp: Response timestamp
        confidence_score: Data reliability score (0-1)
        fallback_used: Whether fallback sources were used
    """

    def __init__(
        self,
        data: Dict[str, Any],
        source: str,
        confidence_score: float = 1.0,
        fallback_used: bool = False,
    ):
        self.data = data
        self.source = source
        self.timestamp = datetime.utcnow()
        self.confidence_score = confidence_score
        self.fallback_used = fallback_used

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "confidence_score": self.confidence_score,
            "fallback_used": self.fallback_used,
        }


class MultiSourceOrchestrator:
    """Advanced multi-source orchestration for blockchain data.

    Implements:
    - Intelligent query routing based on complexity
    - Automatic fallback chains
    - Concurrent query execution
    - Adaptive learning for routing decisions
    """

    def __init__(
        self,
        dune_api_key: Optional[str] = None,
        etherscan_api_keys: Optional[Dict[str, str]] = None,
        cache_dir: str = "data/cache",
        cryptopanic_api_token: Optional[str] = None,
        github_api_token: Optional[str] = None,
    ):
        """Initialize orchestrator with data source adapters.

        Args:
            dune_api_key: Optional Dune Analytics API key.
            etherscan_api_keys: Optional dict of Etherscan API keys by chain.
            cache_dir: Directory for caching data.
            cryptopanic_api_token: Optional CryptoPanic API token.
            github_api_token: Optional GitHub API token.
        """
        self.cache = BlockchainDataCache(cache_dir)

        # Initialize all adapters
        self.adapters = {
            DataSourceType.DEFILLAMA: DeFiLlamaAdapter(self.cache),
            DataSourceType.DUNE: DuneAnalyticsAdapter(dune_api_key, self.cache),
            DataSourceType.COINGECKO: CoinGeckoAdapter(self.cache),
            DataSourceType.ETHERSCAN: EtherscanAdapter(etherscan_api_keys, self.cache),
            # Alternative data adapters
            DataSourceType.CRYPTOPANIC: CryptoPanicAdapter(self.cache, cryptopanic_api_token),
            DataSourceType.REDDIT: RedditSentimentAdapter(self.cache),
            DataSourceType.GOOGLE_TRENDS: GoogleTrendsAdapter(self.cache),
            DataSourceType.GITHUB: GitHubActivityAdapter(self.cache, github_api_token),
            DataSourceType.DERIBIT: DeribitOptionsAdapter(self.cache),
        }

        # Query routing statistics for adaptive learning
        self.query_stats = {
            source: {"success": 0, "failure": 0, "avg_latency": 0.0}
            for source in DataSourceType
        }

        # Source selection mapping
        self.source_map = {
            'tvl': DataSourceType.DEFILLAMA,
            'protocol_metrics': DataSourceType.DEFILLAMA,
            'chain_metrics': DataSourceType.DEFILLAMA,
            'token_price': DataSourceType.COINGECKO,
            'token_metrics': DataSourceType.COINGECKO,
            'market_data': DataSourceType.COINGECKO,
            'historical_analytics': DataSourceType.DUNE,
            'complex_analytics': DataSourceType.DUNE,
            'whale_tracking': DataSourceType.DUNE,
            'transaction_history': DataSourceType.ETHERSCAN,
            'token_balance': DataSourceType.ETHERSCAN,
            'contract_data': DataSourceType.ETHERSCAN,
            # Alternative data source mappings
            'news_sentiment': DataSourceType.CRYPTOPANIC,
            'reddit_sentiment': DataSourceType.REDDIT,
            'social_sentiment': DataSourceType.REDDIT,
            'google_trends': DataSourceType.GOOGLE_TRENDS,
            'search_interest': DataSourceType.GOOGLE_TRENDS,
            'github_activity': DataSourceType.GITHUB,
            'development_activity': DataSourceType.GITHUB,
            'options_data': DataSourceType.DERIBIT,
            'options_metrics': DataSourceType.DERIBIT,
        }

        # Fallback chain definitions
        self.fallback_chains = {
            'tvl': [DataSourceType.DEFILLAMA, DataSourceType.DUNE],
            'token_price': [DataSourceType.COINGECKO, DataSourceType.DEFILLAMA],
            'analytics': [DataSourceType.DUNE, DataSourceType.DEFILLAMA],
            'balance': [DataSourceType.ETHERSCAN],
        }

    def assess_query_complexity(self, request: BlockchainQueryRequest) -> float:
        """AI-driven query complexity assessment.

        Args:
            request: Query request to assess.

        Returns:
            float: Complexity score (0-1).
        """
        complexity_factors = {
            'multi_chain': len(request.chains) * 0.1,
            'real_time': 0.2 if request.real_time else 0.0,
            'analytics': 0.3 if 'analytics' in request.query_type else 0.0,
            'historical': 0.3 if request.parameters.get('historical') else 0.0,
        }

        total_complexity = sum(complexity_factors.values())
        return min(total_complexity, 1.0)

    def select_primary_source(self, query_type: str) -> DataSourceType:
        """Select primary data source based on query type.

        Args:
            query_type: Type of query.

        Returns:
            DataSourceType: Selected primary source.
        """
        return self.source_map.get(query_type, DataSourceType.DEFILLAMA)

    async def execute_query(
        self, request: BlockchainQueryRequest
    ) -> BlockchainQueryResponse:
        """Execute blockchain query with intelligent routing.

        Args:
            request: Structured query request.

        Returns:
            BlockchainQueryResponse: Query results with metadata.
        """
        complexity = self.assess_query_complexity(request)

        if complexity > 0.8:
            return await self._route_complex_query(request)
        elif complexity > 0.5:
            return await self._route_multi_source_query(request)
        else:
            return await self._route_simple_query(request)

    async def _route_simple_query(
        self, request: BlockchainQueryRequest
    ) -> BlockchainQueryResponse:
        """Route simple queries with caching.

        Args:
            request: Query request.

        Returns:
            BlockchainQueryResponse: Query response.
        """
        primary_source = self.select_primary_source(request.query_type)

        try:
            data = await self._execute_on_source(primary_source, request)
            return BlockchainQueryResponse(
                data=data,
                source=primary_source.value,
                confidence_score=1.0,
                fallback_used=False,
            )
        except Exception as e:
            # Simple fallback
            return await self._execute_fallback(request, [primary_source])

    async def _route_multi_source_query(
        self, request: BlockchainQueryRequest
    ) -> BlockchainQueryResponse:
        """Route multi-source queries with parallel execution.

        Args:
            request: Query request.

        Returns:
            BlockchainQueryResponse: Aggregated response.
        """
        # Determine relevant sources
        relevant_sources = self._get_relevant_sources(request.query_type)

        # Execute in parallel with timeout
        tasks = [
            self._execute_on_source(source, request)
            for source in relevant_sources
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate results
            valid_results = [
                (source, result)
                for source, result in zip(relevant_sources, results)
                if not isinstance(result, Exception) and result
            ]

            if valid_results:
                # Use best result (could implement voting/consensus here)
                best_source, best_result = valid_results[0]
                confidence = len(valid_results) / len(relevant_sources)

                return BlockchainQueryResponse(
                    data=best_result,
                    source=best_source.value,
                    confidence_score=confidence,
                    fallback_used=len(valid_results) < len(relevant_sources),
                )

        except Exception:
            pass

        # All sources failed
        return await self._execute_fallback(request, relevant_sources)

    async def _route_complex_query(
        self, request: BlockchainQueryRequest
    ) -> BlockchainQueryResponse:
        """Route complex analytical queries with fallback chain.

        Args:
            request: Query request.

        Returns:
            BlockchainQueryResponse: Query response.
        """
        # Complex queries prefer Dune, then DeFiLlama
        fallback_order = [DataSourceType.DUNE, DataSourceType.DEFILLAMA]

        for source in fallback_order:
            try:
                result = await asyncio.wait_for(
                    self._execute_on_source(source, request),
                    timeout=60,  # Longer timeout for complex queries
                )

                if result:
                    return BlockchainQueryResponse(
                        data=result,
                        source=source.value,
                        confidence_score=1.0,
                        fallback_used=source != fallback_order[0],
                    )

            except asyncio.TimeoutError:
                continue
            except Exception:
                continue

        # All sources failed
        return BlockchainQueryResponse(
            data={"error": "All sources failed for complex query"},
            source="none",
            confidence_score=0.0,
            fallback_used=True,
        )

    async def _execute_on_source(
        self, source: DataSourceType, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on specific data source.

        Args:
            source: Data source to query.
            request: Query request.

        Returns:
            Dict containing query results.
        """
        adapter = self.adapters[source]
        start_time = datetime.utcnow()

        try:
            # Route to appropriate adapter method
            if source == DataSourceType.DEFILLAMA:
                return await self._execute_defillama(adapter, request)
            elif source == DataSourceType.DUNE:
                return await self._execute_dune(adapter, request)
            elif source == DataSourceType.COINGECKO:
                return await self._execute_coingecko(adapter, request)
            elif source == DataSourceType.ETHERSCAN:
                return await self._execute_etherscan(adapter, request)
            # Alternative data sources
            elif source == DataSourceType.CRYPTOPANIC:
                return await self._execute_cryptopanic(adapter, request)
            elif source == DataSourceType.REDDIT:
                return await self._execute_reddit(adapter, request)
            elif source == DataSourceType.GOOGLE_TRENDS:
                return await self._execute_google_trends(adapter, request)
            elif source == DataSourceType.GITHUB:
                return await self._execute_github(adapter, request)
            elif source == DataSourceType.DERIBIT:
                return await self._execute_deribit(adapter, request)
            else:
                return {"error": f"Unknown source: {source}"}

        except Exception as e:
            self._update_stats(source, success=False)
            raise
        finally:
            latency = (datetime.utcnow() - start_time).total_seconds()
            self._update_latency(source, latency)

    async def _execute_defillama(
        self, adapter: DeFiLlamaAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on DeFiLlama.

        Args:
            adapter: DeFiLlama adapter instance.
            request: Query request.

        Returns:
            Dict containing DeFiLlama data.
        """
        query_type = request.query_type
        params = request.parameters

        if query_type in ['tvl', 'protocol_metrics']:
            protocol = params.get('protocol', 'aave')
            return await adapter.get_protocol_tvl(protocol)

        elif query_type in ['chain_metrics', 'chain_tvl']:
            chain = params.get('chain', 'Ethereum')
            return await adapter.get_chain_tvl(chain)

        elif query_type == 'stablecoin_data':
            stablecoin = params.get('stablecoin')
            return await adapter.get_stablecoin_charts(stablecoin)

        return {"error": f"Unsupported query type for DeFiLlama: {query_type}"}

    async def _execute_dune(
        self, adapter: DuneAnalyticsAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on Dune Analytics.

        Args:
            adapter: Dune adapter instance.
            request: Query request.

        Returns:
            Dict containing Dune Analytics data.
        """
        params = request.parameters
        query_id = params.get('query_id')

        if not query_id:
            return {"error": "Dune query requires 'query_id' parameter"}

        query_params = params.get('query_params', {})

        if params.get('use_latest', False):
            return await adapter.get_latest_result(query_id)
        else:
            return await adapter.execute_query(query_id, query_params)

    async def _execute_coingecko(
        self, adapter: CoinGeckoAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on CoinGecko.

        Args:
            adapter: CoinGecko adapter instance.
            request: Query request.

        Returns:
            Dict containing CoinGecko data.
        """
        query_type = request.query_type
        params = request.parameters

        if query_type in ['token_price', 'simple_price']:
            token_ids = params.get('token_ids', ['bitcoin'])
            if isinstance(token_ids, str):
                token_ids = [token_ids]
            vs_currencies = params.get('vs_currencies', ['usd'])
            return await adapter.get_simple_price(token_ids, vs_currencies)

        elif query_type in ['token_metrics', 'token_data']:
            token_id = params.get('token_id', 'bitcoin')
            return await adapter.get_token_data(token_id)

        return {"error": f"Unsupported query type for CoinGecko: {query_type}"}

    async def _execute_etherscan(
        self, adapter: EtherscanAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on Etherscan-family APIs.

        Args:
            adapter: Etherscan adapter instance.
            request: Query request.

        Returns:
            Dict containing blockchain explorer data.
        """
        query_type = request.query_type
        params = request.parameters
        chain = request.chains[0] if request.chains else 'ethereum'

        if query_type == 'token_balance':
            contract = params.get('contract_address')
            address = params.get('address')
            if not contract or not address:
                return {"error": "token_balance requires contract_address and address"}
            return await adapter.get_token_balance(chain, contract, address)

        elif query_type == 'transaction_history':
            address = params.get('address')
            limit = params.get('limit', 100)
            if not address:
                return {"error": "transaction_history requires address"}
            return await adapter.get_transactions(chain, address, limit)

        return {"error": f"Unsupported query type for Etherscan: {query_type}"}

    async def _execute_cryptopanic(
        self, adapter: CryptoPanicAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on CryptoPanic.

        Args:
            adapter: CryptoPanic adapter instance.
            request: Query request.

        Returns:
            Dict containing news sentiment data.
        """
        params = request.parameters
        currencies = params.get('currencies', ['BTC', 'ETH'])
        kind = params.get('kind', 'news')

        return await adapter.get_news_sentiment(currencies, kind)

    async def _execute_reddit(
        self, adapter: RedditSentimentAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on Reddit.

        Args:
            adapter: Reddit adapter instance.
            request: Query request.

        Returns:
            Dict containing Reddit sentiment data.
        """
        params = request.parameters
        subreddit = params.get('subreddit', 'cryptocurrency')
        limit = params.get('limit', 100)

        return await adapter.get_subreddit_sentiment(subreddit, limit)

    async def _execute_google_trends(
        self, adapter: GoogleTrendsAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on Google Trends.

        Args:
            adapter: Google Trends adapter instance.
            request: Query request.

        Returns:
            Dict containing search interest data.
        """
        params = request.parameters
        keywords = params.get('keywords', ['Bitcoin', 'Ethereum'])
        timeframe = params.get('timeframe', 'now 7-d')

        return await adapter.get_search_interest(keywords, timeframe)

    async def _execute_github(
        self, adapter: GitHubActivityAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on GitHub.

        Args:
            adapter: GitHub adapter instance.
            request: Query request.

        Returns:
            Dict containing repository activity data.
        """
        params = request.parameters
        owner = params.get('owner')
        repo = params.get('repo')

        if not owner or not repo:
            return {"error": "GitHub query requires 'owner' and 'repo' parameters"}

        return await adapter.get_repository_activity(owner, repo)

    async def _execute_deribit(
        self, adapter: DeribitOptionsAdapter, request: BlockchainQueryRequest
    ) -> Dict[str, Any]:
        """Execute query on Deribit.

        Args:
            adapter: Deribit adapter instance.
            request: Query request.

        Returns:
            Dict containing options market data.
        """
        params = request.parameters
        currency = params.get('currency', 'BTC')

        return await adapter.get_options_summary(currency)

    async def _execute_fallback(
        self, request: BlockchainQueryRequest, failed_sources: List[DataSourceType]
    ) -> BlockchainQueryResponse:
        """Execute fallback chain when primary sources fail.

        Args:
            request: Query request.
            failed_sources: List of sources that have already failed.

        Returns:
            BlockchainQueryResponse: Fallback response.
        """
        # Determine fallback category
        if 'tvl' in request.query_type:
            fallback_sources = self.fallback_chains['tvl']
        elif 'price' in request.query_type:
            fallback_sources = self.fallback_chains['token_price']
        elif 'analytics' in request.query_type:
            fallback_sources = self.fallback_chains['analytics']
        else:
            fallback_sources = list(DataSourceType)

        # Try remaining sources
        for source in fallback_sources:
            if source in failed_sources:
                continue

            try:
                result = await self._execute_on_source(source, request)
                if result and not result.get('error'):
                    return BlockchainQueryResponse(
                        data=result,
                        source=source.value,
                        confidence_score=0.7,  # Lower confidence for fallback
                        fallback_used=True,
                    )
            except Exception:
                continue

        # All fallbacks failed
        return BlockchainQueryResponse(
            data={"error": "All data sources failed", "failed_sources": [s.value for s in failed_sources]},
            source="none",
            confidence_score=0.0,
            fallback_used=True,
        )

    def _get_relevant_sources(self, query_type: str) -> List[DataSourceType]:
        """Get relevant data sources for query type.

        Args:
            query_type: Type of query.

        Returns:
            List of relevant data sources.
        """
        if 'tvl' in query_type or 'protocol' in query_type:
            return [DataSourceType.DEFILLAMA, DataSourceType.DUNE]
        elif 'price' in query_type or 'market' in query_type:
            return [DataSourceType.COINGECKO, DataSourceType.DEFILLAMA]
        elif 'transaction' in query_type or 'balance' in query_type:
            return [DataSourceType.ETHERSCAN]
        else:
            return [DataSourceType.DEFILLAMA, DataSourceType.COINGECKO]

    def _update_stats(self, source: DataSourceType, success: bool):
        """Update query statistics for adaptive learning.

        Args:
            source: Data source.
            success: Whether query succeeded.
        """
        if success:
            self.query_stats[source]["success"] += 1
        else:
            self.query_stats[source]["failure"] += 1

    def _update_latency(self, source: DataSourceType, latency: float):
        """Update average latency for source.

        Args:
            source: Data source.
            latency: Query latency in seconds.
        """
        stats = self.query_stats[source]
        total_queries = stats["success"] + stats["failure"]

        if total_queries > 0:
            stats["avg_latency"] = (
                (stats["avg_latency"] * (total_queries - 1) + latency) / total_queries
            )

    def get_source_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for all sources.

        Returns:
            Dict containing statistics for each source.
        """
        return {
            source.value: {
                "success_rate": (
                    stats["success"] / max(stats["success"] + stats["failure"], 1)
                ),
                "total_queries": stats["success"] + stats["failure"],
                "avg_latency_ms": stats["avg_latency"] * 1000,
            }
            for source, stats in self.query_stats.items()
        }


# Convenience functions for common queries
async def get_protocol_tvl(orchestrator: MultiSourceOrchestrator, protocol: str) -> Dict[str, Any]:
    """Get TVL for a DeFi protocol.

    Args:
        orchestrator: Orchestrator instance.
        protocol: Protocol slug (e.g., 'aave', 'uniswap').

    Returns:
        Dict containing TVL data.
    """
    request = BlockchainQueryRequest(
        query_type='tvl',
        parameters={'protocol': protocol},
    )
    response = await orchestrator.execute_query(request)
    return response.to_dict()


async def get_token_price(
    orchestrator: MultiSourceOrchestrator, token_ids: List[str]
) -> Dict[str, Any]:
    """Get prices for multiple tokens.

    Args:
        orchestrator: Orchestrator instance.
        token_ids: List of token IDs.

    Returns:
        Dict containing price data.
    """
    request = BlockchainQueryRequest(
        query_type='token_price',
        parameters={'token_ids': token_ids},
        real_time=True,
    )
    response = await orchestrator.execute_query(request)
    return response.to_dict()


async def get_whale_activity(
    orchestrator: MultiSourceOrchestrator, query_id: int, threshold: float
) -> Dict[str, Any]:
    """Get whale activity from Dune Analytics.

    Args:
        orchestrator: Orchestrator instance.
        query_id: Dune query ID for whale tracking.
        threshold: Minimum transaction size to consider.

    Returns:
        Dict containing whale activity data.
    """
    request = BlockchainQueryRequest(
        query_type='whale_tracking',
        parameters={
            'query_id': query_id,
            'query_params': {'threshold': threshold},
        },
    )
    response = await orchestrator.execute_query(request)
    return response.to_dict()


if __name__ == "__main__":
    async def test_orchestrator():
        """Test orchestrator functionality."""
        orchestrator = MultiSourceOrchestrator()

        # Test TVL query
        print("Testing protocol TVL...")
        tvl_result = await get_protocol_tvl(orchestrator, 'aave')
        print(f"Source: {tvl_result['source']}")
        print(f"Confidence: {tvl_result['confidence_score']}")

        # Test token price
        print("\nTesting token prices...")
        price_result = await get_token_price(orchestrator, ['bitcoin', 'ethereum'])
        print(f"Source: {price_result['source']}")

        # Print statistics
        print("\nSource Statistics:")
        stats = orchestrator.get_source_statistics()
        for source, metrics in stats.items():
            print(f"{source}: {metrics}")

    asyncio.run(test_orchestrator())
