import asyncio
from datetime import datetime

from fury_api.lib.celery_app import celery_app
from ..base import FuryBaseTask
from fury_api.domain.plugins.models import Plugin
from fury_api.lib.integrations.x_user import XUserClient


@celery_app.task(
    name="datasync.x.bookmarks.fetch_all",
    bind=True,
    base=FuryBaseTask,
    queue="datasync",
    time_limit=1800,  # 30 mins
    soft_time_limit=1700,
)
def fetch_all_x_bookmarks(self, organization_id: int, plugin_id: int):
    """Background task to fetch all X bookmarks for a plugin."""
    return asyncio.run(_fetch_all_x_bookmarks_async(organization_id=organization_id, plugin_id=plugin_id))


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


async def _fetch_all_x_bookmarks_async(organization_id: int, plugin_id: int):
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

        # 2. Get/Create Collection
        collection = await collections_service.get_or_create_all_x_bookmarks_collection(plugin_id)

        created_total = 0
        failed_total = 0
        synced_total = 0

        async with XUserClient(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            token_obtained_at=token_obtained_at,
            expires_in=expires_in,
            on_tokens_refreshed=on_tokens_refreshed,
        ) as x_client:
            # 3. Iterate All Pages
            pagination_token = None
            while True:
                response = await x_client.get_bookmarks(
                    user_id=x_user_id,
                    pagination_token=pagination_token,
                    max_results=100,
                )
                posts = response.data or []

                # If no posts on this page, try next page or break
                if not posts:
                    if not response.meta or not response.meta.next_token:
                        break
                    pagination_token = response.meta.next_token
                    continue

                # 4. Sync Authors (Batch)
                author_map = await authors_service.ensure_x_authors_batch(posts)

                # 5. Prepare Content Objects
                items_to_create = []
                for post in posts:
                    author_id = author_map.get(post.author_id)
                    if author_id:
                        content = contents_service.convert_x_content_payload(post, author_id)
                        items_to_create.append(content)

                if items_to_create:
                    # 6. Bulk Create & Handle Duplicates
                    result = await contents_service.create_items_with_insertion_results(items_to_create)

                    created_count = len(result.created)
                    failed_count = len(result.failed)  # Duplicates usually
                    created_total += created_count
                    failed_total += failed_count

                    # 7. Link to Collection
                    items_to_link = list(result.created)

                    # Handle duplicates: fetch existing IDs to link them too
                    if result.failed:
                        failed_ids = [f.external_id for f in result.failed if f.external_id]
                        if failed_ids:
                            existing = await contents_service.get_by_external_ids(failed_ids)
                            items_to_link.extend(existing)

                    await content_collections_service.link_items_to_collection(items_to_link, collection.id)
                    synced_total += len(items_to_link)

                pagination_token = response.meta.next_token if response.meta else None
                if not pagination_token:
                    break

        return {
            "plugin_id": plugin_id,
            "organization_id": organization_id,
            "created_count": created_total,
            "duplicate_count": failed_total,
            "linked_count": synced_total,
            "status": "completed",
        }
