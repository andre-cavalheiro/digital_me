"""
Community Archive integration client.

This client wraps access to the Community Archive API. The underlying API is
not yet implemented; calling the search method will raise NotImplementedError.
"""

from fury_api.lib.settings import config


class CommunityArchiveClient:
    """
    Client for interacting with the Community Archive.

    For now this is a stub that carries configuration and exposes the intended
    interface surface.
    """

    def __init__(self, bearer_token: str | None = None) -> None:
        """
        Initialize the Community Archive client.

        Args:
            bearer_token: Bearer token for authentication. If not provided, uses settings.
        """
        token_from_settings = (
            config.community_archive.BEARER_TOKEN.get_secret_value()
            if config.community_archive.BEARER_TOKEN is not None
            else None
        )
        self._bearer_token = bearer_token or token_from_settings
        if not self._bearer_token:
            raise ValueError("Community Archive bearer token is not configured")

    def search(self, query: str) -> None:
        """
        Search Community Archive content by query.

        Raises:
            NotImplementedError: Always, until the API integration is built.
        """
        raise NotImplementedError("Not Implemented")


def get_community_archive_client(bearer_token: str | None = None) -> CommunityArchiveClient:
    """
    Create a configured Community Archive client.

    Args:
        bearer_token: Optional bearer token override.

    Returns:
        CommunityArchiveClient ready for future use.
    """
    return CommunityArchiveClient(bearer_token=bearer_token)
