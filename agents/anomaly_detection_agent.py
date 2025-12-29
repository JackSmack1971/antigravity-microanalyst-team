"""
Anomaly Detection Agent module for identifying unusual market behavior.

This module defines the Anomaly Detection Agent, which monitors market data
for unusual patterns, volume spikes, whale activity, and other anomalies
that could signal trading opportunities or risks.
"""
import json
import os
import httpx
from datetime import datetime
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import (
    AnomalyReport,
    Anomaly,
    TechnicalData,
    FundamentalData
)
from deps.dependencies import CryptoDependencies

# Define the Anomaly Detection Agent with explicit types
anomaly_detection_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are an Anomaly Detection Agent specializing in identifying unusual "
        "market behavior and patterns in cryptocurrency markets.\n\n"
        "Your responsibilities:\n"
        "1. Detect volume spikes (>3x average volume)\n"
        "2. Identify unusual price movements (>5% rapid moves)\n"
        "3. Flag extreme technical indicator readings\n"
        "4. Detect unusual on-chain activity (whale movements, exchange flows)\n"
        "5. Monitor sentiment extremes (fear/greed index)\n"
        "6. Identify microstructure anomalies (funding rate extremes, OI spikes)\n"
        "7. Flag macro regime shifts or correlation breakdowns\n\n"
        "For each anomaly detected:\n"
        "- Classify the type and severity (0-100)\n"
        "- Assess market impact (bullish/bearish/neutral)\n"
        "- Recommend monitoring or action steps\n\n"
        "Focus on actionable anomalies that could affect trading decisions."
    ),
    deps_type=CryptoDependencies,
    result_type=AnomalyReport
)

@anomaly_detection_agent.tool
def load_technical_data(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load technical analysis data.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Technical data including price, volume, and indicators.

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

@anomaly_detection_agent.tool
def load_fundamental_data(ctx: RunContext[CryptoDependencies]) -> dict:
    """Load fundamental and on-chain data.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Fundamental data including macro, on-chain, and sentiment metrics.

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

@anomaly_detection_agent.tool
def detect_statistical_anomalies(
    ctx: RunContext[CryptoDependencies],
    current_value: float,
    mean_value: float,
    std_dev: float,
    metric_name: str
) -> dict:
    """Detect statistical anomalies using z-score analysis.

    Args:
        ctx: PydanticAI context containing dependencies.
        current_value: Current value of the metric.
        mean_value: Historical mean of the metric.
        std_dev: Standard deviation of the metric.
        metric_name: Name of the metric being analyzed.

    Returns:
        dict: Anomaly detection results:
            - is_anomaly: Whether an anomaly was detected
            - z_score: Standard deviations from mean
            - severity: Severity score (0-100)
            - direction: "high" or "low"
    """
    try:
        # Calculate z-score
        if std_dev == 0:
            z_score = 0
        else:
            z_score = (current_value - mean_value) / std_dev

        # Classify anomaly
        abs_z = abs(z_score)
        is_anomaly = abs_z > 2.0  # 2 standard deviations

        # Map z-score to severity (0-100)
        if abs_z <= 2.0:
            severity = 0
        elif abs_z <= 3.0:
            severity = min(50 + int((abs_z - 2.0) * 25), 75)
        else:
            severity = min(75 + int((abs_z - 3.0) * 12.5), 100)

        direction = "high" if z_score > 0 else "low"

        return {
            "metric_name": metric_name,
            "is_anomaly": is_anomaly,
            "z_score": round(z_score, 2),
            "severity": severity,
            "direction": direction,
            "current_value": current_value,
            "mean_value": mean_value
        }
    except Exception as e:
        return {"error": f"Failed to detect anomalies: {str(e)}"}

async def run_anomaly_detection_agent(
    symbol: str = "BTC-USD"
) -> AnomalyReport:
    """Run the Anomaly Detection Agent to identify market anomalies.

    Args:
        symbol: The cryptocurrency ticker (e.g., 'BTC-USD'). Defaults to "BTC-USD".

    Returns:
        AnomalyReport: Structured Pydantic model containing detected anomalies.

    Raises:
        Exception: If the agent run fails or data cannot be saved.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "anomaly-detection-001"},
            symbol=symbol
        )

        try:
            result = await anomaly_detection_agent.run(
                f"Analyze market data for {symbol} and detect anomalies.\n\n"
                "Steps:\n"
                "1. Load technical_data to check:\n"
                "   - RSI extremes (>80 overbought, <20 oversold)\n"
                "   - Volume spikes (compare last_vol to avg_vol)\n"
                "   - Price volatility (check price_std)\n"
                "   - Microstructure extremes (funding_rate_bias, squeeze_risk)\n"
                "2. Load fundamental_data to check:\n"
                "   - Fear & Greed Index extremes (<20 extreme fear, >80 extreme greed)\n"
                "   - Whale accumulation signals\n"
                "   - Exchange flow anomalies\n"
                "   - Macro regime shifts\n"
                "   - Alternative data signals (if available)\n"
                "3. Use detect_statistical_anomalies tool for quantitative checks\n"
                "4. For each anomaly found:\n"
                "   - Classify type (e.g., 'volume_spike', 'rsi_extreme', 'whale_movement')\n"
                "   - Assign severity (0-100, use tool results where applicable)\n"
                "   - Determine impact (bullish/bearish/neutral)\n"
                "   - Provide clear description\n"
                "5. Generate severity_scores dict mapping anomaly types to max severity\n"
                "6. Recommend specific actions (e.g., 'Monitor for breakout', 'Watch for reversal')\n"
                "7. Set monitoring alerts for ongoing surveillance\n\n"
                "Focus on actionable anomalies. Minor deviations are not anomalies.",
                deps=deps
            )

            output = result.data.model_dump()

            # Save artifact
            os.makedirs("data", exist_ok=True)
            with open("data/anomaly_report.json", "w") as f:
                json.dump(output, f, indent=2, default=str)

            print(f"Anomaly report saved to data/anomaly_report.json")
            return result.data

        except Exception as e:
            print(f"Error in anomaly_detection_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"

    async def main():
        data = await run_anomaly_detection_agent(symbol)
        print(data.model_dump_json(indent=2))

    asyncio.run(main())
