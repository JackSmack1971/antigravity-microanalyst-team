# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-12-28

### Added

- **PydanticAI Integration**: Migrated all agents (Quant, Scout, Coordinator, Analyst, Editor) to the PydanticAI framework.
- **Dependency Injection**: Implemented `CryptoDependencies` for safe, typed resource sharing across the swarm.
- **Agent Factory**: Created `agent_factory.py` for standardized agent creation with OpenRouter/OpenAI provider support.
- **Production Resilience**:
  - Exponential backoff retries using `tenacity`.
  - Structured output validation using `@agent.output_validator`.
  - Standardized `ModelSettings` (temperature, timeout, max_tokens).
- **Logic Matrix Synchronization**: Injected explicit boolean logic (Macro Veto, Structure Priority, Liquidity Filter) into the Lead Analyst Agent.
- **Nested Schema Compliance**: Updated `FinalDirective` model to match the formal `module_9_synthesizer.md` specification.
- **Comprehensive Documentation**: Automated generation of `README.md`, `API_DOCUMENTATION.md`, and Google-style inline docstrings.

### Changed

- Refactored `run_quant_agent` to use asynchronous dependency injection.
- Standardized file persistence for agent outputs (JSON-based reports).
- Refined `analyst_agent` to handle nested Pydantic models in directives.

### Fixed

- Resolved `ModuleNotFoundError` during agent initialization by standardizing imports.
- Corrected `Agent` constructor parameters to align with `pydantic-ai` v1.39.0 (`output_type`).
