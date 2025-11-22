from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from typing import Any, Optional

from pydantic import AliasChoices, ConfigDict, Field as PydanticField, field_validator
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
    "DocumentContentUpsert",
]


class DocumentBase(BaseSQLModel):
    title: str
    metadata_: dict[str, Any] | None = Field(default=None)

    @field_validator("metadata_", mode="before")
    @classmethod
    def coerce_sa_metadata(cls, value: Any) -> Any:
        # When validating from ORM objects, SQLAlchemy injects a MetaData attribute named `metadata`.
        # If that comes through, drop it so we don't try to serialize the SQLAlchemy MetaData object.
        if isinstance(value, sa.MetaData):
            return None
        return value


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
        default=None,
        sa_column=sa.Column("metadata", sa.JSON, nullable=True),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class DocumentSchemaBase(BaseSQLModel):
    title: str
    metadata_: dict[str, Any] | None = PydanticField(
        default=None,
        validation_alias=AliasChoices("metadata_", "metadata"),
        serialization_alias="metadata",
    )


class DocumentRead(DocumentSchemaBase):
    # Ignore extra fields to allow direct SQLA model usage in responses.
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class DocumentCreate(DocumentSchemaBase):
    title: str = PydanticField()
    metadata_: Optional[dict[str, Any]] = PydanticField(
        default=None,
        validation_alias=AliasChoices("metadata_", "metadata"),
        serialization_alias="metadata",
    )


class DocumentUpdate(BaseSQLModel):
    title: str | None = None
    metadata_: dict[str, Any] | None = PydanticField(
        default=None,
        validation_alias=AliasChoices("metadata_", "metadata"),
        serialization_alias="metadata",
    )


class DocumentContentBase(BaseSQLModel):
    title: str | None = None
    content: str
    order_index: int
    word_count: int | None = None


class DocumentContent(DocumentContentBase, BigIntIDModel, table=True):
    __tablename__: str = "document_content"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    document_id: int = Field(
        sa_column=sa.Column(sa.BigInteger, sa.ForeignKey("document.id", ondelete="CASCADE"), nullable=False)
    )
    title: str | None = Field(default=None, nullable=True)
    content: str = Field(nullable=False)
    order_index: int = Field(nullable=False)
    word_count: int | None = Field(default=None, nullable=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class DocumentContentRead(DocumentContentBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    document_id: int
    order_index: int
    title: str | None = None
    updated_at: datetime


class DocumentContentCreate(DocumentContentBase):
    content: str = Field()
    order_index: int = Field()
    title: str | None = None
    word_count: int | None = None


class DocumentContentUpdate(BaseSQLModel):
    content: str | None = None
    title: str | None = None
    order_index: int | None = None
    word_count: int | None = None


class DocumentContentUpsert(BaseSQLModel):
    sections: list[DocumentContentCreate]
