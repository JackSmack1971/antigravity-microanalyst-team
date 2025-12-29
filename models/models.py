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

# Risk Manager Agent Models
class RiskAssessment(BaseModel):
    """Risk assessment output from Risk Manager Agent."""
    position_size_btc: float = Field(..., description="Recommended position size in BTC")
    portfolio_risk_percentage: float = Field(..., ge=0, le=100, description="Percentage of portfolio at risk")
    stop_loss_price: float = Field(..., description="Recommended stop-loss price level")
    take_profit_targets: List[float] = Field(..., description="List of take-profit target prices")
    max_drawdown_estimate: float = Field(..., description="Estimated maximum drawdown percentage")
    tail_risk_score: int = Field(..., ge=0, le=100, description="Tail risk score (0=low, 100=extreme)")
    correlation_warning: Optional[str] = Field(None, description="Warning about correlation risks if applicable")
    timestamp_utc: datetime

# Scenario Planner Agent Models
class MarketScenario(BaseModel):
    """Individual market scenario projection."""
    name: str = Field(..., description="Scenario name (e.g., 'Bull Case', 'Bear Case', 'Base Case')")
    description: str = Field(..., description="Detailed scenario description")
    probability: float = Field(..., ge=0, le=1, description="Probability of scenario occurring")
    price_target: float = Field(..., description="Price target for this scenario")
    timeframe: str = Field(..., description="Expected timeframe (e.g., '1 week', '1 month')")
    key_drivers: List[str] = Field(..., description="Key drivers for this scenario")

class ScenarioAnalysis(BaseModel):
    """Scenario analysis output from Scenario Planner Agent."""
    scenarios: List[MarketScenario] = Field(..., description="List of market scenarios")
    most_likely_scenario: str = Field(..., description="Name of most likely scenario")
    probability_distribution: dict[str, float] = Field(..., description="Map of scenario name to probability")
    key_catalysts: List[str] = Field(..., description="Key catalysts to monitor")
    invalidation_levels: dict[str, float] = Field(..., description="Price levels that invalidate scenarios")
    timestamp_utc: datetime

# Anomaly Detection Agent Models
class Anomaly(BaseModel):
    """Individual anomaly detection."""
    type: str = Field(..., description="Type of anomaly (e.g., 'volume_spike', 'whale_transaction', 'unusual_price_movement')")
    severity: int = Field(..., ge=0, le=100, description="Severity score (0=minor, 100=critical)")
    description: str = Field(..., description="Detailed description of the anomaly")
    detected_at: datetime = Field(..., description="When the anomaly was detected")
    impact: str = Field(..., description="Potential market impact (bullish/bearish/neutral)")

class AnomalyReport(BaseModel):
    """Anomaly detection output from Anomaly Detection Agent."""
    anomalies_detected: List[Anomaly] = Field(..., description="List of detected anomalies")
    severity_scores: dict[str, int] = Field(..., description="Map of anomaly type to severity score")
    recommended_actions: List[str] = Field(..., description="Recommended actions based on anomalies")
    monitoring_alerts: List[str] = Field(..., description="Alerts for ongoing monitoring")
    timestamp_utc: datetime

# Validator Agent Models
class ValidationIssue(BaseModel):
    """Individual validation issue found."""
    severity: str = Field(..., description="Severity level (critical/warning/info)")
    component: str = Field(..., description="Component with the issue (e.g., 'Quant Agent', 'Logic Matrix')")
    issue_type: str = Field(..., description="Type of issue (e.g., 'data_mismatch', 'logical_inconsistency', 'unsupported_claim')")
    description: str = Field(..., description="Detailed description of the issue")
    recommendation: str = Field(..., description="Recommended fix or action")

class ValidationReport(BaseModel):
    """Validation output from Validator Agent."""
    validation_passed: bool = Field(..., description="Whether validation passed overall")
    issues_found: List[ValidationIssue] = Field(..., description="List of validation issues")
    consistency_score: int = Field(..., ge=0, le=100, description="Overall consistency score")
    data_quality_score: int = Field(..., ge=0, le=100, description="Data quality score")
    logic_quality_score: int = Field(..., ge=0, le=100, description="Logic quality score")
    summary: str = Field(..., description="Summary of validation findings")
    timestamp_utc: datetime

# Correlation & Market Regime Analyzer Models
class AssetCorrelation(BaseModel):
    """Correlation between two assets."""
    asset_pair: str = Field(..., description="Asset pair name (e.g., 'BTC-SPX', 'BTC-DXY')")
    correlation_coefficient: float = Field(..., ge=-1, le=1, description="Pearson correlation coefficient")
    rolling_30d: float = Field(..., ge=-1, le=1, description="30-day rolling correlation")
    rolling_90d: float = Field(..., ge=-1, le=1, description="90-day rolling correlation")
    trend: str = Field(..., description="Correlation trend (strengthening/weakening/stable)")
    interpretation: str = Field(..., description="What this correlation means for trading")

class MarketRegime(BaseModel):
    """Current market regime classification."""
    regime_type: str = Field(..., description="Regime type (risk_on/risk_off/transitional/decoupled)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in regime classification")
    duration_days: int = Field(..., description="Days since regime started")
    characteristics: List[str] = Field(..., description="Key characteristics of current regime")
    stability: str = Field(..., description="Regime stability (stable/volatile/shifting)")

class CorrelationBreakdown(BaseModel):
    """Detection of correlation breakdown events."""
    event_type: str = Field(..., description="Type of breakdown (flight_to_quality/decoupling/contagion)")
    severity: int = Field(..., ge=0, le=100, description="Severity of breakdown (0=minor, 100=severe)")
    affected_assets: List[str] = Field(..., description="Assets affected by the breakdown")
    description: str = Field(..., description="Description of the breakdown event")
    trading_implications: str = Field(..., description="What this means for trading strategy")

class ContagionRisk(BaseModel):
    """Cross-asset contagion risk assessment."""
    risk_level: str = Field(..., description="Risk level (low/moderate/high/extreme)")
    risk_score: int = Field(..., ge=0, le=100, description="Quantitative risk score")
    transmission_paths: List[str] = Field(..., description="Potential contagion transmission paths")
    vulnerable_assets: List[str] = Field(..., description="Assets most vulnerable to contagion")
    mitigation_strategies: List[str] = Field(..., description="Strategies to mitigate contagion risk")

class CorrelationMarketRegimeAnalysis(BaseModel):
    """Complete correlation and market regime analysis output."""
    correlations: List[AssetCorrelation] = Field(..., description="Asset correlation analysis")
    current_regime: MarketRegime = Field(..., description="Current market regime")
    correlation_breakdowns: List[CorrelationBreakdown] = Field(..., description="Detected correlation breakdowns")
    contagion_risk: ContagionRisk = Field(..., description="Cross-asset contagion risk assessment")
    key_insights: List[str] = Field(..., description="Key actionable insights from the analysis")
    regime_outlook: str = Field(..., description="Outlook for regime continuation or change")
    timestamp_utc: datetime
