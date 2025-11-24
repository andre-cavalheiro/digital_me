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
from fury_api.domain.sources.models import Source


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import X bookmarks for a user")
    parser.add_argument("--organization-id", type=int, required=True, help="Organization ID")
    parser.add_argument("--user-id", type=int, required=True, help="User ID")
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


async def _ensure_source(
    sources_service,
    *,
    organization_id: int,
    plugin_id: int,
    user_id: int,
) -> Source:
    uow = sources_service.uow
    if uow is None or uow.session is None:
        raise ValueError("UnitOfWork session is not initialized for sources service")

    existing = await uow.sources.list(
        uow.session,
        filters={
            "plugin_id": plugin_id,
            "external_id": str(user_id),
            "source_type": "x_bookmarks",
        },
    )
    if existing:
        return existing[0]

    source = Source(
        organization_id=organization_id,
        plugin_id=plugin_id,
        user_id=user_id,
        source_type="x_bookmarks",
        external_id=str(user_id),
        display_name="My X Bookmarks",
        platform_type="x",
        sync_status="active",
        is_active=True,
    )
    return await sources_service.create_item(source)


def _map_posts_to_content(posts: Iterable[Any], *, organization_id: int, source_id: int) -> list[Content]:
    contents: list[Content] = []
    for post in posts:
        body = post.text or ""
        contents.append(
            Content(
                organization_id=organization_id,
                source_id=source_id,
                external_id=post.id,
                external_url=post.tweet_url,
                title=None,
                body=body,
                excerpt=body,
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
    user_id = args.user_id
    plugin_id = args.plugin_id
    max_results = args.max_results
    fetch_all = args.fetch_all

    async with UnitOfWorkFactory.get_uow(organization_id=org_id) as uow:
        plugins_service = ServiceFactory.create_service(ServiceType.PLUGINS, uow, has_system_access=True)
        sources_service = ServiceFactory.create_service(ServiceType.SOURCES, uow, has_system_access=True)
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
        # IMPORTANT: Uses existing plugins_service within same UoW context
        # Does NOT commit - outer UoW handles transaction
        async def on_tokens_refreshed(new_access_token: str, new_refresh_token: str) -> None:
            """Update plugin credentials with new tokens after refresh."""
            print(f"DEBUG: Updating plugin {plugin_id} credentials with refreshed tokens")
            updated_creds = {
                **(plugin.credentials or {}),
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_obtained_at": datetime.now().isoformat(),
            }
            # Update plugin in database using existing service/UoW (no commit here)
            plugin.credentials = updated_creds
            await plugins_service.update_item(plugin_id, plugin)
            print("DEBUG: Plugin credentials updated successfully")

        source = await _ensure_source(
            sources_service,
            organization_id=org_id,
            plugin_id=plugin_id,
            user_id=user_id,
        )
        # Access display_name while still in async context to avoid lazy-loading issues
        source_display_name = source.display_name

        async with XUserClient(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            token_obtained_at=token_obtained_at,
            expires_in=expires_in,
            on_tokens_refreshed=on_tokens_refreshed,
        ) as x_user_client:
            # Use the authenticated X user's ID, not the command-line user_id
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
                contents = _map_posts_to_content(posts, organization_id=org_id, source_id=source.id)  # type: ignore[arg-type]
                result = await contents_service.create_items_with_results(contents)
                created_count = len(result.created)
                failed_count = len(result.failed)
                total_created += created_count
                total_failed += failed_count
                print(
                    f"Page {page_num}: created={created_count}, failed={failed_count}"
                    + (f" (errors: {[f.error for f in result.failed]})" if failed_count else "")
                )

            print(
                f"Imported {total_created} bookmark(s) into content for source '{source_display_name}'. "
                f"Failed: {total_failed}."
            )


if __name__ == "__main__":
    asyncio.run(main())
