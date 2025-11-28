#!/usr/bin/env python3
"""
Import X bookmarks for a given organization/user/plugin.

Usage:
    python import_x_bookmarks.py --organization-id 1 --user-id 1 --plugin-id 1 [--max-results 20] [--fetch-all]
"""

import argparse
import asyncio
from datetime import datetime, timezone
from collections.abc import AsyncIterator
from typing import Any, Iterable

from fury_api.lib.factories import ServiceFactory, UnitOfWorkFactory
from fury_api.lib.factories.service_factory import ServiceType
from fury_api.lib.integrations.x_user import XUserClient
from fury_api.domain.content.models import Content
from fury_api.domain.plugins.models import Plugin
from fury_api.domain.authors.models import Author
from fury_api.domain.collections.models import Collection

TWITTER_PLATORM_LABEL = "twitter"

ALL_BOOKMARKS_COLLETION_TYPE = "all_bookmarks"

MY_BOOKMARKS_COLLECTION_LABEL = "My X Bookmarks"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import X bookmarks for a user")
    parser.add_argument("--organization-id", type=int, required=True, help="Organization ID")
    parser.add_argument("--plugin-id", type=int, required=True, help="Plugin ID containing X credentials")
    parser.add_argument("--max-results", type=int, default=20, help="Max results per request (default: 20)")
    parser.add_argument(
        "--fetch-all",
        action="store_true",
        help="Fetch all pages of bookmarks (defaults to a single page)",
    )
    return parser.parse_args()


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


async def _ensure_collection(
    collections_service,
    *,
    organization_id: int,
    plugin_id: int,
) -> Collection:
    """Ensure the 'My X Bookmarks' collection exists, create if not."""
    collection = await collections_service.get_by_platform_name(
        platform=TWITTER_PLATORM_LABEL,
        name=MY_BOOKMARKS_COLLECTION_LABEL,
    )

    if collection is None:
        collection = await collections_service.create_item(
            Collection.model_validate(
                {
                    "type": ALL_BOOKMARKS_COLLETION_TYPE,
                    "platform": TWITTER_PLATORM_LABEL,
                    "name": MY_BOOKMARKS_COLLECTION_LABEL,
                    "external_id": f"{TWITTER_PLATORM_LABEL}:{ALL_BOOKMARKS_COLLETION_TYPE}",
                    "description": None,
                    "collection_url": None,
                    "plugin_id": plugin_id,
                    "organization_id": organization_id,
                }
            )
        )
    return collection


async def _ensure_author(
    authors_service,
    *,
    author_data: dict[str, Any],
) -> Author:
    """Ensure the author exists, create or update if needed."""
    author = await authors_service.get_by_platform_id(platform=TWITTER_PLATORM_LABEL, external_id=author_data.get("id"))
    if not author:
        author = await authors_service.create_item(
            Author.model_validate(
                {
                    "platform": TWITTER_PLATORM_LABEL,
                    "external_id": author_data.get("id"),
                    "display_name": author_data.get("name", ""),
                    "handle": author_data.get("username"),
                    "avatar_url": author_data.get("profile_image_url"),
                    "profile_url": f"https://x.com/{author_data.get('username')}",
                    "bio": author_data.get("description"),
                    "follower_count": author_data.get("public_metrics", {}).get("followers_count"),
                    "following_count": author_data.get("public_metrics", {}).get("following_count"),
                }
            )
        )
    return author


def _map_posts_to_content(
    posts: Iterable[Any],
    *,
    organization_id: int,
    author_id_map: dict[str, int],
) -> list[Content]:
    """Map X posts to Content objects with author_id."""
    contents: list[Content] = []
    for post in posts:
        # For long-form tweets (>280 chars), use note_tweet.text; otherwise use text
        body = (post.note_tweet.text if post.note_tweet else post.text) or ""
        # Excerpt should be truncated for display (limit to 280 chars)
        excerpt = body[:280] + "..." if len(body) > 280 else body

        # Get author_id from the map (populated by _ensure_author)
        author_id = author_id_map.get(post.author_id)
        if not author_id:
            print(f"Warning: No author_id found for post {post.id}, skipping...")
            continue

        contents.append(
            Content(
                organization_id=organization_id,
                author_id=author_id,
                external_id=post.id,
                external_url=post.tweet_url,
                title=None,
                body=body,
                excerpt=excerpt,
                published_at=post.created_at,
                synced_at=datetime.now(timezone.utc),
                platform_metadata=post.model_dump(),
            )
        )
    return contents


async def fetch_bookmark_pages(
    client: XUserClient, *, user_id: str, max_results: int, fetch_all: bool
) -> AsyncIterator[list[Any]]:
    pagination_token: str | None = None

    while True:
        response = await client.get_bookmarks(
            user_id=user_id,
            pagination_token=pagination_token,
            max_results=max_results,
        )
        yield response.data or []
        pagination_token = response.meta.next_token if response.meta else None

        if not fetch_all or not pagination_token:
            break


async def main() -> None:
    args = parse_args()
    org_id = args.organization_id
    plugin_id = args.plugin_id
    max_results = args.max_results
    fetch_all = args.fetch_all

    async with UnitOfWorkFactory.get_uow(organization_id=org_id) as uow:
        plugins_service = ServiceFactory.create_service(ServiceType.PLUGINS, uow, has_system_access=True)
        authors_service = ServiceFactory.create_service(ServiceType.AUTHORS, uow, has_system_access=True)
        collections_service = ServiceFactory.create_service(ServiceType.COLLECTIONS, uow, has_system_access=True)
        content_collections_service = ServiceFactory.create_service(
            ServiceType.CONTENT_COLLECTIONS, uow, has_system_access=True
        )
        contents_service = ServiceFactory.create_service(ServiceType.CONTENTS, uow, has_system_access=True)

        plugin = await plugins_service.get_item(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        access_token, refresh_token, token_type, token_obtained_at, expires_in = _extract_tokens(plugin)
        if not access_token and not refresh_token:
            raise ValueError("Plugin credentials must include access_token or refresh_token for X user auth")

        # Get the authenticated X user's ID from plugin properties (stored during OAuth)
        x_user_id = plugin.properties.get("x_user_id") if plugin.properties else None
        if not x_user_id:
            raise ValueError(f"Plugin {plugin_id} is missing x_user_id in properties. Re-authorize the X integration.")

        # Define callback to update plugin credentials when tokens are refreshed
        async def on_tokens_refreshed(new_access_token: str, new_refresh_token: str) -> None:
            """Update plugin credentials with new tokens after refresh."""
            print(f"DEBUG: Updating plugin {plugin_id} credentials with refreshed tokens")
            updated_creds = {
                **(plugin.credentials or {}),
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_obtained_at": datetime.now().isoformat(),
            }
            plugin.credentials = updated_creds
            await plugins_service.update_item(plugin_id, plugin)
            print("DEBUG: Plugin credentials updated successfully")

        # Ensure the MY_BOOKMARKS_COLLECTION_LABEL collection exists
        collection = await _ensure_collection(
            collections_service,
            organization_id=org_id,
            plugin_id=plugin_id,
        )
        collection_name = collection.name

        async with XUserClient(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            token_obtained_at=token_obtained_at,
            expires_in=expires_in,
            on_tokens_refreshed=on_tokens_refreshed,
        ) as x_user_client:
            pages = fetch_bookmark_pages(
                x_user_client,
                user_id=x_user_id,
                max_results=max_results,
                fetch_all=fetch_all,
            )

            total_created = 0
            total_failed = 0
            page_num = 0

            async for posts in pages:
                page_num += 1

                # First, ensure all authors exist
                author_id_map: dict[str, int] = {}
                for post in posts:
                    if not post.author:
                        print(f"Warning: Post {post.id} has no author data, skipping...")
                        continue

                    author = await _ensure_author(
                        authors_service,
                        author_data=post.author.model_dump() if hasattr(post.author, "model_dump") else post.author,
                    )
                    author_id_map[post.author_id] = author.id  # type: ignore[assignment]

                # Map posts to Content objects
                contents = _map_posts_to_content(posts, organization_id=org_id, author_id_map=author_id_map)
                result = await contents_service.create_items_with_results(contents)

                created_count = len(result.created)
                failed_count = len(result.failed)
                total_created += created_count
                total_failed += failed_count

                # Link created content to the collection
                for content in result.created:
                    await content_collections_service.link_content_to_collection(
                        content_id=content.id,
                        collection_id=collection.id,  # type: ignore[arg-type]
                    )

                print(
                    f"Page {page_num}: created={created_count}, failed={failed_count}"
                    + (f" (errors: {[f.error for f in result.failed]})" if failed_count else "")
                )

            print(
                f"Imported {total_created} bookmark(s) into content for collection '{collection_name}'. "
                f"Failed: {total_failed}."
            )


if __name__ == "__main__":
    asyncio.run(main())
