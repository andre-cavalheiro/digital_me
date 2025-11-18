from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from fury_api.lib.repository import GenericSqlExtendedRepository
from fury_api.lib.settings import config

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession

__all__ = [
    "AsyncAbstractUnitOfWork",
    "AsyncSqlAlchemyUnitOfWork",
    "UnitOfWork",
    "UnitOfWorkError",
    "UnitOfWorkRepositoryNotFoundError",
]

T = TypeVar("T", bound=SQLModel)


class AsyncAbstractUnitOfWork(ABC):
    async def __aenter__(self) -> AsyncAbstractUnitOfWork:
        """This method is called when entering the context manager."""
        return self

    async def __aexit__(self, *args: tuple, **kwargs: dict) -> None:
        """This method is called when exiting the context manager."""
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError


class AsyncSqlAlchemyUnitOfWork(AsyncAbstractUnitOfWork):
    def __init__(
        self, session_factory: sessionmaker, autocommit: bool = False, autocommit_ignore_nested: bool = True
    ) -> None:
        self._session_factory = session_factory
        self.session: AsyncSession | None = None

        self.autocommit = autocommit
        self.autocommit_ignore_nested = autocommit_ignore_nested
        self._context_depth = 0

        super().__init__()

    @property
    def is_in_context(self) -> bool:
        return self._context_depth > 0

    @property
    def is_root_context(self) -> bool:
        return self._context_depth == 1

    async def _begin_new_session(self):
        self.session = self._session_factory()
        # Note: post_begin_session_hook is called in with_organization after organization_id is set
        return self.session

    async def __aenter__(self) -> AsyncSqlAlchemyUnitOfWork:
        """This method is called when entering the context manager."""
        self._context_depth += 1

        if self.session is None:
            await self._begin_new_session()

        return await super().__aenter__()

    async def __aexit__(self, *args: tuple, **kwargs: dict) -> None:
        """This method is called when exiting the context manager."""
        self._context_depth -= 1

        if self.is_in_context:
            if args and args[0] is not None:
                return
            if self.autocommit and not self.autocommit_ignore_nested:
                await self.commit()
            return

        try:
            if args and args[0] is not None:
                await self.rollback()
            else:
                if self.autocommit:
                    await self.commit()

            await super().__aexit__(*args, **kwargs)
            await self.session.close()
        finally:
            self.session = None

    async def commit(self) -> None:
        if self.session is not None:
            await self.pre_commit_hook()
            await self.session.commit()

    async def rollback(self) -> None:
        if self.session is not None:
            await self.session.rollback()

    async def post_begin_session_hook(self) -> None:
        """This method is called after creating a new session."""
        pass

    async def pre_commit_hook(self) -> None:
        """This method is called before committing the session."""
        pass


class UnitOfWork(AsyncSqlAlchemyUnitOfWork):
    def __init__(
        self,
        session_factory: sessionmaker,
        autocommit: bool = False,
        autocommit_ignore_nested: bool = True,
        *,
        organization_id: int | None = None,
        read_only: bool = False,
        query_user: bool = False,
    ):
        super().__init__(session_factory, autocommit, autocommit_ignore_nested)
        self.organization_id = organization_id
        self.read_only = read_only
        self.query_user = query_user

    async def __aenter__(self) -> UnitOfWork:
        """This method is called when entering the context manager."""
        if self.is_in_context:
            return await super().__aenter__()

        # Avoid circular import
        from fury_api.domain.organizations.repository import OrganizationRepository
        from fury_api.domain.users.repository import UserRepository
        from fury_api.domain.plugins.repository import PluginRepository
        from fury_api.domain.documents.repository import DocumentRepository, DocumentContentRepository
        from fury_api.domain.conversations.repository import ConversationRepository, MessageRepository
        from fury_api.domain.sources.repository import (
            SourceRepository,
            ContentRepository,
            SourceGroupRepository,
            SourceGroupMemberRepository,
            DocumentSourceConfigRepository,
            CitationRepository,
        )

        self.organizations = OrganizationRepository()
        self.users = UserRepository()
        self.plugins = PluginRepository()
        self.documents = DocumentRepository()
        self.document_contents = DocumentContentRepository()
        self.conversations = ConversationRepository()
        self.messages = MessageRepository()
        self.sources = SourceRepository()
        self.contents = ContentRepository()
        self.source_groups = SourceGroupRepository()
        self.source_group_members = SourceGroupMemberRepository()
        self.document_source_configs = DocumentSourceConfigRepository()
        self.citations = CitationRepository()

        self._repos = {
            repo._model_cls: repo
            for repo in (
                self.organizations,
                self.users,
                self.plugins,
                self.documents,
                self.document_contents,
                self.conversations,
                self.messages,
                self.sources,
                self.contents,
                self.source_groups,
                self.source_group_members,
                self.document_source_configs,
                self.citations,
            )
        }

        return await super().__aenter__()

    async def __aexit__(self, *args: tuple, **kwargs: dict) -> None:
        """This method is called when exiting the context manager."""
        await super().__aexit__(*args, **kwargs)

        if self.is_in_context:
            return

        del self._repos
        del self.organizations
        del self.users
        del self.plugins
        del self.documents
        del self.document_contents
        del self.conversations
        del self.messages
        del self.sources
        del self.contents
        del self.source_groups
        del self.source_group_members
        del self.document_source_configs
        del self.citations

    def get_repository(self, model_cls: type[T]) -> GenericSqlExtendedRepository[T]:
        """Return the repository for the given model class."""
        repo = self._repos.get(model_cls)
        if repo is None:
            raise UnitOfWorkRepositoryNotFoundError(model_cls)
        return repo

    @asynccontextmanager
    async def with_organization(
        self, organization_id: int, *, read_only: bool | None = None, query_user: bool | None = None
    ) -> UnitOfWork:
        """Context manager to change the current organization."""
        if self.organization_id is not None and organization_id != self.organization_id:
            raise ValueError("Cannot change organization_id when already in a tenant context")

        backup_args = (self.organization_id, self.read_only, self.query_user)

        async with self:
            self.organization_id = organization_id
            if read_only is not None:
                self.read_only = read_only
            if query_user is not None:
                self.query_user = query_user

            await self.post_begin_session_hook()
            try:
                yield self
                await self.pre_commit_hook()
            finally:
                self.organization_id, self.read_only, self.query_user = backup_args

    async def post_begin_session_hook(self) -> None:
        """This method is called after creating a new session."""
        # Skip if we're in a nested context - don't override the parent's role!
        if self._context_depth > 1:
            return

        if config.database.TENANT_ROLE_ENABLED and self.organization_id is not None:
            if self.query_user:
                role = config.database.TENANT_QUERY_ROLE_RO
            elif self.read_only:
                role = config.database.TENANT_ROLE_RO
            else:
                role = config.database.TENANT_ROLE

            await self.session.exec(text(f"set session role {role}"))
            await self.session.exec(text(f"set {config.database.TENANT_PARAMETER} = {self.organization_id}"))

    async def pre_commit_hook(self) -> None:
        """This method is called before committing the session."""
        if self._context_depth > 1:
            return

        with suppress(SQLAlchemyError):
            await self.session.exec(text("reset role"))


class UnitOfWorkError(Exception):
    """Base exception for UnitOfWork errors."""


class UnitOfWorkRepositoryNotFoundError(UnitOfWorkError):
    """Raised when a repository is not found."""

    def __init__(self, model_cls: type[SQLModel]):
        super().__init__(f"No repository found for model {model_cls.__name__}")
        self.model_cls = model_cls
