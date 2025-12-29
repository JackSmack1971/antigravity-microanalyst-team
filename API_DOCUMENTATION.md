# API Documentation: Agent Interfaces

This document outlines the programmatic interfaces for the Antigravity Microanalyst swarm. All agents are built using `pydantic-ai` and support dependency injection via `CryptoDependencies`.

## Dependency Injection

### `CryptoDependencies`

Defined in `deps/dependencies.py`.

| Attribute | Type | Description |
|-----------|------|-------------|
| `http_client` | `httpx.AsyncClient` | Shared HTTP client for asynchronous requests. |
| `user_context` | `dict[str, Any]` | Metadata for tracking requests (e.g., `request_id`). |
| `symbol` | `str` | The target crypto asset ticker (default: "BTC-USD"). |

---

## Technical Data API

### `run_quant_agent(symbol: str)`

**Source**: `agents/quant_agent.py`

Performs technical analysis and returns a `TechnicalData` model.

**Returns (`TechnicalData`)**:

- `module_1_price_structure`: Nested price metrics and risk profiles.
- `module_5_market_microstructure`: Funding rates and squeeze risks.

---

## Fundamental Data API

### `run_scout_agent()`

**Source**: `agents/scout_agent.py`

Performs macro/fundamental analysis and returns a `FundamentalData` model.

**Returns (`FundamentalData`)**:

- `module_2_macro`: S&P 500 and DXY levels.
- `module_3_onchain`: Whale accumulation and exchange flows.
- `module_4_sentiment`: Fear & Greed index and social volume.

---

## Aggregation API

### `run_coordinator_agent()`

**Source**: `agents/coordinator_agent.py`

Aggregates technical and fundamental files into a `MasterState`.

**Returns (`MasterState`)**:

- `technical`: `TechnicalData`
- `fundamental`: `FundamentalData`
- `status`: Aggregation status string.

---

## Strategy Synthesis API

### `run_analyst_agent()`

**Source**: `agents/analyst_agent.py`

Applies the **Logic Matrix** to the master state to produce a `FinalDirective`.

**Returns (`FinalDirective`)**:

- `report_metadata`: Date and confidence levels.
- `final_directive`: Stance, leverage, and conviction score.
- `thesis_summary`: Deep logical breakdown of the synthesis.

---

## Report Generation API

### `run_editor_agent()`

**Source**: `agents/editor_agent.py`

Converts the latest directive into Markdown.

**Returns (`EditorResult`)**:

- `summary_path`: String path to the generated `EXECUTIVE_SUMMARY_*.md` file.

---

## Shared Models

All models are defined in `models/models.py`. They leverage Pydantic v2 for strict runtime validation.
