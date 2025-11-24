import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette import EventSourceResponse

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
    Conversation,
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    Message,
    MessageCreate,
    MessageRead,
    MessageStatus,
)
from fury_api.lib.security import get_current_user
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from .services import ConversationsService, MessagesService
from fury_api.lib.model_filters import Filter, FilterOp, ModelFilterAndSortDefinition, get_default_ops_for_type
from .streams import assistant_stream_broker, schedule_mock_progress

conversation_router = APIRouter()

MAX_TITLE_LENGTH_FROM_FIRST_MESSAGE = 80

CONVERSATIONS_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Conversation,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "document_id": get_default_ops_for_type(int),
    },
    allowed_sorts={"id", "document_id", "created_at"},
)

MESSAGES_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model=Message,
    allowed_filters={
        "id": get_default_ops_for_type(Identifier),
        "conversation_id": get_default_ops_for_type(int),
    },
    allowed_sorts={"id", "conversation_id", "created_at"},
)


@conversation_router.post(paths.CONVERSATIONS, response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    conversation_service: Annotated[
        ConversationsService,
        Depends(
            get_service(
                ServiceType.CONVERSATIONS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Conversation:
    converted_conversation = Conversation.model_validate(conversation)
    converted_conversation.organization_id = current_user.organization_id
    return await conversation_service.create_item(converted_conversation)


@conversation_router.get(paths.CONVERSATIONS, response_model=CursorPage[ConversationRead])
async def get_conversations(
    conversation_service: Annotated[
        ConversationsService,
        Depends(
            get_service(
                ServiceType.CONVERSATIONS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(CONVERSATIONS_FILTERS_DEFINITION))
    ],
) -> CursorPage[ConversationRead]:
    return await conversation_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@conversation_router.get(paths.CONVERSATIONS_ID, response_model=ConversationRead)
async def get_conversation(
    id_: int,
    conversation_service: Annotated[
        ConversationsService,
        Depends(
            get_service(
                ServiceType.CONVERSATIONS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> ConversationRead:
    conversation = await conversation_service.get_item(id_)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation


@conversation_router.put(paths.CONVERSATIONS_ID, response_model=ConversationRead)
async def update_conversation(
    id_: int,
    conversation_update: ConversationUpdate,
    conversation_service: Annotated[
        ConversationsService,
        Depends(get_service(ServiceType.CONVERSATIONS)),
    ],
) -> Conversation:
    conversation = await conversation_service.get_item(id_)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    try:
        updated_conversation = await conversation_service.update_item(id_, conversation_update)
        return updated_conversation
    except exceptions.ConversationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@conversation_router.delete(paths.CONVERSATIONS_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id_: int,
    conversation_service: Annotated[
        ConversationsService,
        Depends(get_service(ServiceType.CONVERSATIONS)),
    ],
) -> None:
    conversation = await conversation_service.get_item(id_)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    try:
        await conversation_service.delete_item(conversation)
    except exceptions.ConversationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@conversation_router.post(
    paths.DOCUMENT_CONVERSATIONS, response_model=ConversationRead, status_code=status.HTTP_201_CREATED
)
async def create_document_conversation(
    id_: int,
    conversation: ConversationCreate,
    conversation_service: Annotated[
        ConversationsService,
        Depends(
            get_service(
                ServiceType.CONVERSATIONS,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Conversation:
    converted_conversation = Conversation(
        title=conversation.title,
        document_id=id_,
        organization_id=current_user.organization_id,
    )
    return await conversation_service.create_item(converted_conversation)


@conversation_router.get(paths.DOCUMENT_CONVERSATIONS, response_model=CursorPage[ConversationRead])
async def list_document_conversations(
    id_: int,
    conversation_service: Annotated[
        ConversationsService,
        Depends(
            get_service(
                ServiceType.CONVERSATIONS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(CONVERSATIONS_FILTERS_DEFINITION))
    ],
) -> CursorPage[ConversationRead]:
    filters_parser.add_filter(Filter("document_id", FilterOp.EQ, id_, field_type=int))
    return await conversation_service.get_items_paginated(
        model_filters=filters_parser.filters,
        model_sorts=filters_parser.sorts,
    )


@conversation_router.post(paths.CONVERSATION_MESSAGES, response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(
    id_: int,
    message: MessageCreate,
    message_service: Annotated[
        MessagesService,
        Depends(
            get_service(
                ServiceType.MESSAGES,
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> Message:
    user_message = Message(
        **message.model_dump(exclude={"context_sources"}, exclude_none=True),
        organization_id=current_user.organization_id,
        conversation_id=id_,
        status=MessageStatus.COMPLETED,
        metadata_={"mock": True, "generated": False},
    )
    created_user_message = await message_service.create_item(user_message)

    await _set_conversation_title_from_first_message(
        message_service,
        conversation_id=id_,
        organization_id=current_user.organization_id,
        message_content=message.content,
    )

    assistant_message = Message(
        role="assistant",
        content=f"(Mock assistant) Echo: {message.content}",
        conversation_id=id_,
        organization_id=current_user.organization_id,
        status=MessageStatus.COMPLETED,
        metadata_={"mock": True, "generated": True},
    )
    created_assistant_message = await message_service.create_item(assistant_message)

    schedule_mock_progress(id_, created_assistant_message.id)
    return created_user_message


@conversation_router.get(paths.CONVERSATION_MESSAGES, response_model=CursorPage[MessageRead])
async def list_messages(
    id_: int,
    message_service: Annotated[
        MessagesService,
        Depends(
            get_service(
                ServiceType.MESSAGES,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory(MESSAGES_FILTERS_DEFINITION))
    ],
) -> CursorPage[MessageRead]:
    filters_parser.add_filter(Filter("conversation_id", FilterOp.EQ, id_, field_type=int))
    return await message_service.get_items_paginated(
        model_filters=filters_parser.filters,
        model_sorts=filters_parser.sorts,
    )


async def _set_conversation_title_from_first_message(
    message_service: MessagesService,
    *,
    conversation_id: int,
    organization_id: int,
    message_content: str,
) -> None:
    # Normalize whitespace and truncate; called after the first user message is stored.
    normalized = " ".join(message_content.split()).strip()
    if not normalized:
        return None
    truncated = normalized[:MAX_TITLE_LENGTH_FROM_FIRST_MESSAGE]
    await message_service.set_conversation_title_if_empty(
        conversation_id,
        truncated,
        organization_id=organization_id,
    )


@conversation_router.get(paths.CONVERSATION_MESSAGES_STREAM)
async def stream_messages_events(id_: int) -> EventSourceResponse:
    async def event_generator():
        async for event in assistant_stream_broker.stream(id_):
            yield {
                "event": event.get("type", "message"),
                "data": json.dumps(event),
            }

    return EventSourceResponse(event_generator())
