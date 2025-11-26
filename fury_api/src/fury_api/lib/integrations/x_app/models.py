from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field

__all__ = [
    "UserPublicMetrics",
    "SearchUser",
    "SearchMedia",
    "TweetPublicMetrics",
    "ReferencedTweet",
    "NoteTweet",
    "SearchPost",
    "SearchIncludes",
    "SearchMeta",
    "SearchAllResult",
]


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


class NoteTweet(BaseModel):
    """Long-form tweet content (for tweets > 280 characters)."""

    text: str
    entities: dict[str, Any] | None = None


class SearchPost(BaseModel):
    """Tweet payload with full display data."""

    model_config = ConfigDict(extra="allow")

    id: str
    text: str | None = None
    note_tweet: NoteTweet | None = None
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

    # === Denormalized fields (populated after joining includes) ===
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

        users_by_id = {user.id: user for user in self.includes.users}
        media_by_key = {m.media_key: m for m in self.includes.media}

        for tweet in self.data:
            if tweet.author_id and tweet.author_id in users_by_id:
                tweet.author = users_by_id[tweet.author_id]

            if tweet.attachments and "media_keys" in tweet.attachments:
                tweet.media = [media_by_key[key] for key in tweet.attachments["media_keys"] if key in media_by_key]

        return self
