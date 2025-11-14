from __future__ import annotations

import inspect
from collections.abc import Generator, Mapping
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar
from uuid import UUID, uuid4
from pydantic import ConfigDict, constr
from sqlalchemy import event
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import TIMESTAMP, BigInteger, Field, SQLModel, func

from fury_api.lib.settings import config
from fury_api.lib.utils.dicts import merge_dicts
from fury_api.lib.utils.string import snake_case_to_camel

__all__ = [
    "metadata",
    "BaseSQLModel",
    "ExcludeUnset",
    "Auditable",
    "NullableAuditable",
    "BigIntIDModel",
    "UUIDModel",
    "Identifier",
    "PropertyIdentifier",
    "PropertyIdentifierPath",
    "SafeIdentifier",
    "Tag",
    "NoneNullable",
]

# Common regex patterns
re_common_lowercase = r"[a-z0-9_.-]"
re_common = r"[a-zA-Z0-9_.-]"

Identifier = constr(pattern=rf"^({re_common_lowercase}+)$")
PropertyIdentifier = constr(pattern=rf"^({re_common}+)$")
PropertyIdentifierPath = constr(pattern=rf"^({re_common}+)(\/{re_common}+)*$")
SafeIdentifier = constr(pattern=r"^([a-z0-9_]+)$")


# Set metadata
#  Note: schema is not set here and is only set on migrations to avoid issues with alembic
metadata = SQLModel.metadata
metadata.naming_convention = config.database.NAMING_CONVENTION


class Nullable(Enum):
    null = None


NoneNullable = Nullable | None


class BaseSQLModel(SQLModel):
    __id_attr__: str | None = None
    __force_exclude_if_none__: ClassVar[set[str]] = set()
    __exclude_from_update__: ClassVar[set[str]] = set()

    metadata = metadata

    model_config = ConfigDict(alias_generator=snake_case_to_camel, populate_by_name=True, extra="forbid")

    @classmethod
    def __init_subclass__(cls) -> None:
        """Extend class variables from base classes."""
        class_vars_to_extend = ("__force_exclude_if_none__", "__exclude_from_update__")
        for class_var in class_vars_to_extend:
            bases_class_vars = set.union(*(getattr(base, class_var, set()) for base in cls.__bases__))
            setattr(cls, class_var, bases_class_vars | getattr(cls, class_var, set()))

    def update(
        self, updates: dict[str, Any] | BaseSQLModel, patch: bool = False, patched_nested: bool | None = None
    ) -> BaseSQLModel:
        data_to_set = updates.model_dump(exclude_unset=True) if isinstance(updates, BaseSQLModel) else updates

        if self.__exclude_from_update__:
            data_to_set = {k: v for k, v in data_to_set.items() if k not in self.__exclude_from_update__}

        updated_data = data_to_set if not patch else merge_dicts(self.model_dump(), data_to_set)

        for key, value in updated_data.items():
            existing_value = getattr(self, key)
            if isinstance(existing_value, BaseSQLModel):
                existing_value.update(value, patch=patched_nested if patched_nested is not None else patch)
            else:
                setattr(self, key, value)

        return self

    def mark_as_modified(self, field: str) -> None:
        flag_modified(self, field)

    def rebuild_nested_models(self) -> None:
        """Rebuilds the nested models to ensure they are not dicts.

        This is a workaround for a bug in SQLModel with Pydantic V1 where nested models are dicts after fetching
        with SQLAlchemy.
        """
        pass

    def model_dump(
        self,
        *,
        include: set[str | int] | Mapping[str | int, Any] | None = None,
        exclude: set[str | int] | Mapping[str | int, Any] | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> dict[str, Any]:
        data = super().model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            round_trip=round_trip,
            warnings=warnings,
        )
        if self.__force_exclude_if_none__:
            for key in self.__force_exclude_if_none__:
                if data.get(key, -1) is None:
                    data.pop(key)
        return data

    def dict(
        self,
        include: set[str | int] | Mapping[str | int, Any] | None = None,
        exclude: set[str | int] | Mapping[str | int, Any] | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,  # retained for compatibility; ignored
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        return self.model_dump(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    @property
    @classmethod
    def __fields_by_alias__(cls) -> dict[str, Any]:
        """Get fields by alias."""
        return {meta.alias: field for field, meta in cls.model_fields.items() if meta.alias is not None}

    @classmethod
    def __fields_by_alias_iter__(cls) -> Generator[tuple[str, Any], None, None]:
        """Iterate over fields by alias."""
        yield from ((meta.alias, field) for field, meta in cls.model_fields.items() if meta.alias is not None)

    @classmethod
    def get_field_alias(cls, name: str) -> str | None:
        """Get field alias."""
        if name in cls.model_fields:
            return cls.model_fields[name].alias
        for alias, _ in cls.__fields_by_alias_iter__():
            if alias == name:
                return alias
        return None

    # https://github.com/pydantic/pydantic/issues/1577#issuecomment-790506164
    def __setattr__(self, name: str, value: Any) -> None:
        """Allow use properties with setters and access properties using their alias."""
        try:
            if name in self.model_fields:
                super().__setattr__(name, value)
            else:
                for alias, field in self.__fields_by_alias_iter__():
                    if alias == name:
                        super().__setattr__(field, value)
                        return
            super().__setattr__(name, value)
        except ValueError:
            setters = inspect.getmembers(
                self.__class__, predicate=lambda x: isinstance(x, property) and x.fset is not None
            )
            for setter_name, _ in setters:
                if setter_name == name:
                    object.__setattr__(self, name, value)
                    break
            else:
                raise

    def __getattr__(self, name: str) -> Any:
        """Enable object attributes to be accessed using its alias."""
        model_fields = self.model_fields
        if name in model_fields:
            return super().__getattribute__(name)
        for alias, field in self.__fields_by_alias_iter__():
            if alias == name:
                return getattr(self, field)
        return super().__getattribute__(name)


class ExcludeUnset(BaseSQLModel):
    """Base class for models that exclude unset fields.

    **Note**: This overrides any `exclude_unset` kwarg passed for the model and its nested models.
    """

    def dict(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        kwargs["exclude_unset"] = True
        return super().dict(*args, **kwargs)


class Auditable(BaseSQLModel):
    """Base class for models that have audit columns."""

    __exclude_from_update__: ClassVar[set[str]] = {"created_at", "created_by_id"}

    # User FKs are missing because we don't have a User model yet.
    #   It must also be nullable becase we don't have auth yet.

    created_at: datetime = Field(sa_type=TIMESTAMP(timezone=True), sa_column_kwargs={"server_default": func.now()})
    created_by_id: int | None = Field(sa_type=BigInteger, sa_column_kwargs={"name": "created_by"}, alias="createdBy")

    updated_at: datetime = Field(
        sa_type=TIMESTAMP(timezone=True), sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
    updated_by_id: int | None = Field(sa_type=BigInteger, sa_column_kwargs={"name": "updated_by"}, alias="updatedBy")


class NullableAuditable(Auditable):
    """Base class for models that have audit columns that are nullable."""

    created_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True), sa_column_kwargs={"server_default": func.now()}
    )
    created_by_id: int | None = Field(sa_type=BigInteger, sa_column_kwargs={"name": "created_by"}, alias="createdBy")

    updated_at: datetime | None = Field(
        sa_type=TIMESTAMP(timezone=True), sa_column_kwargs={"server_default": func.now(), "onupdate": func.now()}
    )
    updated_by_id: int | None = Field(sa_type=BigInteger, sa_column_kwargs={"name": "updated_by"}, alias="updatedBy")


class BigIntIDModel(BaseSQLModel):
    """Base class for models that have a bigint ID."""

    __id_attr__ = "id"
    __exclude_from_update__: ClassVar[set[str]] = {"id"}

    id: int | None = Field(default=None, primary_key=True, sa_type=BigInteger, sa_column_kwargs={"autoincrement": True})


class UUIDModel(BaseSQLModel):
    """Base class for models that have a UUID ID."""

    __id_attr__ = "id"
    __exclude_from_update__: ClassVar[set[str]] = {"id"}

    id: UUID = Field(primary_key=True, default_factory=uuid4)


class Tag(BaseSQLModel):
    """Tag model."""

    key: str = Field(..., nullable=False)
    value: str = Field(..., nullable=False)


@event.listens_for(Auditable, "before_insert", propagate=True)
def set_audit_fields(mapper: Any, connection: Any, target: Any) -> None:
    """Set audit fields on insert and update."""
    if target.created_by_id is None:
        target.created_by_id = target.updated_by_id
