from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from fury_api.domain import paths
from fury_api.domain.users.models import User
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
) -> Plugin:
    payload = plugin.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
    payload["organization_id"] = current_user.organization_id
    # Set default empty dicts if not provided
    if "credentials" not in payload or payload["credentials"] is None:
        payload["credentials"] = {}
    if "properties" not in payload or payload["properties"] is None:
        payload["properties"] = {}
    converted_plugin = Plugin.model_validate(payload)
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
