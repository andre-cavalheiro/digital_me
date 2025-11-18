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
    Citation,
    CitationCreate,
    CitationRead,
    CitationUpdate,
    Content,
    ContentCreate,
    ContentRead,
    DocumentSourceConfig,
    DocumentSourceConfigRead,
    Source,
    SourceCreate,
    SourceRead,
    SourceUpdate,
    SourceGroup,
    SourceGroupCreate,
    SourceGroupRead,
    SourceGroupUpdate,
    SourceGroupMember,
    SourceGroupMemberCreate,
    SourceGroupMemberRead,
)
from fury_api.lib.security import get_current_user
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from fury_api.lib.model_filters.models import Filter, FilterOp
from .services import (
    CitationsService,
    ContentsService,
    DocumentSourceConfigsService,
    SourceGroupMembersService,
    SourceGroupsService,
    SourcesService,
)
from fury_api.lib.model_filters import ModelFilterAndSortDefinition, get_default_ops_for_type

sources_router = APIRouter()

SOURCES_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Source,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "platform_type": get_default_ops_for_type(str),
        "is_active": get_default_ops_for_type(bool),
    },
    allowed_sorts={"id", "platform_type", "is_active", "created_at"},
)

CONTENTS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Content,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "source_id": get_default_ops_for_type(int),
        "published_at": get_default_ops_for_type(str),
    },
    allowed_sorts={"id", "source_id", "published_at", "synced_at", "created_at"},
)

SOURCE_GROUPS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=SourceGroup,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "name": get_default_ops_for_type(str),
    },
    allowed_sorts={"id", "name", "created_at"},
)

SOURCE_GROUP_MEMBERS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=SourceGroupMember,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "source_group_id": get_default_ops_for_type(int),
        "source_id": get_default_ops_for_type(int),
    },
    allowed_sorts={"id", "source_group_id", "source_id", "added_at"},
)

DOCUMENT_SOURCE_CONFIGS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=DocumentSourceConfig,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "document_id": get_default_ops_for_type(int),
    },
    allowed_sorts={"id", "document_id", "added_at"},
)

CITATIONS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Citation,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "document_id": get_default_ops_for_type(int),
    },
    allowed_sorts={"id", "document_id", "citation_number", "created_at"},
)


# Sources
@sources_router.post(paths.SOURCES, response_model=SourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    source: SourceCreate,
    source_service: Annotated[
        SourcesService,
        Depends(
            get_service(
                ServiceType.SOURCES,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Source:
    payload = source.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
    payload["organization_id"] = current_user.organization_id
    payload["user_id"] = current_user.id
    converted_source = Source.model_validate(payload)
    return await source_service.create_item(converted_source)


@sources_router.get(paths.SOURCES, response_model=CursorPage[SourceRead])
async def get_sources(
    source_service: Annotated[
        SourcesService,
        Depends(
            get_service(
                ServiceType.SOURCES,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(SOURCES_FILTERS_DEFINITION))
    ],
) -> CursorPage[SourceRead]:
    return await source_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@sources_router.get(paths.SOURCES_ID, response_model=SourceRead)
async def get_source(
    id_: int,
    source_service: Annotated[
        SourcesService,
        Depends(
            get_service(
                ServiceType.SOURCES,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> SourceRead:
    source = await source_service.get_item(id_)
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@sources_router.patch(paths.SOURCES_ID, response_model=SourceRead)
async def update_source(
    id_: int,
    source_update: SourceUpdate,
    source_service: Annotated[
        SourcesService,
        Depends(get_service(ServiceType.SOURCES)),
    ],
) -> Source:
    source = await source_service.get_item(id_)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    try:
        updated_source = await source_service.update_item(id_, source_update)
        return updated_source
    except exceptions.SourceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@sources_router.delete(paths.SOURCES_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    id_: int,
    source_service: Annotated[
        SourcesService,
        Depends(get_service(ServiceType.SOURCES)),
    ],
) -> None:
    source = await source_service.get_item(id_)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    try:
        await source_service.delete_item(source)
    except exceptions.SourceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@sources_router.post(paths.SOURCE_SYNC, status_code=status.HTTP_202_ACCEPTED)
async def trigger_source_sync(
    id_: int,
    source_service: Annotated[
        SourcesService,
        Depends(get_service(ServiceType.SOURCES)),
    ],
) -> None:
    raise Exception("Not Implemented Yet")


@sources_router.get(paths.SOURCE_SYNC_STATUS)
async def get_source_sync_status(
    id_: int,
    source_service: Annotated[
        SourcesService,
        Depends(get_service(ServiceType.SOURCES, read_only=True)),
    ],
) -> dict:
    raise Exception("Not Implemented Yet")


@sources_router.get(paths.PLUGINS_AVAILABLE_SOURCES)
async def get_plugin_available_sources(
    id_: int,
    source_service: Annotated[
        SourcesService,
        Depends(get_service(ServiceType.SOURCES, read_only=True)),
    ],
) -> list[dict]:
    raise Exception("Not Implemented Yet")


# Content
@sources_router.get(paths.CONTENTS, response_model=CursorPage[ContentRead])
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
) -> CursorPage[ContentRead]:
    return await content_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@sources_router.get(paths.CONTENTS_ID, response_model=ContentRead)
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


@sources_router.post(paths.CONTENTS, response_model=ContentRead, status_code=status.HTTP_201_CREATED)
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
    # Create Content with organization_id from current user
    payload = content_data.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
    payload["organization_id"] = current_user.organization_id
    converted_content = Content.model_validate(payload)
    return await content_service.create_item(converted_content)


@sources_router.delete(paths.CONTENTS_ID, status_code=status.HTTP_204_NO_CONTENT)
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


@sources_router.post(paths.CONTENT_SEARCH, response_model=list[ContentRead])
async def search_content(
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
) -> list[ContentRead]:
    # Simple search: return all content (TODO: Add actual search logic with filters/query)
    # get_items() returns an async generator, so we need to consume it
    results = []
    async for item in content_service.get_items():
        results.append(item)
    return results


# Source Groups
@sources_router.post(paths.SOURCE_GROUPS, response_model=SourceGroupRead, status_code=status.HTTP_201_CREATED)
async def create_source_group(
    source_group: SourceGroupCreate,
    source_group_service: Annotated[
        SourceGroupsService,
        Depends(
            get_service(
                ServiceType.SOURCE_GROUPS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SourceGroup:
    converted_group = SourceGroup.model_validate(source_group)
    converted_group.organization_id = current_user.organization_id
    converted_group.user_id = current_user.id
    return await source_group_service.create_item(converted_group)


@sources_router.get(paths.SOURCE_GROUPS, response_model=CursorPage[SourceGroupRead])
async def get_source_groups(
    source_group_service: Annotated[
        SourceGroupsService,
        Depends(
            get_service(
                ServiceType.SOURCE_GROUPS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(SOURCE_GROUPS_FILTERS_DEFINITION))
    ],
) -> CursorPage[SourceGroupRead]:
    return await source_group_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@sources_router.get(paths.SOURCE_GROUPS_ID, response_model=SourceGroupRead)
async def get_source_group(
    id_: int,
    source_group_service: Annotated[
        SourceGroupsService,
        Depends(
            get_service(
                ServiceType.SOURCE_GROUPS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> SourceGroupRead:
    source_group = await source_group_service.get_item(id_)
    if not source_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source group not found")
    return source_group


@sources_router.patch(paths.SOURCE_GROUPS_ID, response_model=SourceGroupRead)
async def update_source_group(
    id_: int,
    source_group_update: SourceGroupUpdate,
    source_group_service: Annotated[
        SourceGroupsService,
        Depends(get_service(ServiceType.SOURCE_GROUPS)),
    ],
) -> SourceGroup:
    source_group = await source_group_service.get_item(id_)
    if source_group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source group not found")

    try:
        updated_group = await source_group_service.update_item(id_, source_group_update)
        return updated_group
    except exceptions.SourceGroupError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@sources_router.delete(paths.SOURCE_GROUPS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_source_group(
    id_: int,
    source_group_service: Annotated[
        SourceGroupsService,
        Depends(get_service(ServiceType.SOURCE_GROUPS)),
    ],
) -> None:
    source_group = await source_group_service.get_item(id_)
    if source_group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source group not found")

    try:
        await source_group_service.delete_item(source_group)
    except exceptions.SourceGroupError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@sources_router.post(
    paths.SOURCE_GROUP_MEMBERS, response_model=SourceGroupMemberRead, status_code=status.HTTP_201_CREATED
)
async def add_source_to_group(
    member: SourceGroupMemberCreate,
    source_group_member_service: Annotated[
        SourceGroupMembersService,
        Depends(
            get_service(
                ServiceType.SOURCE_GROUP_MEMBERS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> SourceGroupMember:
    converted_member = SourceGroupMember.model_validate(member)
    converted_member.organization_id = current_user.organization_id
    return await source_group_member_service.create_item(converted_member)


@sources_router.get(paths.SOURCE_GROUP_MEMBERS, response_model=CursorPage[SourceGroupMemberRead])
async def list_source_group_members(
    source_group_member_service: Annotated[
        SourceGroupMembersService,
        Depends(
            get_service(
                ServiceType.SOURCE_GROUP_MEMBERS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(SOURCE_GROUP_MEMBERS_FILTERS_DEFINITION))
    ],
) -> CursorPage[SourceGroupMemberRead]:
    return await source_group_member_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@sources_router.delete(paths.SOURCE_GROUP_MEMBERS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_source_group_member(
    id_: int,
    source_group_member_service: Annotated[
        SourceGroupMembersService,
        Depends(get_service(ServiceType.SOURCE_GROUP_MEMBERS)),
    ],
) -> None:
    member = await source_group_member_service.get_item(id_)
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source group member not found")

    try:
        await source_group_member_service.delete_item(member)
    except exceptions.SourceGroupMemberError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@sources_router.get(paths.SOURCE_GROUP_CONTENT)
async def list_group_content(
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
) -> CursorPage[ContentRead]:
    raise Exception("Not Implemented Yet")


# Document Source Config
@sources_router.get(paths.DOCUMENT_SOURCE_CONFIG, response_model=DocumentSourceConfigRead)
async def get_document_source_config(
    id_: int,
    document_source_config_service: Annotated[
        DocumentSourceConfigsService,
        Depends(
            get_service(
                ServiceType.DOCUMENT_SOURCE_CONFIGS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> DocumentSourceConfigRead:
    raise Exception("Not Implemented Yet")


@sources_router.post(paths.DOCUMENT_SOURCE_CONFIG_GROUP, status_code=status.HTTP_201_CREATED)
async def add_group_to_document(
    id_: int,
    group_id: int,
    document_source_config_service: Annotated[
        DocumentSourceConfigsService,
        Depends(get_service(ServiceType.DOCUMENT_SOURCE_CONFIGS)),
    ],
) -> None:
    raise Exception("Not Implemented Yet")


@sources_router.delete(paths.DOCUMENT_SOURCE_CONFIG_GROUP, status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_from_document(
    id_: int,
    group_id: int,
    document_source_config_service: Annotated[
        DocumentSourceConfigsService,
        Depends(get_service(ServiceType.DOCUMENT_SOURCE_CONFIGS)),
    ],
) -> None:
    raise Exception("Not Implemented Yet")


@sources_router.post(paths.DOCUMENT_SOURCE_CONFIG_SOURCE, status_code=status.HTTP_201_CREATED)
async def add_source_to_document(
    id_: int,
    source_id: int,
    document_source_config_service: Annotated[
        DocumentSourceConfigsService,
        Depends(get_service(ServiceType.DOCUMENT_SOURCE_CONFIGS)),
    ],
) -> None:
    raise Exception("Not Implemented Yet")


@sources_router.delete(paths.DOCUMENT_SOURCE_CONFIG_SOURCE, status_code=status.HTTP_204_NO_CONTENT)
async def remove_source_from_document(
    id_: int,
    source_id: int,
    document_source_config_service: Annotated[
        DocumentSourceConfigsService,
        Depends(get_service(ServiceType.DOCUMENT_SOURCE_CONFIGS)),
    ],
) -> None:
    raise Exception("Not Implemented Yet")


# Citations
@sources_router.get(paths.DOCUMENT_CITATIONS, response_model=CursorPage[CitationRead])
async def get_document_citations(
    id_: int,
    citation_service: Annotated[
        CitationsService,
        Depends(
            get_service(
                ServiceType.CITATIONS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(CITATIONS_FILTERS_DEFINITION))
    ],
) -> CursorPage[CitationRead]:
    filters = filters_parser.filters + [
        Filter(field="document_id", op=FilterOp.EQ, value=id_, field_type=int),
    ]
    return await citation_service.get_items_paginated(model_filters=filters, model_sorts=filters_parser.sorts)


@sources_router.post(paths.DOCUMENT_CITATIONS, response_model=CitationRead, status_code=status.HTTP_201_CREATED)
async def create_citation(
    id_: int,
    citation: CitationCreate,
    citation_service: Annotated[
        CitationsService,
        Depends(
            get_service(
                ServiceType.CITATIONS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
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
) -> Citation:
    content = await content_service.get_item(citation.content_id)
    if content is None or content.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")

    payload = citation.model_dump(by_alias=True, exclude_unset=True, exclude_none=True)
    payload.update(
        {
            "documentId": id_,
            "organizationId": current_user.organization_id,
        }
    )
    converted = Citation.model_validate(payload)
    return await citation_service.create_item(converted)


@sources_router.patch(paths.CITATIONS_ID, response_model=CitationRead)
async def update_citation(
    id_: int,
    citation_update: CitationUpdate,
    citation_service: Annotated[
        CitationsService,
        Depends(get_service(ServiceType.CITATIONS)),
    ],
) -> Citation:
    existing = await citation_service.get_item(id_)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    updated = await citation_service.update_item(id_, citation_update)
    return updated


@sources_router.delete(paths.CITATIONS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_citation(
    id_: int,
    citation_service: Annotated[
        CitationsService,
        Depends(get_service(ServiceType.CITATIONS)),
    ],
) -> None:
    existing = await citation_service.get_item(id_)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Citation not found")
    await citation_service.delete_item(existing)
