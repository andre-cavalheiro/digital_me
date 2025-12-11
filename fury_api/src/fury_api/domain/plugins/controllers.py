from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body

from fury_api.domain import paths
from fury_api.domain.users.models import User
from fury_api.domain.jobs.services import JobsService
from fury_api.domain.jobs.models import TaskInfo
from fury_api.lib.dependencies import (
    FiltersAndSortsParser,
    ServiceType,
    get_models_filters_parser_factory,
    get_service,
    get_uow_tenant,
    get_uow_tenant_ro,
)
from . import exceptions
from .models import (
    Plugin,
    PluginCreate,
    PluginRead,
    PluginUpdate,
)
from fury_api.lib.security import get_current_user
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from .services import PluginsService
from fury_api.lib.model_filters import ModelFilterAndSortDefinition, get_default_ops_for_type

plugin_router = APIRouter()

PLUGINS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Plugin,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "title": get_default_ops_for_type(str),
        "data_source": get_default_ops_for_type(str),
    },
    allowed_sorts={"id", "title", "data_source"},
)


@plugin_router.post(paths.PLUGINS, response_model=PluginRead, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    plugin: PluginCreate,
    plugin_service: Annotated[
        PluginsService,
        Depends(
            get_service(
                ServiceType.PLUGINS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> PluginRead:
    plugin_data = plugin.model_dump()
    plugin_data["organization_id"] = current_user.organization_id
    converted_plugin = Plugin.model_validate(plugin_data)
    return await plugin_service.create_item(converted_plugin)


@plugin_router.get(paths.PLUGINS, response_model=CursorPage[PluginRead])
async def get_items(
    plugin_service: Annotated[
        PluginsService,
        Depends(
            get_service(
                ServiceType.PLUGINS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(PLUGINS_FILTERS_DEFINITION))
    ],
) -> CursorPage[PluginRead]:
    return await plugin_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@plugin_router.get(paths.PLUGINS_ID, response_model=PluginRead)
async def get_item(
    id_: int,
    plugin_service: Annotated[
        PluginsService,
        Depends(
            get_service(
                ServiceType.PLUGINS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> PluginRead:
    plugin = await plugin_service.get_item(id_)
    if not plugin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")
    return plugin


@plugin_router.put(paths.PLUGINS_ID, response_model=PluginRead)
async def update_item(
    id_: int,
    plugin_update: PluginUpdate,
    plugin_service: Annotated[
        PluginsService,
        Depends(get_service(ServiceType.PLUGINS)),
    ],
) -> Plugin:
    plugin = await plugin_service.get_item(id_)
    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    try:
        updated_plugin = await plugin_service.update_item(id_, plugin_update)
        return updated_plugin
    except exceptions.PluginError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@plugin_router.delete(paths.PLUGINS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    id_: int,
    plugin_service: Annotated[
        PluginsService,
        Depends(get_service(ServiceType.PLUGINS)),
    ],
) -> None:
    plugin = await plugin_service.get_item(id_)
    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    try:
        await plugin_service.delete_item(plugin)
    except exceptions.PluginError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@plugin_router.post(paths.PLUGINS_ID_TRIGGER_JOB, response_model=TaskInfo, status_code=status.HTTP_202_ACCEPTED)
async def trigger_plugin_job(
    id_: int,
    request: dict[str, Any] = Body(...),
    plugin_service: PluginsService = Depends(
        get_service(ServiceType.PLUGINS, read_only=True, uow=Depends(get_uow_tenant_ro))
    ),
    jobs_service: JobsService = Depends(lambda: JobsService()),
) -> TaskInfo:
    """Trigger a background job for a plugin."""
    plugin = await plugin_service.get_item(id_)
    if not plugin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    job_type = request.get("job_type")
    job_params = request.get("job_params", {})

    if not job_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="job_type is required")

    # Map job types to Celery tasks
    task_map = {
        "x": {
            "fetch_all_bookmarks": "datasync.x.bookmarks.fetch_all",
            "sync_folders": "datasync.x.bookmark_folders.sync",
            "fetch_folder_content": "datasync.x.bookmark_folders.fetch_content",
        }
    }

    if plugin.data_source not in task_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"No jobs available for data source '{plugin.data_source}'"
        )

    if job_type not in task_map[plugin.data_source]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job type '{job_type}' for {plugin.data_source}. Valid types: {', '.join(task_map[plugin.data_source].keys())}",
        )

    task_name = task_map[plugin.data_source][job_type]

    # Merge default params with request params
    params = {"plugin_id": plugin.id, **job_params}

    # Validate required params for specific jobs
    if job_type == "fetch_folder_content" and "collection_id" not in params:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="collection_id is required for fetch_folder_content job"
        )

    return jobs_service.push_task(task_name=task_name, organization_id=plugin.organization_id, **params)
