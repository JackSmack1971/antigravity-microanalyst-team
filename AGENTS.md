# Agent Architecture Documentation

## Overview

The Antigravity Microanalyst Team is a multi-agent system built with **PydanticAI** and **OpenRouter** for cryptocurrency market analysis. The architecture employs specialized AI agents that collaborate to gather data, perform analysis, and generate trading directives.

This document provides a comprehensive guide to the agent architecture, implementation patterns, and data flow throughout the system.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Agents](#core-agents)
3. [Agent Factory & Configuration](#agent-factory--configuration)
4. [Dependency Injection System](#dependency-injection-system)
5. [Data Models](#data-models)
6. [Multi-Source Orchestration](#multi-source-orchestration)
7. [Agent Pipeline Flow](#agent-pipeline-flow)
8. [Tools & Capabilities](#tools--capabilities)
9. [Production Features](#production-features)
10. [Extension Guide](#extension-guide)

---

## System Architecture

### High-Level Design

The system follows a modular, pipeline-based architecture where specialized agents perform distinct roles:

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION PHASE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │ Quant Agent  │    │ Scout Agent  │    │  Blockchain  │      │
│  │              │    │              │    │    Agent     │      │
│  │ Technical    │    │ Fundamental  │    │              │      │
│  │ Analysis     │    │ & Macro      │    │  On-Chain    │      │
│  │              │    │              │    │  Analysis    │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│         └───────────────────┴───────────────────┘               │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                     AGGREGATION PHASE                            │
├────────────────────────────┼────────────────────────────────────┤
│                            │                                    │
│                  ┌─────────▼──────────┐                         │
│                  │  Coordinator Agent │                         │
│                  │                    │                         │
│                  │  Data Aggregation  │                         │
│                  │  Master State Gen  │                         │
│                  └─────────┬──────────┘                         │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                     ANALYSIS PHASE                               │
├────────────────────────────┼────────────────────────────────────┤
│                            │                                    │
│                  ┌─────────▼──────────┐                         │
│                  │ Lead Analyst Agent │                         │
│                  │                    │                         │
│                  │  Logic Matrix      │                         │
│                  │  Strategy Synth    │                         │
│                  └─────────┬──────────┘                         │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                     OUTPUT PHASE                                 │
├────────────────────────────┼────────────────────────────────────┤
│                            │                                    │
│                  ┌─────────▼──────────┐                         │
│                  │   Editor Agent     │                         │
│                  │                    │                         │
│                  │  Report Generation │                         │
│                  │  Human-Readable    │                         │
│                  └─────────┬──────────┘                         │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│              COMPLEMENTARY ANALYSIS PHASE (OPTIONAL)             │
├────────────────────────────┼────────────────────────────────────┤
│                            │                                    │
│  ┌─────────────┐  ┌───────▼─────────┐  ┌──────────────┐       │
│  │   Risk      │  │   Scenario      │  │   Anomaly    │       │
│  │  Manager    │  │   Planner       │  │  Detection   │       │
│  │             │  │                 │  │              │       │
│  │ Position    │  │ What-If         │  │ Pattern      │       │
│  │ Sizing &    │  │ Scenarios &     │  │ Detection &  │       │
│  │ Stop-Loss   │  │ Probabilities   │  │ Alerts       │       │
│  └─────────────┘  └─────────────────┘  └──────────────┘       │
│                                                                   │
│                  ┌─────────────────┐                            │
│                  │   Validator     │                            │
│                  │                 │                            │
│                  │  QA & Logic     │                            │
│                  │  Consistency    │                            │
│                  └─────────────────┘                            │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

### Architecture Principles

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Type Safety**: Pydantic models ensure data integrity throughout the pipeline
3. **Dependency Injection**: Clean dependency management via `CryptoDependencies`
4. **Resilience**: Exponential backoff, retries, and fallback chains for production reliability
5. **Observability**: Structured outputs persisted as JSON artifacts for auditing

---

## Core Agents

### 1. Quant Agent (`agents/quant_agent.py`)

**Purpose**: Performs technical analysis on cryptocurrency price data.

**Model**: `openai/gpt-4o-mini` via OpenRouter

**Input Dependencies**:
- `CryptoDependencies` (symbol, http_client)

**Output Type**: `TechnicalData`

**Tools**:
- `fetch_market_data()`: Fetches OHLCV data from yfinance, calculates EMA-200, RSI-14, volume metrics, and price volatility

**Responsibilities**:
- Calculate technical indicators (EMA, RSI)
- Identify market regime (Trending_Up, Trending_Down, Consolidation)
- Assess market microstructure (funding rate bias, OI trends, squeeze risk)
- Generate risk profiles (support/resistance zones, invalidation stops)

**Output Artifact**: `data/technical_data.json`

**Example Usage**:
```bash
python -m agents.quant_agent BTC-USD
```

---

### 2. Scout Agent (`agents/scout_agent.py`)

**Purpose**: Gathers fundamental, macro-economic, and alternative data sources.

**Model**: `openai/gpt-4o-mini` via OpenRouter

**Input Dependencies**:
- `CryptoDependencies`
- Multi-source orchestrator for blockchain data
- Alternative data adapters

**Output Type**: `FundamentalData`

**Tools**:
- `fetch_macro_data()`: Retrieves S&P 500 and DXY (US Dollar Index) levels
- `fetch_defi_tvl_data()`: Gets Total Value Locked for DeFi protocols (DeFiLlama)
- `fetch_crypto_market_data()`: Fetches token prices and market data (CoinGecko)
- `fetch_news_sentiment()`: Analyzes news sentiment from CryptoPanic
- `fetch_social_media_sentiment()`: Monitors Reddit (r/cryptocurrency, r/bitcoin)
- `fetch_google_trends()`: Tracks search interest correlation
- `fetch_github_activity()`: Measures development activity
- `fetch_options_market_data()`: Retrieves Deribit options flow (P/C ratios, IV)

**Responsibilities**:
- Monitor macro regime (Risk_On vs Risk_Off)
- Track on-chain metrics (exchange flows, active addresses, whale activity)
- Analyze sentiment signals (Fear & Greed Index, social volume)
- Integrate alternative data for early signal detection

**Output Artifact**: `data/fundamental_data.json`

**Data Sources**:
- **Free Tier**: DeFiLlama (unlimited), CoinGecko (50 calls/min)
- **Optional API Keys**: Dune Analytics (1000/day), Etherscan (100K/day), CryptoPanic, GitHub, Deribit

**Example Usage**:
```bash
python -m agents.scout_agent BTC
```

---

### 3. Blockchain Agent (`agents/blockchain_agent.py`)

**Purpose**: Specialized on-chain analysis using multi-source orchestration.

**Model**: `openai/gpt-4o-mini` via OpenRouter

**Input Dependencies**:
- `CryptoDependencies`
- `MultiSourceOrchestrator`

**Output Type**: `BlockchainAnalysisResult`

**Tools**:
- `get_defi_protocol_metrics()`: Fetch protocol TVL and chain breakdown
- `get_token_market_data()`: Real-time prices, volume, market cap
- `get_whale_wallet_activity()`: Track large holder movements
- `query_blockchain_data()`: Complex on-chain queries via Dune Analytics

**Responsibilities**:
- Analyze DeFi protocol health via TVL trends
- Monitor whale accumulation patterns
- Track exchange inflows/outflows
- Assess network activity and adoption metrics

**Key Features**:
- **Multi-source fallback**: Automatically switches between DeFiLlama → CoinGecko → Dune → Etherscan
- **Intelligent caching**: File-based three-tier cache (hot/warm/cold) reduces API calls
- **Query complexity routing**: Routes simple queries to fast sources, complex queries to Dune

**Output Artifact**: `data/blockchain_analysis.json`

**Example Usage**:
```bash
python -m agents.blockchain_agent
```

---

### 4. Coordinator Agent (`agents/coordinator_agent.py`)

**Purpose**: Aggregates data from Quant and Scout agents into a unified Master State.

**Model**: `openai/gpt-4o-mini` via OpenRouter

**Input Dependencies**:
- `CryptoDependencies`

**Output Type**: `MasterState`

**Tools**:
- `load_technical_data()`: Reads `technical_data.json`
- `load_fundamental_data()`: Reads `fundamental_data.json`

**Responsibilities**:
- Merge technical and fundamental data
- Validate data completeness
- Generate unified timestamp
- Prepare data for Lead Analyst consumption

**Output Artifact**: `data/master_state.json`

**Data Model**:
```python
class MasterState(BaseModel):
    technical: TechnicalData
    fundamental: FundamentalData
    status: str
    aggregation_timestamp: datetime
```

---

### 5. Lead Analyst Agent (`agents/analyst_agent.py`)

**Purpose**: Synthesizes Master State into trading directives using a strict Logic Matrix.

**Model**: `openai/gpt-4o` via OpenRouter (uses more capable model for complex reasoning)

**Input Dependencies**:
- `CryptoDependencies`

**Output Type**: `FinalDirective`

**Tools**:
- `get_master_state()`: Loads aggregated market data

**Logic Matrix** (Hardcoded Boolean Rules):

1. **Macro Veto**:
   - IF `macro_regime == 'Risk_Off'` AND `technical.regime == 'Trending_Up'`
   - THEN `directive = 'Neutral'` (Macro overrides Technicals)

2. **Structure Priority**:
   - IF `technical.regime == 'Trending_Up'` AND `sentiment_signal == 'Sell'`
   - THEN IGNORE sentiment (Trend > Contrarian Signal)

3. **Liquidity Filter**:
   - IF `squeeze_risk == 'High'` OR `funding_rate_bias == 'Extreme'`
   - THEN reduce exposure (mentioned in thesis_summary)

**Responsibilities**:
- Apply Logic Matrix to Master State
- Generate stance (Aggressive_Long | Defensive_Long | Neutral | Tactical_Short)
- Set leverage cap (1x | 3x | 5x)
- Assign conviction score (0-100)
- Provide detailed thesis summary

**Output Artifact**: `data/FINAL_DIRECTIVE_YYYYMMDD.json`

**Output Validation**:
- Ensures thesis summary is at least 50 characters
- Uses `@analyst_agent.output_validator` decorator
- Raises `ModelRetry` if output is insufficient

**Production Resilience**:
- Exponential backoff with `tenacity`
- Custom `RateLimitError` handling for 429 responses
- 3 retry attempts with 2s → 4s → 8s backoff

---

### 6. Editor Agent (`agents/editor_agent.py`)

**Purpose**: Transforms technical directives into polished executive summaries.

**Model**: `openai/gpt-4o-mini` via OpenRouter

**Input Dependencies**:
- `CryptoDependencies`

**Output Type**: `str` (Markdown-formatted report)

**Tools**:
- `get_final_directive()`: Loads directive from Lead Analyst

**Responsibilities**:
- Convert JSON directive to human-readable prose
- Structure report with executive summary, market assessment, strategy recommendation
- Maintain professional tone suitable for stakeholders
- Highlight key risk factors and confidence levels

**Output Artifact**: `reports/EXECUTIVE_SUMMARY_YYYYMMDD.md`

**Report Structure**:
```markdown
# Executive Summary - [Date]

## Market Assessment
[High-level market conditions]

## Strategy Recommendation
[Actionable directive with rationale]

## Risk Considerations
[Key risk factors and invalidation levels]

## Confidence Level
[Overall confidence with caveats]
```

**Example Usage**:
```bash
python -m agents.editor_agent
```

---

### 7. Risk Manager Agent (`agents/risk_manager_agent.py`)

**Purpose**: Dedicated risk assessment and position sizing recommendations.

**Model**: `openai/gpt-4o-mini` via OpenRouter

**Input Dependencies**:
- `CryptoDependencies`

**Output Type**: `RiskAssessment`

**Tools**:
- `load_master_state()`: Loads aggregated market data for risk analysis
- `load_final_directive()`: Retrieves current directive and stance
- `calculate_position_metrics()`: Calculates position sizing based on volatility and risk tolerance

**Responsibilities**:
- Calculate appropriate position sizes based on portfolio risk tolerance
- Monitor correlation risks across crypto assets
- Assess tail risk scenarios (black swan events)
- Generate stop-loss and take-profit recommendations
- Estimate maximum drawdown based on volatility
- Provide risk-adjusted leverage recommendations

**Output Artifact**: `data/risk_assessment.json`

**Output Model**:
```python
class RiskAssessment(BaseModel):
    position_size_btc: float
    portfolio_risk_percentage: float
    stop_loss_price: float
    take_profit_targets: List[float]
    max_drawdown_estimate: float
    tail_risk_score: int  # 0-100
    correlation_warning: Optional[str]
```

**Example Usage**:
```bash
python -m agents.risk_manager_agent BTC-USD 10000 2.0
```

---

### 8. Scenario Planner Agent (`agents/scenario_planner_agent.py`)

**Purpose**: Generate what-if market scenarios with probability assessments.

**Model**: `openai/gpt-4o` via OpenRouter (uses more capable model for complex scenario analysis)

**Input Dependencies**:
- `CryptoDependencies`

**Output Type**: `ScenarioAnalysis`

**Tools**:
- `load_master_state()`: Loads market data for scenario modeling
- `load_final_directive()`: Retrieves current analytical stance
- `calculate_price_targets()`: Calculates scenario-based price targets using technical levels

**Responsibilities**:
- Model bull/bear/base case market scenarios
- Assess impact of macro events (Fed decisions, regulatory changes)
- Generate probability-weighted outcomes
- Identify key price levels and catalysts
- Define invalidation levels for each scenario
- Provide timeframe estimates for scenario realization

**Output Artifact**: `data/scenario_analysis.json`

**Output Model**:
```python
class ScenarioAnalysis(BaseModel):
    scenarios: List[MarketScenario]
    most_likely_scenario: str
    probability_distribution: Dict[str, float]
    key_catalysts: List[str]
    invalidation_levels: Dict[str, float]
```

**Example Usage**:
```bash
python -m agents.scenario_planner_agent BTC-USD "1 week"
```

---

### 9. Anomaly Detection Agent (`agents/anomaly_detection_agent.py`)

**Purpose**: Identify unusual market behavior and potential trading opportunities.

**Model**: `openai/gpt-4o-mini` via OpenRouter

**Input Dependencies**:
- `CryptoDependencies`

**Output Type**: `AnomalyReport`

**Tools**:
- `load_technical_data()`: Loads technical indicators for anomaly detection
- `load_fundamental_data()`: Loads on-chain and sentiment data
- `detect_statistical_anomalies()`: Performs z-score based anomaly detection

**Responsibilities**:
- Detect volume spikes and unusual price movements
- Identify extreme technical indicator readings
- Flag unusual on-chain activity (whale movements, exchange flows)
- Monitor sentiment extremes (Fear & Greed Index)
- Detect microstructure anomalies (funding rate extremes, OI spikes)
- Flag macro regime shifts or correlation breakdowns
- Provide actionable recommendations based on anomalies

**Output Artifact**: `data/anomaly_report.json`

**Output Model**:
```python
class AnomalyReport(BaseModel):
    anomalies_detected: List[Anomaly]
    severity_scores: Dict[str, int]
    recommended_actions: List[str]
    monitoring_alerts: List[str]
```

**Example Usage**:
```bash
python -m agents.anomaly_detection_agent BTC-USD
```

---

### 10. Validator Agent (`agents/validator_agent.py`)

**Purpose**: Cross-check analysis outputs for consistency and quality.

**Model**: `openai/gpt-4o` via OpenRouter (uses more capable model for complex validation logic)

**Input Dependencies**:
- `CryptoDependencies`

**Output Type**: `ValidationReport`

**Tools**:
- `load_technical_data()`: Loads technical data for validation
- `load_fundamental_data()`: Loads fundamental data for validation
- `load_master_state()`: Loads aggregated state for cross-checking
- `load_final_directive()`: Loads directive for logic validation
- `validate_data_integrity()`: Validates field consistency across outputs

**Responsibilities**:
- Validate that Quant + Scout data matches Coordinator output
- Check for logical inconsistencies in Analyst directives
- Flag contradictions between stance and market conditions
- Verify that conviction scores align with evidence strength
- Detect unsupported claims in thesis summaries
- Assess overall data quality and consistency
- Generate quality scores for consistency, data, and logic

**Output Artifact**: `data/validation_report.json`

**Output Model**:
```python
class ValidationReport(BaseModel):
    validation_passed: bool
    issues_found: List[ValidationIssue]
    consistency_score: int  # 0-100
    data_quality_score: int  # 0-100
    logic_quality_score: int  # 0-100
    summary: str
```

**Example Usage**:
```bash
python -m agents.validator_agent BTC-USD
```

---

## Agent Factory & Configuration

### Factory Pattern (`config/agent_factory.py`)

The `agent_factory` module provides standardized agent creation with production-grade settings.

**Key Functions**:

1. **`create_openrouter_model(model_name: str)`**
   - Initializes OpenAI-compatible model for OpenRouter
   - Loads `OPENROUTER_API_KEY` from environment
   - Sets base URL to `https://openrouter.ai/api/v1`

2. **`create_agent(model_name, system_prompt, deps_type, result_type)`**
   - Creates fully configured PydanticAI Agent
   - Applies standard `ModelSettings`:
     - `temperature=0.1` (analytical consistency)
     - `max_tokens=2000`
     - `timeout=60.0s`

**Example**:
```python
from config.agent_factory import create_agent
from models.models import TechnicalData

quant_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt="You are a Quantitative Analyst...",
    deps_type=CryptoDependencies,
    result_type=TechnicalData
)
```

### Model Selection Strategy

| Agent | Model | Rationale |
|-------|-------|-----------|
| Quant | `gpt-4o-mini` | Fast, cost-effective for technical calculations |
| Scout | `gpt-4o-mini` | High throughput for multi-source data gathering |
| Blockchain | `gpt-4o-mini` | Efficient on-chain data interpretation |
| Coordinator | `gpt-4o-mini` | Simple aggregation logic |
| **Lead Analyst** | `gpt-4o` | Complex reasoning for Logic Matrix application |
| Editor | `gpt-4o-mini` | Straightforward text transformation |
| **Risk Manager** | `gpt-4o-mini` | Efficient risk calculations and position sizing |
| **Scenario Planner** | `gpt-4o` | Complex scenario modeling requires advanced reasoning |
| **Anomaly Detection** | `gpt-4o-mini` | Pattern detection and statistical analysis |
| **Validator** | `gpt-4o` | Complex validation logic and consistency checking |

**Cost Optimization**: Only the Lead Analyst, Scenario Planner, and Validator use the premium `gpt-4o` model where complex reasoning quality is critical.

---

## Dependency Injection System

### CryptoDependencies (`deps/dependencies.py`)

**Purpose**: Type-safe container for shared resources across the agent pipeline.

**Definition**:
```python
@dataclass
class CryptoDependencies:
    http_client: httpx.AsyncClient
    user_context: dict[str, Any]
    symbol: str = "BTC-USD"
```

**Attributes**:
- `http_client`: Asynchronous HTTP client for API requests (shared connection pool)
- `user_context`: Request-specific metadata (e.g., `request_id`, user_id)
- `symbol`: Cryptocurrency ticker being analyzed (default: "BTC-USD")

**Benefits**:
1. **No Global State**: All external services injected explicitly
2. **Type Safety**: IDE autocomplete and static analysis
3. **Testability**: Easy to mock dependencies in unit tests
4. **Resource Management**: Single HTTP client shared across tools

**Usage Pattern**:
```python
async with httpx.AsyncClient() as client:
    deps = CryptoDependencies(
        http_client=client,
        user_context={"request_id": "quant-001"},
        symbol="BTC-USD"
    )

    result = await agent.run("Analyze BTC", deps=deps)
```

**Tool Access**:
```python
@agent.tool
async def my_tool(ctx: RunContext[CryptoDependencies]) -> str:
    # Access dependencies through context
    symbol = ctx.deps.symbol
    response = await ctx.deps.http_client.get(f"https://api.example.com/{symbol}")
    return response.json()
```

---

## Data Models

### Type-Safe Schema (`models/models.py`)

All agent inputs and outputs use **Pydantic v2** models for validation and serialization.

#### Technical Data Models

```python
class PriceMetrics(BaseModel):
    current_price: float
    rsi_4h: float
    vwap_deviation: float
    regime: str  # "Trending_Up" | "Trending_Down" | "Consolidation"

class RiskProfile(BaseModel):
    invalidation_hard_stop: float
    support_zone: List[float]
    resistance_zone: List[float]

class MicrostructureMetrics(BaseModel):
    funding_rate_bias: str  # "Neutral" | "Long_Heavy" | "Short_Heavy" | "Extreme"
    open_interest_trend: str
    squeeze_risk: str  # "Low" | "Medium" | "High"

class TechnicalData(BaseModel):
    module_1_price_structure: PriceStructure
    module_5_market_microstructure: MicrostructureMetrics
    timestamp_utc: datetime
```

#### Fundamental Data Models

```python
class MacroMetrics(BaseModel):
    spx_level: float
    dxy_index: float
    macro_regime: str  # "Risk_On" | "Risk_Off" | "Neutral"

class OnChainMetrics(BaseModel):
    exchange_net_flow: str
    active_addresses_trend: str
    whale_accumulation: str

class SentimentMetrics(BaseModel):
    fear_greed_index: int  # 0-100
    social_volume: str
    sentiment_signal: str  # "Buy" | "Sell" | "Neutral"
    alternative_data: Optional[AlternativeDataMetrics] = None

class FundamentalData(BaseModel):
    module_2_macro: MacroMetrics
    module_3_onchain: OnChainMetrics
    module_4_sentiment: SentimentMetrics
    timestamp_utc: datetime
```

#### Alternative Data Models

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
    direction: str  # "rising" | "falling" | "stable"

class GitHubActivityData(BaseModel):
    activity_score: float  # 0-100
    trend: str  # "accelerating" | "growing" | "stable" | "slowing" | "declining"
    recent_commits: int

class OptionsMarketData(BaseModel):
    put_call_ratio: float
    avg_implied_volatility: float
    market_sentiment: str  # "bullish" | "neutral" | "bearish"
```

#### Directive Models

```python
class DirectiveContent(BaseModel):
    stance: str  # "Aggressive_Long" | "Defensive_Long" | "Neutral" | "Tactical_Short"
    leverage_cap: str  # "1x" | "3x" | "5x"
    conviction_score: int  # 0-100

class FinalDirective(BaseModel):
    report_metadata: ReportMetadata
    final_directive: DirectiveContent
    thesis_summary: str  # Detailed reasoning (min 50 chars)
```

### Validation Benefits

- **Runtime Validation**: Pydantic catches schema violations before downstream errors
- **Serialization**: Automatic JSON conversion with `.model_dump_json()`
- **Field Constraints**: `ge=0, le=100` for conviction scores, `Field(...)` for required fields
- **Documentation**: Field descriptions guide LLM output formatting

---

## Multi-Source Orchestration

### BlockchainOrchestrator (`tools/blockchain_orchestrator.py`)

**Purpose**: Intelligent routing and fallback management for blockchain data queries.

**Architecture**:
```
Query Request
     │
     ▼
┌─────────────────────┐
│  Query Complexity   │
│  Assessment         │
└──────────┬──────────┘
           │
           ▼
     ┌────┴────┐
     │ Simple? │
     └────┬────┘
          │
    ┌─────┴─────┐
    │           │
   Yes         No
    │           │
    ▼           ▼
┌────────┐  ┌─────────┐
│DeFiLlama│  │  Dune   │
│  or     │  │Analytics│
│CoinGecko│  │         │
└───┬─────┘  └────┬────┘
    │             │
    │ Fail?       │ Fail?
    ▼             ▼
┌────────────┐ ┌──────────┐
│ Fallback   │ │Etherscan │
│  Chain     │ │ Family   │
└────────────┘ └──────────┘
```

**Data Source Capabilities**:

| Source | Free Tier | Best For | Latency |
|--------|-----------|----------|---------|
| **DeFiLlama** | Unlimited | TVL, protocol metrics, stablecoin dominance | 200-500ms |
| **CoinGecko** | 50 calls/min | Token prices, market cap, volume, exchange data | 300-800ms |
| **Dune Analytics** | 1000/day | Complex SQL queries, custom analytics, historical trends | 2-5s |
| **Etherscan Family** | 100K/day | Transaction data, wallet balances, smart contract calls | 500-1500ms |

**Orchestrator Features**:

1. **Automatic Fallback Chains**:
   ```python
   # Example: Token price lookup
   Primary: CoinGecko (fast, free)
       ↓ (on failure)
   Secondary: DeFiLlama (alternative free source)
       ↓ (on failure)
   Tertiary: Dune Analytics (query historical data)
   ```

2. **Query Complexity Routing**:
   - **Simple** (TVL, price): → DeFiLlama, CoinGecko
   - **Medium** (24h flows, holder count): → Etherscan, Dune
   - **Complex** (multi-table joins, custom metrics): → Dune Analytics

3. **Three-Tier Caching**:
   ```python
   Hot Cache (5 min TTL):  Frequently accessed, rapidly changing data
   Warm Cache (1 hr TTL):  Moderate update frequency (protocol TVL)
   Cold Cache (24 hr TTL): Stable reference data (token metadata)
   ```

4. **Rate Limit Handling**:
   - Exponential backoff: 2s → 4s → 8s → 16s
   - Automatic provider rotation on 429 errors
   - Request queuing for burst traffic

**Usage Example**:
```python
from tools.blockchain_orchestrator import MultiSourceOrchestrator, get_protocol_tvl

orchestrator = MultiSourceOrchestrator(
    dune_api_key=os.getenv("DUNE_API_KEY"),
    etherscan_api_keys={'ethereum': os.getenv("ETHERSCAN_API_KEY")}
)

# Automatically selects best source and handles fallbacks
result = await get_protocol_tvl(orchestrator, "aave")
print(f"Aave TVL: ${result['data']['tvl']:,.0f}")
print(f"Data source: {result['source']}")  # e.g., "defillama"
print(f"Confidence: {result['confidence_score']}")  # e.g., 0.95
```

### Alternative Data Adapters (`tools/alternative_data_adapters.py`)

Provides unified interface for non-traditional data sources:

**Adapters**:
1. **CryptoPanic News Sentiment**: Aggregates crypto news with sentiment scoring
2. **Reddit Social Media**: Monitors r/cryptocurrency and r/bitcoin for community conviction
3. **Google Trends**: Tracks search interest as retail attention proxy
4. **GitHub Dev Activity**: Measures project development health
5. **Deribit Options Flow**: Analyzes smart money positioning via P/C ratios

**Key Features**:
- Standardized return format across all adapters
- Built-in error handling and retry logic
- Configurable caching per adapter
- Optional API keys (most work without)

---

## Agent Pipeline Flow

### Complete Execution Sequence

**Phase 1: Parallel Data Collection** (30-60s)
```bash
# Run concurrently
python -m agents.quant_agent BTC-USD &       # Technical analysis
python -m agents.scout_agent BTC &            # Fundamental + alternative data
python -m agents.blockchain_agent &           # On-chain analysis
wait
```

**Outputs**:
- `data/technical_data.json`
- `data/fundamental_data.json`
- `data/blockchain_analysis.json` (optional, can be merged into fundamental)

---

**Phase 2: Data Aggregation** (5-10s)
```bash
python -m agents.coordinator_agent
```

**Process**:
1. Load `technical_data.json` and `fundamental_data.json`
2. Validate schema completeness
3. Merge into `MasterState` model
4. Add aggregation timestamp

**Output**:
- `data/master_state.json`

---

**Phase 3: Strategic Analysis** (10-20s)
```bash
python -m agents.analyst_agent
```

**Process**:
1. Load `master_state.json`
2. Apply Logic Matrix boolean rules
3. Generate `FinalDirective` with thesis summary
4. Validate output (min 50 char thesis)
5. Retry up to 3 times if validation fails

**Output**:
- `data/FINAL_DIRECTIVE_20251229.json`

---

**Phase 4: Report Generation** (5-10s)
```bash
python -m agents.editor_agent
```

**Process**:
1. Load `FINAL_DIRECTIVE_*.json`
2. Transform JSON to markdown prose
3. Structure with executive summary, assessment, recommendation, risks

**Output**:
- `reports/EXECUTIVE_SUMMARY_20251229.md`

---

### End-to-End Execution

**Single Command**:
```bash
python -m agents.editor_agent
```

The `editor_agent` module orchestrates the entire pipeline by calling preceding agents in sequence.

**Total Pipeline Duration**: ~50-90 seconds (depending on API latency)

---

## Tools & Capabilities

### Tool Implementation Pattern

All tools follow this structure:

```python
@agent.tool
async def tool_name(
    ctx: RunContext[CryptoDependencies],
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """Clear docstring explaining tool purpose (LLM reads this).

    Args:
        ctx: PydanticAI context with dependencies.
        param1: Description of parameter.
        param2: Optional parameter with default.

    Returns:
        dict: Description of return structure.

    Raises:
        ModelRetry: When to retry (temporary errors).
    """
    try:
        # Access dependencies
        client = ctx.deps.http_client
        symbol = ctx.deps.symbol

        # Perform operation
        result = await some_async_operation(param1)

        return {"data": result, "status": "success"}

    except TemporaryError as e:
        # Let LLM retry with context
        raise ModelRetry(f"Temporary failure: {e}. Please try again.")

    except PermanentError as e:
        # Return error as string for LLM to handle
        return {"error": str(e), "status": "failed"}
```

### Tool Registry by Agent

**Quant Agent**:
- `fetch_market_data()`: yfinance OHLCV + indicators

**Scout Agent**:
- `fetch_macro_data()`: SPX, DXY levels
- `fetch_defi_tvl_data()`: DeFi protocol TVL (DeFiLlama)
- `fetch_crypto_market_data()`: Token prices (CoinGecko)
- `fetch_news_sentiment()`: CryptoPanic news analysis
- `fetch_social_media_sentiment()`: Reddit community monitoring
- `fetch_google_trends()`: Search interest tracking
- `fetch_github_activity()`: Dev activity metrics
- `fetch_options_market_data()`: Deribit options flow

**Blockchain Agent**:
- `get_defi_protocol_metrics()`: Protocol TVL, chain breakdown
- `get_token_market_data()`: Real-time market data
- `get_whale_wallet_activity()`: Large holder tracking
- `query_blockchain_data()`: Custom Dune Analytics queries

**Coordinator Agent**:
- `load_technical_data()`: Read technical JSON artifact
- `load_fundamental_data()`: Read fundamental JSON artifact

**Lead Analyst Agent**:
- `get_master_state()`: Load aggregated Master State

**Editor Agent**:
- `get_final_directive()`: Load directive from Lead Analyst

### Tool Best Practices

1. **Error Handling**:
   - Use `ModelRetry` for recoverable errors (rate limits, temporary network issues)
   - Return error dicts for permanent failures
   - Log errors for debugging

2. **Docstrings**:
   - LLM reads docstrings to understand tool purpose
   - Include clear parameter descriptions
   - Provide usage examples

3. **Type Hints**:
   - Fully type all parameters and return values
   - Use `Optional[T]` for nullable fields
   - Leverage `RunContext[DepsType]` for dependency access

4. **Async/Await**:
   - Mark I/O-bound tools as `async`
   - Use `await` for HTTP requests, file I/O
   - Enables concurrent tool execution

---

## Production Features

### 1. Output Validation

**Mechanism**: `@agent.output_validator` decorator

**Example** (Lead Analyst):
```python
@analyst_agent.output_validator
async def validate_analyst_output(
    ctx: RunContext[CryptoDependencies],
    output: FinalDirective,
) -> FinalDirective:
    """Ensure thesis summary is sufficiently detailed."""
    if len(output.thesis_summary) < 50:
        raise ModelRetry("Thesis too brief. Provide detailed logic breakdown.")
    return output
```

**Benefits**:
- Enforces quality thresholds
- Automatically retries if validation fails
- Prevents low-quality outputs from propagating

---

### 2. Retry Logic with Exponential Backoff

**Implementation** (using `tenacity`):
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(RateLimitError),
)
async def run_analyst_with_retry(deps: CryptoDependencies):
    try:
        result = await analyst_agent.run("Analyze...", deps=deps)
        return result
    except Exception as e:
        if "429" in str(e):
            raise RateLimitError(str(e))
        raise
```

**Backoff Schedule**:
- Attempt 1: Immediate
- Attempt 2: Wait 2s
- Attempt 3: Wait 4s
- Attempt 4: Wait 8s (max)

---

### 3. Usage Tracking

**Access Metrics**:
```python
result = await agent.run(prompt, deps=deps)
usage = result.usage()

print(f"Input tokens: {usage.input_tokens}")
print(f"Output tokens: {usage.output_tokens}")
print(f"Total tokens: {usage.total_tokens}")
print(f"Requests made: {usage.requests}")
```

**Cost Monitoring**:
- Log token usage per agent run
- Aggregate metrics for cost analysis
- Set alerts for abnormal usage patterns

---

### 4. Message History Management

**Maintaining Context Across Runs**:
```python
messages: List[ModelMessage] = []

# First run
result = await agent.run("Initial prompt", deps=deps)
messages.extend(result.new_messages())

# Follow-up with context
result = await agent.run(
    "Follow-up question",
    deps=deps,
    message_history=messages
)
messages.extend(result.new_messages())
```

**Conversation Pruning** (for long sessions):
```python
def prune_messages(messages: List[ModelMessage], max_length: int = 10) -> List[ModelMessage]:
    """Keep recent messages, summarize old ones."""
    if len(messages) <= max_length:
        return messages
    return messages[-max_length:]  # Keep last N messages
```

---

### 5. Structured Logging

**Recommended Pattern**:
```python
import structlog

logger = structlog.get_logger()

@agent.tool
async def my_tool(ctx: RunContext[CryptoDependencies]) -> dict:
    logger.info("tool_called", tool_name="my_tool", symbol=ctx.deps.symbol)

    try:
        result = await operation()
        logger.info("tool_success", result_size=len(result))
        return result
    except Exception as e:
        logger.error("tool_error", error=str(e), error_type=type(e).__name__)
        raise
```

**Benefits**:
- Structured JSON logs for easy parsing
- Contextual debugging information
- Production observability

---

## Extension Guide

### Adding a New Agent

**Step 1: Define Output Model** (`models/models.py`)
```python
class MyAgentOutput(BaseModel):
    result: str
    confidence: float = Field(ge=0.0, le=1.0)
```

**Step 2: Create Agent File** (`agents/my_agent.py`)
```python
from config.agent_factory import create_agent
from models.models import MyAgentOutput
from deps.dependencies import CryptoDependencies

my_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt="You are MyAgent. Your purpose is...",
    deps_type=CryptoDependencies,
    result_type=MyAgentOutput
)

@my_agent.tool
async def my_tool(ctx: RunContext[CryptoDependencies]) -> dict:
    """Tool description for LLM."""
    # Implementation
    return {"data": "result"}

async def run_my_agent() -> MyAgentOutput:
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "my-001"},
            symbol="BTC-USD"
        )
        result = await my_agent.run("Perform task", deps=deps)
        return result.data
```

**Step 3: Integrate into Pipeline**
- Add agent call to `coordinator_agent.py` or `editor_agent.py`
- Update data flow diagram in README
- Document in this file

---

### Adding a New Data Source

**Step 1: Create Adapter** (`tools/my_data_adapter.py`)
```python
import httpx
from typing import Dict, Any

async def fetch_my_data(
    http_client: httpx.AsyncClient,
    param: str
) -> Dict[str, Any]:
    """Fetch data from MyDataSource API."""
    try:
        response = await http_client.get(
            f"https://api.mydatasource.com/v1/{param}",
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        return {"error": str(e)}
```

**Step 2: Add to Orchestrator** (`tools/blockchain_orchestrator.py`)
```python
from tools.my_data_adapter import fetch_my_data

class MultiSourceOrchestrator:
    async def get_my_data(self, param: str) -> BlockchainQueryResult:
        """Query MyDataSource with fallback."""
        # Try MyDataSource first
        result = await fetch_my_data(self.http_client, param)
        if 'error' not in result:
            return BlockchainQueryResult(
                data=result,
                source='mydatasource',
                latency_ms=100,
                confidence_score=0.9
            )

        # Fallback to alternative source
        return await self._fallback_query(param)
```

**Step 3: Create Agent Tool** (`agents/scout_agent.py`)
```python
@scout_agent.tool
async def fetch_from_my_source(
    ctx: RunContext[CryptoDependencies],
    param: str
) -> Dict[str, Any]:
    """Fetch data from MyDataSource."""
    orchestrator = get_orchestrator()
    result = await orchestrator.get_my_data(param)
    return result.data
```

---

### Adding Alternative Data

**Step 1: Create Pydantic Model** (`models/models.py`)
```python
class MyAlternativeData(BaseModel):
    metric: float = Field(..., description="Key metric")
    trend: str = Field(..., description="Trend direction")
```

**Step 2: Create Adapter** (`tools/alternative_data_adapters.py`)
```python
async def fetch_my_alternative_data(
    http_client: httpx.AsyncClient,
    asset: str
) -> MyAlternativeData:
    """Fetch alternative data for asset."""
    response = await http_client.get(f"https://api.example.com/{asset}")
    data = response.json()

    return MyAlternativeData(
        metric=data['metric'],
        trend=data['trend']
    )
```

**Step 3: Add to Scout Agent** (`agents/scout_agent.py`)
```python
@scout_agent.tool
async def fetch_my_alternative_data_tool(
    ctx: RunContext[CryptoDependencies]
) -> Dict[str, Any]:
    """Fetch MyAlternativeData for current symbol."""
    from tools.alternative_data_adapters import fetch_my_alternative_data

    result = await fetch_my_alternative_data(
        ctx.deps.http_client,
        ctx.deps.symbol.split('-')[0]  # BTC-USD -> BTC
    )

    return result.model_dump()
```

**Step 4: Update AlternativeDataMetrics** (`models/models.py`)
```python
class AlternativeDataMetrics(BaseModel):
    # ... existing fields ...
    my_alternative_data: Optional[MyAlternativeData] = None
```

---

## Current State & Direction

### System Maturity (v0.5.0)

**Completed** ✅:
- ✅ Core agent architecture with PydanticAI
- ✅ Multi-source blockchain data integration
- ✅ Alternative data sources (news, social, trends, dev activity, options)
- ✅ Dependency injection with `CryptoDependencies`
- ✅ Production resilience (retries, fallbacks, validation)
- ✅ File-based caching system (hot/warm/cold)
- ✅ Logic Matrix for strategy synthesis
- ✅ Comprehensive data models with Pydantic
- ✅ OpenRouter integration with model selection
- ✅ Structured artifact persistence (JSON reports)
- ✅ **Risk Manager Agent** - Position sizing and risk assessment
- ✅ **Scenario Planner Agent** - What-if scenario modeling
- ✅ **Anomaly Detection Agent** - Unusual pattern detection
- ✅ **Validator Agent** - Quality assurance and consistency checking

**In Progress** 🚧:
- Documentation improvements (this file)
- Test coverage expansion
- Performance benchmarking
- Integration of new agents into main pipeline

**Planned** 📋:
- Real-time streaming data support
- WebSocket integrations for live price feeds
- Advanced caching with TTL optimization
- Multi-asset portfolio analysis
- Backtesting framework integration
- API endpoint exposure (FastAPI)

### Future Enhancements

**Phase 1: Real-Time Capabilities**
- Integrate WebSocket feeds from Binance/Coinbase
- Stream-based technical analysis updates
- Live on-chain monitoring (Dune Analytics webhooks)

**Phase 2: Portfolio Management**
- Multi-asset correlation analysis
- Portfolio optimization agent
- Risk allocation across assets

**Phase 3: Backtesting & Validation**
- Historical directive evaluation
- Strategy performance metrics
- Automated parameter tuning

**Phase 4: Production API**
- FastAPI wrapper for agent pipeline
- Authentication and rate limiting
- Webhook notifications for directive updates

---

## Conclusion

The Antigravity Microanalyst Team demonstrates a production-grade multi-agent architecture built on modern AI engineering principles:

- **Type Safety**: Pydantic models ensure data integrity
- **Modularity**: Clear separation of concerns across specialized agents
- **Resilience**: Comprehensive error handling and retry logic
- **Observability**: Structured artifacts enable full audit trails
- **Extensibility**: Well-defined patterns for adding agents, tools, and data sources

This architecture provides a solid foundation for building sophisticated trading analysis systems with AI agents.

---

**Document Version**: 1.0.0
**Last Updated**: 2025-12-29
**Codebase Version**: v0.4.0
