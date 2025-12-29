"""
Data Models module for structured trading state and directives.

This module defines Pydantic models for technical, fundamental, and 
macro data, as well as the final synthesis directives used by the pipeline.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PriceMetrics(BaseModel):
    current_price: float
    rsi_4h: float
    vwap_deviation: float
    regime: str

class RiskProfile(BaseModel):
    invalidation_hard_stop: float
    support_zone: List[float]
    resistance_zone: List[float]

class PriceStructure(BaseModel):
    asset: str
    metrics: PriceMetrics
    risk_profile: RiskProfile

class MicrostructureMetrics(BaseModel):
    funding_rate_bias: str
    open_interest_trend: str
    squeeze_risk: str

class TechnicalData(BaseModel):
    module_1_price_structure: PriceStructure
    module_5_market_microstructure: MicrostructureMetrics
    timestamp_utc: datetime

class MacroMetrics(BaseModel):
    spx_level: float
    dxy_index: float
    macro_regime: str

class OnChainMetrics(BaseModel):
    exchange_net_flow: str
    active_addresses_trend: str
    whale_accumulation: str

class SentimentMetrics(BaseModel):
    fear_greed_index: int
    social_volume: str
    sentiment_signal: str

class FundamentalData(BaseModel):
    module_2_macro: MacroMetrics
    module_3_onchain: OnChainMetrics
    module_4_sentiment: SentimentMetrics
    timestamp_utc: datetime

class MasterState(BaseModel):
    technical: TechnicalData
    fundamental: FundamentalData
    status: str
    aggregation_timestamp: datetime

class ReportMetadata(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    overall_confidence: str = Field(..., description="High|Medium|Low")

class DirectiveContent(BaseModel):
    stance: str = Field(..., description="Aggressive_Long|Defensive_Long|Neutral|Tactical_Short")
    leverage_cap: str = Field(..., description="1x|3x|5x")
    conviction_score: int = Field(..., ge=0, le=100)

class FinalDirective(BaseModel):
    report_metadata: ReportMetadata
    final_directive: DirectiveContent
    thesis_summary: str = Field(..., description="String explaining the synthesis of winning signals.")
