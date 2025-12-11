import asyncio
from datetime import datetime

from fury_api.lib.celery_app import celery_app
from ..base import FuryBaseTask
from fury_api.domain.plugins.models import Plugin
from fury_api.domain.content.enums import Platform
from fury_api.domain.collections.models import CollectionType
from fury_api.lib.integrations.x_user import XUserClient


@celery_app.task(
    name="datasync.x.bookmark_folders.sync",
    bind=True,
    base=FuryBaseTask,
    queue="datasync",
    time_limit=900,
    soft_time_limit=870,
)
def sync_x_bookmark_folders(self, organization_id: int, plugin_id: int):
    """Background task to sync X bookmark folders for a plugin."""
    return asyncio.run(_sync_x_bookmark_folders_async(organization_id=organization_id, plugin_id=plugin_id))


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


async def _sync_x_bookmark_folders_async(organization_id: int, plugin_id: int):
    from fury_api.lib.factories import UnitOfWorkFactory, ServiceFactory
    from fury_api.lib.factories.service_factory import ServiceType

    async with UnitOfWorkFactory.get_uow(organization_id=organization_id) as uow:
        plugins_service = ServiceFactory.create_service(ServiceType.PLUGINS, uow, has_system_access=True)
        collections_service = ServiceFactory.create_service(ServiceType.COLLECTIONS, uow, has_system_access=True)

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

        folder_count = 0

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
                response = await x_client.get_bookmark_folders(
                    user_id=x_user_id,
                    pagination_token=pagination_token,
                    max_results=100,
                )
                folders = response.data or []

                for folder in folders:
                    await collections_service.get_or_create_platform_collection(
                        platform=Platform.X.value,
                        type=CollectionType.BOOKMARK_FOLDER.value,
                        name=folder.name,
                        external_id=folder.id,
                        plugin_id=plugin_id,
                    )
                    folder_count += 1

                pagination_token = response.meta.next_token if response.meta else None
                if not pagination_token:
                    break

        return {
            "plugin_id": plugin_id,
            "organization_id": organization_id,
            "folder_count": folder_count,
            "status": "completed",
        }
