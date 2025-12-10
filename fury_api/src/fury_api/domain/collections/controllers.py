from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from fury_api.domain import paths
from fury_api.domain.users.models import User
from fury_api.domain.content.services import ContentsService
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
    Collection,
    CollectionCreate,
    CollectionRead,
    CollectionAuthorStatistics,
    ContentCollection,
    ContentCollectionLinkRequest,
)
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from fury_api.lib.security import get_current_user
from fury_api.lib.model_filters.models import Filter, FilterOp
from .services import CollectionsService, ContentCollectionsService
from fury_api.lib.model_filters import ModelFilterAndSortDefinition, get_default_ops_for_type

collections_router = APIRouter()

COLLECTIONS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Collection,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "platform_type": get_default_ops_for_type(str),
        "name": get_default_ops_for_type(str),
    },
    allowed_sorts={"id", "platform_type", "name", "created_at"},
)


@collections_router.post(paths.COLLECTIONS, response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection: CollectionCreate,
    collection_service: Annotated[
        CollectionsService,
        Depends(
            get_service(
                ServiceType.COLLECTIONS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CollectionRead:
    collection_data = collection.model_dump()
    collection_data["organization_id"] = current_user.organization_id
    converted_collection = Collection.model_validate(collection_data)
    return await collection_service.create_item(converted_collection)


@collections_router.get(paths.COLLECTIONS, response_model=CursorPage[CollectionRead])
async def get_collections(
    collections_service: Annotated[CollectionsService, Depends(get_service(ServiceType.COLLECTIONS, read_only=True))],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(COLLECTIONS_FILTERS_DEFINITION))
    ],
    platform_type: str | None = Query(None, description="Filter by platform type"),
) -> CursorPage[CollectionRead]:
    """List all collections with optional filtering."""
    filters = filters_parser.filters

    # Add platform_type filter if provided
    if platform_type:
        filters.append(Filter(field="platform_type", op=FilterOp.EQ, value=platform_type, field_type=str))

    return await collections_service.get_items_paginated(
        model_filters=filters,
        model_sorts=filters_parser.sorts,
    )


@collections_router.get(paths.COLLECTIONS_ID, response_model=CollectionRead)
async def get_collection(
    id_: Annotated[int, paths.COLLECTIONS_ID_PARAM],
    collections_service: Annotated[CollectionsService, Depends(get_service(ServiceType.COLLECTIONS, read_only=True))],
) -> Collection:
    """Get a specific collection by ID."""
    collection = await collections_service.get_item(id_)
    if not collection:
        raise exceptions.CollectionNotFoundError(id_)
    return collection


@collections_router.get(paths.COLLECTIONS_ID_AUTHOR_STATISTICS, response_model=CollectionAuthorStatistics)
async def get_collection_author_statistics(
    id_: Annotated[int, paths.COLLECTIONS_ID_PARAM],
    collections_service: Annotated[CollectionsService, Depends(get_service(ServiceType.COLLECTIONS, read_only=True))],
) -> CollectionAuthorStatistics:
    """Get author contribution statistics for a specific collection."""
    # Verify collection exists
    collection = await collections_service.get_item(id_)
    if not collection:
        raise exceptions.CollectionNotFoundError(id_)

    return await collections_service.get_author_statistics(id_)


@collections_router.post(
    paths.COLLECTIONS_ID_CONTENT,
    response_model=ContentCollection,
    status_code=status.HTTP_201_CREATED,
)
async def link_content_to_collection(
    id_: Annotated[int, paths.COLLECTIONS_ID_PARAM],
    payload: ContentCollectionLinkRequest,
    collections_service: Annotated[
        CollectionsService,
        Depends(get_service(ServiceType.COLLECTIONS, read_only=True, uow=Depends(get_uow_tenant_ro))),
    ],
    contents_service: Annotated[
        ContentsService,
        Depends(get_service(ServiceType.CONTENTS, read_only=True, uow=Depends(get_uow_tenant_ro))),
    ],
    content_collections_service: Annotated[
        ContentCollectionsService,
        Depends(get_service(ServiceType.CONTENT_COLLECTIONS, read_only=False, uow=Depends(get_uow_tenant))),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContentCollection:
    """Link an existing content item to a collection for the current organization."""
    collection = await collections_service.get_item(id_)
    if collection is None or collection.organization_id != current_user.organization_id:
        raise exceptions.CollectionNotFoundError(id_)

    content = await contents_service.get_item(payload.content_id)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    try:
        return await content_collections_service.link_content_to_collection(
            content_id=payload.content_id,
            collection_id=id_,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
