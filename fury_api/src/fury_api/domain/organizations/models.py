from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel
from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship

__all__ = [
    "Organization",
    "OrganizationCreate",
    "OrganizationRead",
    "OrganizationUpdate",
]


class OrganizationBase(BaseSQLModel):
    name: str = ""


class Organization(OrganizationBase, BigIntIDModel, table=True):
    __tablename__: str = "organization"
    __id_attr__ = "id"

    id: int | None = Field(default=None, primary_key=True, sa_type=BigInteger, sa_column_kwargs={"autoincrement": True})

    users: Mapped[list["User"]] = Relationship(  # noqa (otherwise, circular dependency for User)
        back_populates="organization", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class OrganizationRead(OrganizationBase):
    id: int


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseSQLModel):
    name: str | None = None
