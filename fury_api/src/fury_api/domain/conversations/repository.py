from .models import Conversation, Message
from fury_api.lib.repository import GenericSqlExtendedRepository

__all__ = ["ConversationRepository", "MessageRepository"]


class ConversationRepository(GenericSqlExtendedRepository[Conversation]):
    def __init__(self) -> None:
        super().__init__(model_cls=Conversation)


class MessageRepository(GenericSqlExtendedRepository[Message]):
    def __init__(self) -> None:
        super().__init__(model_cls=Message)
