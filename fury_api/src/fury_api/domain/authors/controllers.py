from typing import Annotated

from fastapi import APIRouter, Depends, Query

from fury_api.domain import paths
from fury_api.domain.content.models import ContentRead
from fury_api.domain.content.services import ContentsService
from fury_api.lib.dependencies import (
    FiltersAndSortsParser,
    ServiceType,
    get_models_filters_parser_factory,
    get_service,
)
from . import exceptions
from .models import Author, AuthorRead
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from fury_api.lib.model_filters.models import Filter, FilterOp
from .services import AuthorsService
from fury_api.lib.model_filters import ModelFilterAndSortDefinition, get_default_ops_for_type

authors_router = APIRouter()

AUTHORS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Author,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "platform": get_default_ops_for_type(str),
        "handle": get_default_ops_for_type(str),
    },
    allowed_sorts={"id", "platform", "display_name", "created_at"},
)


# Authors endpoints


@authors_router.get(paths.AUTHORS, response_model=CursorPage[AuthorRead])
async def get_authors(
    authors_service: Annotated[AuthorsService, Depends(get_service(ServiceType.AUTHORS, read_only=True))],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(AUTHORS_FILTERS_DEFINITION))
    ],
    platform_type: str | None = Query(None, description="Filter by platform type"),
) -> CursorPage[AuthorRead]:
    """List all authors with optional filtering."""
    filters = filters_parser.filters

    # Add platform_type filter if provided
    if platform_type:
        filters.append(Filter(field="platform_type", op=FilterOp.EQ, value=platform_type, field_type=str))

    return await authors_service.get_items_paginated(
        model_filters=filters,
        model_sorts=filters_parser.sorts,
    )


@authors_router.get(paths.AUTHORS_ID, response_model=AuthorRead)
async def get_author(
    id_: Annotated[int, paths.AUTHORS_ID_PARAM],
    authors_service: Annotated[AuthorsService, Depends(get_service(ServiceType.AUTHORS, read_only=True))],
) -> Author:
    """Get a specific author by ID."""
    author = await authors_service.get_item(id_)
    if not author:
        raise exceptions.AuthorNotFoundError(id_)
    return author


@authors_router.get(paths.AUTHORS_ID_CONTENT, response_model=CursorPage[ContentRead])
async def get_author_content(
    id_: Annotated[int, paths.AUTHORS_ID_PARAM],
    authors_service: Annotated[AuthorsService, Depends(get_service(ServiceType.AUTHORS, read_only=True))],
    contents_service: Annotated[ContentsService, Depends(get_service(ServiceType.CONTENTS, read_only=True))],
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
) -> CursorPage[ContentRead]:
    """Get all content by a specific author."""
    # Verify author exists
    author = await authors_service.get_item(id_)
    if not author:
        raise exceptions.AuthorNotFoundError(id_)

    # Get content filtered by this author
    filters = [Filter(field="author_id", op=FilterOp.EQ, value=id_, field_type=int)]

    return await contents_service.get_items_paginated(
        model_filters=filters,
        model_sorts=[],
        limit=limit,
    )
