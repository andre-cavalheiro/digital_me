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
    get_ai_client,
)
from fury_api.lib.integrations import BaseAIClient
from fury_api.lib.settings import config
from fury_api.domain.jobs.services import JobsService
from fury_api.domain.jobs.models import TaskInfo
from . import exceptions
from .models import (
    Conversation,
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    Message,
    MessageCreate,
    MessageRead,
    MessageUpdate,
    MessageStatus,
)
from fury_api.lib.security import get_current_user
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from .services import ConversationsService, MessagesService
from fury_api.lib.model_filters import Filter, FilterOp, ModelFilterAndSortDefinition, get_default_ops_for_type
from .streams import assistant_stream_broker
from fury_api.domain.documents.services import DocumentContentsService
from fury_api.domain.content.services import ContentsService
from .ai import build_chat_messages

conversation_router = APIRouter()

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

###################
## Conversations ##
###################


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
    conversation_data = conversation.model_dump()
    conversation_data["organization_id"] = current_user.organization_id
    converted_conversation = Conversation.model_validate(conversation_data)
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


###################
## Messages ##
###################


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


@conversation_router.post(paths.CONVERSATION_MESSAGES, response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def create_message(
    id_: int,
    message: MessageCreate,
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
    document_content_service: Annotated[
        DocumentContentsService,
        Depends(
            get_service(
                ServiceType.DOCUMENT_CONTENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> Message:
    conversation = await conversation_service.get_item(id_)
    if not conversation or conversation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    context_sources = message.context_sources
    user_message = Message(
        **message.model_dump(exclude={"context_sources"}, exclude_none=True),
        organization_id=current_user.organization_id,
        conversation_id=id_,
        status=MessageStatus.COMPLETED,
        metadata_={"generated": False, "context_sources": context_sources.model_dump() if context_sources else None},
    )
    created_user_message = await message_service.create_item(user_message)

    await message_service.set_conversation_title_from_message(
        conversation_id=id_,
        message_content=message.content,
        organization_id=current_user.organization_id,
    )

    sections = (
        await document_content_service.get_by_ids(context_sources.section_ids, document_id=conversation.document_id)
        if context_sources and context_sources.section_ids
        else []
    )
    contents = (
        await content_service.get_by_ids(context_sources.content_ids)
        if context_sources and context_sources.content_ids
        else []
    )

    history = await message_service.get_recent_by_conversation(
        id_,
        limit=config.ai.HISTORY_MESSAGE_LIMIT,
        organization_id=current_user.organization_id,
        exclude_ids=[created_user_message.id],
    )
    chat_messages, context_metadata = build_chat_messages(
        base_prompt=config.ai.SYSTEM_PROMPT,
        history=history,
        user_message=created_user_message,
        sections=sections,
        contents=contents,
        selection=context_sources.selection if context_sources else None,
        max_section_chars=config.ai.MAX_SECTION_CHARS,
        max_content_chars=config.ai.MAX_CONTENT_CHARS,
    )

    assistant_metadata = {
        "generated": True,
        "provider": config.ai.PROVIDER,
        "model": config.ai_openai.MODEL or config.ai.DEFAULT_MODEL,
        "context": context_metadata,
    }
    assistant_message = Message(
        role="assistant",
        content="",
        conversation_id=id_,
        organization_id=current_user.organization_id,
        status=MessageStatus.RUNNING,
        metadata_=assistant_metadata,
    )
    created_assistant_message = await message_service.create_item(assistant_message)

    await assistant_stream_broker.publish(
        id_,
        {
            "type": "status",
            "stage": "queued",
            "assistant_message_id": created_assistant_message.id,
            "conversation_id": id_,
        },
    )
    await assistant_stream_broker.publish(
        id_,
        {
            "type": "status",
            "stage": "generating",
            "assistant_message_id": created_assistant_message.id,
            "conversation_id": id_,
        },
    )

    try:
        accumulated_content = []
        async for chunk in ai_client.stream_chat(
            messages=chat_messages,
            model=config.ai_openai.MODEL or config.ai.DEFAULT_MODEL,
            temperature=config.ai.TEMPERATURE,
            max_tokens=config.ai.MAX_OUTPUT_TOKENS,
        ):
            accumulated_content.append(chunk)
            await assistant_stream_broker.publish(
                id_,
                {
                    "type": "delta",
                    "conversation_id": id_,
                    "assistant_message_id": created_assistant_message.id,
                    "content": chunk,
                },
            )

        full_content = "".join(accumulated_content)
        updated_assistant = await message_service.update_item(
            created_assistant_message.id,
            MessageUpdate(
                content=full_content,
                status=MessageStatus.COMPLETED,
                metadata_={
                    **assistant_metadata,
                    # "usage": ai_response.usage, # Usage is not easily available in stream usually, or comes at end. Skipping for now.
                    "model": config.ai_openai.MODEL or config.ai.DEFAULT_MODEL,
                },
            ),
        )
    except Exception as exc:
        await message_service.update_item(
            created_assistant_message.id,
            MessageUpdate(
                status=MessageStatus.FAILED,
                metadata_={**assistant_metadata, "error": str(exc)},
            ),
        )
        await assistant_stream_broker.publish(
            id_,
            {
                "type": "error",
                "assistant_message_id": created_assistant_message.id,
                "conversation_id": id_,
                "message": "Assistant failed to generate response",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to generate assistant response"
        ) from exc

    await assistant_stream_broker.publish(
        id_,
        {
            "type": "completed",
            "stage": "completed",
            "assistant_message_id": updated_assistant.id,
            "conversation_id": id_,
        },
    )
    return created_user_message


@conversation_router.get(paths.CONVERSATION_MESSAGES_STREAM)
async def stream_messages_events(id_: int) -> EventSourceResponse:
    async def event_generator():
        async for event in assistant_stream_broker.stream(id_):
            yield {
                "event": event.get("type", "message"),
                "data": json.dumps(event),
            }

    return EventSourceResponse(event_generator())


# This is currently not being used for anything in practise!
# This behaves similarly to `create_message` but instead of calling the AI model itself, it pushes the request into celery.
# Maybe could be used for longer research tasks, keeping it here for future reference.
@conversation_router.post(
    f"{paths.CONVERSATIONS}/{{id_}}/messages/async", response_model=TaskInfo, status_code=status.HTTP_202_ACCEPTED
)
async def create_message_async(
    id_: int,
    message: MessageCreate,
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
    document_content_service: Annotated[
        DocumentContentsService,
        Depends(
            get_service(
                ServiceType.DOCUMENT_CONTENTS,
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
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
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskInfo:
    """
    Queue an async AI message generation job.

    Returns task info for status tracking. The message will be generated
    by a background worker and updated in the database when complete.
    """
    conversation = await conversation_service.get_item(id_)
    if not conversation or conversation.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    context_sources = message.context_sources
    user_message = Message(
        **message.model_dump(exclude={"context_sources"}, exclude_none=True),
        organization_id=current_user.organization_id,
        conversation_id=id_,
        status=MessageStatus.COMPLETED,
        metadata_={"generated": False, "context_sources": context_sources.model_dump() if context_sources else None},
    )
    created_user_message = await message_service.create_item(user_message)

    await message_service.set_conversation_title_from_message(
        conversation_id=id_,
        message_content=message.content,
        organization_id=current_user.organization_id,
    )

    sections = (
        await document_content_service.get_by_ids(context_sources.section_ids, document_id=conversation.document_id)
        if context_sources and context_sources.section_ids
        else []
    )
    contents = (
        await content_service.get_by_ids(context_sources.content_ids)
        if context_sources and context_sources.content_ids
        else []
    )

    history = await message_service.get_recent_by_conversation(
        id_,
        limit=config.ai.HISTORY_MESSAGE_LIMIT,
        organization_id=current_user.organization_id,
        exclude_ids=[created_user_message.id],
    )
    chat_messages, context_metadata = build_chat_messages(
        base_prompt=config.ai.SYSTEM_PROMPT,
        history=history,
        user_message=created_user_message,
        sections=sections,
        contents=contents,
        selection=context_sources.selection if context_sources else None,
        max_section_chars=config.ai.MAX_SECTION_CHARS,
        max_content_chars=config.ai.MAX_CONTENT_CHARS,
    )

    assistant_message = Message(
        role="assistant",
        content="",
        conversation_id=id_,
        organization_id=current_user.organization_id,
        status=MessageStatus.QUEUED,
        metadata_={
            "generated": True,
            "provider": config.ai.PROVIDER,
            "model": config.ai_openai.MODEL or config.ai.DEFAULT_MODEL,
            "context": context_metadata,
        },
    )
    created_assistant_message = await message_service.create_item(assistant_message)

    jobs_service = JobsService()
    task_info = jobs_service.push_task(
        task_name="ai.conversation.generate_response",
        organization_id=current_user.organization_id,
        conversation_id=id_,
        message_id=created_assistant_message.id,
        chat_messages=[{"role": msg.role, "content": msg.content} for msg in chat_messages],
        context_metadata=context_metadata,
    )

    return task_info
