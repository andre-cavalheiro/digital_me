from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = [
    "Document",
    "DocumentCreate",
    "DocumentRead",
    "DocumentUpdate",
    "DocumentContent",
    "DocumentContentCreate",
    "DocumentContentRead",
    "DocumentContentUpdate",
]


class DocumentBase(BaseSQLModel):
    title: str
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class Document(DocumentBase, BigIntIDModel, table=True):
    __tablename__: str = "document"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    user_id: int = Field(sa_type=sa.BigInteger, foreign_key="user.id", nullable=False)
    title: str = Field(nullable=False)
    metadata_: dict[str, Any] | None = Field(
        default=None, alias="metadata", sa_column=sa.Column("metadata", sa.JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class DocumentRead(DocumentBase):
    # Ignore extra fields to allow direct SQLA model usage in responses.
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class DocumentCreate(DocumentBase):
    title: str = Field()
    metadata_: Optional[dict[str, Any]] = Field(default=None, alias="metadata")


class DocumentUpdate(BaseSQLModel):
    title: str | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class DocumentContentBase(BaseSQLModel):
    content: str
    word_count: int | None = None


class DocumentContent(DocumentContentBase, BigIntIDModel, table=True):
    __tablename__: str = "document_content"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    document_id: int = Field(
        sa_type=sa.BigInteger, foreign_key="document.id", nullable=False, sa_column_kwargs={"unique": True}
    )
    content: str = Field(nullable=False)
    word_count: int | None = Field(default=None, nullable=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class DocumentContentRead(DocumentContentBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    document_id: int
    updated_at: datetime


class DocumentContentCreate(DocumentContentBase):
    content: str = Field()
    word_count: int | None = None


class DocumentContentUpdate(BaseSQLModel):
    content: str | None = None
    word_count: int | None = None
