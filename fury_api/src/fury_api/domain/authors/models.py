from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = [
    "Author",
    "AuthorCreate",
    "AuthorRead",
    "AuthorUpdate",
]


class AuthorBase(BaseSQLModel):
    platform: str
    external_id: str
    display_name: str
    handle: str
    avatar_url: str
    profile_url: str
    bio: str | None = None
    follower_count: int | None
    following_count: int | None


class Author(AuthorBase, BigIntIDModel, table=True):
    __tablename__: str = "author"
    __id_attr__ = "id"

    __table_args__ = (sa.UniqueConstraint("platform", "external_id", name="uq_author_platform_external"),)

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class AuthorRead(AuthorBase):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: int
    created_at: datetime
    updated_at: datetime


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(BaseSQLModel):
    display_name: str
    avatar_url: str
    profile_url: str
    bio: str | None = None
