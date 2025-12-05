from typing import Annotated

from fastapi import APIRouter, Depends, Query

from fury_api.domain import paths
from fury_api.domain.content.models import ContentRead
from fury_api.domain.content.services import ContentsService
from fury_api.domain.content.controllers import CONTENTS_FILTERS_DEFINITION
from fury_api.lib.dependencies import (
    FiltersAndSortsParser,
    ServiceType,
    get_models_filters_parser_factory,
    get_service,
)
from . import exceptions
from .models import Collection, CollectionRead, CollectionAuthorStatistics
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
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


@collections_router.get(paths.COLLECTIONS_ID_CONTENT, response_model=CursorPage[ContentRead])
async def get_collection_content(
    id_: Annotated[int, paths.COLLECTIONS_ID_PARAM],
    collections_service: Annotated[CollectionsService, Depends(get_service(ServiceType.COLLECTIONS, read_only=True))],
    content_collections_service: Annotated[
        ContentCollectionsService, Depends(get_service(ServiceType.CONTENT_COLLECTIONS, read_only=True))
    ],
    contents_service: Annotated[ContentsService, Depends(get_service(ServiceType.CONTENTS, read_only=True))],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(CONTENTS_FILTERS_DEFINITION))
    ],
) -> CursorPage[ContentRead]:
    """Get all content in a specific collection."""
    # Verify collection exists
    collection = await collections_service.get_item(id_)
    if not collection:
        raise exceptions.CollectionNotFoundError(id_)

    # Get content IDs for this collection
    content_ids = await content_collections_service.get_content_for_collection(id_)

    if not content_ids:
        # Return empty page if no content in collection
        return CursorPage(items=[], next_cursor=None)

    # Add content ID filter to the parsed filters
    filters_parser.add_filter(Filter(field="id", op=FilterOp.IN, value=content_ids, field_type=int))

    return await contents_service.get_items_paginated(
        model_filters=filters_parser.filters,
        model_sorts=filters_parser.sorts,
    )


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
