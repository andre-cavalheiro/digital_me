"""
X API integration client using the official X SDK (xdk).

This client wraps the xdk Client to provide a simple, typed interface for
running X search queries. The underlying SDK handles HTTP connections, so no
async lifecycle management is required.
"""

from typing import Any

from xdk import Client

from fury_api.lib.settings import config


class XClient:
    """
    Client for interacting with the X API via the xdk SDK.

    Usage:
        x_client = XClient()
        response = x_client.search_all(query=\"from:someone has:links\", max_results=100)
        posts = response.data
    """

    def __init__(self, bearer_token: str | None = None, client: Client | None = None) -> None:
        """
        Initialize the X client.

        Args:
            bearer_token: X API bearer token. Falls back to config.x.BEARER_TOKEN if not provided.
            client: Optional pre-configured xdk Client (useful for testing).
        """
        token_from_settings = (
            config.x.BEARER_TOKEN.get_secret_value() if config.x.BEARER_TOKEN is not None else None
        )
        token = bearer_token or token_from_settings
        if not token:
            raise ValueError("X bearer token is not configured")
        self._client = client or Client(bearer_token=token)

    def search_all(
        self,
        *,
        query: str,
        start_time: str | None = None,
        end_time: str | None = None,
        since_id: str | None = None,
        until_id: str | None = None,
        max_results: int | None = None,
        next_token: str | None = None,
        pagination_token: str | None = None,
        sort_order: str | None = None,
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        user_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
    ) -> Any:
        """
        Run a full-archive search against X using the xdk `search_all` endpoint.

        Args:
            query: Query string to match posts.
            start_time: Oldest UTC timestamp (inclusive), format YYYY-MM-DDTHH:mm:ssZ.
            end_time: Newest UTC timestamp (exclusive), format YYYY-MM-DDTHH:mm:ssZ.
            since_id: Return posts with IDs greater than this value.
            until_id: Return posts with IDs less than this value.
            max_results: Maximum number of results to return.
            next_token: Pagination token for fetching the next page of results.
            pagination_token: Alternative pagination token for fetching the next page of results.
            sort_order: Order in which to return results.
            tweet_fields: Tweet fields to include in the response.
            expansions: Fields to expand in the response.
            media_fields: Media fields to include in the response.
            poll_fields: Poll fields to include in the response.
            user_fields: User fields to include in the response.
            place_fields: Place fields to include in the response.

        Returns:
            The raw SearchAllResponse object from xdk.
        """
        return self._client.posts.search_all(
            query=query,
            start_time=start_time,
            end_time=end_time,
            since_id=since_id,
            until_id=until_id,
            max_results=max_results,
            next_token=next_token,
            pagination_token=pagination_token,
            sort_order=sort_order,
            tweet_fields=tweet_fields,
            expansions=expansions,
            media_fields=media_fields,
            poll_fields=poll_fields,
            user_fields=user_fields,
            place_fields=place_fields,
        )


def get_x_client(bearer_token: str | None = None, client: Client | None = None) -> XClient:
    """
    Create a configured X client.

    Args:
        bearer_token: Optional explicit bearer token.
        client: Optional pre-configured xdk Client.

    Returns:
        XClient ready to perform X API operations.
    """
    return XClient(bearer_token=bearer_token, client=client)
