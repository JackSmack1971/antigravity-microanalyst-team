"""
Scenario Planner Agent module for what-if market scenario analysis.

This module defines the Scenario Planner Agent, which generates multiple
market scenarios (bull/bear/base cases) with probability assessments and
identifies key catalysts and invalidation levels.
"""
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import (
    ScenarioAnalysis,
    MarketScenario,
    MasterState
)
from deps.dependencies import CryptoDependencies

# Define the Scenario Planner Agent with explicit types
scenario_planner_agent = create_agent(
    model_name="openai/gpt-4o",  # Use more capable model for complex scenario analysis
    system_prompt=(
        "You are a Scenario Planner Agent specializing in market scenario analysis. "
        "Your task is to analyze current market conditions and generate multiple "
        "plausible future scenarios with probability assessments.\n\n"
        "For each scenario, you must:\n"
        "1. Define clear bull, base, and bear cases\n"
        "2. Assign realistic probabilities that sum to 1.0\n"
        "3. Set specific price targets and timeframes\n"
        "4. Identify key drivers and catalysts\n"
        "5. Define invalidation levels for each scenario\n\n"
        "Consider technical levels, fundamental factors, macro events, and on-chain data. "
        "Scenarios should be mutually exclusive and collectively exhaustive. "
        "Be specific about what conditions would trigger each scenario."
    ),
    deps_type=CryptoDependencies,
    result_type=ScenarioAnalysis
)

@scenario_planner_agent.tool
def load_master_state(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load the Master State containing technical and fundamental data.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Master State data with technical and fundamental metrics.

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

@scenario_planner_agent.tool
def load_final_directive(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load the latest Final Directive from the Lead Analyst.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Final Directive data with stance, leverage cap, and conviction.

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

@scenario_planner_agent.tool
def calculate_price_targets(
    ctx: RunContext[CryptoDependencies],
    current_price: float,
    support_levels: list[float],
    resistance_levels: list[float],
    volatility_pct: float
) -> dict:
    """Calculate scenario-based price targets using technical levels and volatility.

    Args:
        ctx: PydanticAI context containing dependencies.
        current_price: Current asset price.
        support_levels: List of support price levels.
        resistance_levels: List of resistance price levels.
        volatility_pct: Price volatility as percentage.

    Returns:
        dict: Calculated price targets for different scenarios:
            - bull_target: Aggressive upside target
            - base_target: Moderate target
            - bear_target: Downside target
            - extreme_bull: Extreme upside (tail scenario)
            - extreme_bear: Extreme downside (tail scenario)
    """
    try:
        # Calculate targets based on volatility and technical levels
        volatility_move = current_price * (volatility_pct / 100)

        # Bull scenario: Break resistance, 2-3x volatility upside
        bull_target = max(
            resistance_levels + [current_price * 1.15]
        ) if resistance_levels else current_price + (2.5 * volatility_move)

        # Base scenario: Moderate movement, 1-1.5x volatility
        base_target = current_price + (1.2 * volatility_move)

        # Bear scenario: Test support, 2-3x volatility downside
        bear_target = min(
            support_levels + [current_price * 0.90]
        ) if support_levels else current_price - (2.5 * volatility_move)

        # Extreme scenarios (tail risks)
        extreme_bull = current_price * 1.30  # +30%
        extreme_bear = current_price * 0.75  # -25%

        return {
            "bull_target": round(bull_target, 2),
            "base_target": round(base_target, 2),
            "bear_target": round(bear_target, 2),
            "extreme_bull_target": round(extreme_bull, 2),
            "extreme_bear_target": round(extreme_bear, 2),
            "current_price": round(current_price, 2)
        }
    except Exception as e:
        return {"error": f"Failed to calculate price targets: {str(e)}"}

async def run_scenario_planner_agent(
    symbol: str = "BTC-USD",
    timeframe: str = "1 week"
) -> ScenarioAnalysis:
    """Run the Scenario Planner Agent to generate market scenarios.

    Args:
        symbol: The cryptocurrency ticker (e.g., 'BTC-USD'). Defaults to "BTC-USD".
        timeframe: Timeframe for scenarios (default: "1 week").

    Returns:
        ScenarioAnalysis: Structured Pydantic model containing scenario analysis.

    Raises:
        Exception: If the agent run fails or data cannot be saved.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "scenario-planner-001"},
            symbol=symbol
        )

        try:
            result = await scenario_planner_agent.run(
                f"Generate comprehensive scenario analysis for {symbol} over {timeframe}.\n\n"
                "Steps:\n"
                "1. Load master_state to understand current market structure, regime, and conditions.\n"
                "2. Load final_directive to see the current analytical stance.\n"
                "3. Use calculate_price_targets tool to get technical-based price levels.\n"
                "4. Create 3-5 scenarios including:\n"
                "   - Bull Case: What drives price higher? (e.g., breakout, positive catalyst)\n"
                "   - Base Case: Most likely outcome based on current data\n"
                "   - Bear Case: What drives price lower? (e.g., breakdown, negative catalyst)\n"
                "   - Optional: Extreme Bull/Bear tail scenarios if appropriate\n"
                "5. Assign probabilities that sum to 1.0 (be realistic, not overly optimistic)\n"
                "6. For each scenario, specify:\n"
                "   - Specific price target from tool or your analysis\n"
                "   - Key drivers (technical, fundamental, macro, on-chain)\n"
                "   - Expected timeframe\n"
                "7. Identify key catalysts to monitor (events, data releases, technical levels)\n"
                "8. Define invalidation levels (prices that would negate each scenario)\n"
                "9. Select the most_likely_scenario based on current data\n\n"
                "Be specific and actionable. Consider current regime, sentiment, and microstructure.",
                deps=deps
            )

            output = result.data.model_dump()

            # Save artifact
            os.makedirs("data", exist_ok=True)
            with open("data/scenario_analysis.json", "w") as f:
                json.dump(output, f, indent=2, default=str)

            print(f"Scenario analysis saved to data/scenario_analysis.json")
            return result.data

        except Exception as e:
            print(f"Error in scenario_planner_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    timeframe = sys.argv[2] if len(sys.argv) > 2 else "1 week"

    async def main():
        data = await run_scenario_planner_agent(symbol, timeframe)
        print(data.model_dump_json(indent=2))

    asyncio.run(main())
