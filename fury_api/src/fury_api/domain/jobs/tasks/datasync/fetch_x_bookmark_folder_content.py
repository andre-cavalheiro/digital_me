import asyncio
from datetime import datetime

from fury_api.lib.celery_app import celery_app
from ..base import FuryBaseTask
from fury_api.domain.plugins.models import Plugin
from fury_api.domain.collections.models import CollectionType
from fury_api.lib.integrations.x_user import XUserClient


@celery_app.task(
    name="datasync.x.bookmark_folders.fetch_content",
    bind=True,
    base=FuryBaseTask,
    queue="datasync",
    time_limit=1800,  # 30 mins
    soft_time_limit=1700,
)
def fetch_x_bookmark_folder_content(self, organization_id: int, plugin_id: int, collection_id: int):
    """Background task to fetch content for a specific X bookmark folder."""
    return asyncio.run(
        _fetch_x_bookmark_folder_content_async(
            organization_id=organization_id, plugin_id=plugin_id, collection_id=collection_id
        )
    )


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


async def _fetch_x_bookmark_folder_content_async(organization_id: int, plugin_id: int, collection_id: int):
    from fury_api.lib.factories import UnitOfWorkFactory, ServiceFactory
    from fury_api.lib.factories.service_factory import ServiceType

    async with UnitOfWorkFactory.get_uow(organization_id=organization_id) as uow:
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

        collection = await collections_service.get_item(collection_id)
        if not collection:
            raise ValueError(f"Collection {collection_id} not found")

        if collection.type != CollectionType.BOOKMARK_FOLDER.value:
            raise ValueError(f"Collection {collection_id} is not a bookmark folder")

        folder_external_id = collection.external_id

        # Also ensure "All Bookmarks" collection exists to link everything there too
        all_bookmarks_collection = await collections_service.get_or_create_all_x_bookmarks_collection(plugin_id)

        access_token, refresh_token, token_type, token_obtained_at, expires_in = _extract_tokens(plugin)
        if not access_token and not refresh_token:
            raise ValueError("Plugin credentials must include access_token or refresh_token for X user auth")

        x_user_id = plugin.properties.get("x_user_id") if plugin.properties else None
        if not x_user_id:
            raise ValueError(f"Plugin {plugin_id} is missing x_user_id in properties. Re-authorize the X integration.")

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

        created_total = 0
        linked_total = 0

        async with XUserClient(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            token_obtained_at=token_obtained_at,
            expires_in=expires_in,
            on_tokens_refreshed=on_tokens_refreshed,
        ) as x_client:
            pagination_token = None
            while True:
                # 1. Get IDs from folder
                response = await x_client.get_bookmarks_by_folder(
                    user_id=x_user_id,
                    folder_id=folder_external_id,
                    pagination_token=pagination_token,
                )
                bookmark_items = response.data or []
                if not bookmark_items:
                    if not response.meta or not response.meta.next_token:
                        break
                    pagination_token = response.meta.next_token
                    continue

                page_ids = [item.id for item in bookmark_items]

                # 2. Filter Existing
                existing_contents = await contents_service.get_by_external_ids(page_ids)
                existing_ids = {c.external_id for c in existing_contents}
                missing_ids = [pid for pid in page_ids if pid not in existing_ids]

                # 3. Fetch New
                new_contents = []
                if missing_ids:
                    # Batch fetch if needed (X API allows up to 100, page size is usually 100 too, but good to be safe)
                    # We'll just do one call for now as pages are small
                    tweets_response = await x_client.get_tweets_by_ids(ids=missing_ids)
                    posts = tweets_response.data or []

                    if posts:
                        # 4. Process New
                        author_map = await authors_service.ensure_x_authors_batch(posts)

                        items_to_create = []
                        for post in posts:
                            author_id = author_map.get(post.author_id)
                            if author_id:
                                content = contents_service.convert_x_content_payload(post, author_id)
                                items_to_create.append(content)

                        if items_to_create:
                            result = await contents_service.create_items_with_insertion_results(items_to_create)
                            new_contents = result.created
                            created_total += len(new_contents)
                            # Add any failed (duplicates race condition) to existing list logic if needed,
                            # but filtering above should handle most.
                            if result.failed:
                                # If creation failed, they might exist now, so fetch them to link
                                failed_ids = [f.external_id for f in result.failed if f.external_id]
                                if failed_ids:
                                    recovered = await contents_service.get_by_external_ids(failed_ids)
                                    existing_contents.extend(recovered)

                # 5. Link ALL
                all_items_to_link = existing_contents + new_contents
                if all_items_to_link:
                    # Link to the folder collection
                    await content_collections_service.link_items_to_collection(all_items_to_link, collection.id)
                    # Link to the "All Bookmarks" collection
                    await content_collections_service.link_items_to_collection(
                        all_items_to_link, all_bookmarks_collection.id
                    )
                    linked_total += len(all_items_to_link)

                pagination_token = response.meta.next_token if response.meta else None
                if not pagination_token:
                    break

        return {
            "plugin_id": plugin_id,
            "organization_id": organization_id,
            "collection_id": collection_id,
            "created_count": created_total,
            "linked_count": linked_total,
            "status": "completed",
        }
