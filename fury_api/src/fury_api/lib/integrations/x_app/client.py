"""
Client for interacting with the X API via the xdk SDK.
"""

from xdk import Client

from fury_api.lib.settings import config
from fury_api.lib.integrations.x_app.models import SearchAllResult

__all__ = ["XAppClient", "get_x_app_client"]


class XAppClient:
    """
    Client for interacting with the X API via the xdk SDK.
    """

    DEFAULT_TWEET_FIELDS = [
        "id",
        "text",
        "conversation_id",
        "created_at",
        "author_id",
        "public_metrics",
        "referenced_tweets",
        "attachments",
        "entities",
        "source",
        "lang",
        "possibly_sensitive",
        "reply_settings",
        "edit_history_tweet_ids",
    ]

    DEFAULT_EXPANSIONS = [
        "author_id",
        "attachments.media_keys",
        "referenced_tweets.id",
        "referenced_tweets.id.author_id",
    ]

    DEFAULT_USER_FIELDS = [
        "id",
        "username",
        "name",
        "profile_image_url",
        "verified",
        "verified_type",
        "description",
        "public_metrics",
    ]

    DEFAULT_MEDIA_FIELDS = [
        "media_key",
        "type",
        "url",
        "preview_image_url",
        "width",
        "height",
        "alt_text",
        "duration_ms",
    ]

    def __init__(self, bearer_token: str | None = None, client: Client | None = None) -> None:
        token_from_settings = (
            config.x_app.BEARER_TOKEN.get_secret_value() if config.x_app.BEARER_TOKEN is not None else None
        )
        token = bearer_token or token_from_settings
        if not token:
            raise ValueError("X App bearer token is not configured")
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
        user_fields: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
        hydrate: bool = True,
    ) -> SearchAllResult:
        """
        Run a full-archive search against X with complete tweet data.
        """
        raw_response = self._client.posts.search_all(
            query=query,
            start_time=start_time,
            end_time=end_time,
            since_id=since_id,
            until_id=until_id,
            max_results=max_results,
            next_token=next_token,
            pagination_token=pagination_token,
            sort_order=sort_order,
            expansions=expansions or self.DEFAULT_EXPANSIONS,
            tweetfields=tweet_fields or self.DEFAULT_TWEET_FIELDS,
            userfields=user_fields or self.DEFAULT_USER_FIELDS,
            mediafields=media_fields or self.DEFAULT_MEDIA_FIELDS,
            pollfields=poll_fields,
            placefields=place_fields,
        )

        result = SearchAllResult.model_validate(raw_response.model_dump())

        if hydrate:
            result.hydrate()

        return result


def get_x_app_client(bearer_token: str | None = None, client: Client | None = None) -> XAppClient:
    """Create a configured X client."""
    return XAppClient(bearer_token=bearer_token, client=client)
