"""Unit tests for dependency injection (deps/dependencies.py)."""
import pytest
import httpx
from deps.dependencies import CryptoDependencies


class TestCryptoDependencies:
    """Tests for CryptoDependencies dataclass."""

    def test_create_dependencies(self, mock_http_client):
        """Test creation of CryptoDependencies."""
        deps = CryptoDependencies(
            http_client=mock_http_client,
            user_context={"user_id": "123"},
            symbol="BTC-USD"
        )

        assert deps.http_client == mock_http_client
        assert deps.user_context == {"user_id": "123"}
        assert deps.symbol == "BTC-USD"

    def test_default_symbol(self, mock_http_client):
        """Test default symbol value."""
        deps = CryptoDependencies(
            http_client=mock_http_client,
            user_context={}
        )

        assert deps.symbol == "BTC-USD"

    def test_custom_symbol(self, mock_http_client):
        """Test custom symbol override."""
        deps = CryptoDependencies(
            http_client=mock_http_client,
            user_context={},
            symbol="ETH-USD"
        )

        assert deps.symbol == "ETH-USD"

    def test_user_context_flexibility(self, mock_http_client):
        """Test user_context can hold various data."""
        context = {
            "user_id": "123",
            "session_id": "abc",
            "preferences": {"risk_level": "aggressive"}
        }

        deps = CryptoDependencies(
            http_client=mock_http_client,
            user_context=context
        )

        assert deps.user_context["user_id"] == "123"
        assert deps.user_context["preferences"]["risk_level"] == "aggressive"
