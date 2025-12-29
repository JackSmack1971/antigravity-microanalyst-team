from dataclasses import dataclass
from typing import Any, Optional
import httpx

@dataclass
class CryptoDependencies:
    """Dependency injection container for Crypto Agents.

    This container holds shared resources like HTTP clients and contextual
    information required across the multi-agent pipeline.

    Attributes:
        http_client: Asynchronous HTTP client for API requests.
        user_context: Generic dictionary for request-specific metadata.
        symbol: The cryptocurrency symbol being analyzed. Defaults to "BTC-USD".
    """
    http_client: httpx.AsyncClient
    user_context: dict[str, Any]
    symbol: str = "BTC-USD"
