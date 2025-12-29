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

class NewsSentimentData(BaseModel):
    """News sentiment from CryptoPanic and other sources."""
    sentiment_score: float = Field(..., description="Overall sentiment score (-100 to +100)")
    positive_pct: float = Field(..., description="Percentage of positive news")
    negative_pct: float = Field(..., description="Percentage of negative news")
    total_posts: int = Field(..., description="Number of news articles analyzed")

class SocialMediaData(BaseModel):
    """Social media sentiment from Reddit and other platforms."""
    reddit_sentiment: float = Field(..., description="Reddit sentiment score (0-100)")
    engagement_score: float = Field(..., description="Social engagement level")
    total_posts: int = Field(..., description="Number of posts analyzed")

class GoogleTrendsData(BaseModel):
    """Google Trends search interest data."""
    current_interest: int = Field(..., description="Current search interest (0-100)")
    momentum_pct: float = Field(..., description="Momentum percentage change")
    direction: str = Field(..., description="Trend direction")

class GitHubActivityData(BaseModel):
    """GitHub development activity metrics."""
    activity_score: float = Field(..., description="Development activity score (0-100)")
    trend: str = Field(..., description="Activity trend (accelerating/growing/stable/slowing/declining)")
    recent_commits: int = Field(..., description="Recent commit count")

class OptionsMarketData(BaseModel):
    """Options market metrics from Deribit."""
    put_call_ratio: float = Field(..., description="Put/Call ratio by volume")
    avg_implied_volatility: float = Field(..., description="Average IV percentage")
    market_sentiment: str = Field(..., description="Options-based sentiment (bullish/neutral/bearish)")

class AlternativeDataMetrics(BaseModel):
    """Alternative data sources aggregation."""
    news_sentiment: Optional[NewsSentimentData] = None
    social_media: Optional[SocialMediaData] = None
    google_trends: Optional[GoogleTrendsData] = None
    github_activity: Optional[GitHubActivityData] = None
    options_market: Optional[OptionsMarketData] = None

class SentimentMetrics(BaseModel):
    fear_greed_index: int
    social_volume: str
    sentiment_signal: str
    alternative_data: Optional[AlternativeDataMetrics] = None

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
