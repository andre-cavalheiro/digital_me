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
    converted_source = Source.model_validate(source)
    converted_source.organization_id = current_user.organization_id
    converted_source.user_id = current_user.id
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
    converted_content = Content.model_validate(content_data)
    converted_content.organization_id = current_user.organization_id
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
    # TODO: Implement actual content search
    from datetime import datetime
    return [
        ContentRead(
            id=1,
            organization_id=1,
            source_id=1,
            external_id="tweet_001",
            external_url="https://twitter.com/user/status/123456789",
            title="Insights on AI Development",
            body="Just finished reading an amazing paper on transformer architectures. The attention mechanism is truly revolutionary for natural language processing!",
            excerpt="Just finished reading an amazing paper on transformer architectures...",
            published_at=datetime(2025, 11, 15, 10, 30),
            synced_at=datetime(2025, 11, 17, 8, 0),
            platform_metadata={"likes": 42, "retweets": 15, "platform": "twitter"},
            created_at=datetime(2025, 11, 17, 8, 0),
            updated_at=datetime(2025, 11, 17, 8, 0),
        ),
        ContentRead(
            id=2,
            organization_id=1,
            source_id=2,
            external_id="article_002",
            external_url="https://medium.com/@author/article-slug",
            title="Building Scalable APIs with FastAPI",
            body="FastAPI has become my go-to framework for building modern APIs. Its automatic documentation, type hints, and async support make development incredibly efficient. In this article, I'll share some best practices I've learned over the past year.",
            excerpt="FastAPI has become my go-to framework for building modern APIs...",
            published_at=datetime(2025, 11, 10, 14, 20),
            synced_at=datetime(2025, 11, 17, 8, 5),
            platform_metadata={"claps": 128, "reading_time_minutes": 8, "platform": "medium"},
            created_at=datetime(2025, 11, 17, 8, 5),
            updated_at=datetime(2025, 11, 17, 8, 5),
        ),
        ContentRead(
            id=3,
            organization_id=1,
            source_id=1,
            external_id="tweet_003",
            external_url="https://twitter.com/user/status/987654321",
            title=None,
            body="Hot take: Documentation is just as important as the code itself. Future you will thank present you! 📚✨",
            excerpt="Hot take: Documentation is just as important as the code itself...",
            published_at=datetime(2025, 11, 16, 16, 45),
            synced_at=datetime(2025, 11, 17, 8, 10),
            platform_metadata={"likes": 87, "retweets": 23, "platform": "twitter"},
            created_at=datetime(2025, 11, 17, 8, 10),
            updated_at=datetime(2025, 11, 17, 8, 10),
        ),
        ContentRead(
            id=4,
            organization_id=1,
            source_id=3,
            external_id="note_004",
            external_url=None,
            title="Meeting Notes - Product Roadmap Q4",
            body="Discussed upcoming features for Q4: 1) Enhanced search functionality with semantic search, 2) Real-time collaboration features, 3) Mobile app development kickoff. Action items: Schedule design review for search UI, Assign backend team to research vector databases.",
            excerpt="Discussed upcoming features for Q4: Enhanced search, real-time collaboration...",
            published_at=datetime(2025, 11, 14, 9, 0),
            synced_at=datetime(2025, 11, 17, 8, 15),
            platform_metadata={"attendees": 5, "duration_minutes": 60, "platform": "notion"},
            created_at=datetime(2025, 11, 17, 8, 15),
            updated_at=datetime(2025, 11, 17, 8, 15),
        ),
        ContentRead(
            id=5,
            organization_id=1,
            source_id=2,
            external_id="article_005",
            external_url="https://dev.to/author/microservices-patterns",
            title="Design Patterns for Microservices Architecture",
            body="Microservices have transformed how we build scalable applications. This comprehensive guide covers essential patterns including Circuit Breaker, Service Discovery, API Gateway, and Event Sourcing. Learn when and how to apply each pattern effectively.",
            excerpt="Microservices have transformed how we build scalable applications...",
            published_at=datetime(2025, 11, 12, 11, 15),
            synced_at=datetime(2025, 11, 17, 8, 20),
            platform_metadata={"reactions": 245, "comments": 18, "reading_time_minutes": 12, "platform": "dev.to"},
            created_at=datetime(2025, 11, 17, 8, 20),
            updated_at=datetime(2025, 11, 17, 8, 20),
        ),
        ContentRead(
            id=6,
            organization_id=1,
            source_id=1,
            external_id="tweet_006",
            external_url="https://twitter.com/user/status/456789123",
            title=None,
            body="Debugging tip: When you're stuck, explain the problem out loud to a rubber duck (or a colleague). The act of explaining often reveals the solution! 🦆💡",
            excerpt="Debugging tip: When you're stuck, explain the problem out loud...",
            published_at=datetime(2025, 11, 13, 8, 20),
            synced_at=datetime(2025, 11, 17, 8, 25),
            platform_metadata={"likes": 156, "retweets": 42, "platform": "twitter"},
            created_at=datetime(2025, 11, 17, 8, 25),
            updated_at=datetime(2025, 11, 17, 8, 25),
        ),
        ContentRead(
            id=7,
            organization_id=1,
            source_id=4,
            external_id="github_007",
            external_url="https://github.com/user/awesome-repo/discussions/42",
            title="RFC: Implementing WebSocket Support",
            body="Proposing to add WebSocket support for real-time features. This would enable live updates, collaborative editing, and instant notifications. Implementation would use Socket.IO for browser compatibility and automatic reconnection handling.",
            excerpt="Proposing to add WebSocket support for real-time features...",
            published_at=datetime(2025, 11, 11, 15, 30),
            synced_at=datetime(2025, 11, 17, 8, 30),
            platform_metadata={"upvotes": 34, "comments": 12, "platform": "github"},
            created_at=datetime(2025, 11, 17, 8, 30),
            updated_at=datetime(2025, 11, 17, 8, 30),
        ),
        ContentRead(
            id=8,
            organization_id=1,
            source_id=3,
            external_id="note_008",
            external_url=None,
            title="Research: Vector Databases Comparison",
            body="Compared three vector database solutions: Pinecone, Weaviate, and Qdrant. Key findings: Pinecone offers best ease of use, Weaviate has superior filtering capabilities, Qdrant provides best performance for our use case. Recommendation: Start with Qdrant for cost-effectiveness and performance.",
            excerpt="Compared three vector database solutions for semantic search...",
            published_at=datetime(2025, 11, 9, 13, 45),
            synced_at=datetime(2025, 11, 17, 8, 35),
            platform_metadata={"collaborators": 3, "platform": "notion"},
            created_at=datetime(2025, 11, 17, 8, 35),
            updated_at=datetime(2025, 11, 17, 8, 35),
        ),
        ContentRead(
            id=9,
            organization_id=1,
            source_id=1,
            external_id="tweet_009",
            external_url="https://twitter.com/user/status/789123456",
            title=None,
            body="TIL: Python's 'walrus operator' (:=) can make your code more concise. Instead of assigning and checking in separate lines, you can do both at once! Mind = blown 🤯",
            excerpt="TIL: Python's 'walrus operator' can make your code more concise...",
            published_at=datetime(2025, 11, 8, 17, 10),
            synced_at=datetime(2025, 11, 17, 8, 40),
            platform_metadata={"likes": 203, "retweets": 67, "platform": "twitter"},
            created_at=datetime(2025, 11, 17, 8, 40),
            updated_at=datetime(2025, 11, 17, 8, 40),
        ),
        ContentRead(
            id=10,
            organization_id=1,
            source_id=2,
            external_id="article_010",
            external_url="https://medium.com/@author/react-performance",
            title="React Performance Optimization: A Deep Dive",
            body="Performance optimization in React applications requires understanding the rendering lifecycle. This article explores useMemo, useCallback, React.memo, and virtualization techniques. Includes practical examples and benchmarks showing 60% performance improvement in a real-world application.",
            excerpt="Performance optimization in React applications requires understanding...",
            published_at=datetime(2025, 11, 7, 10, 0),
            synced_at=datetime(2025, 11, 17, 8, 45),
            platform_metadata={"claps": 342, "reading_time_minutes": 15, "platform": "medium"},
            created_at=datetime(2025, 11, 17, 8, 45),
            updated_at=datetime(2025, 11, 17, 8, 45),
        ),
        ContentRead(
            id=11,
            organization_id=1,
            source_id=5,
            external_id="linkedin_011",
            external_url="https://linkedin.com/posts/user_activity123",
            title="Lessons Learned: Scaling to 1M Users",
            body="Reflecting on our journey from 0 to 1 million users. Key takeaways: 1) Start with a monolith, 2) Monitor everything from day one, 3) Database optimization is crucial, 4) Horizontal scaling beats vertical scaling, 5) Culture matters more than technology. Happy to share more details in the comments!",
            excerpt="Reflecting on our journey from 0 to 1 million users...",
            published_at=datetime(2025, 11, 6, 9, 30),
            synced_at=datetime(2025, 11, 17, 8, 50),
            platform_metadata={"likes": 1247, "comments": 89, "shares": 156, "platform": "linkedin"},
            created_at=datetime(2025, 11, 17, 8, 50),
            updated_at=datetime(2025, 11, 17, 8, 50),
        ),
        ContentRead(
            id=12,
            organization_id=1,
            source_id=3,
            external_id="note_012",
            external_url=None,
            title="Design System Guidelines v2.0",
            body="Updated design system with new components and patterns. Major changes: Dark mode support, new color palette with better accessibility, responsive spacing scale, updated typography system. All components now support both light and dark themes. Migration guide available in the wiki.",
            excerpt="Updated design system with new components and patterns...",
            published_at=datetime(2025, 11, 5, 14, 15),
            synced_at=datetime(2025, 11, 17, 8, 55),
            platform_metadata={"pages": 8, "last_edited_by": "design_team", "platform": "notion"},
            created_at=datetime(2025, 11, 17, 8, 55),
            updated_at=datetime(2025, 11, 17, 8, 55),
        ),
        ContentRead(
            id=13,
            organization_id=1,
            source_id=1,
            external_id="tweet_013",
            external_url="https://twitter.com/user/status/321654987",
            title=None,
            body="Code review best practice: Start with positive feedback. Point out what's done well before suggesting improvements. This creates a more collaborative and less defensive environment. 🤝",
            excerpt="Code review best practice: Start with positive feedback...",
            published_at=datetime(2025, 11, 4, 12, 0),
            synced_at=datetime(2025, 11, 17, 9, 0),
            platform_metadata={"likes": 412, "retweets": 98, "platform": "twitter"},
            created_at=datetime(2025, 11, 17, 9, 0),
            updated_at=datetime(2025, 11, 17, 9, 0),
        ),
        ContentRead(
            id=14,
            organization_id=1,
            source_id=4,
            external_id="github_014",
            external_url="https://github.com/user/project/issues/156",
            title="Feature Request: Add Export Functionality",
            body="Users have been requesting the ability to export their data in multiple formats (CSV, JSON, PDF). This would improve data portability and enable integration with external tools. Proposed implementation: Add export button in settings, support batch exports, include filters for date range and content type.",
            excerpt="Users requesting ability to export data in multiple formats...",
            published_at=datetime(2025, 11, 3, 16, 20),
            synced_at=datetime(2025, 11, 17, 9, 5),
            platform_metadata={"upvotes": 67, "comments": 23, "labels": ["enhancement", "user-request"], "platform": "github"},
            created_at=datetime(2025, 11, 17, 9, 5),
            updated_at=datetime(2025, 11, 17, 9, 5),
        ),
        ContentRead(
            id=15,
            organization_id=1,
            source_id=2,
            external_id="article_015",
            external_url="https://dev.to/author/testing-strategies",
            title="Testing Strategies for Modern Web Applications",
            body="Comprehensive guide to testing: unit tests for business logic, integration tests for API endpoints, E2E tests for critical user flows. The testing pyramid is outdated - consider the testing trophy instead. Includes setup guides for Jest, Pytest, and Playwright with real-world examples.",
            excerpt="Comprehensive guide to testing modern web applications...",
            published_at=datetime(2025, 11, 2, 11, 45),
            synced_at=datetime(2025, 11, 17, 9, 10),
            platform_metadata={"reactions": 389, "comments": 45, "reading_time_minutes": 18, "platform": "dev.to"},
            created_at=datetime(2025, 11, 17, 9, 10),
            updated_at=datetime(2025, 11, 17, 9, 10),
        ),
    ]

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
    raise Exception("Not Implemented Yet")


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
) -> Citation:
    raise Exception("Not Implemented Yet")


@sources_router.patch(paths.CITATIONS_ID, response_model=CitationRead)
async def update_citation(
    id_: int,
    citation_update: CitationUpdate,
    citation_service: Annotated[
        CitationsService,
        Depends(get_service(ServiceType.CITATIONS)),
    ],
) -> Citation:
    raise Exception("Not Implemented Yet")


@sources_router.delete(paths.CITATIONS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_citation(
    id_: int,
    citation_service: Annotated[
        CitationsService,
        Depends(get_service(ServiceType.CITATIONS)),
    ],
) -> None:
    raise Exception("Not Implemented Yet")
