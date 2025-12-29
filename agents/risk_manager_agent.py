"""
Risk Manager Agent module for risk assessment and position sizing.

This module defines the Risk Manager Agent, which analyzes market conditions
and generates risk-adjusted position sizing recommendations with stop-loss
and take-profit levels.
"""
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import (
    RiskAssessment,
    MasterState,
    FinalDirective
)
from deps.dependencies import CryptoDependencies

# Define the Risk Manager Agent with explicit types
risk_manager_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Risk Manager Agent specializing in cryptocurrency risk assessment. "
        "Your task is to analyze market conditions, technical data, and current directives "
        "to provide risk-adjusted position sizing recommendations. You must calculate:\n"
        "1. Appropriate position sizes based on volatility and risk tolerance\n"
        "2. Stop-loss levels to protect capital\n"
        "3. Take-profit targets aligned with risk/reward ratios\n"
        "4. Tail risk assessment for black swan events\n"
        "5. Correlation risks across crypto assets\n"
        "Always prioritize capital preservation and provide conservative estimates when uncertain."
    ),
    deps_type=CryptoDependencies,
    result_type=RiskAssessment
)

@risk_manager_agent.tool
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

@risk_manager_agent.tool
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

@risk_manager_agent.tool
def calculate_position_metrics(
    ctx: RunContext[CryptoDependencies],
    current_price: float,
    volatility: float,
    portfolio_size_usd: float = 10000.0,
    risk_tolerance_pct: float = 2.0
) -> dict:
    """Calculate position sizing metrics based on volatility and risk parameters.

    Args:
        ctx: PydanticAI context containing dependencies.
        current_price: Current price of the asset.
        volatility: Price volatility (standard deviation).
        portfolio_size_usd: Total portfolio size in USD (default: $10,000).
        risk_tolerance_pct: Maximum portfolio risk per trade (default: 2%).

    Returns:
        dict: Position sizing metrics including:
            - position_size_usd: Position size in USD
            - position_size_btc: Position size in BTC
            - risk_amount_usd: Amount at risk
            - stop_distance_pct: Recommended stop distance as percentage
    """
    try:
        # Calculate risk amount
        risk_amount_usd = portfolio_size_usd * (risk_tolerance_pct / 100)

        # Stop distance based on volatility (typically 2-3x volatility)
        stop_distance_pct = min(volatility * 2.5, 15.0)  # Cap at 15%

        # Position size = Risk Amount / Stop Distance
        position_size_usd = risk_amount_usd / (stop_distance_pct / 100)

        # Cap position size at 20% of portfolio
        max_position_size = portfolio_size_usd * 0.20
        position_size_usd = min(position_size_usd, max_position_size)

        # Convert to BTC
        position_size_btc = position_size_usd / current_price if current_price > 0 else 0

        return {
            "position_size_usd": round(position_size_usd, 2),
            "position_size_btc": round(position_size_btc, 6),
            "risk_amount_usd": round(risk_amount_usd, 2),
            "stop_distance_pct": round(stop_distance_pct, 2)
        }
    except Exception as e:
        return {"error": f"Failed to calculate position metrics: {str(e)}"}

async def run_risk_manager_agent(
    symbol: str = "BTC-USD",
    portfolio_size_usd: float = 10000.0,
    risk_tolerance_pct: float = 2.0
) -> RiskAssessment:
    """Run the Risk Manager Agent to generate risk assessment and position sizing.

    Args:
        symbol: The cryptocurrency ticker (e.g., 'BTC-USD'). Defaults to "BTC-USD".
        portfolio_size_usd: Total portfolio size in USD (default: $10,000).
        risk_tolerance_pct: Maximum portfolio risk per trade (default: 2%).

    Returns:
        RiskAssessment: Structured Pydantic model containing risk analysis and recommendations.

    Raises:
        Exception: If the agent run fails or data cannot be saved.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "risk-manager-001"},
            symbol=symbol
        )

        try:
            result = await risk_manager_agent.run(
                f"Analyze risk parameters for {symbol} and generate position sizing recommendations. "
                f"Portfolio size: ${portfolio_size_usd:,.2f}, Risk tolerance: {risk_tolerance_pct}%.\n\n"
                "Steps:\n"
                "1. Load the master_state to get current price, volatility, and market conditions.\n"
                "2. Load the final_directive to understand the current stance and conviction.\n"
                "3. Use calculate_position_metrics tool to determine optimal position size.\n"
                "4. Set stop-loss level based on technical support and volatility.\n"
                "5. Define 2-3 take-profit targets with risk/reward ratios of at least 2:1.\n"
                "6. Assess tail risk (0-100 score) based on market microstructure and macro regime.\n"
                "7. Calculate max drawdown estimate based on volatility and leverage.\n"
                "8. Check for correlation warnings if macro regime is Risk_Off or extreme funding.\n"
                "Provide conservative estimates that prioritize capital preservation.",
                deps=deps
            )

            output = result.data.model_dump()

            # Save artifact
            os.makedirs("data", exist_ok=True)
            with open("data/risk_assessment.json", "w") as f:
                json.dump(output, f, indent=2, default=str)

            print(f"Risk assessment saved to data/risk_assessment.json")
            return result.data

        except Exception as e:
            print(f"Error in risk_manager_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    portfolio_size = float(sys.argv[2]) if len(sys.argv) > 2 else 10000.0
    risk_tolerance = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0

    async def main():
        data = await run_risk_manager_agent(symbol, portfolio_size, risk_tolerance)
        print(data.model_dump_json(indent=2))

    asyncio.run(main())
