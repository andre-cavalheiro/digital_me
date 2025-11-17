from typing import TYPE_CHECKING

from .models import Conversation, Message
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService

if TYPE_CHECKING:
    pass

__all__ = ["ConversationsService", "MessagesService"]


class ConversationsService(SqlService[Conversation]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Conversation, uow, auth_user=auth_user, **kwargs)


class MessagesService(SqlService[Message]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Message, uow, auth_user=auth_user, **kwargs)
