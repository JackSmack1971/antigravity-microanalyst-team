# Alternative Data Sources Integration

This document describes the alternative data sources integrated into the Antigravity Microanalyst Team system. These sources provide non-traditional data for enhanced market analysis and early signal detection.

## Overview

Alternative data sources capture market narrative, sentiment shifts, and fundamental development activity that traditional price/volume data may miss. These sources can provide early signals before price action occurs.

## Implemented Data Sources

### 1. News Sentiment Analysis (CryptoPanic)

**Purpose**: Aggregate cryptocurrency news with sentiment indicators

**Data Provided**:
- Sentiment score (-100 to +100)
- Positive/Negative/Neutral breakdown
- News article count
- Community voting on relevance

**API Details**:
- **Provider**: CryptoPanic (https://cryptopanic.com)
- **Cost**: Free tier available (rate limits apply)
- **API Token**: Optional (higher rate limits with token)
- **Setup**: Set `CRYPTOPANIC_API_TOKEN` in `.env` (optional)

**Usage Example**:
```python
from tools.blockchain_orchestrator import MultiSourceOrchestrator, BlockchainQueryRequest

orchestrator = MultiSourceOrchestrator()
request = BlockchainQueryRequest(
    query_type='news_sentiment',
    parameters={'currencies': ['BTC', 'ETH'], 'kind': 'news'}
)
result = await orchestrator.execute_query(request)
```

**Benefits**:
- Captures breaking news impact
- Identifies sentiment shifts before price action
- Aggregates multiple news sources
- Community-validated relevance

---

### 2. Social Media Monitoring (Reddit)

**Purpose**: Track cryptocurrency community sentiment and engagement

**Data Provided**:
- Reddit sentiment score (0-100)
- Engagement metrics (upvotes, comments)
- Post volume analysis
- Community activity trends

**API Details**:
- **Provider**: Reddit API (https://www.reddit.com/dev/api)
- **Cost**: Free with registration
- **Credentials Required**:
  - `REDDIT_CLIENT_ID`
  - `REDDIT_CLIENT_SECRET`
  - `REDDIT_USER_AGENT`
- **Setup**: Create app at https://www.reddit.com/prefs/apps

**Subreddits Monitored**:
- r/cryptocurrency (general crypto discussion)
- r/bitcoin (Bitcoin-specific)
- r/ethereum (Ethereum-specific)
- Custom subreddits as needed

**Usage Example**:
```python
request = BlockchainQueryRequest(
    query_type='reddit_sentiment',
    parameters={'subreddit': 'cryptocurrency', 'limit': 100}
)
result = await orchestrator.execute_query(request)
```

**Benefits**:
- Real-time community sentiment
- Engagement metrics indicate conviction
- Early detection of narrative shifts
- Free and reliable API

---

### 3. Google Trends Data

**Purpose**: Correlate search interest with price movements

**Data Provided**:
- Search interest over time (0-100 scale)
- Trend momentum percentage
- Direction (accelerating/growing/stable/declining)
- Peak and minimum interest levels

**API Details**:
- **Provider**: Google Trends (via pytrends library)
- **Cost**: Free (no API key required)
- **Rate Limits**: Generous (built-in backoff)
- **Setup**: No configuration needed

**Usage Example**:
```python
request = BlockchainQueryRequest(
    query_type='google_trends',
    parameters={'keywords': ['Bitcoin', 'Ethereum'], 'timeframe': 'now 7-d'}
)
result = await orchestrator.execute_query(request)
```

**Timeframes Available**:
- `now 1-H`: Last hour
- `now 4-H`: Last 4 hours
- `now 1-d`: Last day
- `now 7-d`: Last 7 days (default)
- `today 1-m`: Past month
- `today 3-m`: Past 3 months

**Benefits**:
- Leading indicator (search precedes action)
- Retail interest measurement
- Cross-correlation with price
- Zero cost, unlimited usage

---

### 4. GitHub Development Activity

**Purpose**: Monitor cryptocurrency project development health

**Data Provided**:
- Activity score (0-100)
- Development trend (accelerating/growing/stable/slowing/declining)
- Recent commit count
- Repository stars/forks
- Contributor engagement

**API Details**:
- **Provider**: GitHub API (https://api.github.com)
- **Cost**: Free tier
  - Unauthenticated: 60 requests/hour
  - Authenticated: 5,000 requests/hour
- **Setup**: Set `GITHUB_API_TOKEN` in `.env` (optional but recommended)
- **Token Creation**: https://github.com/settings/tokens

**Usage Example**:
```python
request = BlockchainQueryRequest(
    query_type='github_activity',
    parameters={'owner': 'bitcoin', 'repo': 'bitcoin'}
)
result = await orchestrator.execute_query(request)
```

**Key Projects to Monitor**:
- Bitcoin: `bitcoin/bitcoin`
- Ethereum: `ethereum/go-ethereum`
- Solana: `solana-labs/solana`
- Cardano: `input-output-hk/cardano-node`
- Polkadot: `paritytech/polkadot`

**Benefits**:
- Fundamental development strength
- Early warning of project abandonment
- Technical momentum indicator
- Free for most use cases

---

### 5. Options Market Data (Deribit)

**Purpose**: Analyze sophisticated trader positioning via options flow

**Data Provided**:
- Put/Call ratio (by volume and open interest)
- Average implied volatility (IV)
- Market sentiment (bullish/neutral/bearish)
- Total options volume
- Options open interest

**API Details**:
- **Provider**: Deribit (https://www.deribit.com)
- **Cost**: Public endpoints are FREE (no authentication required)
- **Rate Limits**: Generous for public data
- **Setup**: No configuration needed

**Supported Assets**:
- BTC (Bitcoin)
- ETH (Ethereum)

**Usage Example**:
```python
request = BlockchainQueryRequest(
    query_type='options_data',
    parameters={'currency': 'BTC'}
)
result = await orchestrator.execute_query(request)
```

**Interpretation**:
- **P/C Ratio > 1.2**: Bearish (more puts than calls)
- **P/C Ratio 0.8-1.2**: Neutral
- **P/C Ratio < 0.8**: Bullish (more calls than puts)
- **High IV**: Uncertainty, potential large moves expected
- **Low IV**: Complacency, low volatility expected

**Benefits**:
- Smart money positioning
- Volatility expectations
- Risk sentiment gauge
- Completely free access

---

## Integration Architecture

### Adapter Pattern

All alternative data sources follow a consistent adapter pattern:

```python
class DataAdapter:
    def __init__(self, cache: BlockchainDataCache, api_key: Optional[str] = None):
        self.cache = cache
        self.api_key = api_key

    @retry(exponential_backoff)
    async def fetch_data(self, params) -> Dict[str, Any]:
        # 1. Check cache (hot/warm/cold tiers)
        # 2. Fetch from API
        # 3. Handle rate limits with retries
        # 4. Cache result
        # 5. Return data
```

### Caching Strategy

**Three-Tier Cache**:
- **Hot** (1 minute): Real-time data (prices, options)
- **Warm** (5 minutes): Recent data (news, social sentiment)
- **Cold** (24 hours): Historical data (GitHub stats, trends)

**Cache Benefits**:
- Reduces API calls
- Faster response times
- Respects rate limits
- No external dependencies (file-based)

### Error Handling

All adapters implement:
- Exponential backoff retries
- Rate limit detection and waiting
- Graceful degradation (returns error dict, doesn't crash)
- Detailed error messages for debugging

---

## Scout Agent Integration

The Scout Agent has access to all alternative data sources via dedicated tools:

### Available Tools

1. **`fetch_news_sentiment(currencies)`**
   - Fetches crypto news sentiment
   - Default: ['BTC', 'ETH']

2. **`fetch_social_media_sentiment(subreddit)`**
   - Fetches Reddit sentiment
   - Default: 'cryptocurrency'

3. **`fetch_google_trends(keywords)`**
   - Fetches search interest trends
   - Default: ['Bitcoin', 'Ethereum']

4. **`fetch_github_activity(repositories)`**
   - Fetches development metrics
   - Default: Bitcoin and Ethereum repos

5. **`fetch_options_market_data(currency)`**
   - Fetches options flow and IV
   - Default: 'BTC'

### Example Agent Prompt

```python
result = await scout_agent.run(
    "Perform comprehensive market analysis:\n"
    "1. Fetch news sentiment for BTC and ETH\n"
    "2. Fetch Reddit sentiment from r/cryptocurrency\n"
    "3. Fetch Google Trends for 'Bitcoin'\n"
    "4. Fetch GitHub activity for bitcoin/bitcoin\n"
    "5. Fetch BTC options data from Deribit\n\n"
    "Synthesize these alternative data signals with on-chain metrics.",
    deps=deps
)
```

---

## Pydantic Models

Alternative data is structured using Pydantic models for type safety:

```python
class NewsSentimentData(BaseModel):
    sentiment_score: float  # -100 to +100
    positive_pct: float
    negative_pct: float
    total_posts: int

class SocialMediaData(BaseModel):
    reddit_sentiment: float  # 0-100
    engagement_score: float
    total_posts: int

class GoogleTrendsData(BaseModel):
    current_interest: int  # 0-100
    momentum_pct: float
    direction: str

class GitHubActivityData(BaseModel):
    activity_score: float  # 0-100
    trend: str
    recent_commits: int

class OptionsMarketData(BaseModel):
    put_call_ratio: float
    avg_implied_volatility: float
    market_sentiment: str

class AlternativeDataMetrics(BaseModel):
    news_sentiment: Optional[NewsSentimentData]
    social_media: Optional[SocialMediaData]
    google_trends: Optional[GoogleTrendsData]
    github_activity: Optional[GitHubActivityData]
    options_market: Optional[OptionsMarketData]
```

These models are integrated into `SentimentMetrics.alternative_data`.

---

## Setup Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `praw>=7.7.0` (Reddit API)
- `pytrends>=4.9.0` (Google Trends)
- `beautifulsoup4>=4.12.0` (Web scraping)
- `lxml>=4.9.0` (HTML parser)
- `requests>=2.31.0` (HTTP requests)
- `textblob>=0.17.0` (Sentiment analysis)

### 2. Configure API Keys (Optional)

Copy `.env.example` to `.env` and configure:

```bash
# Optional: Higher rate limits
CRYPTOPANIC_API_TOKEN=your_token_here

# Optional: Reddit sentiment
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=crypto-sentiment-analyzer/1.0

# Optional: Higher GitHub rate limits
GITHUB_API_TOKEN=your_github_token
```

**Note**: Most sources work without API keys, but authentication provides:
- Higher rate limits
- More reliable access
- Additional features

### 3. Test Integration

```bash
# Test alternative data adapters
python tools/alternative_data_adapters.py

# Test orchestrator with alternative sources
python tools/blockchain_orchestrator.py

# Test Scout agent with alternative data
python agents/scout_agent.py
```

---

## Use Cases

### 1. Early Signal Detection

**Scenario**: Detect bullish momentum before price breakout

**Data Combination**:
- Google Trends ↗️ (rising search interest)
- Reddit Sentiment > 60 (positive community)
- News Sentiment > 40 (positive headlines)
- Options P/C < 0.8 (bullish positioning)

**Interpretation**: Confluence of bullish alternative signals suggests potential upside before technical breakout.

---

### 2. Fundamental Strength Assessment

**Scenario**: Evaluate long-term project viability

**Data Combination**:
- GitHub Activity > 70 (strong development)
- GitHub Trend: "accelerating" (growing team)
- News Sentiment stable (no negative catalysts)
- Community engagement rising (Reddit scores)

**Interpretation**: Strong fundamentals support long-term holding thesis.

---

### 3. Risk Management

**Scenario**: Detect early warning signs

**Data Combination**:
- GitHub Activity declining (dev exodus)
- News Sentiment < -20 (negative headlines)
- Reddit Sentiment falling (community panic)
- Options IV spiking (volatility expected)

**Interpretation**: Multiple red flags suggest reducing position size.

---

### 4. Volatility Forecasting

**Scenario**: Anticipate major price movements

**Data Combination**:
- Options IV > historical average (big move expected)
- Google Trends spiking (retail FOMO)
- News volume surging (catalyst event)
- Social media engagement 2x normal (viral attention)

**Interpretation**: High probability of large price swing (direction uncertain).

---

## Rate Limits and Best Practices

### CryptoPanic
- **Free**: ~50 requests/hour
- **With Token**: ~300 requests/hour
- **Best Practice**: Cache for 5 minutes (warm tier)

### Reddit API
- **Limit**: 60 requests/minute
- **Best Practice**: Analyze 100 posts max, cache for 5 minutes

### Google Trends
- **Limit**: ~100 requests/hour (soft limit)
- **Best Practice**: Built-in retry logic, cache for 5 minutes

### GitHub API
- **Unauthenticated**: 60/hour
- **Authenticated**: 5,000/hour
- **Best Practice**: Use token, cache for 5 minutes

### Deribit Public API
- **Limit**: Very generous (~100 requests/minute)
- **Best Practice**: Cache for 1 minute (hot tier)

---

## Troubleshooting

### Issue: Reddit API Not Working

**Solution**:
1. Verify credentials in `.env`
2. Ensure Reddit app is created at https://www.reddit.com/prefs/apps
3. Check app type is "script"
4. Verify `user_agent` is unique

### Issue: Google Trends Returns Empty Data

**Solution**:
1. Check keyword spelling (case-sensitive)
2. Use broader timeframe (e.g., 'today 1-m' instead of 'now 1-d')
3. Try alternative keywords ('BTC' vs 'Bitcoin')
4. Wait 60 seconds between requests (rate limiting)

### Issue: GitHub Rate Limit Exceeded

**Solution**:
1. Set `GITHUB_API_TOKEN` in `.env` for 5,000/hour limit
2. Reduce query frequency
3. Cache is working correctly (5 minute warm tier)

### Issue: CryptoPanic Returns No Data

**Solution**:
1. Check currency codes are correct ('BTC' not 'BITCOIN')
2. Verify internet connectivity
3. Try without API token first (public endpoint)
4. Check CryptoPanic service status

---

## Future Enhancements

### Planned Additions

1. **Twitter/X Monitoring**
   - Requires Twitter API v2 (paid)
   - Alternative: Web scraping (terms of service risk)

2. **On-Chain Metrics Enhancement**
   - Whale wallet tracking
   - Exchange flow analysis
   - Gas price correlation

3. **Macro Correlation**
   - Traditional market correlation
   - Sector rotation analysis
   - Risk-on/risk-off signals

4. **Machine Learning Integration**
   - Sentiment prediction models
   - Anomaly detection
   - Signal combination optimization

---

## API Endpoint Reference

### CryptoPanic
```
GET https://cryptopanic.com/api/v1/posts/
Parameters:
  - auth_token (optional)
  - currencies: BTC,ETH
  - kind: news
```

### Reddit (via PRAW)
```python
reddit = praw.Reddit(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)
subreddit = reddit.subreddit('cryptocurrency')
posts = subreddit.hot(limit=100)
```

### Google Trends (via pytrends)
```python
pytrends = TrendReq(hl='en-US', tz=0)
pytrends.build_payload(['Bitcoin'], timeframe='now 7-d')
data = pytrends.interest_over_time()
```

### GitHub
```
GET https://api.github.com/repos/{owner}/{repo}
GET https://api.github.com/repos/{owner}/{repo}/stats/commit_activity
Headers:
  - Authorization: token GITHUB_TOKEN (optional)
```

### Deribit
```
GET https://www.deribit.com/api/v2/public/get_book_summary_by_currency
Parameters:
  - currency: BTC
  - kind: option
```

---

## Contributing

To add new alternative data sources:

1. Create adapter in `tools/alternative_data_adapters.py`
2. Add source type to `DataSourceType` enum
3. Implement executor in `blockchain_orchestrator.py`
4. Add Pydantic model in `models/models.py`
5. Create Scout agent tool in `agents/scout_agent.py`
6. Update documentation
7. Add tests

---

## License and Terms of Service

### Important Notes

- **CryptoPanic**: Review their ToS for commercial use
- **Reddit**: Must comply with Reddit API terms
- **Google Trends**: For research purposes, not commercial forecasting
- **GitHub**: Public data usage allowed, respect rate limits
- **Deribit**: Public data is free, check ToS for restrictions

**Disclaimer**: This system is for educational and research purposes. Always review API provider terms of service before production use.

---

## Support

For issues or questions:
- Check troubleshooting section above
- Review adapter code in `tools/alternative_data_adapters.py`
- Examine orchestrator routing in `tools/blockchain_orchestrator.py`
- Test individual adapters independently

---

**Last Updated**: 2025-12-29
**Version**: 1.0
