from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

import sqlalchemy as sa
from pydantic import ConfigDict, field_validator
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
    "MessageStatus",
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
    document_id: int | None = Field(
        default=None,
        sa_column=sa.Column(sa.BigInteger, sa.ForeignKey("document.id", ondelete="CASCADE"), nullable=True),
    )
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


class MessageStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Message(MessageBase, BigIntIDModel, table=True):
    __tablename__: str = "message"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    conversation_id: int = Field(
        sa_column=sa.Column(sa.BigInteger, sa.ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False)
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    role: str = Field(nullable=False)
    content: str = Field(nullable=False)
    context_sources: list[int] | None = Field(default=None, sa_type=sa.JSON, nullable=True)
    status: MessageStatus = Field(default=MessageStatus.COMPLETED, sa_column=sa.Column(sa.String, nullable=False))
    metadata_: dict[str, Any] | None = Field(
        default_factory=dict,
        sa_type=sa.JSON,
        nullable=True,
        alias="metadata",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    @field_validator("metadata_", mode="before")
    @classmethod
    def coerce_sa_metadata(cls, value: Any) -> Any:
        # Drop SQLAlchemy MetaData object that gets attached as `metadata` on ORM instances.
        if isinstance(value, sa.MetaData):
            return None
        return value


class MessageRead(MessageBase):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, alias_generator=None)

    id: int
    conversation_id: int
    organization_id: int
    status: MessageStatus
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
    created_at: datetime

    @field_validator("metadata_", mode="before")
    @classmethod
    def coerce_sa_metadata(cls, value: Any) -> Any:
        if isinstance(value, sa.MetaData):
            return None
        return value


class MessageCreate(MessageBase):
    role: str = Field()
    content: str = Field()
    context_sources: list[int] | None = None


class MessageUpdate(BaseSQLModel):
    role: str | None = None
    content: str | None = None
    context_sources: list[int] | None = None
    status: MessageStatus | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")
