"""
Base HTTP client for external API integrations.

This module provides a base class for HTTP clients that:
1. Manage a long-lived httpx.AsyncClient connection for efficiency
2. Handle lifecycle with async context manager (__aenter__/__aexit__)
3. Automatically close connections when done
4. Support dependency injection in FastAPI

Pattern:
- Client creates httpx.AsyncClient on __aenter__
- Reuses the same client for all requests (connection pooling)
- Closes client on __aexit__
- Must be used with `async with` or via FastAPI dependency injection
"""

from __future__ import annotations

from typing import Optional

import httpx


class BaseHTTPClient:
    """
    Base class for HTTP API clients with lifecycle management.

    This client implements the async context manager protocol to ensure
    proper setup and teardown of HTTP connections.

    Usage:
        async with MyClient(base_url="https://api.example.com") as client:
            result = await client.some_method()
        # Connection automatically closed

    Attributes:
        base_url: The base URL for the API
        timeout: Request timeout in seconds
        headers: Default headers for all requests
    """

    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        """
        Initialize the HTTP client.

        Args:
            base_url: Base URL for the API endpoint
            timeout: Request timeout in seconds (default: 30.0)
            headers: Optional default headers for requests
            http_client: Optional pre-configured httpx client (for testing/advanced use)
        """
        self._base_url = base_url
        self._timeout = timeout
        self._headers = headers or {}
        self._client = http_client
        self._owns_client = http_client is None

    async def __aenter__(self) -> "BaseHTTPClient":
        """
        Enter async context manager - create httpx client if needed.

        Returns:
            Self, ready for use
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                headers=self._headers,
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Exit async context manager - close httpx client if we own it.

        Only closes the client if it was created by this instance
        (not injected via http_client parameter).
        """
        if self._owns_client and self._client is not None:
            await self._client.aclose()

    @property
    def _http_client(self) -> httpx.AsyncClient:
        """
        Get the underlying httpx client.

        Raises:
            RuntimeError: If accessed before entering async context

        Returns:
            The httpx.AsyncClient instance
        """
        if self._client is None:
            raise RuntimeError(
                f"{self.__class__.__name__} must be used within an async context manager. "
                "Use `async with client:` or ensure it's used via FastAPI Depends()."
            )
        return self._client
