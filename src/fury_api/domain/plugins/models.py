from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = ["Plugin", "PluginCreate", "PluginRead", "PluginUpdate"]


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
    model_config = ConfigDict(extra="ignore")

    id: int
    data_source: str
    title: str
    properties: Optional[dict[str, Any]] = None


class PluginCreate(PluginBase):
    data_source: str = Field()
    title: str = Field()
    credentials: Optional[dict[str, Any]] = None
    properties: Optional[dict[str, Any]] = None


class PluginUpdate(BaseSQLModel):
    title: str | None = None
    credentials: dict[str, Any] | None = None
    properties: dict[str, Any] | None = None
