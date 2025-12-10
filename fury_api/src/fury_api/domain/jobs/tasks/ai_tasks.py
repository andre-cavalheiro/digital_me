import asyncio
from fury_api.lib.celery_app import celery_app
from .base import FuryBaseTask


@celery_app.task(
    name="ai.conversation.generate_response",
    bind=True,
    base=FuryBaseTask,
    queue="ai",
    time_limit=900,
    soft_time_limit=870,
)
def generate_assistant_response(
    self, organization_id: int, conversation_id: int, message_id: int, chat_messages: list[dict], context_metadata: dict
):
    """Generate AI assistant response for a conversation message."""
    return asyncio.run(
        _generate_response_async(
            organization_id=organization_id,
            conversation_id=conversation_id,
            message_id=message_id,
            chat_messages=chat_messages,
            context_metadata=context_metadata,
        )
    )


async def _generate_response_async(
    organization_id: int, conversation_id: int, message_id: int, chat_messages: list[dict], context_metadata: dict
):
    """Async implementation of assistant response generation."""
    from fury_api.lib.integrations import OpenAIClient
    from fury_api.lib.integrations.base_ai import ChatMessage
    from fury_api.lib.settings import config
    from fury_api.lib.factories import UnitOfWorkFactory, ServiceFactory
    from fury_api.lib.factories.service_factory import ServiceType
    from fury_api.domain.conversations.models import MessageUpdate, MessageStatus

    async with UnitOfWorkFactory.get_uow(organization_id=organization_id) as uow:
        messages_service = ServiceFactory.create_service(ServiceType.MESSAGES, uow, has_system_access=True)

        # Convert dictionaries back to ChatMessage objects
        chat_message_objects = [ChatMessage(role=msg["role"], content=msg["content"]) for msg in chat_messages]

        ai_client = OpenAIClient(
            api_key=config.ai_openai.API_KEY.get_secret_value() if config.ai_openai.API_KEY else "",
            default_model=config.ai_openai.MODEL or config.ai.DEFAULT_MODEL,
        )
        response = await ai_client.chat(
            messages=chat_message_objects,
            model=config.ai_openai.MODEL or config.ai.DEFAULT_MODEL,
            temperature=config.ai.TEMPERATURE,
            max_tokens=config.ai.MAX_OUTPUT_TOKENS,
        )

        await messages_service.update_item(
            message_id,
            MessageUpdate(
                content=response.message.content,
                status=MessageStatus.COMPLETED,
                metadata_={
                    "generated": True,
                    "provider": config.ai.PROVIDER,
                    "model": response.model,
                    "usage": response.usage,
                    "context": context_metadata,
                },
            ),
        )

        return {
            "message_id": message_id,
            "conversation_id": conversation_id,
            "content_length": len(response.message.content),
            "model": response.model,
            "usage": response.usage,
        }
