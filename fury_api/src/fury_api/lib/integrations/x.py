"""
X API integration client using the official X SDK (xdk).
"""

from typing import Any
from datetime import datetime

from xdk import Client
from pydantic import BaseModel, ConfigDict, Field, computed_field

from fury_api.lib.settings import config


# ============================================================================
# User Models (from includes.users)
# ============================================================================


class UserPublicMetrics(BaseModel):
    """Public metrics for a user."""

    followers_count: int = 0
    following_count: int = 0
    tweet_count: int = 0
    listed_count: int = 0


class SearchUser(BaseModel):
    """User object returned in includes.users."""

    model_config = ConfigDict(extra="allow")

    id: str
    username: str  # The @handle
    name: str  # Display name
    profile_image_url: str | None = None
    verified: bool = False
    verified_type: str | None = None  # "blue", "business", "government", or None
    description: str | None = None
    public_metrics: UserPublicMetrics | None = None


# ============================================================================
# Media Models (from includes.media)
# ============================================================================


class SearchMedia(BaseModel):
    """Media object returned in includes.media."""

    model_config = ConfigDict(extra="allow")

    media_key: str
    type: str  # "photo", "video", "animated_gif"
    url: str | None = None  # For photos
    preview_image_url: str | None = None  # For videos/gifs
    width: int | None = None
    height: int | None = None
    alt_text: str | None = None
    duration_ms: int | None = None  # For videos


# ============================================================================
# Tweet Models
# ============================================================================


class TweetPublicMetrics(BaseModel):
    """Engagement metrics for a tweet."""

    like_count: int = 0
    retweet_count: int = 0
    reply_count: int = 0
    quote_count: int = 0
    impression_count: int = 0
    bookmark_count: int = 0


class ReferencedTweet(BaseModel):
    """Reference to another tweet (retweet, quote, reply)."""

    type: str  # "retweeted", "quoted", "replied_to"
    id: str


class SearchPost(BaseModel):
    """Tweet payload with full display data."""

    model_config = ConfigDict(extra="allow")

    id: str
    text: str | None = None
    conversation_id: str | None = None
    created_at: datetime | None = None
    author_id: str | None = None

    # Engagement metrics
    public_metrics: TweetPublicMetrics | None = None

    # For threading/quotes/retweets
    referenced_tweets: list[ReferencedTweet] | None = None

    # Media attachment keys (resolve via includes.media)
    attachments: dict[str, Any] | None = None

    # URLs, mentions, hashtags, etc.
    entities: dict[str, Any] | None = None

    # Tweet metadata
    source: str | None = None  # "Twitter for iPhone", etc.
    lang: str | None = None
    possibly_sensitive: bool = False
    reply_settings: str | None = None  # "everyone", "mentionedUsers", "followers"

    edit_history_tweet_ids: list[str] | None = None

    # === Denormalized fields (populated after joining with includes) ===
    author: SearchUser | None = None
    media: list[SearchMedia] | None = None

    @computed_field
    @property
    def is_retweet(self) -> bool:
        """Check if this tweet is a retweet."""
        if not self.referenced_tweets:
            return False
        return any(ref.type == "retweeted" for ref in self.referenced_tweets)

    @computed_field
    @property
    def is_quote(self) -> bool:
        """Check if this tweet is a quote tweet."""
        if not self.referenced_tweets:
            return False
        return any(ref.type == "quoted" for ref in self.referenced_tweets)

    @computed_field
    @property
    def is_reply(self) -> bool:
        """Check if this tweet is a reply."""
        if not self.referenced_tweets:
            return False
        return any(ref.type == "replied_to" for ref in self.referenced_tweets)

    @computed_field
    @property
    def tweet_url(self) -> str | None:
        """Construct the tweet URL."""
        if self.author and self.author.username:
            return f"https://x.com/{self.author.username}/status/{self.id}"
        return f"https://x.com/i/status/{self.id}"


class SearchIncludes(BaseModel):
    """Expanded objects referenced by tweets."""

    model_config = ConfigDict(extra="allow")

    users: list[SearchUser] = Field(default_factory=list)
    media: list[SearchMedia] = Field(default_factory=list)
    tweets: list["SearchPost"] = Field(default_factory=list)  # For referenced tweets


class SearchMeta(BaseModel):
    """Pagination and summary metadata for X search results."""

    newest_id: str | None = None
    oldest_id: str | None = None
    result_count: int | None = None
    next_token: str | None = None
    previous_token: str | None = None


class SearchAllResult(BaseModel):
    """Structured response for the X full-archive search endpoint."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    data: list[SearchPost] = Field(default_factory=list)
    meta: SearchMeta | None = None
    includes: SearchIncludes | None = None

    def hydrate(self) -> "SearchAllResult":
        """
        Denormalize the response by joining includes data into tweets.

        Call this after parsing to populate author/media on each tweet.
        """
        if not self.includes:
            return self

        # Build lookup maps
        users_by_id = {user.id: user for user in self.includes.users}
        media_by_key = {m.media_key: m for m in self.includes.media}

        # Hydrate each tweet
        for tweet in self.data:
            # Attach author
            if tweet.author_id and tweet.author_id in users_by_id:
                tweet.author = users_by_id[tweet.author_id]

            # Attach media
            if tweet.attachments and "media_keys" in tweet.attachments:
                tweet.media = [media_by_key[key] for key in tweet.attachments["media_keys"] if key in media_by_key]

        return self


# ============================================================================
# Client
# ============================================================================


class XClient:
    """
    Client for interacting with the X API via the xdk SDK.
    """

    # Fields to request for complete tweet display
    DEFAULT_TWEET_FIELDS = [
        "id",
        "text",
        "conversation_id",
        "created_at",
        "author_id",
        "public_metrics",  # likes, retweets, replies, quotes, impressions, bookmarks
        "referenced_tweets",  # for detecting RT/quote/reply
        "attachments",  # media keys
        "entities",  # URLs, mentions, hashtags
        "source",  # client used to post
        "lang",  # language
        "possibly_sensitive",
        "reply_settings",
        "edit_history_tweet_ids",
    ]

    # Expansions to resolve referenced objects
    DEFAULT_EXPANSIONS = [
        "author_id",  # Get user objects
        "attachments.media_keys",  # Get media objects
        "referenced_tweets.id",  # Get quoted/retweeted tweets
        "referenced_tweets.id.author_id",  # Get authors of referenced tweets
    ]

    # User fields when expanding author_id
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

    # Media fields when expanding attachments.media_keys
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
        token_from_settings = config.x.BEARER_TOKEN.get_secret_value() if config.x.BEARER_TOKEN is not None else None
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
        # Allow overriding defaults, but provide sensible defaults
        tweet_fields: list[str] | None = None,
        expansions: list[str] | None = None,
        user_fields: list[str] | None = None,
        media_fields: list[str] | None = None,
        poll_fields: list[str] | None = None,
        place_fields: list[str] | None = None,
        hydrate: bool = True,  # Auto-join includes by default
    ) -> SearchAllResult:
        """
        Run a full-archive search against X with complete tweet data.

        By default, returns fully hydrated tweets with author info,
        engagement metrics, and media attached.
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


def get_x_client(bearer_token: str | None = None, client: Client | None = None) -> XClient:
    """Create a configured X client."""
    return XClient(bearer_token=bearer_token, client=client)
