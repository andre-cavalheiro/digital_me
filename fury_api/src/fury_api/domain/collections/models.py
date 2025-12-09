from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from typing import Any

from pydantic import AliasChoices, ConfigDict, Field as PydanticField
from sqlmodel import Field

from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = [
    "Collection",
    "CollectionRead",
    "CollectionCreate",
    "CollectionUpdate",
    "ContentCollection",
    "AuthorContribution",
    "CollectionAuthorStatistics",
]


# ============================================================================
# Collection Models
# ============================================================================


class CollectionBase(BaseSQLModel):
    """Base model for Collection."""

    type: str
    platform: str

    name: str
    external_id: str
    description: str | None = None
    collection_url: str | None = None

    last_synced_at: datetime | None = None


class Collection(CollectionBase, BigIntIDModel, table=True):
    """Collection table model."""

    __tablename__: str = "collection"
    __id_attr__ = "id"

    __table_args__ = (sa.UniqueConstraint("organization_id", "platform", "name", name="uq_collection_platform_name"),)

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    plugin_id: int | None = Field(default=None, sa_type=sa.BigInteger, foreign_key="plugin.id", nullable=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class CollectionRead(CollectionBase):
    """Collection read model for API responses."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    organization_id: int

    created_at: datetime
    updated_at: datetime


class CollectionCreate(CollectionBase):
    """Collection create model for API requests."""

    plugin_id: int | None


class CollectionUpdate(BaseSQLModel):
    """Collection update model for API requests."""

    name: str | None = None
    external_id: str | None = None
    description: str | None = None
    collection_url: str | None = None

    last_synced_at: datetime | None = None

    metadata_: dict[str, Any] | None = PydanticField(
        default=None,
        validation_alias=AliasChoices("metadata_", "metadata"),
        serialization_alias="metadata",
    )


# ============================================================================
# Content Collection Models (Junction Table)
# ============================================================================


class ContentCollection(BigIntIDModel, table=True):
    """ContentCollection junction table model."""

    __tablename__: str = "content_collection"
    __id_attr__ = "id"

    __table_args__ = (
        sa.UniqueConstraint("organization_id", "content_id", "collection_id", name="uq_content_collection"),
    )

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)

    content_id: int = Field(sa_type=sa.BigInteger, foreign_key="content.id", nullable=False)
    collection_id: int = Field(sa_type=sa.BigInteger, foreign_key="collection.id", nullable=False)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


# ============================================================================
# Collection Author Statistics Models
# ============================================================================


class AuthorContribution(BaseSQLModel):
    """Model representing an author's contribution to a collection."""

    author_id: int
    display_name: str
    handle: str
    avatar_url: str | None
    content_count: int
    percentage: float


class CollectionAuthorStatistics(BaseSQLModel):
    """Model representing author statistics for a collection."""

    collection_id: int
    total_content_count: int
    unique_author_count: int
    contributors: list[AuthorContribution]
