"""
Blockchain Data Adapters module for on-chain data fetching.

This module provides adapters for multiple free blockchain data sources including:
- DeFiLlama (TVL, yields, fees, volumes)
- Dune Analytics (complex queries)
- CoinGecko (token metrics, prices)
- Etherscan Family (transaction data, balances)

All adapters are designed to work with free API tiers and include
intelligent caching and fallback mechanisms.
"""
import os
import json
import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import aiohttp
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)


class RateLimitError(Exception):
    """Exception raised when API rate limits are exceeded."""
    pass


class BlockchainDataCache:
    """Simple file-based caching for blockchain data.

    Falls back to file-based caching if Redis is not available.
    Supports multi-tier TTL for different data types.
    """

    def __init__(self, cache_dir: str = "data/cache"):
        """Initialize cache with directory.

        Args:
            cache_dir: Directory to store cache files.
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # Multi-tier TTL in seconds
        self.tiered_ttl = {
            'hot': 60,      # 1 minute for real-time data
            'warm': 300,    # 5 minutes for recent data
            'cold': 86400   # 24 hours for historical data
        }

    def _get_cache_path(self, key: str, tier: str = 'hot') -> str:
        """Generate cache file path.

        Args:
            key: Cache key.
            tier: Cache tier (hot/warm/cold).

        Returns:
            str: Full path to cache file.
        """
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{tier}_{key_hash}.json")

    async def get(self, key: str, tier: str = 'hot') -> Optional[Dict]:
        """Retrieve data from cache.

        Args:
            key: Cache key.
            tier: Cache tier to check.

        Returns:
            Optional[Dict]: Cached data or None if not found or expired.
        """
        cache_path = self._get_cache_path(key, tier)

        if not os.path.exists(cache_path):
            # Try warm cache if hot misses
            if tier == 'hot':
                return await self.get(key, 'warm')
            return None

        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)

            # Check if expired
            cached_time = datetime.fromisoformat(cached['timestamp'])
            ttl = self.tiered_ttl[tier]

            if datetime.utcnow() - cached_time > timedelta(seconds=ttl):
                os.remove(cache_path)
                return None

            return cached['data']

        except Exception:
            return None

    async def set(self, key: str, data: Dict, tier: str = 'hot'):
        """Store data in cache.

        Args:
            key: Cache key.
            data: Data to cache.
            tier: Cache tier for TTL management.
        """
        cache_path = self._get_cache_path(key, tier)

        cached = {
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }

        with open(cache_path, 'w') as f:
            json.dump(cached, f, indent=2, default=str)


class DeFiLlamaAdapter:
    """Adapter for DeFiLlama free API.

    DeFiLlama provides completely free access to:
    - TVL (Total Value Locked) data
    - Protocol metrics
    - Chain metrics
    - Yields and APY
    - Fees and volumes

    No API key required for most endpoints.
    """

    BASE_URL = "https://api.llama.fi"

    def __init__(self, cache: BlockchainDataCache):
        """Initialize DeFiLlama adapter.

        Args:
            cache: Cache instance for data persistence.
        """
        self.cache = cache

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_protocol_tvl(self, protocol: str) -> Dict[str, Any]:
        """Get TVL data for a specific protocol.

        Args:
            protocol: Protocol slug (e.g., 'uniswap', 'aave').

        Returns:
            Dict containing TVL data and chain breakdown.

        Example:
            >>> adapter = DeFiLlamaAdapter(cache)
            >>> data = await adapter.get_protocol_tvl('aave')
            >>> print(data['tvl'])
        """
        cache_key = f"defillama:protocol:{protocol}"

        # Try cache first
        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        url = f"{self.BASE_URL}/protocol/{protocol}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 429:
                    raise RateLimitError("DeFiLlama rate limit exceeded")

                response.raise_for_status()
                data = await response.json()

                # Cache for 5 minutes
                await self.cache.set(cache_key, data, 'warm')

                return data

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def get_chain_tvl(self, chain: str) -> Dict[str, Any]:
        """Get TVL data for a specific blockchain.

        Args:
            chain: Chain name (e.g., 'Ethereum', 'BSC', 'Polygon').

        Returns:
            Dict containing chain TVL history.
        """
        cache_key = f"defillama:chain:{chain}"

        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        url = f"{self.BASE_URL}/v2/historicalChainTvl/{chain}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                await self.cache.set(cache_key, data, 'warm')
                return data

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def get_stablecoin_charts(self, stablecoin: Optional[str] = None) -> Dict[str, Any]:
        """Get stablecoin market cap data.

        Args:
            stablecoin: Optional specific stablecoin (e.g., 'USDT', 'USDC').

        Returns:
            Dict containing stablecoin market cap data.
        """
        cache_key = f"defillama:stablecoin:{stablecoin or 'all'}"

        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        url = f"{self.BASE_URL}/stablecoincharts/all"
        if stablecoin:
            url += f"?stablecoin={stablecoin}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

                await self.cache.set(cache_key, data, 'warm')
                return data


class DuneAnalyticsAdapter:
    """Adapter for Dune Analytics free API.

    Dune provides free tier access to:
    - Execute existing queries (1000/day free tier)
    - Access community dashboards
    - SQL-based blockchain analytics

    Requires API key (free tier available).
    """

    BASE_URL = "https://api.dune.com/api/v1"

    def __init__(self, api_key: Optional[str], cache: BlockchainDataCache):
        """Initialize Dune Analytics adapter.

        Args:
            api_key: Dune API key (get free tier at dune.com).
            cache: Cache instance for data persistence.
        """
        self.api_key = api_key or os.getenv("DUNE_API_KEY")
        self.cache = cache
        self.headers = {
            "X-Dune-API-Key": self.api_key
        } if self.api_key else {}

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def execute_query(self, query_id: int, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute a Dune Analytics query.

        Args:
            query_id: Dune query ID.
            parameters: Optional query parameters.

        Returns:
            Dict containing query execution results.

        Example:
            >>> adapter = DuneAnalyticsAdapter(api_key, cache)
            >>> results = await adapter.execute_query(12345, {"token": "USDC"})
        """
        if not self.api_key:
            return {"error": "Dune API key not configured"}

        cache_key = f"dune:query:{query_id}:{json.dumps(parameters or {}, sort_keys=True)}"

        # Try cache first (queries are often historical)
        if cached := await self.cache.get(cache_key, 'cold'):
            return cached

        # First, trigger execution
        url = f"{self.BASE_URL}/query/{query_id}/execute"

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=parameters or {}) as response:
                if response.status == 429:
                    raise RateLimitError("Dune rate limit exceeded")

                response.raise_for_status()
                execution = await response.json()
                execution_id = execution.get('execution_id')

            # Poll for results
            status_url = f"{self.BASE_URL}/execution/{execution_id}/status"

            for _ in range(30):  # Max 30 attempts (60 seconds)
                await asyncio.sleep(2)

                async with session.get(status_url, headers=self.headers) as response:
                    response.raise_for_status()
                    status = await response.json()

                    if status.get('state') == 'QUERY_STATE_COMPLETED':
                        # Get results
                        results_url = f"{self.BASE_URL}/execution/{execution_id}/results"
                        async with session.get(results_url, headers=self.headers) as results_response:
                            results_response.raise_for_status()
                            data = await results_response.json()

                            # Cache for 24 hours (historical data)
                            await self.cache.set(cache_key, data, 'cold')
                            return data

                    elif status.get('state') == 'QUERY_STATE_FAILED':
                        return {"error": "Query execution failed"}

            return {"error": "Query execution timeout"}

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def get_latest_result(self, query_id: int) -> Dict[str, Any]:
        """Get the latest cached result for a query.

        Args:
            query_id: Dune query ID.

        Returns:
            Dict containing latest query results.
        """
        if not self.api_key:
            return {"error": "Dune API key not configured"}

        cache_key = f"dune:latest:{query_id}"

        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        url = f"{self.BASE_URL}/query/{query_id}/results"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 429:
                    raise RateLimitError("Dune rate limit exceeded")

                response.raise_for_status()
                data = await response.json()

                # Cache for 5 minutes
                await self.cache.set(cache_key, data, 'warm')
                return data


class CoinGeckoAdapter:
    """Adapter for CoinGecko free API.

    CoinGecko provides free tier access to:
    - Token prices and market data
    - Historical data
    - Market cap rankings
    - Volume data

    Free tier: 50 calls/minute (no API key required).
    """

    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, cache: BlockchainDataCache):
        """Initialize CoinGecko adapter.

        Args:
            cache: Cache instance for data persistence.
        """
        self.cache = cache

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_token_data(self, token_id: str) -> Dict[str, Any]:
        """Get comprehensive token data.

        Args:
            token_id: CoinGecko token ID (e.g., 'bitcoin', 'ethereum').

        Returns:
            Dict containing price, market cap, volume, and other metrics.

        Example:
            >>> adapter = CoinGeckoAdapter(cache)
            >>> data = await adapter.get_token_data('bitcoin')
            >>> print(data['market_data']['current_price']['usd'])
        """
        cache_key = f"coingecko:token:{token_id}"

        # Try cache first
        if cached := await self.cache.get(cache_key, 'hot'):
            return cached

        url = f"{self.BASE_URL}/coins/{token_id}"
        params = {
            'localization': 'false',
            'tickers': 'false',
            'community_data': 'true',
            'developer_data': 'false'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    raise RateLimitError("CoinGecko rate limit exceeded")

                response.raise_for_status()
                data = await response.json()

                # Cache for 1 minute
                await self.cache.set(cache_key, data, 'hot')
                return data

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def get_simple_price(self, token_ids: List[str], vs_currencies: List[str] = ['usd']) -> Dict[str, Any]:
        """Get simple price data for multiple tokens.

        Args:
            token_ids: List of CoinGecko token IDs.
            vs_currencies: List of currencies (default: USD).

        Returns:
            Dict mapping token IDs to prices.
        """
        cache_key = f"coingecko:price:{','.join(sorted(token_ids))}"

        if cached := await self.cache.get(cache_key, 'hot'):
            return cached

        url = f"{self.BASE_URL}/simple/price"
        params = {
            'ids': ','.join(token_ids),
            'vs_currencies': ','.join(vs_currencies),
            'include_24hr_vol': 'true',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                await self.cache.set(cache_key, data, 'hot')
                return data


class EtherscanAdapter:
    """Adapter for Etherscan-family APIs.

    Supports Etherscan, BSCScan, PolygonScan, etc.
    Free tier: 5 calls/second, 100K calls/day.

    Provides:
    - Transaction history
    - Token balances
    - Contract data
    - Gas prices
    """

    EXPLORERS = {
        'ethereum': 'https://api.etherscan.io/api',
        'bsc': 'https://api.bscscan.com/api',
        'polygon': 'https://api.polygonscan.com/api',
        'arbitrum': 'https://api.arbiscan.io/api',
        'optimism': 'https://api-optimistic.etherscan.io/api',
        'avalanche': 'https://api.snowtrace.io/api',
    }

    def __init__(self, api_keys: Optional[Dict[str, str]], cache: BlockchainDataCache):
        """Initialize Etherscan adapter.

        Args:
            api_keys: Dict mapping chain names to API keys.
            cache: Cache instance for data persistence.
        """
        self.api_keys = api_keys or {}
        self.cache = cache

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(RateLimitError)
    )
    async def get_token_balance(self, chain: str, contract_address: str, address: str) -> Dict[str, Any]:
        """Get ERC20 token balance for an address.

        Args:
            chain: Chain name (e.g., 'ethereum', 'bsc').
            contract_address: Token contract address.
            address: Wallet address to check.

        Returns:
            Dict containing balance data.
        """
        cache_key = f"etherscan:{chain}:balance:{contract_address}:{address}"

        if cached := await self.cache.get(cache_key, 'hot'):
            return cached

        base_url = self.EXPLORERS.get(chain)
        if not base_url:
            return {"error": f"Unsupported chain: {chain}"}

        params = {
            'module': 'account',
            'action': 'tokenbalance',
            'contractaddress': contract_address,
            'address': address,
            'tag': 'latest'
        }

        # Add API key if available
        if api_key := self.api_keys.get(chain) or os.getenv(f"{chain.upper()}_SCAN_API_KEY"):
            params['apikey'] = api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                if response.status == 429:
                    raise RateLimitError(f"{chain} explorer rate limit exceeded")

                response.raise_for_status()
                data = await response.json()

                # Cache for 1 minute
                await self.cache.set(cache_key, data, 'hot')
                return data

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    async def get_transactions(self, chain: str, address: str, limit: int = 100) -> Dict[str, Any]:
        """Get transaction history for an address.

        Args:
            chain: Chain name.
            address: Wallet address.
            limit: Maximum number of transactions.

        Returns:
            Dict containing transaction history.
        """
        cache_key = f"etherscan:{chain}:txs:{address}:{limit}"

        if cached := await self.cache.get(cache_key, 'warm'):
            return cached

        base_url = self.EXPLORERS.get(chain)
        if not base_url:
            return {"error": f"Unsupported chain: {chain}"}

        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'page': 1,
            'offset': limit,
            'sort': 'desc'
        }

        if api_key := self.api_keys.get(chain) or os.getenv(f"{chain.upper()}_SCAN_API_KEY"):
            params['apikey'] = api_key

        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                # Cache for 5 minutes
                await self.cache.set(cache_key, data, 'warm')
                return data


# Example usage and testing functions
async def test_adapters():
    """Test all blockchain data adapters."""
    cache = BlockchainDataCache()

    # Test DeFiLlama
    print("Testing DeFiLlama...")
    defillama = DeFiLlamaAdapter(cache)
    aave_tvl = await defillama.get_protocol_tvl('aave')
    print(f"Aave TVL: ${aave_tvl.get('tvl', 0):,.0f}")

    # Test CoinGecko
    print("\nTesting CoinGecko...")
    coingecko = CoinGeckoAdapter(cache)
    btc_data = await coingecko.get_simple_price(['bitcoin', 'ethereum'])
    print(f"BTC: ${btc_data.get('bitcoin', {}).get('usd', 0):,.0f}")

    print("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(test_adapters())
