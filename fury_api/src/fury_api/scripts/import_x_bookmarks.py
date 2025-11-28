#!/usr/bin/env python3
"""
Import X bookmarks (folders + all-bookmarks super collection) for a given organization/user/plugin.

Usage:
    python import_x_bookmarks.py --organization-id 1 --plugin-id 1 [--max-results 20] [--fetch-all]
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any, Iterable

from fury_api.lib.factories import ServiceFactory, UnitOfWorkFactory
from fury_api.lib.factories.service_factory import ServiceType
from fury_api.lib.integrations.x_user import BookmarkFolder, XUserClient
from fury_api.domain.authors.models import Author
from fury_api.domain.collections.models import Collection, CollectionUpdate
from fury_api.domain.content.models import Content
from fury_api.domain.plugins.models import Plugin

TWITTER_PLATORM_LABEL = "twitter"
ALL_BOOKMARKS_COLLETION_TYPE = "all_bookmarks"
BOOKMARK_FOLDER_COLLECTION_TYPE = "bookmark_folder"
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


async def _ensure_all_bookmarks_collection(
    collections_service,
    *,
    organization_id: int,
    plugin_id: int,
) -> Collection:
    """Ensure the 'My X Bookmarks' super-collection exists."""
    collection = await collections_service.get_by_platform_name(
        platform=TWITTER_PLATORM_LABEL,
        name=MY_BOOKMARKS_COLLECTION_LABEL,
    )

    now = datetime.now(timezone.utc)
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
                    "last_synced_at": now,
                }
            )
        )
    else:
        await collections_service.update_item(collection.id, CollectionUpdate(last_synced_at=now))  # type: ignore[arg-type]
    return collection


async def _ensure_folder_collection(
    collections_service,
    *,
    organization_id: int,
    plugin_id: int,
    folder: BookmarkFolder,
) -> Collection:
    """Ensure a folder-backed collection exists and is up to date."""
    collection = await collections_service.get_by_platform_external_id(
        platform=TWITTER_PLATORM_LABEL,
        external_id=folder.id,
    )

    now = datetime.now(timezone.utc)
    if collection is None:
        collection = await collections_service.create_item(
            Collection.model_validate(
                {
                    "type": BOOKMARK_FOLDER_COLLECTION_TYPE,
                    "platform": TWITTER_PLATORM_LABEL,
                    "name": folder.name,
                    "external_id": folder.id,
                    "description": None,
                    "collection_url": None,
                    "plugin_id": plugin_id,
                    "organization_id": organization_id,
                    "last_synced_at": now,
                }
            )
        )
        return collection

    updates: dict[str, Any] = {"last_synced_at": now}
    if folder.name and folder.name != collection.name:
        updates["name"] = folder.name

    if updates:
        await collections_service.update_item(collection.id, CollectionUpdate(**updates))  # type: ignore[arg-type]

    return collection


async def _ensure_author(
    authors_service,
    *,
    author_data: dict[str, Any],
) -> Author | None:
    """Ensure the author exists, create or update if needed."""
    external_id = author_data.get("id")
    if not external_id:
        return None

    author = await authors_service.get_by_platform_id(platform=TWITTER_PLATORM_LABEL, external_id=external_id)
    if not author:
        author = await authors_service.create_item(
            Author.model_validate(
                {
                    "platform": TWITTER_PLATORM_LABEL,
                    "external_id": external_id,
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


async def _ensure_authors_map(
    posts: Iterable[Any],
    authors_service,
) -> dict[str, int]:
    """Make sure all authors exist and return an id map by external id."""
    author_id_map: dict[str, int] = {}
    for post in posts:
        if not post.author:
            print(f"Warning: Post {post.id} has no author data, skipping author creation...")
            continue

        author = await _ensure_author(
            authors_service,
            author_data=post.author.model_dump() if hasattr(post.author, "model_dump") else post.author,
        )
        if author:
            author_id_map[post.author_id] = author.id  # type: ignore[assignment]
    return author_id_map


def _map_posts_to_content(
    posts: Iterable[Any],
    *,
    organization_id: int,
    author_id_map: dict[str, int],
) -> list[Content]:
    """Map X posts to Content objects with author_id and quote tweet data."""
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
                organization_id=organization_id,
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
    posts: Iterable[Any],
    *,
    organization_id: int,
    author_id_map: dict[str, int],
    contents_service,
    content_cache: dict[str, Content],
) -> tuple[list[Content], int, int]:
    """Return Content objects for posts, creating any that do not already exist."""
    resolved: list[Content] = []
    to_create_candidates: list[Content] = []

    for content in _map_posts_to_content(posts, organization_id=organization_id, author_id_map=author_id_map):
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


async def fetch_folder_bookmark_ids(
    client: XUserClient, *, user_id: str, folder_id: str, fetch_all: bool
) -> AsyncIterator[list[str]]:
    pagination_token: str | None = None

    while True:
        response = await client.get_bookmarks_by_folder(
            user_id=user_id,
            folder_id=folder_id,
            pagination_token=pagination_token,
        )
        ids = [item.id for item in response.data or [] if item.id]
        yield ids
        pagination_token = response.meta.next_token if response.meta else None

        if not fetch_all or not pagination_token:
            break


async def fetch_bookmark_folders(
    client: XUserClient, *, user_id: str, max_results: int, fetch_all: bool
) -> list[BookmarkFolder]:
    pagination_token: str | None = None
    folders: list[BookmarkFolder] = []

    while True:
        response = await client.get_bookmark_folders(
            user_id=user_id,
            pagination_token=pagination_token,
            max_results=max_results,
        )
        folders.extend(response.data or [])
        pagination_token = response.meta.next_token if response.meta else None

        if not fetch_all or not pagination_token:
            break

    return folders


async def _reconcile_collection_links(
    content_collections_service, collection_id: int, desired_content_ids: set[int]
) -> None:
    """Ensure collection membership matches the desired set."""
    existing_ids = set(await content_collections_service.get_content_for_collection(collection_id))
    to_unlink = existing_ids - desired_content_ids
    if not to_unlink:
        return

    for content_id in to_unlink:
        await content_collections_service.unlink_content_from_collection(
            content_id=content_id,
            collection_id=collection_id,
        )


async def _sync_bookmark_scope(
    *,
    scope_name: str,
    posts_iterator: AsyncIterator[list[Any]],
    organization_id: int,
    authors_service,
    contents_service,
    content_collections_service,
    all_collection_id: int,
    folder_collection_id: int | None,
    content_cache: dict[str, Content],
) -> tuple[set[int], int, int]:
    """Sync a stream of bookmark pages into content + collections."""
    created_total = 0
    failed_total = 0
    scope_content_ids: set[int] = set()
    page_num = 0

    async for posts in posts_iterator:
        page_num += 1
        if not posts:
            print(f"{scope_name} page {page_num}: no posts returned")
            continue

        author_id_map = await _ensure_authors_map(posts, authors_service)
        contents, created_count, failed_count = await _get_or_create_contents(
            posts,
            organization_id=organization_id,
            author_id_map=author_id_map,
            contents_service=contents_service,
            content_cache=content_cache,
        )

        created_total += created_count
        failed_total += failed_count

        for content in contents:
            if content.id is None:
                continue
            scope_content_ids.add(content.id)
            await content_collections_service.link_content_to_collection(
                content_id=content.id,
                collection_id=all_collection_id,
            )
            if folder_collection_id is not None:
                await content_collections_service.link_content_to_collection(
                    content_id=content.id,
                    collection_id=folder_collection_id,
                )

        print(f"{scope_name} page {page_num}: created={created_count}, failed={failed_count}, linked={len(contents)}")

    return scope_content_ids, created_total, failed_total


async def _sync_folder_links(
    *,
    scope_name: str,
    ids_iterator: AsyncIterator[list[str]],
    contents_service,
    content_collections_service,
    all_collection_id: int,
    folder_collection_id: int,
    content_cache: dict[str, Content],
) -> tuple[set[int], list[str]]:
    """Link existing content to a folder collection using only bookmark IDs."""
    folder_content_ids: set[int] = set()
    missing_ids: list[str] = []
    page_num = 0

    async for ids in ids_iterator:
        page_num += 1
        if not ids:
            print(f"{scope_name} page {page_num}: no ids returned")
            continue

        needed_ids = [i for i in ids if i not in content_cache]
        if needed_ids:
            existing = await contents_service.get_by_external_ids(needed_ids)
            for content in existing:
                content_cache[content.external_id] = content

        for external_id in ids:
            content = content_cache.get(external_id)
            if not content or content.id is None:
                missing_ids.append(external_id)
                continue

            folder_content_ids.add(content.id)
            await content_collections_service.link_content_to_collection(
                content_id=content.id,
                collection_id=all_collection_id,
            )
            await content_collections_service.link_content_to_collection(
                content_id=content.id,
                collection_id=folder_collection_id,
            )

        print(f"{scope_name} page {page_num}: linked={len(ids)}, missing={len(missing_ids)} (cumulative)")

    return folder_content_ids, missing_ids


async def _hydrate_missing_ids(
    *,
    missing_by_collection: dict[int, list[str]],
    x_user_client: XUserClient,
    organization_id: int,
    authors_service,
    contents_service,
    content_collections_service,
    all_collection_id: int,
    content_cache: dict[str, Content],
    batch_size: int = 100,
) -> tuple[int, int, int]:
    """
    Fetch missing tweets by ID, create content, and link to collections.

    Returns (created_count, failed_count, unresolved_count).
    """
    if not missing_by_collection:
        return 0, 0, 0

    id_to_collections: dict[str, set[int]] = {}
    for collection_id, ids in missing_by_collection.items():
        for id_ in ids:
            id_to_collections.setdefault(id_, set()).add(collection_id)

    all_missing_ids = list(id_to_collections.keys())
    created_total = 0
    failed_total = 0
    unresolved_total = 0

    for i in range(0, len(all_missing_ids), batch_size):
        batch_ids = all_missing_ids[i : i + batch_size]
        try:
            resp = await x_user_client.get_tweets_by_ids(ids=batch_ids)
        except Exception as exc:  # pragma: no cover - defensive
            print(f"Error hydrating missing ids batch {i // batch_size + 1}: {exc}")
            unresolved_total += len(batch_ids)
            continue

        posts = resp.data or []
        author_id_map = await _ensure_authors_map(posts, authors_service)
        contents, created_count, failed_count = await _get_or_create_contents(
            posts,
            organization_id=organization_id,
            author_id_map=author_id_map,
            contents_service=contents_service,
            content_cache=content_cache,
        )

        created_total += created_count
        failed_total += failed_count

        found_ids = set()
        for content in contents:
            if content.id is None:
                continue
            external_id = content.external_id
            found_ids.add(external_id)
            await content_collections_service.link_content_to_collection(
                content_id=content.id,
                collection_id=all_collection_id,
            )
            for collection_id in id_to_collections.get(external_id, set()):
                await content_collections_service.link_content_to_collection(
                    content_id=content.id,
                    collection_id=collection_id,
                )

        unresolved_in_batch = set(batch_ids) - found_ids
        unresolved_total += len(unresolved_in_batch)

    return created_total, failed_total, unresolved_total


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

        # Ensure the super collection exists
        all_collection = await _ensure_all_bookmarks_collection(
            collections_service,
            organization_id=org_id,
            plugin_id=plugin_id,
        )

        async with XUserClient(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            token_obtained_at=token_obtained_at,
            expires_in=expires_in,
            on_tokens_refreshed=on_tokens_refreshed,
        ) as x_user_client:
            content_cache: dict[str, Content] = {}
            all_content_ids: set[int] = set()
            failed_scopes: list[str] = []

            # First fetch the global bookmarks endpoint to build/update content and cache
            try:
                base_content_ids, created, failed = await _sync_bookmark_scope(
                    scope_name="all-bookmarks endpoint",
                    posts_iterator=fetch_bookmark_pages(
                        x_user_client,
                        user_id=x_user_id,
                        max_results=max_results,
                        fetch_all=fetch_all,
                    ),
                    organization_id=org_id,
                    authors_service=authors_service,
                    contents_service=contents_service,
                    content_collections_service=content_collections_service,
                    all_collection_id=all_collection.id,  # type: ignore[arg-type]
                    folder_collection_id=None,
                    content_cache=content_cache,
                )
                all_content_ids.update(base_content_ids)
                print(
                    f"Synced all-bookmarks endpoint: created={created}, failed={failed}, total_seen={len(base_content_ids)}"
                )
            except Exception as exc:  # pragma: no cover - defensive
                failed_scopes.append(f"all-bookmarks endpoint: {exc}")
                print(f"Error syncing all-bookmarks endpoint: {exc}")

            # Sync folder collections (IDs only)
            folders = await fetch_bookmark_folders(
                x_user_client,
                user_id=x_user_id,
                max_results=max_results,
                fetch_all=fetch_all,
            )
            folder_collections: dict[str, Collection] = {}
            for folder in folders:
                collection = await _ensure_folder_collection(
                    collections_service,
                    organization_id=org_id,
                    plugin_id=plugin_id,
                    folder=folder,
                )
                folder_collections[folder.id] = collection

            missing_by_collection: dict[int, list[str]] = {}
            for folder in folders:
                collection = folder_collections[folder.id]
                try:
                    folder_content_ids, missing_ids = await _sync_folder_links(
                        scope_name=f"folder '{folder.name}'",
                        ids_iterator=fetch_folder_bookmark_ids(
                            x_user_client,
                            user_id=x_user_id,
                            folder_id=folder.id,
                            fetch_all=fetch_all,
                        ),
                        contents_service=contents_service,
                        content_collections_service=content_collections_service,
                        all_collection_id=all_collection.id,  # type: ignore[arg-type]
                        folder_collection_id=collection.id,  # type: ignore[arg-type]
                        content_cache=content_cache,
                    )
                    all_content_ids.update(folder_content_ids)
                    await _reconcile_collection_links(
                        content_collections_service,
                        collection.id,  # type: ignore[arg-type]
                        folder_content_ids,
                    )
                    if missing_ids:
                        print(
                            f"Folder '{folder.name}' missing {len(missing_ids)} items not present in content (first few: {missing_ids[:5]})"
                        )
                        missing_by_collection[collection.id] = missing_ids
                    print(
                        f"Synced folder '{folder.name}': linked={len(folder_content_ids)}, missing={len(missing_ids)}"
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    failed_scopes.append(f"folder {folder.id} ({folder.name}): {exc}")
                    print(f"Error syncing folder '{folder.name}': {exc}")

            # Hydrate any missing IDs (likely older bookmarks not returned by the all-bookmarks endpoint)
            if missing_by_collection:
                created, failed, unresolved = await _hydrate_missing_ids(
                    missing_by_collection=missing_by_collection,
                    x_user_client=x_user_client,
                    organization_id=org_id,
                    authors_service=authors_service,
                    contents_service=contents_service,
                    content_collections_service=content_collections_service,
                    all_collection_id=all_collection.id,  # type: ignore[arg-type]
                    content_cache=content_cache,
                )
                print(
                    f"Hydrated missing by ID: created={created}, failed={failed}, unresolved_after_lookup={unresolved}"
                )

            # Reconcile All Bookmarks collection membership if all scopes succeeded
            if failed_scopes:
                print(f"Skipped cleanup for '{MY_BOOKMARKS_COLLECTION_LABEL}' due to failures: {failed_scopes}")
            else:
                await _reconcile_collection_links(
                    content_collections_service,
                    all_collection.id,  # type: ignore[arg-type]
                    all_content_ids,
                )
                print(
                    f"Reconciled '{MY_BOOKMARKS_COLLECTION_LABEL}' membership to {len(all_content_ids)} items across folders + all-bookmarks endpoint."
                )


if __name__ == "__main__":
    asyncio.run(main())
