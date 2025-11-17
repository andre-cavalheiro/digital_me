from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = [
    "Conversation",
    "ConversationCreate",
    "ConversationRead",
    "ConversationUpdate",
    "Message",
    "MessageCreate",
    "MessageRead",
    "MessageUpdate",
]


class ConversationBase(BaseSQLModel):
    title: str | None = None
    document_id: int | None = None


class Conversation(ConversationBase, BigIntIDModel, table=True):
    __tablename__: str = "conversation"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    document_id: int | None = Field(sa_type=sa.BigInteger, foreign_key="document.id", nullable=True)
    title: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ConversationRead(ConversationBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    created_at: datetime


class ConversationCreate(ConversationBase):
    title: str | None = None
    document_id: int | None = None


class ConversationUpdate(BaseSQLModel):
    title: str | None = None
    document_id: int | None = None


class MessageBase(BaseSQLModel):
    role: str
    content: str
    context_sources: list[int] | None = None


class Message(MessageBase, BigIntIDModel, table=True):
    __tablename__: str = "message"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    conversation_id: int = Field(sa_type=sa.BigInteger, foreign_key="conversation.id", nullable=False)
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    role: str = Field(nullable=False)
    content: str = Field(nullable=False)
    context_sources: list[int] | None = Field(default=None, sa_type=sa.JSON, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class MessageRead(MessageBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    conversation_id: int
    organization_id: int
    created_at: datetime


class MessageCreate(MessageBase):
    role: str = Field()
    content: str = Field()
    context_sources: list[int] | None = None


class MessageUpdate(BaseSQLModel):
    role: str | None = None
    content: str | None = None
    context_sources: list[int] | None = None
