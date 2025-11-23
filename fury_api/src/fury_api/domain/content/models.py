from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = ["Content", "ContentCreate", "ContentRead", "ContentUpdate", "ContentSearchRequest"]


class ContentBase(BaseSQLModel):
    external_id: str
    external_url: str | None = None
    title: str | None = None
    body: str
    excerpt: str | None = None
    published_at: datetime | None = None
    synced_at: datetime | None = None
    platform_metadata: dict[str, Any] | None = None


class Content(ContentBase, BigIntIDModel, table=True):
    __tablename__: str = "content"
    __id_attr__ = "id"

    __table_args__ = (sa.UniqueConstraint("source_id", "external_id", name="uq_content_source_external"),)

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    source_id: int = Field(sa_type=sa.BigInteger, foreign_key="source.id", nullable=False)
    external_id: str = Field(nullable=False)
    external_url: str | None = Field(default=None, nullable=True)
    title: str | None = Field(default=None, nullable=True)
    body: str = Field(sa_type=sa.Text, nullable=False)
    excerpt: str | None = Field(default=None, nullable=True)
    published_at: datetime | None = Field(default=None, nullable=True)
    synced_at: datetime | None = Field(default_factory=datetime.utcnow, nullable=True)
    platform_metadata: dict[str, Any] | None = Field(default=None, sa_type=sa.JSON, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class ContentRead(ContentBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    source_id: int
    created_at: datetime
    updated_at: datetime


class ContentCreate(ContentBase):
    source_id: int = Field()
    external_id: str = Field()
    body: str = Field()
    external_url: Optional[str] = None
    title: Optional[str] = None
    excerpt: Optional[str] = None
    published_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None
    platform_metadata: Optional[dict[str, Any]] = None


class ContentUpdate(BaseSQLModel):
    external_url: str | None = None
    title: str | None = None
    body: str | None = None
    excerpt: str | None = None
    published_at: datetime | None = None
    synced_at: datetime | None = None
    platform_metadata: dict[str, Any] | None = None


class ContentSearchRequest(BaseSQLModel):
    query: str
    limit: int | None = 20
