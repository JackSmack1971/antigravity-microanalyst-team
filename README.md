# Antigravity Microanalyst Team

A multi-agent autonomous system for cryptocurrency market analysis, built with PydanticAI and OpenRouter.

## Overview

The Antigravity Microanalyst Team is a specialized swarm of AI agents designed to perform high-fidelity technical and fundamental analysis on crypto assets. The system employs a modular architecture with explicit dependency injection, production-grade resilience, and a strict logic matrix for strategy synthesis.

### What's New

**Recent Enhancements** (December 2025):
- **New Specialized Agents**: Added 6 complementary agents for comprehensive analysis
  - Risk Manager: Position sizing, stop-loss/take-profit recommendations, tail risk assessment
  - Scenario Planner: What-if analysis with probability-weighted outcomes
  - Anomaly Detection: Pattern detection for unusual market behavior and opportunities
  - Validator: Quality assurance and consistency checking across all outputs
  - Black Swan Detector: Monitors extreme market events, price movements >10%, volume spikes >5x, and generates emergency response recommendations
  - Correlation & Market Regime Analyzer: Analyzes cross-asset correlations and detects market regime changes (risk_on/risk_off/transitional/decoupled)
- **Comprehensive On-Chain Data Integration**: Access real blockchain data from 4+ free sources without expensive subscriptions
- **Alternative Data Intelligence**: Capture market sentiment, social trends, and developer activity before they impact prices
- **Zero-Config Quick Start**: Core features work immediately with DeFiLlama and CoinGecko (no API keys required)
- **Multi-Source Orchestration**: Automatic fallback routing ensures analysis continues even when individual APIs fail
- **Intelligent Caching**: File-based caching reduces API calls and improves response times without external dependencies

## Core Agents

### Data Collection Agents
- **Quant Agent**: Performs technical analysis, calculates indicators (EMA, RSI), and identifies market regimes.
- **Scout Agent**: Gathers macro context and real on-chain data from multiple free blockchain data sources (DeFiLlama, CoinGecko, Dune Analytics). Enhanced with alternative data from news sentiment, social media, and market trends.
- **Blockchain Agent**: Specialized agent for comprehensive on-chain analysis using multi-source orchestration. Provides TVL tracking, protocol metrics, exchange flows, and whale wallet monitoring across multiple chains.

### Analysis & Output Agents
- **Coordinator Agent**: Aggregates data from Quant and Scout agents into a unified Master State.
- **Lead Analyst Agent**: Synthesizes the Master State using a strict Logic Matrix to produce trading directives.
- **Editor Agent**: Transforms technical directives into polished, human-readable executive summaries.

### Complementary Analysis Agents
- **Risk Manager Agent**: Dedicated risk assessment with position sizing recommendations, stop-loss/take-profit levels, and tail risk analysis.
- **Scenario Planner Agent**: Generates what-if market scenarios with probability assessments and identifies key catalysts and invalidation levels.
- **Anomaly Detection Agent**: Identifies unusual market behavior, volume spikes, whale movements, and microstructure anomalies for trading opportunities.
- **Validator Agent**: Cross-checks analysis outputs for consistency, validates Logic Matrix application, and ensures report quality.
- **Black Swan Detector Agent**: Monitors market conditions for extreme events including price movements >10%, volume spikes >5x average, volatility explosions, and market structure breakdowns. Generates emergency response recommendations with severity-based position adjustments.
- **Correlation & Market Regime Analyzer Agent**: Analyzes rolling correlations between BTC and major assets (ETH, SPX, DXY, Gold), detects market regime changes, identifies correlation breakdowns, and assesses cross-asset contagion risks for strategy adjustment.

## Architecture

```mermaid
graph TB
    subgraph "Data Sources"
        DS1[yfinance<br/>Market Data]
        DS2[DeFiLlama<br/>TVL & Protocols]
        DS3[CoinGecko<br/>Token Prices]
        DS4[CryptoPanic<br/>News Sentiment]
        DS5[Reddit<br/>Social Sentiment]
        DS6[Google Trends<br/>Search Interest]
        DS7[GitHub<br/>Dev Activity]
        DS8[Deribit<br/>Options Data]
        DS9[Dune Analytics<br/>On-Chain Queries]
        DS10[Etherscan<br/>Wallet & Txns]
    end

    subgraph "Orchestration Layer"
        ORC[Blockchain Orchestrator<br/>Multi-Source Routing & Fallback]
        ALT[Alternative Data Adapters<br/>Sentiment & Trend Analysis]
    end

    subgraph "Data Collection Agents"
        QA[Quant Agent<br/>Technical Analysis]
        SA[Scout Agent<br/>Fundamental & Macro]
        BA[Blockchain Agent<br/>On-Chain Analysis]
    end

    subgraph "Data Artifacts"
        TD[technical_data.json]
        FD[fundamental_data.json]
        BDA[blockchain_analysis.json]
        MS[master_state.json]
        FDR[FINAL_DIRECTIVE_*.json]
    end

    subgraph "Analysis & Output"
        CA[Coordinator Agent<br/>Data Aggregation]
        LA[Lead Analyst Agent<br/>Strategy Synthesis]
        EA[Editor Agent<br/>Report Generation]
        REP[EXECUTIVE_SUMMARY_*.md]
    end

    %% Data Source Connections
    DS1 --> QA
    DS1 --> SA
    DS2 --> ORC
    DS3 --> ORC
    DS4 --> ALT
    DS5 --> ALT
    DS6 --> ALT
    DS7 --> ALT
    DS8 --> ALT
    DS9 --> ORC
    DS10 --> ORC

    %% Orchestrator to Agents
    ORC --> SA
    ORC --> BA
    ALT --> SA

    %% Agent to Artifact Flow
    QA --> TD
    SA --> FD
    BA --> BDA

    %% Coordinator Flow
    TD --> CA
    FD --> CA
    CA --> MS

    %% Analysis Flow
    MS --> LA
    LA --> FDR
    FDR --> EA
    EA --> REP

    style DS1 fill:#e1f5ff
    style DS2 fill:#e1f5ff
    style DS3 fill:#e1f5ff
    style DS4 fill:#fff4e1
    style DS5 fill:#fff4e1
    style DS6 fill:#fff4e1
    style DS7 fill:#fff4e1
    style DS8 fill:#fff4e1
    style DS9 fill:#e1f5ff
    style DS10 fill:#e1f5ff
    style ORC fill:#f0e1ff
    style ALT fill:#f0e1ff
    style QA fill:#e8f5e9
    style SA fill:#e8f5e9
    style BA fill:#e8f5e9
    style CA fill:#fff3e0
    style LA fill:#fff3e0
    style EA fill:#fff3e0
    style REP fill:#ffebee
```

### Architecture Flow

**Phase 1: Parallel Data Collection**
- **Quant Agent**: Fetches price data from yfinance, calculates technical indicators (EMA, RSI, volatility)
- **Scout Agent**: Gathers macro indicators, DeFi metrics, token prices, and alternative data (news sentiment, social trends, dev activity)
- **Blockchain Agent**: Performs specialized on-chain analysis using multi-source orchestration

**Phase 2: Data Aggregation**
- **Coordinator Agent**: Merges technical and fundamental data into a unified Master State

**Phase 3: Strategic Analysis**
- **Lead Analyst Agent**: Applies Logic Matrix to synthesize trading directives from Master State

**Phase 4: Report Generation**
- **Editor Agent**: Transforms technical directives into human-readable executive summaries

**Phase 5: Complementary Analysis** (Optional)
- **Risk Manager Agent**: Calculates position sizing, stop-loss/take-profit levels, and tail risk metrics
- **Scenario Planner Agent**: Models bull/bear/base scenarios with probability assessments
- **Anomaly Detection Agent**: Identifies unusual patterns, volume spikes, and whale movements
- **Validator Agent**: Cross-checks outputs for consistency and validates Logic Matrix application

## Setup

### Prerequisites

- Python 3.10+
- OpenRouter API Key

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd antigravity-microanalyst-team
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment Variables**:
   Create a `.env` file in the root directory:

   ```env
   OPENROUTER_API_KEY=your_sk_key_here
   ```

## Usage

### Run the full pipeline

To run the complete analysis flow (from data fetching to report generation):

```bash
python -m agents.editor_agent
```

### Run individual agents for targeted analysis

**Technical Analysis**:
```bash
python -m agents.quant_agent BTC-USD
```

**On-Chain Analysis** (uses DeFiLlama, CoinGecko - no API keys needed):
```bash
python -m agents.blockchain_agent
```

**Scout Analysis** (includes news sentiment, social media, trends):
```bash
python -m agents.scout_agent BTC
```

**Risk Assessment** (position sizing, stop-loss, tail risk):
```bash
python -m agents.risk_manager_agent BTC-USD 10000 2.0
```

**Scenario Planning** (what-if analysis with probabilities):
```bash
python -m agents.scenario_planner_agent BTC-USD "1 week"
```

**Anomaly Detection** (unusual patterns and opportunities):
```bash
python -m agents.anomaly_detection_agent BTC-USD
```

**Quality Validation** (consistency checks and logic validation):
```bash
python -m agents.validator_agent BTC-USD
```

**Black Swan Detection** (extreme event monitoring and emergency responses):
```bash
python -m agents.black_swan_detector_agent BTC-USD 24
```

**Correlation & Market Regime Analysis** (cross-asset correlations and regime detection):
```bash
python -m agents.correlation_market_regime_agent BTC-USD 90
```

### Quick Examples

**Test On-Chain Data Integration**:
```bash
# Works immediately without any API keys!
python -m tools.blockchain_adapters
```

**Test Alternative Data Sources**:
```bash
# Fetch news sentiment, Reddit trends, Google search interest
python -m tools.alternative_data_adapters
```

**Run Multi-Source Orchestrator**:
```bash
# Demonstrates automatic fallback and intelligent routing
python -m tools.blockchain_orchestrator
```

## Data Sources

### On-Chain Data Sources

Access real blockchain data without expensive subscriptions:

| Data Source | Best For | Free Tier Limits | API Key Required |
|------------|----------|------------------|------------------|
| **DeFiLlama** | Protocol TVL, DeFi metrics, stablecoin dominance | Unlimited | ❌ No |
| **CoinGecko** | Token prices, market cap, volume, exchange data | 50 calls/min | ❌ No |
| **Dune Analytics** | Custom SQL queries, complex on-chain analytics | 1000 queries/day | ✅ Optional |
| **Etherscan Family** | Transaction history, wallet balances, smart contract calls | 100K calls/day | ✅ Optional |

**Key Capabilities**:
- **TVL Tracking**: Monitor protocol health via Total Value Locked changes (DeFiLlama)
- **Whale Monitoring**: Track large wallet movements and exchange flows (Etherscan)
- **Market Structure**: Real-time price and volume across exchanges (CoinGecko)
- **Custom Analytics**: Run complex blockchain queries for unique insights (Dune)
- **Multi-Chain Support**: Ethereum, BSC, Polygon, Arbitrum, and 20+ chains

**Zero-Setup Quick Start**: DeFiLlama and CoinGecko work immediately without configuration!

See [ONCHAIN_DATA_SOURCES.md](./ONCHAIN_DATA_SOURCES.md) for complete documentation and code examples.

### Alternative Data Sources

The system integrates non-traditional data sources for edge in analysis:

| Data Source | Provider | Insights Provided | Free Tier |
|------------|----------|-------------------|-----------|
| **News Sentiment** | CryptoPanic | Breaking news impact, sentiment shifts (-100 to +100), community validation | ✅ Yes |
| **Social Media** | Reddit | Community conviction via r/cryptocurrency, r/bitcoin engagement metrics | ✅ Yes |
| **Search Interest** | Google Trends | Retail attention correlation, trend momentum, early FOMO detection | ✅ Yes |
| **Developer Activity** | GitHub | Commit frequency, contributor growth, development health for fundamental analysis | ✅ Yes |
| **Options Market** | Deribit | Put/call ratios, implied volatility, smart money positioning | ✅ Yes |

**Real-World Use Cases**:
- **Sentiment Divergence**: Detect when negative news sentiment diverges from price action (potential reversal signal)
- **Social Momentum**: Track Reddit engagement spikes that often precede major moves
- **Retail FOMO Detection**: Google Trends spikes at market tops provide exit signals
- **Fundamental Validation**: GitHub activity decline warns of weakening project fundamentals
- **Smart Money Positioning**: Options flow reveals institutional positioning before retail

**Technical Features**:
- Multi-source orchestration with automatic fallback
- Intelligent caching (file-based, no Redis required)
- Rate limit handling with exponential backoff
- Query complexity assessment for optimal routing

See [ALTERNATIVE_DATA_SOURCES.md](./ALTERNATIVE_DATA_SOURCES.md) for complete documentation and code examples.

## Documentation

- **Agents**: Detailed in [AGENTS.md](./AGENTS.md)
- **On-Chain Data**: Detailed in [ONCHAIN_DATA_SOURCES.md](./ONCHAIN_DATA_SOURCES.md)
- **Alternative Data**: Detailed in [ALTERNATIVE_DATA_SOURCES.md](./ALTERNATIVE_DATA_SOURCES.md)
- **Feature Roadmap**: See [FEATURE_BRAINSTORM.md](./FEATURE_BRAINSTORM.md)
- **Inline Docs**: All modules follow Google-style docstrings.

## License

MIT
