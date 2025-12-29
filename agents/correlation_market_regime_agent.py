"""
Correlation & Market Regime Analyzer Agent module.

This module defines the Correlation & Market Regime Analyzer Agent, which analyzes
rolling correlations between crypto and traditional assets, detects market regime
changes, identifies correlation breakdowns, and assesses contagion risks.
"""
import json
import os
import httpx
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pydantic_ai import RunContext, ModelRetry
from config.agent_factory import create_agent
from models.models import (
    CorrelationMarketRegimeAnalysis,
    MasterState,
    FinalDirective
)
from deps.dependencies import CryptoDependencies

# Define the Correlation & Market Regime Analyzer Agent
correlation_regime_agent = create_agent(
    model_name="openai/gpt-4o-mini",
    system_prompt=(
        "You are a Correlation & Market Regime Analyzer specializing in cross-asset "
        "correlations and market regime detection for cryptocurrency markets. Your task is to:\n"
        "1. Analyze rolling correlations between BTC and major assets (ETH, SPX, DXY, Gold)\n"
        "2. Detect current market regime (risk_on/risk_off/transitional/decoupled)\n"
        "3. Identify correlation breakdowns and flight-to-quality events\n"
        "4. Assess cross-asset contagion risks\n"
        "5. Detect crypto decoupling events from traditional markets\n"
        "6. Provide actionable insights for trading strategy adjustments\n\n"
        "Use statistical methods and historical context to classify regimes and "
        "detect significant changes in correlation patterns. Always provide clear "
        "interpretations and trading implications."
    ),
    deps_type=CryptoDependencies,
    result_type=CorrelationMarketRegimeAnalysis
)

@correlation_regime_agent.tool
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

@correlation_regime_agent.tool
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

@correlation_regime_agent.tool
async def fetch_correlation_data(
    ctx: RunContext[CryptoDependencies],
    lookback_days: int = 90
) -> Dict[str, Any]:
    """Fetch historical price data for correlation analysis.

    Fetches price data for BTC and correlated assets (ETH, SPX, DXY, Gold)
    to calculate rolling correlations.

    Args:
        ctx: PydanticAI context containing dependencies.
        lookback_days: Number of days of historical data to fetch (default: 90).

    Returns:
        dict: Historical price data for correlation calculation with keys:
            - btc_prices: List of BTC prices
            - eth_prices: List of ETH prices
            - spx_prices: List of S&P 500 prices
            - dxy_prices: List of DXY (US Dollar Index) prices
            - gold_prices: List of Gold prices
            - dates: List of date strings
    """
    try:
        import yfinance as yf

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        # Fetch data for all assets
        symbols = {
            'BTC-USD': 'btc_prices',
            'ETH-USD': 'eth_prices',
            '^GSPC': 'spx_prices',  # S&P 500
            'DX-Y.NYB': 'dxy_prices',  # US Dollar Index
            'GC=F': 'gold_prices'  # Gold futures
        }

        result = {}
        dates = None

        for symbol, key in symbols.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)

                if not hist.empty:
                    result[key] = hist['Close'].tolist()
                    if dates is None:
                        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
                else:
                    result[key] = []
            except Exception as e:
                # Return empty list if symbol fetch fails
                result[key] = []

        result['dates'] = dates if dates is not None else []
        result['status'] = 'success'

        return result

    except Exception as e:
        return {
            "error": f"Failed to fetch correlation data: {str(e)}",
            "status": "failed"
        }

@correlation_regime_agent.tool
def calculate_rolling_correlations(
    ctx: RunContext[CryptoDependencies],
    btc_prices: List[float],
    other_prices: List[float],
    window_30d: int = 30,
    window_90d: int = 90
) -> Dict[str, Any]:
    """Calculate rolling correlations between BTC and another asset.

    Args:
        ctx: PydanticAI context containing dependencies.
        btc_prices: List of BTC prices.
        other_prices: List of prices for the other asset.
        window_30d: Window size for 30-day rolling correlation (default: 30).
        window_90d: Window size for 90-day rolling correlation (default: 90).

    Returns:
        dict: Correlation metrics including:
            - correlation_current: Most recent correlation coefficient
            - rolling_30d: 30-day rolling correlation
            - rolling_90d: 90-day rolling correlation
            - correlation_trend: Trend direction (strengthening/weakening/stable)
    """
    try:
        # Ensure we have enough data
        if len(btc_prices) < window_30d or len(other_prices) < window_30d:
            return {
                "error": "Insufficient data for correlation calculation",
                "correlation_current": 0.0,
                "rolling_30d": 0.0,
                "rolling_90d": 0.0,
                "correlation_trend": "insufficient_data"
            }

        # Convert to numpy arrays
        btc_array = np.array(btc_prices)
        other_array = np.array(other_prices)

        # Calculate current correlation (full period)
        correlation_current = float(np.corrcoef(btc_array, other_array)[0, 1])

        # Calculate 30-day rolling correlation (most recent)
        if len(btc_prices) >= window_30d:
            btc_30d = btc_array[-window_30d:]
            other_30d = other_array[-window_30d:]
            rolling_30d = float(np.corrcoef(btc_30d, other_30d)[0, 1])
        else:
            rolling_30d = correlation_current

        # Calculate 90-day rolling correlation (most recent)
        if len(btc_prices) >= window_90d:
            btc_90d = btc_array[-window_90d:]
            other_90d = other_array[-window_90d:]
            rolling_90d = float(np.corrcoef(btc_90d, other_90d)[0, 1])
        else:
            rolling_90d = correlation_current

        # Determine trend
        if abs(rolling_30d - rolling_90d) < 0.1:
            correlation_trend = "stable"
        elif rolling_30d > rolling_90d:
            correlation_trend = "strengthening"
        else:
            correlation_trend = "weakening"

        return {
            "correlation_current": round(correlation_current, 3),
            "rolling_30d": round(rolling_30d, 3),
            "rolling_90d": round(rolling_90d, 3),
            "correlation_trend": correlation_trend,
            "status": "success"
        }

    except Exception as e:
        return {
            "error": f"Failed to calculate correlations: {str(e)}",
            "correlation_current": 0.0,
            "rolling_30d": 0.0,
            "rolling_90d": 0.0,
            "correlation_trend": "error"
        }

@correlation_regime_agent.tool
def detect_regime_change(
    ctx: RunContext[CryptoDependencies],
    btc_spx_corr: float,
    btc_dxy_corr: float,
    btc_gold_corr: float
) -> Dict[str, Any]:
    """Detect current market regime based on correlation patterns.

    Uses correlation patterns to classify market regime:
    - risk_on: Positive BTC-SPX, negative BTC-DXY correlation
    - risk_off: Negative BTC-SPX, positive BTC-DXY correlation
    - decoupled: Low correlation with traditional markets
    - transitional: Mixed or changing correlation patterns

    Args:
        ctx: PydanticAI context containing dependencies.
        btc_spx_corr: BTC-SPX correlation coefficient.
        btc_dxy_corr: BTC-DXY correlation coefficient.
        btc_gold_corr: BTC-Gold correlation coefficient.

    Returns:
        dict: Regime classification with:
            - regime_type: Classified regime type
            - confidence: Confidence score (0-1)
            - characteristics: List of regime characteristics
    """
    try:
        characteristics = []

        # Risk-on regime: BTC moves with equities (positive correlation)
        # and against dollar (negative correlation)
        if btc_spx_corr > 0.5 and btc_dxy_corr < -0.3:
            regime_type = "risk_on"
            confidence = min(abs(btc_spx_corr), abs(btc_dxy_corr))
            characteristics = [
                "BTC tracking equities higher",
                "Negative correlation with US Dollar",
                "Risk appetite driving crypto",
                "Favorable for aggressive positioning"
            ]

        # Risk-off regime: BTC decouples or moves with safe havens
        elif btc_spx_corr < -0.3 or (abs(btc_spx_corr) < 0.3 and btc_gold_corr > 0.5):
            regime_type = "risk_off"
            confidence = 0.7
            characteristics = [
                "BTC decoupling from equities",
                "Potential flight to quality",
                "Increased market uncertainty",
                "Defensive positioning recommended"
            ]

        # Decoupled regime: Low correlation with all traditional assets
        elif abs(btc_spx_corr) < 0.3 and abs(btc_dxy_corr) < 0.3 and abs(btc_gold_corr) < 0.3:
            regime_type = "decoupled"
            confidence = 0.6
            characteristics = [
                "BTC trading independently",
                "Crypto-specific drivers dominant",
                "Low macro influence",
                "Focus on crypto-native catalysts"
            ]

        # Transitional regime: Mixed or unclear signals
        else:
            regime_type = "transitional"
            confidence = 0.5
            characteristics = [
                "Mixed correlation signals",
                "Regime potentially shifting",
                "Increased uncertainty",
                "Monitor for regime confirmation"
            ]

        return {
            "regime_type": regime_type,
            "confidence": float(confidence),
            "characteristics": characteristics,
            "status": "success"
        }

    except Exception as e:
        return {
            "error": f"Failed to detect regime: {str(e)}",
            "regime_type": "unknown",
            "confidence": 0.0,
            "characteristics": [],
            "status": "failed"
        }

async def run_correlation_regime_agent(
    symbol: str = "BTC-USD",
    lookback_days: int = 90
) -> CorrelationMarketRegimeAnalysis:
    """Run the Correlation & Market Regime Analyzer Agent.

    Args:
        symbol: The cryptocurrency ticker (e.g., 'BTC-USD'). Defaults to "BTC-USD".
        lookback_days: Number of days for historical correlation analysis (default: 90).

    Returns:
        CorrelationMarketRegimeAnalysis: Complete correlation and regime analysis.
    """
    async with httpx.AsyncClient() as client:
        deps = CryptoDependencies(
            http_client=client,
            user_context={"request_id": f"correlation-regime-{datetime.now().isoformat()}"},
            symbol=symbol
        )

        result = await correlation_regime_agent.run(
            f"Analyze correlations and market regime for {symbol} using {lookback_days} days of data. "
            f"Calculate rolling correlations with ETH, SPX, DXY, and Gold. Detect the current market regime, "
            f"identify any correlation breakdowns, and assess contagion risks. Provide actionable insights.",
            deps=deps
        )

        # Save the result
        output_file = "data/correlation_regime_analysis.json"
        os.makedirs("data", exist_ok=True)

        with open(output_file, "w") as f:
            f.write(result.data.model_dump_json(indent=2))

        print(f"✓ Correlation & Market Regime Analysis saved to {output_file}")

        return result.data

if __name__ == "__main__":
    import asyncio
    import sys

    # Parse command line arguments
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BTC-USD"
    lookback_days = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    print(f"Running Correlation & Market Regime Analyzer for {symbol}...")
    print(f"Lookback period: {lookback_days} days\n")

    result = asyncio.run(run_correlation_regime_agent(symbol, lookback_days))

    print("\n=== CORRELATION & MARKET REGIME ANALYSIS ===\n")
    print(f"Current Regime: {result.current_regime.regime_type.upper()}")
    print(f"Confidence: {result.current_regime.confidence:.2%}")
    print(f"\nKey Insights:")
    for insight in result.key_insights:
        print(f"  • {insight}")
    print(f"\nRegime Outlook: {result.regime_outlook}")
