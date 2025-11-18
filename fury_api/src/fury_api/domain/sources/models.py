from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = [
    "Source",
    "SourceCreate",
    "SourceRead",
    "SourceUpdate",
    "Content",
    "ContentCreate",
    "ContentRead",
    "ContentUpdate",
    "SourceGroup",
    "SourceGroupCreate",
    "SourceGroupRead",
    "SourceGroupUpdate",
    "SourceGroupMember",
    "SourceGroupMemberCreate",
    "SourceGroupMemberRead",
    "SourceGroupMemberUpdate",
    "DocumentSourceConfig",
    "DocumentSourceConfigCreate",
    "DocumentSourceConfigRead",
    "DocumentSourceConfigUpdate",
    "Citation",
    "CitationCreate",
    "CitationRead",
    "CitationUpdate",
]


class SourceBase(BaseSQLModel):
    source_type: str
    external_id: str | None = None
    display_name: str
    handle: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    platform_type: str
    is_active: bool = True
    last_synced_at: datetime | None = None
    sync_status: str = "pending"
    sync_error: str | None = None


class Source(SourceBase, BigIntIDModel, table=True):
    __tablename__: str = "source"
    __id_attr__ = "id"

    __table_args__ = (
        sa.UniqueConstraint("plugin_id", "external_id", "source_type", name="uq_source_plugin_external_type"),
    )

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    plugin_id: int = Field(sa_type=sa.BigInteger, foreign_key="plugin.id", nullable=False)
    user_id: int = Field(sa_type=sa.BigInteger, foreign_key="user.id", nullable=False)
    source_type: str = Field(nullable=False)
    external_id: str | None = Field(default=None, nullable=True)
    display_name: str = Field(nullable=False)
    handle: str | None = Field(default=None, nullable=True)
    avatar_url: str | None = Field(default=None, nullable=True)
    profile_url: str | None = Field(default=None, nullable=True)
    platform_type: str = Field(nullable=False)
    is_active: bool = Field(True, nullable=False)
    last_synced_at: datetime | None = Field(default=None, nullable=True)
    sync_status: str = Field("pending", nullable=False)
    sync_error: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SourceRead(SourceBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    plugin_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class SourceCreate(SourceBase):
    plugin_id: int = Field()
    user_id: int | None = None
    platform_type: str = Field()
    display_name: str = Field()
    source_type: str = Field()
    external_id: Optional[str] = None
    handle: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_url: Optional[str] = None
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    sync_status: str = "pending"
    sync_error: Optional[str] = None


class SourceUpdate(BaseSQLModel):
    display_name: str | None = None
    handle: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    is_active: bool | None = None
    sync_status: str | None = None
    sync_error: str | None = None


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


class SourceGroupBase(BaseSQLModel):
    name: str
    description: str | None = None
    color: str | None = None
    icon: str | None = None


class SourceGroup(SourceGroupBase, BigIntIDModel, table=True):
    __tablename__: str = "source_group"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    user_id: int = Field(sa_type=sa.BigInteger, foreign_key="user.id", nullable=False)
    name: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)
    color: str | None = Field(default=None, nullable=True)
    icon: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SourceGroupRead(SourceGroupBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    user_id: int
    created_at: datetime


class SourceGroupCreate(SourceGroupBase):
    name: str = Field()
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None


class SourceGroupUpdate(BaseSQLModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None


class SourceGroupMemberBase(BaseSQLModel):
    source_group_id: int
    source_id: int


class SourceGroupMember(SourceGroupMemberBase, BigIntIDModel, table=True):
    __tablename__: str = "source_group_member"
    __id_attr__ = "id"

    __table_args__ = (sa.UniqueConstraint("source_group_id", "source_id", name="uq_source_group_member"),)

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    source_group_id: int = Field(sa_type=sa.BigInteger, foreign_key="source_group.id", nullable=False)
    source_id: int = Field(sa_type=sa.BigInteger, foreign_key="source.id", nullable=False)
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    added_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SourceGroupMemberRead(SourceGroupMemberBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    added_at: datetime


class SourceGroupMemberCreate(SourceGroupMemberBase):
    source_group_id: int = Field()
    source_id: int = Field()


class SourceGroupMemberUpdate(BaseSQLModel):
    pass


class DocumentSourceConfigBase(BaseSQLModel):
    document_id: int
    source_group_id: int | None = None
    source_id: int | None = None
    enabled: bool = True


class DocumentSourceConfig(DocumentSourceConfigBase, BigIntIDModel, table=True):
    __tablename__: str = "document_source_config"
    __id_attr__ = "id"

    __table_args__ = (
        sa.CheckConstraint(
            "(source_group_id IS NOT NULL) OR (source_id IS NOT NULL)", name="ck_document_source_config_target"
        ),
        sa.UniqueConstraint("document_id", "source_group_id", name="uq_document_source_config_group"),
        sa.UniqueConstraint("document_id", "source_id", name="uq_document_source_config_source"),
    )

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    document_id: int = Field(sa_type=sa.BigInteger, foreign_key="document.id", nullable=False)
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    source_group_id: int | None = Field(sa_type=sa.BigInteger, foreign_key="source_group.id", nullable=True)
    source_id: int | None = Field(sa_type=sa.BigInteger, foreign_key="source.id", nullable=True)
    enabled: bool = Field(True, nullable=False)
    added_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class DocumentSourceConfigRead(DocumentSourceConfigBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    added_at: datetime


class DocumentSourceConfigCreate(DocumentSourceConfigBase):
    document_id: int = Field()
    source_group_id: Optional[int] = None
    source_id: Optional[int] = None
    enabled: bool = True


class DocumentSourceConfigUpdate(BaseSQLModel):
    enabled: bool | None = None


class CitationBase(BaseSQLModel):
    document_id: int | None = Field(default=None, alias="documentId")
    content_id: int
    citation_number: int
    position_in_doc: int | None = Field(default=None, alias="position")
    section_index: int | None = Field(default=None, alias="sectionIndex")


class Citation(CitationBase, BigIntIDModel, table=True):
    __tablename__: str = "citation"
    __id_attr__ = "id"

    __table_args__ = (sa.UniqueConstraint("document_id", "citation_number", name="uq_citation_document_number"),)

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    document_id: int = Field(sa_type=sa.BigInteger, foreign_key="document.id", nullable=False)
    content_id: int = Field(sa_type=sa.BigInteger, foreign_key="content.id", nullable=False)
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    citation_number: int = Field(nullable=False)
    position_in_doc: int | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class CitationRead(CitationBase):
    model_config = ConfigDict(extra="ignore")

    id: int
    organization_id: int
    created_at: datetime


class CitationCreate(CitationBase):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    citation_number: int = Field(alias="marker")
    position_in_doc: Optional[int] = Field(default=None, alias="position")
    section_index: Optional[int] = Field(default=None, alias="sectionIndex")

    document_id: int = Field(default=None)
    content_id: int = Field()


class CitationUpdate(BaseSQLModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    citation_number: int | None = Field(default=None, alias="marker")
    position_in_doc: int | None = Field(default=None, alias="position")
    section_index: int | None = Field(default=None, alias="sectionIndex")
