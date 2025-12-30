# Antigravity Microanalyst Team - Project Memory

## Project Overview
A multi-agent autonomous system for cryptocurrency market analysis built with **PydanticAI** and **OpenRouter**. The system employs a swarm of specialized agents (Quant, Scout, Blockchain, Analyst) to gather data, synthesize strategies via a Logic Matrix, and generate executive summaries.

## Core Architecture
- **Framework**: PydanticAI (Agents, Tools, RunContext) + OpenRouter (LLMs).
- **Pattern**: Sequential Pipeline (Collection → Aggregation → Analysis → Output).
- **State Management**: JSON artifacts in `data/` (e.g., `master_state.json`).
- **Dependency Injection**: `CryptoDependencies` (shared `httpx.AsyncClient`).
- **Orchestration**: `MultiSourceOrchestrator` for blockchain data routing/fallback.

## Key Commands

### Setup & Testing
- **Install Dependencies**: `pip install -r requirements.txt`
- **Run Tests**: `pytest` (Configured in `pytest.ini`, covers agents/tools/models)
- **Check Coverage**: `pytest --cov=agents --cov=tools`

### Agent Execution (Primary Workflows)
- **Run Full Pipeline**: `python -m agents.editor_agent` (Triggers entire flow)
- **Technical Analysis**: `python -m agents.quant_agent BTC-USD`
- **Fundamental/Macro**: `python -m agents.scout_agent BTC`
- **On-Chain Analysis**: `python -m agents.blockchain_agent`
- **Risk Assessment**: `python -m agents.risk_manager_agent BTC-USD 10000 2.0`
- **Scenario Planning**: `python -m agents.scenario_planner_agent BTC-USD "1 week"`
- **Anomaly Detection**: `python -m agents.anomaly_detection_agent BTC-USD`

### Tool Testing
- **Test On-Chain Adapters**: `python -m tools.blockchain_adapters`
- **Test Alternative Data**: `python -m tools.alternative_data_adapters`

## Codebase Map & Pointers
- **Agent Definitions**: `agents/*.py` (See `AGENTS.md` for detailed roles).
- **Data Models**: `models/models.py` (Pydantic v2 schemas for all I/O).
- **Configuration**: `config/agent_factory.py` (Model settings, retry logic).
- **Dependencies**: `deps/dependencies.py` (DI container).
- **Orchestration**: `tools/blockchain_orchestrator.py` (Routing logic).

## Coding Standards & Conventions
1. **Type Safety**: Use **Pydantic models** for all agent inputs/outputs. Validation is strict.
2. **Dependency Injection**: Never use global state. Inject `CryptoDependencies` into tools via `ctx: RunContext[CryptoDependencies]`.
3. **Async/Await**: All I/O tools must be `async`. Use `await` for HTTP calls.
4. **Error Handling**:
   - Use `ModelRetry` for transient errors (rate limits).
   - Return error dicts for permanent failures.
5. **Documentation**: Google-style docstrings are required for all tools (LLMs read these).
6. **Logging**: Use `structlog` patterns for observability.

## Important Context
- **API Keys**: Requires `OPENROUTER_API_KEY` in `.env`. Optional keys for Dune/Etherscan.
- **Model Selection**: `gpt-4o-mini` for data/tasks, `gpt-4o` for complex reasoning (Analyst/Validator).
- **Artifacts**: Agents communicate via files in `data/`. Do not assume in-memory state sharing between separate process runs.
