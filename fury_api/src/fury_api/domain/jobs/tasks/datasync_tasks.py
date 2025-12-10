import asyncio
from fury_api.lib.celery_app import celery_app
from .base import FuryBaseTask


@celery_app.task(
    name="datasync.x.bookmarks.sync",
    bind=True,
    base=FuryBaseTask,
    queue="datasync",
    time_limit=900,
    soft_time_limit=870,
)
def sync_x_bookmarks(self, organization_id: int, plugin_id: int, max_results: int = 100, fetch_all: bool = False):
    """Background task to sync X bookmarks for a plugin."""
    return asyncio.run(
        _sync_x_bookmarks_async(
            organization_id=organization_id, plugin_id=plugin_id, max_results=max_results, fetch_all=fetch_all
        )
    )


async def _sync_x_bookmarks_async(organization_id: int, plugin_id: int, max_results: int, fetch_all: bool):
    """
    Async wrapper for X bookmarks sync.

    TODO: Refactor import_x_bookmarks.py logic into reusable async functions
    and implement the full sync logic here.
    """
    from fury_api.lib.factories import UnitOfWorkFactory, ServiceFactory
    from fury_api.lib.factories.service_factory import ServiceType

    async with UnitOfWorkFactory.get_uow(organization_id=organization_id) as uow:
        plugins_service = ServiceFactory.create_service(ServiceType.PLUGINS, uow, has_system_access=True)

        plugin = await plugins_service.get_item(plugin_id)
        if not plugin:
            raise ValueError(f"Plugin {plugin_id} not found")

        # TODO: Import and run sync logic from import_x_bookmarks.py
        # For now, return a placeholder response

        return {
            "plugin_id": plugin_id,
            "organization_id": organization_id,
            "synced_count": 0,
            "failed_count": 0,
            "status": "TODO: Implement X bookmarks sync",
        }
