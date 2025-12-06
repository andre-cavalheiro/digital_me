from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from fury_api.domain import paths
from fury_api.domain.users.models import User
from fury_api.lib.dependencies import (
    FiltersAndSortsParser,
    ServiceType,
    get_models_filters_parser_factory,
    get_service,
    get_ai_client,
    get_uow_tenant,
    get_uow_tenant_ro,
)
from fury_api.lib.integrations.base_ai import BaseAIClient
from . import exceptions
from .models import (
    Content,
    ContentBulkCreate,
    ContentBulkResult,
    ContentCreate,
    ContentRead,
    ContentSearchRequest,
)
from fury_api.lib.security import get_current_user
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from .services import ContentsService
from fury_api.lib.model_filters import ModelFilterAndSortDefinition, get_default_ops_for_type

content_router = APIRouter()

CONTENTS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Content,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "author_id": get_default_ops_for_type(int),
        "published_at": get_default_ops_for_type(str),
        "collection_id": get_default_ops_for_type(int),
    },
    allowed_sorts={"id", "author_id", "published_at", "synced_at", "created_at"},
)


@content_router.get(paths.CONTENTS, response_model=CursorPage[ContentRead])
async def get_content_items(
    content_service: Annotated[
        ContentsService,
        Depends(
            get_service(
                ServiceType.CONTENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(CONTENTS_FILTERS_DEFINITION))
    ],
    include: str | None = None,
) -> CursorPage[ContentRead]:
    # Parse include parameter
    include_author = bool(include and "author" in include.split(","))

    return await content_service.get_items_paginated(
        model_filters=filters_parser.filters,
        model_sorts=filters_parser.sorts,
        include_author=include_author,
    )


@content_router.get(paths.CONTENTS_ID, response_model=ContentRead)
async def get_content_item(
    id_: int,
    content_service: Annotated[
        ContentsService,
        Depends(
            get_service(
                ServiceType.CONTENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> ContentRead:
    content = await content_service.get_item(id_)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    return content


@content_router.post(paths.CONTENTS, response_model=ContentRead, status_code=status.HTTP_201_CREATED)
async def create_content_item(
    content_data: ContentCreate,
    content_service: Annotated[
        ContentsService,
        Depends(
            get_service(
                ServiceType.CONTENTS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Content:
    payload = content_data.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
    converted_content = Content.model_validate(payload)
    return await content_service.create_item(converted_content)


@content_router.post(paths.CONTENTS_BATCH, response_model=ContentBulkResult, status_code=status.HTTP_201_CREATED)
async def create_content_items(
    content_data: ContentBulkCreate,
    content_service: Annotated[
        ContentsService,
        Depends(
            get_service(
                ServiceType.CONTENTS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> ContentBulkResult:
    items: list[Content] = []
    for item in content_data.items:
        payload = item.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
        items.append(Content.model_validate(payload))

    return await content_service.create_items_with_results(items)


@content_router.delete(paths.CONTENTS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_item(
    id_: int,
    content_service: Annotated[
        ContentsService,
        Depends(get_service(ServiceType.CONTENTS)),
    ],
) -> None:
    content = await content_service.get_item(id_)
    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    try:
        await content_service.delete_item(content)
    except exceptions.ContentError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@content_router.post(paths.CONTENT_SEARCH, response_model=list[ContentRead])
async def search_content(
    search: ContentSearchRequest,
    content_service: Annotated[
        ContentsService,
        Depends(
            get_service(
                ServiceType.CONTENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    ai_client: Annotated[BaseAIClient, Depends(get_ai_client)],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(CONTENTS_FILTERS_DEFINITION))
    ],
    include: str | None = None,
) -> list[ContentRead]:
    # Parse include parameter
    include_author = bool(include and "author" in include.split(","))

    return await content_service.semantic_search(
        search,
        ai_client=ai_client,
        model_filters=filters_parser.filters,
        filter_combine_logic=filters_parser.filter_logic,
        include_author=include_author,
    )
