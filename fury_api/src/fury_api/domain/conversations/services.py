from typing import TYPE_CHECKING, Sequence

import sqlalchemy as sa
from sqlalchemy import select
from .models import Conversation, Message
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService, with_uow

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

    async def set_conversation_title_if_empty(
        self, conversation_id: int, title: str, *, organization_id: int | None = None
    ) -> bool:
        """Set a conversation title only if it is currently empty/Untitled."""
        if not title:
            return False

        params = {"title": title, "conversation_id": conversation_id}
        org_clause = ""
        if organization_id is not None:
            org_clause = " AND organization_id = :organization_id"
            params["organization_id"] = organization_id

        stmt = sa.text(
            f"""
            UPDATE conversation
            SET title = :title
            WHERE id = :conversation_id
              {org_clause}
              AND COALESCE(title, '') IN ('', 'Untitled')
            RETURNING id
            """
        )

        async with self.uow:
            result = await self.session.execute(stmt, params)  # type: ignore[arg-type]
            return result.first() is not None

    @with_uow
    async def get_recent_by_conversation(
        self,
        conversation_id: int,
        *,
        limit: int,
        organization_id: int | None = None,
        exclude_ids: Sequence[int] | None = None,
    ) -> list[Message]:
        query = (
            select(self._model_cls)
            .where(self._model_cls.conversation_id == conversation_id)
            .order_by(self._model_cls.created_at.desc(), self._model_cls.id.desc())
            .limit(limit)
        )

        if organization_id is not None:
            query = query.where(self._model_cls.organization_id == organization_id)
        if exclude_ids:
            query = query.where(sa.not_(self._model_cls.id.in_(exclude_ids)))

        return await self.repository.list(self.session, query=query)
