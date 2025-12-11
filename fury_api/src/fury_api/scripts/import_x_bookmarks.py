#!/usr/bin/env python3
"""
Import X bookmarks using background task logic.

Usage:
    python import_x_bookmarks.py --organization-id 1 --plugin-id 1 [--fetch-all-bookmarks] [--fetch-folders]
"""

from __future__ import annotations

import argparse
import asyncio

from fury_api.lib.factories import ServiceFactory, UnitOfWorkFactory
from fury_api.lib.factories.service_factory import ServiceType
from fury_api.domain.collections.models import CollectionType

# Import async task implementations
from fury_api.domain.jobs.tasks.datasync.fetch_all_x_bookmarks import _fetch_all_x_bookmarks_async
from fury_api.domain.jobs.tasks.datasync.sync_x_bookmark_folders import _sync_x_bookmark_folders_async
from fury_api.domain.jobs.tasks.datasync.fetch_x_bookmark_folder_content import _fetch_x_bookmark_folder_content_async


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import X bookmarks for a user")
    parser.add_argument("--organization-id", type=int, required=True, help="Organization ID")
    parser.add_argument("--plugin-id", type=int, required=True, help="Plugin ID containing X credentials")
    parser.add_argument(
        "--fetch-all-bookmarks",
        action="store_true",
        help="Fetch all bookmarks from the main endpoint",
    )
    parser.add_argument(
        "--fetch-folders",
        action="store_true",
        help="Sync bookmark folders and their content",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    org_id = args.organization_id
    plugin_id = args.plugin_id
    fetch_all_bookmarks = args.fetch_all_bookmarks
    fetch_folders = args.fetch_folders

    print(f"Starting X Bookmarks Import for Org {org_id}, Plugin {plugin_id}")

    if fetch_all_bookmarks:
        print("\n--- Starting 'All Bookmarks' Sync ---")
        try:
            result = await _fetch_all_x_bookmarks_async(
                organization_id=org_id,
                plugin_id=plugin_id,
            )
            print("Result:", result)
        except Exception as e:
            print(f"Error fetching all bookmarks: {e}")

    if fetch_folders:
        print("\n--- Starting Folder Sync ---")
        try:
            # 1. Sync Folder Collections
            folder_result = await _sync_x_bookmark_folders_async(
                organization_id=org_id,
                plugin_id=plugin_id,
            )
            print("Folder Sync Result:", folder_result)

            # 2. Sync Content for Each Folder
            async with UnitOfWorkFactory.get_uow(organization_id=org_id) as uow:
                collections_service = ServiceFactory.create_service(
                    ServiceType.COLLECTIONS, uow, has_system_access=True
                )

                # Fetch all bookmark folder collections for this plugin
                # Using list() or filter on repo - for simplicity here using a manual filter after fetching platform collections
                # Ideally we'd have a specific query, but iterating is fine for script scale

                # Using a direct query helper if available, or just generic list
                # Since we don't have a specific "get_by_type_and_plugin" exposed easily in service without filter construction,
                # let's use the service's filtering capabilities if possible, or raw SQL if needed.
                # Actually, `collections_service.get_by_platform_name` is singular.
                # Let's use `list` with generic filters if supported, or simpler:
                # Just re-fetch folders from DB that match our criteria.

                # We can use the repository directly or just trust the service has list methods.
                # Let's construct a simple filter if the service supports it.
                # The generic service supports `model_filters`.

                # Simpler approach for script: iterate all collections for organization and filter in python (bad for prod, ok for script test)
                # BETTER: Use a query.

                from fury_api.lib.model_filters import Filter

                # Filter by plugin_id and type
                collections_page = await collections_service.list_with_pagination(
                    uow.session,
                    filter_context={"organization_id": org_id},
                    model_filters=[
                        Filter(field="plugin_id", op="eq", value=plugin_id),
                        Filter(field="type", op="eq", value=CollectionType.BOOKMARK_FOLDER.value),
                    ],
                    limit=1000,  # Assume < 1000 folders
                )

                collections = collections_page.items
                print(f"Found {len(collections)} folders to sync content for.")

            for collection in collections:
                print(f"\nSyncing content for folder: {collection.name} ({collection.id})")
                try:
                    content_result = await _fetch_x_bookmark_folder_content_async(
                        organization_id=org_id, plugin_id=plugin_id, collection_id=collection.id
                    )
                    print(f"Folder '{collection.name}' Result:", content_result)
                except Exception as e:
                    print(f"Error syncing folder '{collection.name}': {e}")

        except Exception as e:
            print(f"Error during folder sync: {e}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
