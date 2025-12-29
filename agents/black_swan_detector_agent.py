"""
Black Swan Event Detector Agent module for identifying extreme market events.

This module defines the Black Swan Event Detector Agent, which monitors market
conditions for extreme events that could trigger rapid risk management responses.
"""
import json
import os
import httpx
from datetime import datetime, timedelta
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import (
    BlackSwanEventReport,
    BlackSwanEvent,
    EmergencyResponse,
    MarketStabilityMetrics,
    MasterState
)
from deps.dependencies import CryptoDependencies

# Define the Black Swan Event Detector Agent
black_swan_detector_agent = create_agent(
    model_name="openai/gpt-4o",
    system_prompt=(
        "You are a Black Swan Event Detector Agent specializing in identifying extreme, "
        "unexpected market events that pose significant risks to trading positions. "
        "Your primary responsibility is to detect and assess:\n\n"
        "1. **Extreme Price Movements**: Sudden price changes >10% in short timeframes\n"
        "2. **Volume Spikes**: Trading volume surges >5x the average\n"
        "3. **Volatility Explosions**: VIX-equivalent metrics >50 indicating market panic\n"
        "4. **Market Structure Breakdown**: Exchange outages, liquidity crises, flash crashes\n"
        "5. **External Shocks**: Major regulatory announcements, protocol hacks, systemic failures\n\n"
        "When black swan events are detected, you must:\n"
        "- Assess severity and confidence levels\n"
        "- Generate emergency response recommendations\n"
        "- Recommend defensive positioning (stance override, position reduction)\n"
        "- Flag uncertainty for downstream analysis\n"
        "- Prioritize capital preservation above all else\n\n"
        "Your analysis must be rapid, decisive, and conservative. False positives are "
        "acceptable - missing a true black swan event is not. Always err on the side of caution."
    ),
    deps_type=CryptoDependencies,
    result_type=BlackSwanEventReport
)

@black_swan_detector_agent.tool
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

@black_swan_detector_agent.tool
def fetch_recent_price_data(
    ctx: RunContext[CryptoDependencies],
    symbol: str = "BTC-USD",
    hours: int = 24
) -> dict:
    """Fetch recent price data to analyze for extreme movements.

    Args:
        ctx: PydanticAI context containing dependencies.
        symbol: Trading symbol to analyze.
        hours: Number of hours of historical data to fetch.

    Returns:
        dict: Recent price data including OHLCV and calculated metrics.
    """
    try:
        # In production, this would fetch real data from exchange API
        # For now, we'll return simulated data with realistic patterns
        from datetime import datetime, timedelta
        import random

        current_time = datetime.utcnow()
        base_price = 45000.0  # Base BTC price

        # Generate hourly candles
        candles = []
        for i in range(hours):
            timestamp = current_time - timedelta(hours=hours-i)
            # Add some random volatility
            volatility = random.uniform(-2, 2)  # Normal ±2%

            # Simulate occasional spikes
            if random.random() < 0.05:  # 5% chance of spike
                volatility = random.uniform(-8, 8)

            price = base_price * (1 + volatility/100)
            volume = random.uniform(500, 1500)  # Base volume in millions

            # Simulate volume spikes
            if abs(volatility) > 5:
                volume *= random.uniform(3, 7)

            candles.append({
                "timestamp": timestamp.isoformat(),
                "open": price * 0.998,
                "high": price * 1.002,
                "low": price * 0.998,
                "close": price,
                "volume": volume
            })

        # Calculate metrics
        prices = [c["close"] for c in candles]
        volumes = [c["volume"] for c in candles]

        # Hourly price changes
        hourly_changes = []
        for i in range(1, len(prices)):
            change_pct = ((prices[i] - prices[i-1]) / prices[i-1]) * 100
            hourly_changes.append(change_pct)

        max_hourly_change = max(hourly_changes, key=abs) if hourly_changes else 0
        avg_volume = sum(volumes) / len(volumes) if volumes else 1
        current_volume = volumes[-1] if volumes else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

        # Calculate volatility
        if len(hourly_changes) > 1:
            mean_change = sum(hourly_changes) / len(hourly_changes)
            variance = sum((x - mean_change) ** 2 for x in hourly_changes) / len(hourly_changes)
            volatility_pct = (variance ** 0.5)
        else:
            volatility_pct = 0

        return {
            "symbol": symbol,
            "candles": candles[-10:],  # Return last 10 for context
            "current_price": prices[-1],
            "max_hourly_change_pct": round(max_hourly_change, 2),
            "recent_1h_change_pct": round(hourly_changes[-1], 2) if hourly_changes else 0,
            "recent_4h_change_pct": round(sum(hourly_changes[-4:]), 2) if len(hourly_changes) >= 4 else 0,
            "volatility_pct": round(volatility_pct, 2),
            "avg_volume": round(avg_volume, 2),
            "current_volume": round(current_volume, 2),
            "volume_ratio": round(volume_ratio, 2)
        }
    except Exception as e:
        return {
            "error": f"Failed to fetch price data: {str(e)}",
            "symbol": symbol
        }

@black_swan_detector_agent.tool
def calculate_market_stress_metrics(
    ctx: RunContext[CryptoDependencies],
    volatility_pct: float,
    volume_ratio: float,
    price_change_1h: float,
    rsi: float = 50.0
) -> dict:
    """Calculate comprehensive market stress and stability metrics.

    Args:
        ctx: PydanticAI context containing dependencies.
        volatility_pct: Current volatility percentage.
        volume_ratio: Current volume vs average ratio.
        price_change_1h: 1-hour price change percentage.
        rsi: Current RSI value.

    Returns:
        dict: Market stress metrics including stability scores and stress index.
    """
    try:
        # Calculate volatility percentile (normalized to 0-100)
        # Typical crypto volatility ranges from 1-10%
        volatility_percentile = min((volatility_pct / 10.0) * 100, 100)

        # Price stability score (inverse of volatility)
        price_stability_score = max(0, 100 - (abs(price_change_1h) * 5))

        # Volume stability score
        # Normal volume ratio is 0.5-2.0x, extreme is >5x
        if volume_ratio < 0.5:
            volume_stability_score = 60  # Low volume is concerning
        elif volume_ratio <= 2.0:
            volume_stability_score = 100  # Normal range
        elif volume_ratio <= 5.0:
            volume_stability_score = 50  # Elevated volume
        else:
            volume_stability_score = 20  # Extreme volume spike

        # Liquidity health assessment
        if volume_ratio > 5.0 and abs(price_change_1h) > 10:
            liquidity_health = "crisis"
        elif volume_ratio > 3.0 or abs(price_change_1h) > 5:
            liquidity_health = "stressed"
        else:
            liquidity_health = "healthy"

        # Overall market stress index (0-100)
        stress_components = [
            min(volatility_pct * 10, 100),  # Volatility contribution
            min(abs(price_change_1h) * 5, 100),  # Price change contribution
            min(max(0, volume_ratio - 1) * 20, 100),  # Volume spike contribution
            abs(rsi - 50) * 2  # RSI extremity contribution
        ]
        market_stress_index = int(sum(stress_components) / len(stress_components))

        return {
            "current_volatility": round(volatility_pct, 2),
            "volatility_percentile": round(volatility_percentile, 2),
            "price_stability_score": int(price_stability_score),
            "volume_stability_score": int(volume_stability_score),
            "liquidity_health": liquidity_health,
            "market_stress_index": market_stress_index
        }
    except Exception as e:
        return {
            "error": f"Failed to calculate stress metrics: {str(e)}"
        }

@black_swan_detector_agent.tool
def check_anomaly_report(ctx: RunContext[CryptoDependencies]) -> dict:
    """Check if the Anomaly Detection Agent has flagged any critical anomalies.

    Args:
        ctx: PydanticAI context containing dependencies.

    Returns:
        dict: Anomaly report data if available, including critical alerts.
    """
    try:
        if os.path.exists("data/anomaly_report.json"):
            with open("data/anomaly_report.json", "r") as f:
                data = json.load(f)

            # Extract high-severity anomalies
            critical_anomalies = []
            if "anomalies_detected" in data:
                for anomaly in data["anomalies_detected"]:
                    if anomaly.get("severity", 0) >= 70:
                        critical_anomalies.append(anomaly)

            return {
                "anomalies_available": True,
                "critical_anomalies": critical_anomalies,
                "total_anomalies": len(data.get("anomalies_detected", [])),
                "severity_scores": data.get("severity_scores", {})
            }
        else:
            return {
                "anomalies_available": False,
                "message": "No anomaly report found. This is not an error - continuing with price-based detection."
            }
    except Exception as e:
        return {
            "anomalies_available": False,
            "error": f"Error reading anomaly report: {str(e)}"
        }

async def run_black_swan_detector(
    symbol: str = "BTC-USD",
    lookback_hours: int = 24
) -> BlackSwanEventReport:
    """Run the Black Swan Event Detector Agent to identify extreme market events.

    Args:
        symbol: The cryptocurrency ticker (e.g., 'BTC-USD'). Defaults to "BTC-USD".
        lookback_hours: Hours of historical data to analyze. Defaults to 24.

    Returns:
        BlackSwanEventReport: Structured report containing detected events and responses.

    Raises:
        Exception: If the agent run fails or data cannot be saved.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": "black-swan-detector-001"},
            symbol=symbol
        )

        try:
            result = await black_swan_detector_agent.run(
                f"Analyze {symbol} for black swan events and extreme market conditions.\n\n"
                "**Detection Protocol**:\n"
                "1. Load master_state to get current market conditions and RSI.\n"
                "2. Fetch recent price data using fetch_recent_price_data tool.\n"
                "3. Check for anomaly reports using check_anomaly_report tool.\n"
                "4. Calculate market stress metrics using calculate_market_stress_metrics tool.\n\n"
                "**Black Swan Detection Criteria**:\n"
                "- **Extreme Price Move**: 1-hour price change >10% (severity: 80-100)\n"
                "- **Major Price Move**: 1-hour price change >7% (severity: 60-79)\n"
                "- **Volume Spike**: Volume ratio >5x average (severity: 70-90)\n"
                "- **Volatility Explosion**: Volatility >8% (severity: 60-85)\n"
                "- **Market Stress**: Market stress index >75 (severity: 65-95)\n"
                "- **Critical Anomalies**: High-severity anomalies from anomaly detector\n\n"
                "**Emergency Response Guidelines**:\n"
                "- If severity ≥80: alert_level='critical', recommend Neutral or Exit stance, 50-100% position reduction\n"
                "- If severity 60-79: alert_level='high', recommend Defensive_Long, 25-50% position reduction\n"
                "- If severity 40-59: alert_level='medium', recommend Defensive_Long, 10-25% position reduction\n"
                "- If severity <40: alert_level='low', maintain current stance, monitor closely\n\n"
                "**Always prioritize capital preservation. When in doubt, recommend defensive action.**",
                deps=deps
            )

            output = result.data.model_dump()

            # Save artifact
            os.makedirs("data", exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"data/black_swan_report_{timestamp}.json"

            with open(filename, "w") as f:
                json.dump(output, f, indent=2, default=str)

            # Also save as latest
            with open("data/black_swan_report.json", "w") as f:
                json.dump(output, f, indent=2, default=str)

            print(f"Black Swan Event Report saved to {filename}")
            return result.data

        except Exception as e:
            print(f"Error in black_swan_detector_agent: {e}")
            raise

if __name__ == "__main__":
    import asyncio
    import sys

    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    lookback_hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24

    async def main():
        data = await run_black_swan_detector(symbol, lookback_hours)
        print("\n" + "="*80)
        print("BLACK SWAN EVENT DETECTOR REPORT")
        print("="*80)
        print(data.model_dump_json(indent=2))

        if data.black_swan_detected:
            print("\n⚠️  BLACK SWAN EVENT(S) DETECTED! ⚠️")
            print(f"Overall Risk Level: {data.overall_risk_level}")
            print(f"Severity Score: {data.severity_score}/100")
            print(f"Alert Level: {data.emergency_response.alert_level}")

    asyncio.run(main())
