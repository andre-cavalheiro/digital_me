"""
XUser API integration client.

HTTP-based client that follows the BaseHTTPClient lifecycle pattern. This client
authenticates on behalf of a user via OAuth tokens supplied per instance, rather
than using application-level credentials from settings.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional
from datetime import datetime, timedelta

import httpx

from fury_api.lib.settings import config
from fury_api.lib.integrations.base import BaseHTTPClient
from fury_api.lib.integrations.x_app.client import XAppClient
from fury_api.lib.integrations.x_app.models import SearchAllResult

__all__ = ["XUserClient", "get_x_user_client"]


class XUserClient(BaseHTTPClient):
    """Client for interacting with the X User API over HTTP."""

    DEFAULT_API_URL = "https://api.x.com/2"
    DEFAULT_TOKEN_URL = "https://api.x.com/2/oauth2/token"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_type: str | None = None,
        token_obtained_at: str | None = None,
        expires_in: int | None = None,
        token_url: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        on_tokens_refreshed: Callable[[str, str], Awaitable[None]] | None = None,
        timeout: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize X User API client.

        Args:
            base_url: Base URL for the X User API (defaults to config or docs default).
            access_token: OAuth access token for authentication.
            refresh_token: OAuth refresh token (used when access_token expires).
            token_type: Token type (defaults to "bearer").
            token_obtained_at: ISO timestamp when tokens were obtained.
            expires_in: Token expiry in seconds (typically 7200 for X).
            token_url: OAuth token endpoint (defaults to docs URL if not provided).
            client_id: OAuth client ID (required for refresh token exchange).
            client_secret: OAuth client secret (required for confidential clients).
            on_tokens_refreshed: Async callback called with (new_access_token, new_refresh_token) when tokens are refreshed.
            timeout: Request timeout in seconds.
            http_client: Optional pre-configured httpx client (for testing).
        """
        resolved_base_url = base_url or config.x_user.API_URL or self.DEFAULT_API_URL
        self._token_url = token_url or config.x_user.OAUTH_TOKEN_URL or self.DEFAULT_TOKEN_URL
        self._token_type = (token_type or "bearer").lower()
        self._access_token = access_token
        self._refresh_token = refresh_token
        self._token_obtained_at = datetime.fromisoformat(token_obtained_at) if token_obtained_at else None
        self._expires_in = expires_in or 7200  # X tokens typically expire in 2 hours
        self._client_id = client_id or config.x_user.OAUTH_CLIENT_ID
        self._client_secret = client_secret or (
            config.x_user.OAUTH_CLIENT_SECRET.get_secret_value() if config.x_user.OAUTH_CLIENT_SECRET else None
        )
        self._on_tokens_refreshed = on_tokens_refreshed
        self._timeout = timeout

        # Validate we have at least one way to authenticate
        if not self._access_token and not self._refresh_token:
            raise ValueError("Either access_token or refresh_token must be provided")

        headers = self._build_auth_headers()
        super().__init__(
            base_url=resolved_base_url,
            timeout=timeout,
            headers=headers,
            http_client=http_client,
        )

    def _is_access_token_expired(self) -> bool:
        """Check if the access token has expired or will expire soon (within 5 minutes)."""
        if not self._token_obtained_at:
            # If we don't know when it was obtained, assume it might be expired
            return True

        expiry_time = self._token_obtained_at + timedelta(seconds=self._expires_in)
        # Refresh if expired or expiring within 5 minutes
        buffer = timedelta(minutes=5)
        return datetime.now() >= (expiry_time - buffer)

    async def _ensure_valid_access_token(self) -> None:
        """Ensure we have a valid access token, refreshing if necessary."""
        # If no access token or it's expired, refresh
        if not self._access_token or self._is_access_token_expired():
            if not self._refresh_token:
                raise ValueError("Access token expired and no refresh token available")

            await self._refresh_access_token()

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token and update internal state."""
        if not self._refresh_token:
            raise ValueError("No refresh token available for refresh")

        print("DEBUG: Refreshing access token (current token expired or missing)")

        new_access_token, new_refresh_token = await self._exchange_refresh_token_async(self._refresh_token)

        # Update internal state
        self._access_token = new_access_token
        self._refresh_token = new_refresh_token
        self._token_obtained_at = datetime.now()

        # Update auth headers
        self._http_client.headers.update(self._build_auth_headers())

        # Notify callback if provided
        if self._on_tokens_refreshed:
            await self._on_tokens_refreshed(new_access_token, new_refresh_token)
            print("DEBUG: Token refresh callback completed")

    async def _exchange_refresh_token_async(self, refresh_token: str) -> tuple[str, str]:
        """
        Exchange a refresh token for an access token using the OAuth token endpoint.

        X rotates refresh tokens - each refresh returns a NEW refresh token and invalidates the old one.

        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        if not refresh_token:
            raise ValueError("refresh_token is required")

        if not self._client_id:
            raise ValueError("client_id is required for refresh token exchange")

        # Strip whitespace from token
        refresh_token = refresh_token.strip()

        print("DEBUG: Attempting token refresh")
        print(f"DEBUG: Token URL: {self._token_url}")
        print(f"DEBUG: Client ID: {self._client_id[:20]}...")

        # Per X OAuth 2.0 docs: refresh requests need grant_type and refresh_token
        # For confidential clients: use Basic Auth (client credentials in header, not body)
        # For public clients: include client_id in body

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        if self._client_secret:
            # Confidential client: Use Basic Auth, don't include client_id in body
            import base64

            basic_auth = base64.b64encode(f"{self._client_id}:{self._client_secret}".encode()).decode()
            headers["Authorization"] = f"Basic {basic_auth}"
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
            print("DEBUG: Using Basic Auth (confidential client)")
        else:
            # Public client: Include client_id in body
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._client_id,
            }
            print("DEBUG: Using client_id in body (public client)")

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._token_url, data=data, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            error_detail = ""
            try:
                error_body = exc.response.json()
                error_detail = f" - {error_body}"
            except Exception:
                error_detail = f" - {exc.response.text}"
            raise ValueError(f"Failed to refresh X User access token: {exc}{error_detail}") from exc
        except httpx.HTTPError as exc:
            raise ValueError(f"Failed to refresh X User access token: {exc}") from exc

        new_access_token = payload.get("access_token")
        new_refresh_token = payload.get("refresh_token")

        if not new_access_token or not new_refresh_token:
            raise ValueError(f"Token refresh response missing tokens: {payload}")

        if payload.get("token_type"):
            self._token_type = str(payload["token_type"]).lower()

        if payload.get("expires_in"):
            self._expires_in = int(payload["expires_in"])

        print("DEBUG: Token refresh successful")
        return new_access_token, new_refresh_token

    def _build_auth_headers(self) -> dict[str, str]:
        """Construct authorization headers using the resolved OAuth token."""
        scheme = self._token_type if self._token_type in {"bearer", "token"} else "bearer"
        return {
            "Authorization": f"{scheme.capitalize()} {self._access_token}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self, method: str, endpoint: str, params: dict[str, Any] | None = None, json: Any = None
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the X User API.
        Automatically refreshes access token if expired.
        """
        # Ensure we have a valid access token before making the request
        await self._ensure_valid_access_token()

        url = f"{self._base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        response = await self._http_client.request(method, url, params=params, json=json, follow_redirects=True)
        response.raise_for_status()
        if response.status_code == 204:
            return {}
        return response.json()

    async def get_bookmarks(
        self,
        *,
        user_id: str,
        pagination_token: str | None = None,
        max_results: int | None = None,
        expansions: list[str] | None = None,
        tweet_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
        hydrate: bool = True,
    ) -> SearchAllResult:
        """
        Fetch bookmarks for a user.

        Uses the same default tweet/user/media fields as the X App search
        integration to keep display data consistent.
        """

        # X API expects comma-separated strings, not lists
        def to_comma_separated(value: list[str] | None) -> str | None:
            return ",".join(value) if value else None

        params: dict[str, Any] = {
            "pagination_token": pagination_token,
            "max_results": max_results,
            "expansions": to_comma_separated(expansions or XAppClient.DEFAULT_EXPANSIONS),
            "tweet.fields": to_comma_separated(tweet_fields or XAppClient.DEFAULT_TWEET_FIELDS),
            "user.fields": to_comma_separated(user_fields or XAppClient.DEFAULT_USER_FIELDS),
            "media.fields": to_comma_separated(media_fields or XAppClient.DEFAULT_MEDIA_FIELDS),
            "poll.fields": to_comma_separated(poll_fields) if poll_fields else None,
            "place.fields": to_comma_separated(place_fields) if place_fields else None,
        }
        filtered_params = {k: v for k, v in params.items() if v is not None}

        response = await self._make_request(
            "GET",
            f"users/{user_id}/bookmarks",
            params=filtered_params,
        )

        result = SearchAllResult.model_validate(response)
        if hydrate:
            result.hydrate()
        return result


def get_x_user_client(
    *,
    base_url: str | None = None,
    access_token: str | None = None,
    refresh_token: str | None = None,
    token_type: str | None = None,
    token_obtained_at: str | None = None,
    expires_in: int | None = None,
    token_url: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    on_tokens_refreshed: Callable[[str, str], Awaitable[None]] | None = None,
    timeout: float = 30.0,
    http_client: Optional[httpx.AsyncClient] = None,
) -> XUserClient:
    """
    Create a configured XUserClient instance.

    Auth credentials must be provided per instance (access or refresh token).
    If using refresh_token, client_id and client_secret are also required.
    """
    if not access_token and not refresh_token:
        raise ValueError("Provide either an access_token or a refresh_token to create XUserClient")

    return XUserClient(
        base_url=base_url,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=token_type,
        token_obtained_at=token_obtained_at,
        expires_in=expires_in,
        token_url=token_url,
        client_id=client_id,
        client_secret=client_secret,
        on_tokens_refreshed=on_tokens_refreshed,
        timeout=timeout,
        http_client=http_client,
    )
