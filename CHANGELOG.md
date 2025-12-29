# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-12-29

### Added
- Enhanced README documentation with user-facing features from recent PRs (PR #4)
- "What's New" section showcasing recent enhancements (December 2025)
- Expanded usage section with concrete examples for each agent
- Quick Examples section for immediate testing
- Restructured On-Chain Data Sources with detailed comparison table
- Improved Alternative Data Sources with real-world use cases

### Changed
- Enhanced Core Agents descriptions for Scout and Blockchain agents
- Made system more accessible to new users with clear zero-config quick start examples
- Highlighted free tier capabilities and API key requirements

## [0.3.0] - 2025-12-29

### Added
- **Alternative Data Sources Integration** (PR #3)
  - CryptoPanic news sentiment analysis with positive/negative/neutral breakdown
  - Reddit social media monitoring (r/cryptocurrency, r/bitcoin)
  - Google Trends search interest correlation with price movements
  - GitHub development activity metrics (commit frequency, contributor count)
  - Deribit options market data (Put/Call ratios, implied volatility)
- New file: `tools/alternative_data_adapters.py` with all alternative data adapters
- New file: `ALTERNATIVE_DATA_SOURCES.md` with comprehensive documentation
- 5 new Scout Agent tools:
  - `fetch_news_sentiment()`: CryptoPanic news analysis
  - `fetch_social_media_sentiment()`: Reddit community sentiment
  - `fetch_google_trends()`: Search interest trends
  - `fetch_github_activity()`: Development metrics
  - `fetch_options_market_data()`: Deribit options flow
- Pydantic models for alternative data in `models/models.py`
- Three-tier caching (hot/warm/cold) for alternative data
- Rate limit handling and exponential backoff retry logic
- API configuration for alternative sources in `.env.example`

### Changed
- Updated `requirements.txt` with praw, pytrends, beautifulsoup4
- Enhanced `tools/blockchain_orchestrator.py` with alternative data integration
- Expanded `agents/scout_agent.py` with alternative data fetching capabilities
- Updated `README.md` with alternative data sources section

## [0.2.0] - 2025-12-29

### Added
- **On-Chain Data Sources Integration** (PR #2)
  - Multi-source blockchain data adapters (DeFiLlama, CoinGecko, Dune Analytics, Etherscan)
  - Intelligent query orchestrator with automatic fallback chains
  - File-based caching system with multi-tier TTL (hot/warm/cold)
  - Query complexity assessment for optimal routing
- New blockchain data agent (`agents/blockchain_agent.py`) for on-chain analysis
- New files:
  - `tools/blockchain_adapters.py`: Individual API adapters with retry logic
  - `tools/blockchain_orchestrator.py`: Multi-source orchestration and routing
  - `ONCHAIN_DATA_SOURCES.md`: Comprehensive usage guide
- Data source integrations:
  - DeFiLlama: TVL, protocol metrics, chain data (100% free)
  - CoinGecko: Token prices, market data (50 calls/min free tier)
  - Dune Analytics: Complex SQL queries (1000/day free tier)
  - Etherscan Family: Transaction data, balances (100K/day free tier)
- Enhanced `agents/scout_agent.py` with real on-chain data tools
- API key configuration template in `.env.example`

### Changed
- Updated `requirements.txt` with blockchain data dependencies
- Enhanced `README.md` with on-chain capabilities section

### Performance
- Effective daily capacity: 170K+ queries across all free sources
- Average latency: 200ms-2s (with caching: <10ms)
- Monthly operating cost: $0 using free tiers
- Savings: $500+/month vs premium services (Glassnode, Nansen)

## [0.1.1] - 2025-12-29

### Added
- Comprehensive feature brainstorm document (PR #1)
- `FEATURE_BRAINSTORM.md` with 50+ potential features across 10 categories
- Prioritization matrix from P0 (critical) to P3 (nice-to-have)
- Implementation phases and technical considerations
- Focus areas: data quality, risk management, automation, UX, validation

## [0.1.0] - 2025-12-28

### Added
- **Initial Project Release**
- **PydanticAI Integration**: Migrated all agents (Quant, Scout, Coordinator, Analyst, Editor) to the PydanticAI framework
- **Core Agents**:
  - `agents/quant_agent.py`: Quantitative analysis agent
  - `agents/scout_agent.py`: Data gathering and reconnaissance agent
  - `agents/coordinator_agent.py`: Multi-agent orchestration
  - `agents/analyst_agent.py`: Market analysis and insights
  - `agents/editor_agent.py`: Report generation and formatting
- **Dependency Injection**: Implemented `CryptoDependencies` for safe, typed resource sharing across the swarm
- **Agent Factory**: Created `config/agent_factory.py` for standardized agent creation with OpenRouter/OpenAI provider support
- **Production Resilience**:
  - Exponential backoff retries using `tenacity`
  - Structured output validation using `@agent.output_validator`
  - Standardized `ModelSettings` (temperature, timeout, max_tokens)
- **Logic Matrix Synchronization**: Injected explicit boolean logic (Macro Veto, Structure Priority, Liquidity Filter) into the Lead Analyst Agent
- **Nested Schema Compliance**: Updated `FinalDirective` model to match formal specification
- **Data Models**: Pydantic models in `models/models.py` for type-safe data handling
- **Market Tools**: Basic market data adapters in `tools/market_adapters.py`
- **Initial Data Files**:
  - `data/fundamental_data.json`: Sample fundamental analysis data
  - `data/technical_data.json`: Sample technical analysis data
  - `data/master_state.json`: System state tracking
- **Documentation**:
  - `README.md`: Project overview and quick start guide
  - `AGENTS.md`: Detailed agent architecture and specifications
  - `API_DOCUMENTATION.md`: API reference documentation
  - `review-report.md`: Initial code review report
- **Dependencies**: Core requirements in `requirements.txt`
- **Sample Reports**:
  - `reports/EXECUTIVE_SUMMARY_20251229.md`
  - `reports/FINAL_DIRECTIVE_20251229.json`

### Changed
- Refactored `run_quant_agent` to use asynchronous dependency injection
- Standardized file persistence for agent outputs (JSON-based reports)
- Refined `analyst_agent` to handle nested Pydantic models in directives

### Fixed
- Resolved `ModuleNotFoundError` during agent initialization by standardizing imports
- Corrected `Agent` constructor parameters to align with `pydantic-ai` v1.39.0 (`output_type`)

[Unreleased]: https://github.com/JackSmack1971/antigravity-microanalyst-team/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/JackSmack1971/antigravity-microanalyst-team/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/JackSmack1971/antigravity-microanalyst-team/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/JackSmack1971/antigravity-microanalyst-team/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/JackSmack1971/antigravity-microanalyst-team/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/JackSmack1971/antigravity-microanalyst-team/releases/tag/v0.1.0
