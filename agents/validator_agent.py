"""
Validator Agent module for cross-checking analysis outputs.

This module defines the Validator Agent, which validates the consistency
and quality of outputs from other agents in the pipeline, checking for
logical inconsistencies, data mismatches, and unsupported claims.
"""
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import (
    ValidationReport,
    ValidationIssue,
    TechnicalData,
    FundamentalData,
    MasterState,
    FinalDirective
)
from deps.dependencies import CryptoDependencies

# Define the Validator Agent with explicit types
validator_agent = create_agent(
    model_name="openai/gpt-4o",  # Use more capable model for complex validation logic
    system_prompt=(
        "You are a Validator Agent responsible for quality assurance across the "
        "multi-agent analysis pipeline. Your task is to rigorously validate outputs "
        "for consistency, logic, and data quality.\n\n"
        "Validation checks you must perform:\n"
        "1. DATA CONSISTENCY:\n"
        "   - Verify technical + fundamental data matches master_state\n"
        "   - Check timestamps are consistent and recent\n"
        "   - Validate numeric values are reasonable (no NaN, extreme outliers)\n"
        "2. LOGICAL CONSISTENCY:\n"
        "   - Verify stance aligns with market conditions (e.g., not Aggressive_Long in Risk_Off)\n"
        "   - Check conviction score matches evidence strength\n"
        "   - Validate leverage cap is appropriate for regime and volatility\n"
        "3. CLAIM VALIDATION:\n"
        "   - Flag unsupported claims in thesis_summary\n"
        "   - Verify technical levels (support/resistance) are based on data\n"
        "   - Check sentiment signals align with actual metrics\n"
        "4. RISK VALIDATION:\n"
        "   - Ensure stop-loss levels exist and are reasonable\n"
        "   - Verify risk assessments match market microstructure\n\n"
        "Issue severity levels:\n"
        "- 'critical': Major logical errors, data corruption, dangerous recommendations\n"
        "- 'warning': Minor inconsistencies, missing context, moderate concerns\n"
        "- 'info': Suggestions for improvement, best practice recommendations\n\n"
        "Be thorough but fair. Only flag genuine issues, not stylistic preferences."
    ),
    deps_type=CryptoDependencies,
    result_type=ValidationReport
)

@validator_agent.tool
def load_technical_data(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load technical analysis data.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Technical data from Quant Agent.

    Raises:
        ModelRetry: If technical_data.json cannot be loaded.
    """
    try:
        with open("data/technical_data.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise ModelRetry(
            "technical_data.json not found. Please run quant_agent first."
        )
    except json.JSONDecodeError as e:
        raise ModelRetry(f"Failed to parse technical_data.json: {e}")

@validator_agent.tool
def load_fundamental_data(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load fundamental and on-chain data.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Fundamental data from Scout Agent.

    Raises:
        ModelRetry: If fundamental_data.json cannot be loaded.
    """
    try:
        with open("data/fundamental_data.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise ModelRetry(
            "fundamental_data.json not found. Please run scout_agent first."
        )
    except json.JSONDecodeError as e:
        raise ModelRetry(f"Failed to parse fundamental_data.json: {e}")

@validator_agent.tool
def load_master_state(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load the Master State from Coordinator Agent.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Master State data.

    Raises:
        ModelRetry: If master_state.json cannot be loaded.
    """
    try:
        with open("data/master_state.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise ModelRetry(
            "master_state.json not found. Please run coordinator_agent first."
        )
    except json.JSONDecodeError as e:
        raise ModelRetry(f"Failed to parse master_state.json: {e}")

@validator_agent.tool
def load_final_directive(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load the Final Directive from Lead Analyst Agent.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Final Directive data.

    Raises:
        ModelRetry: If directive file cannot be loaded.
    """
    try:
        # Find the latest directive file
        files = [f for f in os.listdir("data") if f.startswith("FINAL_DIRECTIVE_")]
        if not files:
            raise ModelRetry("No FINAL_DIRECTIVE file found. Please run analyst_agent first.")

        latest_file = sorted(files)[-1]
        with open(f"data/{latest_file}", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        raise ModelRetry("data directory not found. Please run the analysis pipeline first.")
    except json.JSONDecodeError as e:
        raise ModelRetry(f"Failed to parse directive file: {e}")

@validator_agent.tool
def validate_data_integrity(
    ctx: RunContext[CryptoDependencies],
    field_name: str,
    expected_value: any,
    actual_value: any,
    tolerance: float = 0.01
) -> dict:
    """Validate that data fields match between different outputs.

    Args:
        ctx: PydanticAI context containing dependencies.
        field_name: Name of the field being validated.
        expected_value: Expected value from source.
        actual_value: Actual value in target.
        tolerance: Acceptable relative difference for numeric values (default: 1%).

    Returns:
        dict: Validation result:
            - matches: Whether values match within tolerance
            - difference: Absolute or relative difference
            - severity: Issue severity if mismatch found
    """
    try:
        # Handle numeric comparisons
        if isinstance(expected_value, (int, float)) and isinstance(actual_value, (int, float)):
            if expected_value == 0:
                matches = actual_value == 0
                difference = abs(actual_value)
            else:
                rel_diff = abs(expected_value - actual_value) / abs(expected_value)
                matches = rel_diff <= tolerance
                difference = rel_diff
        # Handle string comparisons
        elif isinstance(expected_value, str) and isinstance(actual_value, str):
            matches = expected_value.lower().strip() == actual_value.lower().strip()
            difference = 0 if matches else 1
        # Handle exact comparisons for other types
        else:
            matches = expected_value == actual_value
            difference = 0 if matches else 1

        severity = "critical" if not matches and difference > 0.1 else "warning" if not matches else "info"

        return {
            "field_name": field_name,
            "matches": matches,
            "expected": str(expected_value),
            "actual": str(actual_value),
            "difference": round(difference, 4) if isinstance(difference, float) else difference,
            "severity": severity
        }
    except Exception as e:
        return {"error": f"Failed to validate data integrity: {str(e)}"}

async def run_validator_agent(
    symbol: str = "BTC-USD"
) -> ValidationReport:
    """Run the Validator Agent to validate analysis pipeline outputs.

    Args:
        symbol: The cryptocurrency ticker (e.g., 'BTC-USD'). Defaults to "BTC-USD".

    Returns:
        ValidationReport: Structured Pydantic model containing validation results.

    Raises:
        Exception: If the agent run fails or data cannot be saved.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "validator-001"},
            symbol=symbol
        )

        try:
            result = await validator_agent.run(
                f"Validate all analysis outputs for {symbol}. Perform comprehensive quality checks.\n\n"
                "Validation Steps:\n"
                "1. DATA CONSISTENCY CHECKS:\n"
                "   a. Load technical_data, fundamental_data, and master_state\n"
                "   b. Use validate_data_integrity tool to verify:\n"
                "      - Technical data in master_state matches technical_data source\n"
                "      - Fundamental data in master_state matches fundamental_data source\n"
                "      - Current price is consistent across all outputs\n"
                "   c. Check all timestamps are recent (within last 24 hours)\n"
                "2. LOGICAL CONSISTENCY CHECKS:\n"
                "   a. Load final_directive\n"
                "   b. Validate stance logic:\n"
                "      - If macro_regime='Risk_Off', stance should NOT be Aggressive_Long\n"
                "      - If RSI > 80 and squeeze_risk='High', verify appropriate caution\n"
                "      - If sentiment_signal='Sell' but stance is long, check justification\n"
                "   c. Validate conviction score:\n"
                "      - High conviction (>70) requires strong confirming signals\n"
                "      - Low conviction (<30) with extreme stance is inconsistent\n"
                "   d. Validate leverage cap:\n"
                "      - 5x leverage only appropriate in strong trending markets\n"
                "      - 1x should be used in high volatility or Risk_Off regime\n"
                "3. CLAIM VALIDATION:\n"
                "   a. Review thesis_summary for unsupported claims\n"
                "   b. Verify technical levels mentioned exist in data\n"
                "   c. Check sentiment claims align with fear_greed_index and social_volume\n"
                "4. GENERATE VALIDATION REPORT:\n"
                "   a. Create ValidationIssue for each problem found (severity: critical/warning/info)\n"
                "   b. Calculate consistency_score (0-100): 100 = perfect, deduct 10 per warning, 25 per critical\n"
                "   c. Calculate data_quality_score based on completeness and accuracy\n"
                "   d. Calculate logic_quality_score based on stance/conviction alignment\n"
                "   e. Set validation_passed = true only if no critical issues\n"
                "   f. Provide concise summary of findings\n\n"
                "Be thorough but fair. Only flag genuine issues.",
                deps=deps
            )

            output = result.data.model_dump()

            # Save artifact
            os.makedirs("data", exist_ok=True)
            with open("data/validation_report.json", "w") as f:
                json.dump(output, f, indent=2, default=str)

            print(f"Validation report saved to data/validation_report.json")
            return result.data

        except Exception as e:
            print(f"Error in validator_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"

    async def main():
        data = await run_validator_agent(symbol)
        print(data.model_dump_json(indent=2))

    asyncio.run(main())
