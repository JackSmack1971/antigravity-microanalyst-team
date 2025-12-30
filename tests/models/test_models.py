"""Unit tests for data models (models/models.py)."""
import pytest
from datetime import datetime
from pydantic import ValidationError
from models.models import (
    PriceMetrics, RiskProfile, PriceStructure,
    MicrostructureMetrics, TechnicalData,
    MacroMetrics, OnChainMetrics, SentimentMetrics,
    NewsSentimentData, SocialMediaData, GoogleTrendsData,
    GitHubActivityData, OptionsMarketData, AlternativeDataMetrics,
    FundamentalData, MasterState, ReportMetadata,
    DirectiveContent, FinalDirective,
    RiskAssessment, MarketScenario, ScenarioAnalysis,
    Anomaly, AnomalyReport, ValidationIssue, ValidationReport,
    AssetCorrelation, MarketRegime, CorrelationBreakdown,
    ContagionRisk, CorrelationMarketRegimeAnalysis,
    BlackSwanEvent, EmergencyResponse, MarketStabilityMetrics,
    BlackSwanEventReport
)


class TestPriceMetrics:
    """Tests for PriceMetrics model."""

    def test_valid_price_metrics(self):
        """Test creation of valid PriceMetrics."""
        metrics = PriceMetrics(
            current_price=45000.0,
            rsi_4h=55.0,
            vwap_deviation=0.02,
            regime="bullish"
        )
        assert metrics.current_price == 45000.0
        assert metrics.rsi_4h == 55.0
        assert metrics.vwap_deviation == 0.02
        assert metrics.regime == "bullish"

    def test_price_metrics_types(self):
        """Test type validation in PriceMetrics."""
        with pytest.raises(ValidationError):
            PriceMetrics(
                current_price="invalid",  # Should be float
                rsi_4h=55.0,
                vwap_deviation=0.02,
                regime="bullish"
            )


class TestRiskProfile:
    """Tests for RiskProfile model."""

    def test_valid_risk_profile(self):
        """Test creation of valid RiskProfile."""
        profile = RiskProfile(
            invalidation_hard_stop=40000.0,
            support_zone=[42000.0, 43000.0],
            resistance_zone=[48000.0, 50000.0]
        )
        assert profile.invalidation_hard_stop == 40000.0
        assert len(profile.support_zone) == 2
        assert len(profile.resistance_zone) == 2


class TestTechnicalData:
    """Tests for TechnicalData model."""

    def test_valid_technical_data(self, sample_timestamp):
        """Test creation of valid TechnicalData."""
        price_metrics = PriceMetrics(
            current_price=45000.0,
            rsi_4h=55.0,
            vwap_deviation=0.02,
            regime="bullish"
        )
        risk_profile = RiskProfile(
            invalidation_hard_stop=40000.0,
            support_zone=[42000.0],
            resistance_zone=[48000.0]
        )
        price_structure = PriceStructure(
            asset="BTC-USD",
            metrics=price_metrics,
            risk_profile=risk_profile
        )
        microstructure = MicrostructureMetrics(
            funding_rate_bias="neutral",
            open_interest_trend="rising",
            squeeze_risk="low"
        )

        technical_data = TechnicalData(
            module_1_price_structure=price_structure,
            module_5_market_microstructure=microstructure,
            timestamp_utc=sample_timestamp
        )

        assert technical_data.module_1_price_structure.asset == "BTC-USD"
        assert technical_data.timestamp_utc == sample_timestamp


class TestAlternativeDataMetrics:
    """Tests for Alternative Data models."""

    def test_news_sentiment_data(self):
        """Test NewsSentimentData model."""
        news = NewsSentimentData(
            sentiment_score=75.5,
            positive_pct=80.0,
            negative_pct=20.0,
            total_posts=100
        )
        assert news.sentiment_score == 75.5
        assert news.total_posts == 100

    def test_social_media_data(self):
        """Test SocialMediaData model."""
        social = SocialMediaData(
            reddit_sentiment=65.0,
            engagement_score=80.0,
            total_posts=50
        )
        assert social.reddit_sentiment == 65.0
        assert social.total_posts == 50

    def test_google_trends_data(self):
        """Test GoogleTrendsData model."""
        trends = GoogleTrendsData(
            current_interest=85,
            momentum_pct=15.5,
            direction="up"
        )
        assert trends.current_interest == 85
        assert trends.direction == "up"

    def test_github_activity_data(self):
        """Test GitHubActivityData model."""
        github = GitHubActivityData(
            activity_score=75.0,
            trend="growing",
            recent_commits=120
        )
        assert github.activity_score == 75.0
        assert github.trend == "growing"

    def test_options_market_data(self):
        """Test OptionsMarketData model."""
        options = OptionsMarketData(
            put_call_ratio=0.75,
            avg_implied_volatility=65.0,
            market_sentiment="bullish"
        )
        assert options.put_call_ratio == 0.75
        assert options.market_sentiment == "bullish"

    def test_alternative_data_metrics_complete(self):
        """Test complete AlternativeDataMetrics with all sources."""
        alt_data = AlternativeDataMetrics(
            news_sentiment=NewsSentimentData(
                sentiment_score=75.5,
                positive_pct=80.0,
                negative_pct=20.0,
                total_posts=100
            ),
            social_media=SocialMediaData(
                reddit_sentiment=65.0,
                engagement_score=80.0,
                total_posts=50
            ),
            google_trends=GoogleTrendsData(
                current_interest=85,
                momentum_pct=15.5,
                direction="up"
            ),
            github_activity=GitHubActivityData(
                activity_score=75.0,
                trend="growing",
                recent_commits=120
            ),
            options_market=OptionsMarketData(
                put_call_ratio=0.75,
                avg_implied_volatility=65.0,
                market_sentiment="bullish"
            )
        )
        assert alt_data.news_sentiment is not None
        assert alt_data.social_media is not None
        assert alt_data.github_activity.recent_commits == 120


class TestFundamentalData:
    """Tests for FundamentalData model."""

    def test_valid_fundamental_data(self, sample_timestamp):
        """Test creation of valid FundamentalData."""
        macro = MacroMetrics(
            spx_level=4500.0,
            dxy_index=102.5,
            macro_regime="risk_on"
        )
        onchain = OnChainMetrics(
            exchange_net_flow="outflow",
            active_addresses_trend="rising",
            whale_accumulation="yes"
        )
        sentiment = SentimentMetrics(
            fear_greed_index=65,
            social_volume="rising",
            sentiment_signal="bullish"
        )

        fundamental = FundamentalData(
            module_2_macro=macro,
            module_3_onchain=onchain,
            module_4_sentiment=sentiment,
            timestamp_utc=sample_timestamp
        )

        assert fundamental.module_2_macro.spx_level == 4500.0
        assert fundamental.module_3_onchain.exchange_net_flow == "outflow"
        assert fundamental.module_4_sentiment.fear_greed_index == 65


class TestMasterState:
    """Tests for MasterState model."""

    def test_valid_master_state(self, sample_timestamp):
        """Test creation of valid MasterState."""
        # Create technical data
        price_metrics = PriceMetrics(
            current_price=45000.0,
            rsi_4h=55.0,
            vwap_deviation=0.02,
            regime="bullish"
        )
        risk_profile = RiskProfile(
            invalidation_hard_stop=40000.0,
            support_zone=[42000.0],
            resistance_zone=[48000.0]
        )
        price_structure = PriceStructure(
            asset="BTC-USD",
            metrics=price_metrics,
            risk_profile=risk_profile
        )
        microstructure = MicrostructureMetrics(
            funding_rate_bias="neutral",
            open_interest_trend="rising",
            squeeze_risk="low"
        )
        technical = TechnicalData(
            module_1_price_structure=price_structure,
            module_5_market_microstructure=microstructure,
            timestamp_utc=sample_timestamp
        )

        # Create fundamental data
        macro = MacroMetrics(
            spx_level=4500.0,
            dxy_index=102.5,
            macro_regime="risk_on"
        )
        onchain = OnChainMetrics(
            exchange_net_flow="outflow",
            active_addresses_trend="rising",
            whale_accumulation="yes"
        )
        sentiment = SentimentMetrics(
            fear_greed_index=65,
            social_volume="rising",
            sentiment_signal="bullish"
        )
        fundamental = FundamentalData(
            module_2_macro=macro,
            module_3_onchain=onchain,
            module_4_sentiment=sentiment,
            timestamp_utc=sample_timestamp
        )

        # Create master state
        master_state = MasterState(
            technical=technical,
            fundamental=fundamental,
            status="complete",
            aggregation_timestamp=sample_timestamp
        )

        assert master_state.status == "complete"
        assert master_state.technical.module_1_price_structure.asset == "BTC-USD"
        assert master_state.fundamental.module_2_macro.spx_level == 4500.0


class TestFinalDirective:
    """Tests for FinalDirective model."""

    def test_valid_final_directive(self):
        """Test creation of valid FinalDirective."""
        metadata = ReportMetadata(
            date="2025-12-30",
            overall_confidence="High"
        )
        directive = DirectiveContent(
            stance="Aggressive_Long",
            leverage_cap="3x",
            conviction_score=85
        )

        final = FinalDirective(
            report_metadata=metadata,
            final_directive=directive,
            thesis_summary="Strong bullish momentum with risk-on macro"
        )

        assert final.report_metadata.date == "2025-12-30"
        assert final.final_directive.stance == "Aggressive_Long"
        assert final.final_directive.conviction_score == 85

    def test_conviction_score_validation(self):
        """Test conviction_score range validation."""
        metadata = ReportMetadata(
            date="2025-12-30",
            overall_confidence="High"
        )

        # Valid score
        directive = DirectiveContent(
            stance="Aggressive_Long",
            leverage_cap="3x",
            conviction_score=50
        )
        assert directive.conviction_score == 50

        # Invalid score (>100)
        with pytest.raises(ValidationError):
            DirectiveContent(
                stance="Aggressive_Long",
                leverage_cap="3x",
                conviction_score=150
            )


class TestRiskAssessment:
    """Tests for RiskAssessment model."""

    def test_valid_risk_assessment(self, sample_timestamp):
        """Test creation of valid RiskAssessment."""
        risk = RiskAssessment(
            position_size_btc=0.5,
            portfolio_risk_percentage=5.0,
            stop_loss_price=42000.0,
            take_profit_targets=[48000.0, 50000.0, 52000.0],
            max_drawdown_estimate=15.0,
            tail_risk_score=25,
            correlation_warning="Low correlation risk",
            timestamp_utc=sample_timestamp
        )

        assert risk.position_size_btc == 0.5
        assert len(risk.take_profit_targets) == 3
        assert risk.tail_risk_score == 25


class TestScenarioAnalysis:
    """Tests for ScenarioAnalysis model."""

    def test_valid_scenario_analysis(self, sample_timestamp):
        """Test creation of valid ScenarioAnalysis."""
        scenarios = [
            MarketScenario(
                name="Bull Case",
                description="Strong momentum continues",
                probability=0.6,
                price_target=55000.0,
                timeframe="1 week",
                key_drivers=["Institutional buying", "Macro risk-on"]
            ),
            MarketScenario(
                name="Bear Case",
                description="Correction occurs",
                probability=0.3,
                price_target=40000.0,
                timeframe="1 week",
                key_drivers=["Profit taking", "Macro uncertainty"]
            )
        ]

        analysis = ScenarioAnalysis(
            scenarios=scenarios,
            most_likely_scenario="Bull Case",
            probability_distribution={"Bull Case": 0.6, "Bear Case": 0.3, "Base Case": 0.1},
            key_catalysts=["Fed meeting", "ETF flows"],
            invalidation_levels={"Bull Case": 42000.0, "Bear Case": 50000.0},
            timestamp_utc=sample_timestamp
        )

        assert len(analysis.scenarios) == 2
        assert analysis.most_likely_scenario == "Bull Case"
        assert analysis.probability_distribution["Bull Case"] == 0.6


class TestAnomalyReport:
    """Tests for AnomalyReport model."""

    def test_valid_anomaly_report(self, sample_timestamp):
        """Test creation of valid AnomalyReport."""
        anomalies = [
            Anomaly(
                type="volume_spike",
                severity=75,
                description="Unusual volume spike detected",
                detected_at=sample_timestamp,
                impact="bullish"
            )
        ]

        report = AnomalyReport(
            anomalies_detected=anomalies,
            severity_scores={"volume_spike": 75},
            recommended_actions=["Monitor for continuation"],
            monitoring_alerts=["Watch for reversal"],
            timestamp_utc=sample_timestamp
        )

        assert len(report.anomalies_detected) == 1
        assert report.severity_scores["volume_spike"] == 75


class TestValidationReport:
    """Tests for ValidationReport model."""

    def test_valid_validation_report(self, sample_timestamp):
        """Test creation of valid ValidationReport."""
        issues = [
            ValidationIssue(
                severity="warning",
                component="Quant Agent",
                issue_type="data_mismatch",
                description="Minor data inconsistency",
                recommendation="Verify data source"
            )
        ]

        report = ValidationReport(
            validation_passed=True,
            issues_found=issues,
            consistency_score=85,
            data_quality_score=90,
            logic_quality_score=88,
            summary="Overall validation passed with minor warnings",
            timestamp_utc=sample_timestamp
        )

        assert report.validation_passed is True
        assert report.consistency_score == 85
        assert len(report.issues_found) == 1


class TestCorrelationMarketRegimeAnalysis:
    """Tests for Correlation and Market Regime models."""

    def test_asset_correlation(self):
        """Test AssetCorrelation model."""
        corr = AssetCorrelation(
            asset_pair="BTC-SPX",
            correlation_coefficient=0.75,
            rolling_30d=0.72,
            rolling_90d=0.68,
            trend="strengthening",
            interpretation="Strong positive correlation with equities"
        )
        assert corr.correlation_coefficient == 0.75
        assert corr.trend == "strengthening"

    def test_market_regime(self):
        """Test MarketRegime model."""
        regime = MarketRegime(
            regime_type="risk_on",
            confidence=0.85,
            duration_days=15,
            characteristics=["Rising correlations", "High volatility"],
            stability="stable"
        )
        assert regime.regime_type == "risk_on"
        assert regime.confidence == 0.85

    def test_correlation_market_regime_analysis(self, sample_timestamp):
        """Test complete CorrelationMarketRegimeAnalysis."""
        correlations = [
            AssetCorrelation(
                asset_pair="BTC-SPX",
                correlation_coefficient=0.75,
                rolling_30d=0.72,
                rolling_90d=0.68,
                trend="strengthening",
                interpretation="Strong positive correlation"
            )
        ]

        current_regime = MarketRegime(
            regime_type="risk_on",
            confidence=0.85,
            duration_days=15,
            characteristics=["Rising correlations"],
            stability="stable"
        )

        contagion = ContagionRisk(
            risk_level="moderate",
            risk_score=45,
            transmission_paths=["Equity markets"],
            vulnerable_assets=["BTC", "ETH"],
            mitigation_strategies=["Diversification"]
        )

        analysis = CorrelationMarketRegimeAnalysis(
            correlations=correlations,
            current_regime=current_regime,
            correlation_breakdowns=[],
            contagion_risk=contagion,
            key_insights=["Monitor correlations"],
            regime_outlook="Likely to continue",
            timestamp_utc=sample_timestamp
        )

        assert len(analysis.correlations) == 1
        assert analysis.current_regime.regime_type == "risk_on"
        assert analysis.contagion_risk.risk_level == "moderate"


class TestBlackSwanEventReport:
    """Tests for Black Swan Event models."""

    def test_black_swan_event(self, sample_timestamp):
        """Test BlackSwanEvent model."""
        event = BlackSwanEvent(
            event_type="extreme_price_move",
            severity=85,
            description="Price dropped 15% in 1 hour",
            detected_at=sample_timestamp,
            trigger_metrics={"price_change_pct": -15.0, "volume_ratio": 8.5},
            impact_assessment="Severe negative impact",
            confidence=0.95
        )
        assert event.severity == 85
        assert event.confidence == 0.95

    def test_emergency_response(self):
        """Test EmergencyResponse model."""
        response = EmergencyResponse(
            alert_level="critical",
            recommended_stance="Exit",
            position_reduction_pct=75.0,
            stop_loss_tightening=True,
            leverage_reduction="close leveraged positions",
            immediate_actions=["Reduce exposure", "Raise cash"],
            monitoring_priorities=["Price stability", "Volume"]
        )
        assert response.alert_level == "critical"
        assert response.position_reduction_pct == 75.0

    def test_market_stability_metrics(self):
        """Test MarketStabilityMetrics model."""
        stability = MarketStabilityMetrics(
            current_volatility=85.0,
            volatility_percentile=95.0,
            price_stability_score=25,
            volume_stability_score=30,
            liquidity_health="stressed",
            market_stress_index=85
        )
        assert stability.current_volatility == 85.0
        assert stability.liquidity_health == "stressed"

    def test_black_swan_event_report(self, sample_timestamp):
        """Test complete BlackSwanEventReport."""
        events = [
            BlackSwanEvent(
                event_type="extreme_price_move",
                severity=85,
                description="Major price drop",
                detected_at=sample_timestamp,
                trigger_metrics={"price_change_pct": -15.0},
                impact_assessment="Severe",
                confidence=0.95
            )
        ]

        response = EmergencyResponse(
            alert_level="critical",
            recommended_stance="Exit",
            position_reduction_pct=75.0,
            stop_loss_tightening=True,
            leverage_reduction="close leveraged positions",
            immediate_actions=["Reduce exposure"],
            monitoring_priorities=["Price stability"]
        )

        stability = MarketStabilityMetrics(
            current_volatility=85.0,
            volatility_percentile=95.0,
            price_stability_score=25,
            volume_stability_score=30,
            liquidity_health="stressed",
            market_stress_index=85
        )

        report = BlackSwanEventReport(
            black_swan_detected=True,
            events=events,
            overall_risk_level="extreme",
            severity_score=85,
            emergency_response=response,
            stability_metrics=stability,
            uncertainty_flags=["High volatility"],
            summary="Critical black swan event detected",
            timestamp_utc=sample_timestamp
        )

        assert report.black_swan_detected is True
        assert report.severity_score == 85
        assert len(report.events) == 1
