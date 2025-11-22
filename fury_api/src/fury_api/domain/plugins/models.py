from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import ConfigDict, field_validator
from pydantic import Field as PydanticField
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = ["Plugin", "PluginCreate", "PluginRead", "PluginUpdate", "PluginDataSource"]


class PluginDataSource(str, Enum):
    """Allowed plugin data sources."""
    X = "x"
    COMMUNITY_ARCHIVE = "community_archive"


class PluginBase(BaseSQLModel):
    title: str


class Plugin(PluginBase, BigIntIDModel, table=True):
    __tablename__: str = "plugin"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    data_source: str = Field(nullable=False)
    title: str = Field(nullable=False)
    credentials: dict[str, Any] = Field(sa_type=sa.JSON, nullable=False)
    properties: dict[str, Any] = Field(sa_type=sa.JSON, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class PluginRead(PluginBase):
    # Ignore extra fields to allow direct SQLA model usage in responses.
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int
    organization_id: int
    data_source: str = PydanticField(alias="dataSource")
    title: str
    properties: Optional[dict[str, Any]] = None
    created_at: datetime


class PluginCreate(PluginBase):
    data_source: str = Field()
    title: str = Field()
    credentials: Optional[dict[str, Any]] = None
    properties: Optional[dict[str, Any]] = None

    @field_validator("data_source")
    @classmethod
    def validate_data_source(cls, v: str) -> str:
        """Validate that data_source is a supported plugin type."""
        allowed_sources = {source.value for source in PluginDataSource}
        if v not in allowed_sources:
            raise ValueError(
                f"Invalid data_source '{v}'. Must be one of: {', '.join(allowed_sources)}"
            )
        return v


class PluginUpdate(BaseSQLModel):
    title: str | None = None
    credentials: dict[str, Any] | None = None
    properties: dict[str, Any] | None = None
