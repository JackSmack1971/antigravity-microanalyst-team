# On-Chain Data Sources Documentation

This document provides comprehensive guidance on the blockchain data sources integrated into the Antigravity Microanalyst Team, enabling cost-effective access to on-chain data without expensive premium services.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Data Sources](#data-sources)
4. [Architecture](#architecture)
5. [Usage Examples](#usage-examples)
6. [Performance & Cost Analysis](#performance--cost-analysis)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

## Overview

The system integrates multiple free and freemium blockchain data sources to provide comprehensive on-chain analytics:

- **DeFiLlama**: TVL, protocol metrics, chain data (100% free)
- **CoinGecko**: Token prices, market data (50 calls/min free)
- **Dune Analytics**: Complex SQL queries (1000/day free tier)
- **Etherscan Family**: Transaction data, balances (5 calls/sec free)

### Key Features

✅ **Multi-source orchestration** with automatic fallback
✅ **Intelligent caching** (file-based, no Redis required)
✅ **Rate limit handling** with exponential backoff
✅ **Query complexity assessment** for optimal routing
✅ **Zero cost** for basic usage, scales with free tiers

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Required
OPENROUTER_API_KEY=your_key_here

# Optional (system works without these)
DUNE_API_KEY=your_dune_key
ETHERSCAN_API_KEY=your_etherscan_key
```

**Note**: DeFiLlama and CoinGecko work without API keys!

### 3. Test the Integration

Run the blockchain agent:

```bash
python -m agents.blockchain_agent
```

Or test specific adapters:

```bash
python -m tools.blockchain_adapters
python -m tools.blockchain_orchestrator
```

## Data Sources

### DeFiLlama

**Best for**: TVL data, protocol metrics, DeFi analytics

**Endpoints**:
- Protocol TVL: `/protocol/{protocol}`
- Chain TVL: `/v2/historicalChainTvl/{chain}`
- Stablecoin data: `/stablecoincharts/all`

**Rate Limits**: None (completely free)

**Usage**:
```python
from tools.blockchain_adapters import DeFiLlamaAdapter, BlockchainDataCache

cache = BlockchainDataCache()
adapter = DeFiLlamaAdapter(cache)

# Get Aave TVL
tvl_data = await adapter.get_protocol_tvl('aave')
print(f"Aave TVL: ${tvl_data['tvl']:,.0f}")
```

**Supported Protocols**: aave, uniswap, curve, compound, lido, maker, etc.

### CoinGecko

**Best for**: Token prices, market cap, volume, real-time data

**Endpoints**:
- Simple price: `/simple/price`
- Detailed token data: `/coins/{id}`

**Rate Limits**: 50 calls/minute (free tier)

**Usage**:
```python
from tools.blockchain_adapters import CoinGeckoAdapter

adapter = CoinGeckoAdapter(cache)

# Get BTC and ETH prices
prices = await adapter.get_simple_price(['bitcoin', 'ethereum'])
print(prices)
# {'bitcoin': {'usd': 95000, 'usd_24h_vol': ...}, ...}
```

**Token IDs**: bitcoin, ethereum, cardano, solana, etc. (see [CoinGecko API](https://www.coingecko.com/en/api))

### Dune Analytics

**Best for**: Complex analytics, whale tracking, historical queries

**Endpoints**:
- Execute query: `/query/{query_id}/execute`
- Get results: `/execution/{execution_id}/results`

**Rate Limits**: 1000 queries/day (free tier)

**Usage**:
```python
from tools.blockchain_adapters import DuneAnalyticsAdapter

adapter = DuneAnalyticsAdapter(api_key='your_key', cache=cache)

# Execute a query
results = await adapter.execute_query(
    query_id=12345,
    parameters={'token': 'USDC'}
)
```

**Setup**:
1. Create account at [dune.com](https://dune.com)
2. Fork existing queries or create new ones
3. Get API key from account settings
4. Add to `.env`: `DUNE_API_KEY=xxx`

### Etherscan Family

**Best for**: Transaction history, token balances, contract data

**Supported Chains**:
- Ethereum (etherscan.io)
- BSC (bscscan.com)
- Polygon (polygonscan.com)
- Arbitrum (arbiscan.io)
- Optimism (optimistic.etherscan.io)
- Avalanche (snowtrace.io)

**Rate Limits**: 5 calls/second, 100K calls/day (free tier)

**Usage**:
```python
from tools.blockchain_adapters import EtherscanAdapter

adapter = EtherscanAdapter(
    api_keys={'ethereum': 'your_key'},
    cache=cache
)

# Get token balance
balance = await adapter.get_token_balance(
    chain='ethereum',
    contract_address='0x...', # USDC contract
    address='0x...'  # Wallet address
)

# Get transactions
txs = await adapter.get_transactions(
    chain='ethereum',
    address='0x...',
    limit=100
)
```

## Architecture

### Multi-Source Orchestrator

The orchestrator intelligently routes queries based on complexity and data type:

```
┌─────────────────────────────────────────────┐
│         MultiSourceOrchestrator             │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────────────────────────────┐  │
│  │   Query Complexity Assessment        │  │
│  │   (0.0 - 1.0 score)                  │  │
│  └──────────────────────────────────────┘  │
│                    │                        │
│         ┌──────────┼──────────┐             │
│         ▼          ▼          ▼             │
│   ┌─────────┐ ┌────────┐ ┌─────────┐       │
│   │ Simple  │ │ Medium │ │ Complex │       │
│   │ <0.5    │ │ 0.5-0.8│ │ >0.8    │       │
│   └─────────┘ └────────┘ └─────────┘       │
│        │          │          │              │
│        ▼          ▼          ▼              │
│   ┌─────────────────────────────────┐      │
│   │   Fallback Chain Management     │      │
│   └─────────────────────────────────┘      │
│                    │                        │
│         ┌──────────┼──────────────┐         │
│         ▼          ▼              ▼         │
│   DeFiLlama   CoinGecko    Dune/Etherscan  │
└─────────────────────────────────────────────┘
```

### Caching Strategy

Three-tier caching system optimized for different data types:

| Tier | TTL | Use Case |
|------|-----|----------|
| **Hot** | 1 min | Real-time prices, balances |
| **Warm** | 5 min | Recent market data, TVL |
| **Cold** | 24 hours | Historical analytics, archives |

Cache automatically promotes hot data from warm tier on cache hits.

### Data Flow

```
User Request
    │
    ▼
Blockchain Agent (Pydantic AI)
    │
    ▼
MultiSourceOrchestrator
    │
    ├─► Check Cache (File-based)
    │   └─► Cache Hit? → Return
    │
    ├─► Assess Complexity
    │   └─► Select Primary Source
    │
    ├─► Execute Query
    │   ├─► DeFiLlama Adapter
    │   ├─► CoinGecko Adapter
    │   ├─► Dune Adapter
    │   └─► Etherscan Adapter
    │
    ├─► Handle Rate Limits
    │   └─► Exponential Backoff
    │
    ├─► Fallback on Failure
    │   └─► Try Secondary Sources
    │
    └─► Cache Result
        └─► Return to Agent
```

## Usage Examples

### Example 1: Comprehensive On-Chain Analysis

```python
from agents.blockchain_agent import run_blockchain_agent

# Run comprehensive analysis
result = await run_blockchain_agent(analysis_type="comprehensive")

print(f"Market Sentiment: {result.market_sentiment}")
print(f"TVL: ${result.onchain_metrics.total_value_locked:,.0f}")

for insight in result.key_insights:
    print(f"• {insight}")
```

### Example 2: DeFi Protocol Analysis

```python
# Analyze specific DeFi protocols
result = await run_blockchain_agent(
    analysis_type="defi",
    focus_protocols=['aave', 'compound', 'uniswap']
)

print(result.onchain_metrics.dominant_protocols)
```

### Example 3: Token Market Analysis

```python
# Analyze token metrics
result = await run_blockchain_agent(
    analysis_type="token",
    focus_tokens=['bitcoin', 'ethereum', 'cardano']
)

print(f"Confidence: {result.confidence_score:.2%}")
```

### Example 4: Using Scout Agent with On-Chain Data

```python
from agents.scout_agent import run_scout_agent

# Scout agent now fetches real on-chain data
fundamental_data = await run_scout_agent()

print(fundamental_data.module_2_macro)
print(fundamental_data.module_3_onchain)
print(fundamental_data.module_4_sentiment)
```

### Example 5: Direct Orchestrator Usage

```python
from tools.blockchain_orchestrator import (
    MultiSourceOrchestrator,
    BlockchainQueryRequest,
    get_protocol_tvl,
    get_token_price
)

orchestrator = MultiSourceOrchestrator()

# Get protocol TVL
tvl = await get_protocol_tvl(orchestrator, 'aave')

# Get token prices
prices = await get_token_price(orchestrator, ['bitcoin', 'ethereum'])

# Custom query
request = BlockchainQueryRequest(
    query_type='chain_metrics',
    parameters={'chain': 'Ethereum'},
    priority='high'
)
response = await orchestrator.execute_query(request)
```

### Example 6: Whale Tracking with Dune

```python
# Requires Dune API key and query ID
from tools.blockchain_orchestrator import get_whale_activity

whale_data = await get_whale_activity(
    orchestrator,
    query_id=YOUR_DUNE_QUERY_ID,
    threshold=1000000  # $1M+ transactions
)
```

## Performance & Cost Analysis

### Throughput Comparison

| Solution | Blocks/Sec | Latency | Cost/Month | Setup Time |
|----------|------------|---------|------------|------------|
| **Self-hosted Subsquid** | 50,000+ | <100ms | $50-200 | 4-8h |
| **Our Free APIs** | N/A | 200ms-2s | $0 | 30min |
| **Premium Services** | N/A | <500ms | $500+ | 1h |

### Cost Breakdown

**Free Tier Limits**:
- DeFiLlama: Unlimited
- CoinGecko: 50 calls/min = 72K/day
- Dune: 1000 queries/day
- Etherscan: 100K calls/day

**Effective Daily Capacity**: ~170K+ queries/day across all sources

**Monthly Operating Cost**: $0 (with free tiers)

**Break-even Point vs. Premium**: Immediate (saves $500+/month)

### Query Performance

Average response times (with caching):

- **Cache hit**: <10ms
- **DeFiLlama**: 200-500ms
- **CoinGecko**: 300-800ms
- **Dune Analytics**: 2-10s (query execution)
- **Etherscan**: 500ms-1s

## Advanced Features

### Fallback Chain Configuration

The orchestrator automatically uses fallback chains:

```python
# TVL queries: DeFiLlama → Dune
# Price queries: CoinGecko → DeFiLlama
# Balance queries: Etherscan (primary)
```

Customize fallback behavior:

```python
orchestrator.fallback_chains['tvl'] = [
    DataSourceType.DEFILLAMA,
    DataSourceType.DUNE,
    DataSourceType.CUSTOM
]
```

### Query Statistics

Track source performance:

```python
stats = orchestrator.get_source_statistics()

for source, metrics in stats.items():
    print(f"{source}:")
    print(f"  Success Rate: {metrics['success_rate']:.2%}")
    print(f"  Avg Latency: {metrics['avg_latency_ms']:.0f}ms")
    print(f"  Total Queries: {metrics['total_queries']}")
```

### Custom Cache Directory

```python
orchestrator = MultiSourceOrchestrator(
    cache_dir='/path/to/custom/cache'
)
```

### Adaptive Routing

The orchestrator learns from query patterns and automatically optimizes routing:

- Tracks success rates per source
- Monitors average latency
- Adjusts fallback preferences based on reliability

## Troubleshooting

### Rate Limit Errors

**Symptom**: `RateLimitError` exceptions

**Solution**:
1. Check you're not exceeding free tier limits
2. The system automatically retries with exponential backoff
3. Consider adding API keys to increase limits
4. Distribute queries across multiple sources

```python
# Monitor rate limit status
try:
    result = await orchestrator.execute_query(request)
except RateLimitError as e:
    print(f"Rate limited: {e}")
    # System will automatically retry with backoff
```

### Cache Issues

**Symptom**: Stale data or cache errors

**Solution**:
1. Clear cache directory: `rm -rf data/cache/`
2. Cache automatically expires based on TTL
3. Force fresh data by bypassing cache:

```python
# Clear cache for fresh data
import shutil
shutil.rmtree('data/cache/', ignore_errors=True)
```

### API Key Not Working

**Symptom**: "API key not configured" errors

**Solution**:
1. Verify `.env` file exists in project root
2. Check key format: `DUNE_API_KEY=xxx` (no quotes)
3. Restart Python process after editing `.env`
4. For Dune: verify key at [dune.com/settings](https://dune.com/settings)

### Slow Queries

**Symptom**: Queries taking >10 seconds

**Solution**:
1. Check if Dune query is executing (they can take 5-30s)
2. Use `use_latest=True` for Dune to get cached results:

```python
result = await adapter.get_latest_result(query_id)
```

3. Implement request timeouts:

```python
result = await asyncio.wait_for(
    orchestrator.execute_query(request),
    timeout=30
)
```

### Import Errors

**Symptom**: `ModuleNotFoundError` for aiohttp or tenacity

**Solution**:
```bash
pip install -r requirements.txt --upgrade
```

## Best Practices

1. **Use Caching**: Always enable caching for production use
2. **Monitor Limits**: Track query counts to stay within free tiers
3. **Implement Timeouts**: Set reasonable timeouts for queries
4. **Handle Errors**: Gracefully handle rate limits and API failures
5. **Cite Sources**: Always include `data_sources_used` in reports
6. **Cache Warm-up**: Pre-fetch common queries during off-peak hours
7. **Batch Requests**: Group related queries when possible

## Next Steps

### Potential Enhancements

1. **Self-Hosted Indexers**: Deploy Subsquid for 50,000+ blocks/sec
2. **Redis Caching**: Add Redis for distributed caching
3. **Custom Dune Queries**: Create specialized analytics queries
4. **Webhook Integration**: Real-time alerts for whale movements
5. **GraphQL Endpoints**: Add The Graph for decentralized queries

### Resources

- [DeFiLlama API Docs](https://defillama.com/docs/api)
- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
- [Dune Analytics](https://dune.com/docs/api/)
- [Etherscan API](https://docs.etherscan.io/)
- [Subsquid Documentation](https://docs.subsquid.io/)

## Support

For issues or questions:
1. Check this documentation
2. Review example code in `agents/blockchain_agent.py`
3. Run test suites: `python -m tools.blockchain_adapters`
4. Open issue on GitHub

---

**Last Updated**: 2025-12-29
**Version**: 1.0.0
