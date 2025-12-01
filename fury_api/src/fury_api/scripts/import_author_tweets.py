#!/usr/bin/env python3
"""
Import top tweets from a specific X/Twitter author by relevancy.

Uses the X API search endpoint with sort_order=relevancy to fetch the best tweets
from an author. Updates author metadata and tracks last sync time.

Replies and retweets are excluded by default.

Processes in batches for reliability: each page is fetched and stored before
moving to the next, so partial progress is saved if something fails. On error,
the script prints a resume command with the pagination token.

Usage:
    python import_author_tweets.py --username balajis                     # Fetch ALL tweets
    python import_author_tweets.py --username balajis --total-tweets 300  # Fetch top 300
    python import_author_tweets.py --username balajis --include-retweets  # Include retweets
    python import_author_tweets.py --username balajis --include-replies   # Include replies

Resume after failure:
    python import_author_tweets.py --username balajis --resume-token "TOKEN"
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from fury_api.lib.factories import ServiceFactory, UnitOfWorkFactory
from fury_api.lib.factories.service_factory import ServiceType
from fury_api.lib.integrations.x_user import XUserClient
from fury_api.lib.integrations.x_app.models import SearchPost
from fury_api.domain.authors.models import Author
from fury_api.domain.content.models import Content
from fury_api.domain.plugins.models import Plugin

TWITTER_PLATFORM_LABEL = "twitter"


def _extract_tokens(plugin: Plugin) -> tuple[str | None, str | None, str | None, str | None, int | None]:
    """Extract OAuth tokens and metadata from plugin credentials."""
    creds = plugin.credentials or {}
    return (
        creds.get("access_token"),
        creds.get("refresh_token"),
        creds.get("token_type"),
        creds.get("token_obtained_at"),
        creds.get("expires_in"),
    )


@dataclass
class TweetPage:
    """A page of tweets from the API."""

    posts: list[SearchPost]
    page_number: int
    has_more: bool
    next_token: str | None  # Token to fetch the next page (for resume on failure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import tweets from an X/Twitter author")
    parser.add_argument("--organization-id", type=int, required=True, help="Organization ID")
    parser.add_argument("--plugin-id", type=int, required=True, help="Plugin ID with X credentials")
    parser.add_argument("--username", type=str, required=True, help="X/Twitter username (without @)")
    parser.add_argument(
        "--total-tweets",
        type=int,
        default=None,
        help="Total number of tweets to ingest (default: all)",
    )
    parser.add_argument(
        "--include-retweets",
        action="store_true",
        help="Include retweets (default: excluded)",
    )
    parser.add_argument(
        "--include-replies",
        action="store_true",
        help="Include replies (default: excluded)",
    )
    parser.add_argument(
        "--resume-token",
        type=str,
        default=None,
        help="Pagination token to resume from (printed on failure)",
    )
    return parser.parse_args()


async def fetch_author_tweets_paginated(
    x_client: XUserClient,
    user_id: str,
    username: str,  # Keep for logging
    total_tweets: int | None = None,
    resume_token: str | None = None,
    include_retweets: bool = False,
    include_replies: bool = False,
) -> AsyncIterator[TweetPage]:
    """
    Yield pages of tweets from an author, one at a time.

    This async generator allows the caller to process and save each page before
    fetching the next, making the import resilient to failures.

    Args:
        user_id: The X user ID whose tweets to fetch.
        username: Username for display purposes only.
        total_tweets: Maximum number of tweets to fetch. None means fetch all available.
        resume_token: If provided, start fetching from this pagination token
                      (useful for resuming after a failure).
        include_retweets: If True, include retweets. Default excludes them.
        include_replies: If True, include replies. Default excludes them.
    """
    fetched_count = 0
    pagination_token: str | None = resume_token
    max_results = 100  # API max is 100 per request
    page_number = 0

    # Build exclusion list based on flags
    exclude: list[str] = []
    if not include_retweets:
        exclude.append("retweets")
    if not include_replies:
        exclude.append("replies")

    if resume_token:
        print(f"Resuming from token: {resume_token[:20]}...")

    limit_desc = f"top {total_tweets}" if total_tweets else "all"
    print(f"Fetching {limit_desc} tweets from @{username}")

    while total_tweets is None or fetched_count < total_tweets:
        page_number += 1

        response = await x_client.get_posts(
            user_id=user_id,
            max_results=max_results,
            pagination_token=pagination_token,
            exclude=exclude if exclude else None,
            hydrate=True,
        )
        posts = response.data or []
        if not posts:
            print("No more results from API.")
            break

        fetched_count += len(posts)
        pagination_token = response.meta.next_token if response.meta else None
        has_more = pagination_token is not None and (total_tweets is None or fetched_count < total_tweets)

        yield TweetPage(posts=posts, page_number=page_number, has_more=has_more, next_token=pagination_token)

        if not pagination_token:
            break


async def _ensure_author(
    authors_service,
    author_data: dict[str, Any],
) -> Author | None:
    """
    Ensure the author exists and update their metadata.

    Always syncs the latest profile data (display_name, bio, follower_count, etc.)
    and updates the `updated_at` timestamp to track last sync time.
    """
    external_id = author_data.get("id")
    if not external_id:
        return None

    author = await authors_service.get_by_platform_id(platform=TWITTER_PLATFORM_LABEL, external_id=external_id)

    author_fields = {
        "platform": TWITTER_PLATFORM_LABEL,
        "external_id": external_id,
        "display_name": author_data.get("name", ""),
        "handle": author_data.get("username"),
        "avatar_url": author_data.get("profile_image_url", ""),
        "profile_url": f"https://x.com/{author_data.get('username')}",
        "bio": author_data.get("description"),
        "follower_count": author_data.get("public_metrics", {}).get("followers_count"),
        "following_count": author_data.get("public_metrics", {}).get("following_count"),
    }

    if not author:
        print(f"Creating author: {author_fields['display_name']} (@{author_fields['handle']})")
        author = await authors_service.create_item(Author.model_validate(author_fields))
    else:
        # Update author metadata to sync latest profile data
        print(f"Updating author metadata: {author_fields['display_name']} (@{author_fields['handle']})")

        # Update the author record
        await authors_service.update_item(author.id, Author.model_validate(author_fields))

        # Refresh author object to get updated data
        author = await authors_service.get_item(author.id)

    return author


def _map_posts_to_content(
    posts: Iterable[SearchPost],
    *,
    author_id: int,
) -> list[Content]:
    """Map X posts to Content objects with author_id and quote tweet data."""
    contents: list[Content] = []
    for post in posts:
        # For long-form tweets (>280 chars), use note_tweet.text; otherwise use text
        body = (post.note_tweet.text if post.note_tweet else post.text) or ""
        # Excerpt should be truncated for display (limit to 280 chars)
        excerpt = body[:280] + "..." if len(body) > 280 else body

        # Extract quoted tweet data if this is a quote tweet
        extra_fields = None
        if post.is_quote and post.quoted_tweet:
            qt = post.quoted_tweet
            quoted_text = (qt.note_tweet.text if qt.note_tweet else qt.text) or ""

            extra_fields = {
                "quoted_tweet": {
                    "id": qt.id,
                    "text": quoted_text,
                    "author": {
                        "id": qt.author.id if qt.author else None,
                        "name": qt.author.name if qt.author else None,
                        "username": qt.author.username if qt.author else None,
                        "avatar_url": qt.author.profile_image_url if qt.author else None,
                    }
                    if qt.author
                    else None,
                    "created_at": qt.created_at.isoformat() if qt.created_at else None,
                    "url": qt.tweet_url if hasattr(qt, "tweet_url") else None,
                }
            }

        # Store platform metadata (keep quoted_tweet_id for reference)
        platform_metadata = post.model_dump()
        if post.is_quote and post.referenced_tweets:
            quoted_ref = next((ref for ref in post.referenced_tweets if ref.type == "quoted"), None)
            if quoted_ref:
                platform_metadata["quoted_tweet_id"] = quoted_ref.id

        contents.append(
            Content(
                author_id=author_id,
                external_id=post.id,
                external_url=post.tweet_url,
                title=None,
                body=body,
                excerpt=excerpt,
                published_at=post.created_at,
                synced_at=datetime.now(timezone.utc),
                platform_metadata=platform_metadata,
                extra_fields=extra_fields,
            )
        )
    return contents


async def _get_or_create_contents(
    posts: Iterable[SearchPost],
    *,
    author_id: int,
    contents_service,
    content_cache: dict[str, Content],
) -> tuple[list[Content], int, int]:
    """Return Content objects for posts, creating any that do not already exist."""
    resolved: list[Content] = []
    to_create_candidates: list[Content] = []

    for content in _map_posts_to_content(posts, author_id=author_id):
        cached = content_cache.get(content.external_id)
        if cached:
            resolved.append(cached)
            continue

        to_create_candidates.append(content)

    if not to_create_candidates:
        return resolved, 0, 0

    existing = await contents_service.get_by_external_ids([c.external_id for c in to_create_candidates])
    existing_by_external = {content.external_id: content for content in existing}

    to_create: list[Content] = []
    for candidate in to_create_candidates:
        if candidate.external_id in existing_by_external:
            resolved.append(existing_by_external[candidate.external_id])
            content_cache[candidate.external_id] = existing_by_external[candidate.external_id]
        else:
            to_create.append(candidate)

    created_count = 0
    failed_count = 0
    if to_create:
        result = await contents_service.create_items_with_results(to_create)
        created_count = len(result.created)
        failed_count = len(result.failed)

        for content in result.created:
            resolved.append(content)
            content_cache[content.external_id] = content

        # If creation failed due to uniqueness, fall back to fetching those items
        failed_external_ids = [f.external_id for f in result.failed if f.external_id]
        if failed_external_ids:
            fallback_existing = await contents_service.get_by_external_ids(failed_external_ids)
            existing_map = {c.external_id: c for c in fallback_existing}
            recovered = 0
            for external_id in failed_external_ids:
                if external_id in existing_map:
                    resolved.append(existing_map[external_id])
                    content_cache[external_id] = existing_map[external_id]
                    recovered += 1
            failed_count = max(0, failed_count - recovered)

    return resolved, created_count, failed_count


async def main() -> None:
    args = parse_args()
    org_id = args.organization_id
    plugin_id = args.plugin_id
    username = args.username
    total_tweets = args.total_tweets

    # Initial UoW for plugin/author lookup
    async with UnitOfWorkFactory.get_uow(organization_id=org_id) as uow:
        # Initialize services
        plugins_service = ServiceFactory.create_service(ServiceType.PLUGINS, uow, has_system_access=True)
        authors_service = ServiceFactory.create_service(ServiceType.AUTHORS, uow, has_system_access=True)

        # Load plugin and validate
        plugin = await plugins_service.get_item(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        # Extract tokens
        access_token, refresh_token, token_type, token_obtained_at, expires_in = _extract_tokens(plugin)
        if not access_token and not refresh_token:
            raise ValueError("Plugin credentials must include access_token or refresh_token")

        # Resolve username to user_id via database
        author = await authors_service.get_by_platform_handle(
            platform=TWITTER_PLATFORM_LABEL,
            handle=username,
        )
        if not author or not author.external_id:
            raise ValueError(
                f"Author @{username} not found in database. " "Please ensure the author exists before importing tweets."
            )

        user_id = author.external_id
        print(f"Resolved @{username} to user_id: {user_id}")

        # Define token refresh callback
        async def on_tokens_refreshed(new_access_token: str, new_refresh_token: str) -> None:
            """Update plugin credentials when tokens are refreshed."""
            print(f"Updating plugin {plugin_id} credentials with refreshed tokens")
            updated_creds = {
                **(plugin.credentials or {}),
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_obtained_at": datetime.now().isoformat(),
            }
            plugin.credentials = updated_creds
            await plugins_service.update_item(plugin_id, plugin)
            print("Plugin credentials updated successfully")

        # Initialize XUserClient
        async with XUserClient(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            token_obtained_at=token_obtained_at,
            expires_in=expires_in,
            on_tokens_refreshed=on_tokens_refreshed,
        ) as x_user_client:
            # Create async paginated generator
            pages = fetch_author_tweets_paginated(
                x_user_client,
                user_id=user_id,
                username=username,
                total_tweets=total_tweets,
                resume_token=args.resume_token,
                include_retweets=args.include_retweets,
                include_replies=args.include_replies,
            )

            # Track totals
            total_created = 0
            total_existed = 0
            total_failed = 0
            total_processed = 0
            author_obj: Author | None = None
            current_page: TweetPage | None = None

            try:
                # Process each page with async iteration
                async for page in pages:
                    current_page = page
                    if not page.posts:
                        continue

                    # Fresh UoW per page for incremental commits
                    async with UnitOfWorkFactory.get_uow(organization_id=org_id) as page_uow:
                        page_authors_service = ServiceFactory.create_service(
                            ServiceType.AUTHORS, page_uow, has_system_access=True
                        )
                        page_contents_service = ServiceFactory.create_service(
                            ServiceType.CONTENTS, page_uow, has_system_access=True
                        )

                        # Ensure author exists (first page only)
                        if author_obj is None:
                            first_post = page.posts[0]
                            if not first_post.author:
                                raise ValueError("First tweet missing author data")

                            author_data = first_post.author.model_dump()
                            author_obj = await _ensure_author(page_authors_service, author_data)

                            if not author_obj or not author_obj.id:
                                raise ValueError("Failed to create/retrieve author")

                            print(f"\nAuthor: {author_obj.display_name} (@{author_obj.handle})")

                        # Process content
                        content_cache: dict[str, Content] = {}
                        contents, created_count, failed_count = await _get_or_create_contents(
                            page.posts,
                            author_id=author_obj.id,
                            contents_service=page_contents_service,
                            content_cache=content_cache,
                        )

                        total_created += created_count
                        total_existed += len(contents) - created_count
                        total_failed += failed_count
                        total_processed += len(page.posts)

                        print(
                            f"  Page {page.page_number}: {len(page.posts)} tweets "
                            f"(+{created_count} new, {len(contents) - created_count} existed)"
                        )

            except Exception as e:
                print(f"\n{'='*60}")
                print("ERROR OCCURRED")
                print(f"{'='*60}")
                print(f"\nError: {e}")
                print("\nProgress so far:")
                print(f"  Pages completed: {current_page.page_number - 1 if current_page else 0}")
                print(f"  Tweets processed: {total_processed}")
                print(f"  Created: {total_created}")

                # Print resume command
                if current_page and current_page.next_token:
                    print("\nTo resume, run:")
                    print(
                        f"  python import_author_tweets.py "
                        f"--organization-id {org_id} --plugin-id {plugin_id} "
                        f"--username {username}"
                        f"{f' --total-tweets {total_tweets}' if total_tweets else ''}"
                        f"{' --include-retweets' if args.include_retweets else ''}"
                        f"{' --include-replies' if args.include_replies else ''} "
                        f'--resume-token "{current_page.next_token}"'
                    )
                print(f"{'='*60}")
                raise

            if author_obj is None:
                print(f"No tweets found for @{username}")
                return

            # Success summary
            print(f"\n{'='*60}")
            print("SYNC COMPLETE")
            print(f"{'='*60}")
            print(f"\nAuthor: {author_obj.display_name} (@{author_obj.handle})")
            print(f"  ID: {author_obj.id}")
            print(f"  Followers: {author_obj.follower_count:,}" if author_obj.follower_count else "  Followers: N/A")
            print("\nContent:")
            print(f"  Created: {total_created}")
            print(f"  Already existed: {total_existed}")
            print(f"  Failed: {total_failed}")
            print(f"  Total processed: {total_processed}")
            print(f"\nAPI: GET /authors/{author_obj.id}/content")
            print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
