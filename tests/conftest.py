"""Shared pytest fixtures for test suite."""
import pytest
import httpx
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock
from deps.dependencies import CryptoDependencies

@pytest.fixture
def mock_http_client():
    """Provides a mocked async HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client

@pytest.fixture
def crypto_dependencies(mock_http_client):
    """Provides a CryptoDependencies instance with mocked HTTP client."""
    return CryptoDependencies(
        http_client=mock_http_client,
        user_context={"test": "data"},
        symbol="BTC-USD"
    )

@pytest.fixture
def sample_timestamp():
    """Provides a consistent timestamp for testing."""
    return datetime(2025, 12, 30, 12, 0, 0)

@pytest.fixture
def mock_openrouter_model():
    """Provides a mocked OpenRouter model for agent testing."""
    model = MagicMock()
    model.run = AsyncMock(return_value="Mocked response")
    return model

@pytest.fixture
def sample_price_data():
    """Provides sample price data for testing."""
    return {
        "current_price": 45000.0,
        "rsi_4h": 55.0,
        "vwap_deviation": 0.02,
        "regime": "bullish"
    }

@pytest.fixture
def sample_fundamental_data():
    """Provides sample fundamental data for testing."""
    return {
        "spx_level": 4500.0,
        "dxy_index": 102.5,
        "macro_regime": "risk_on",
        "exchange_net_flow": "outflow",
        "active_addresses_trend": "rising",
        "whale_accumulation": "yes",
        "fear_greed_index": 65,
        "social_volume": "rising",
        "sentiment_signal": "bullish"
    }

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Auto-mocks environment variables for all tests."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key_12345")
    monkeypatch.setenv("REDDIT_CLIENT_ID", "test_reddit_id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "test_reddit_secret")
    monkeypatch.setenv("REDDIT_USER_AGENT", "test_agent")
