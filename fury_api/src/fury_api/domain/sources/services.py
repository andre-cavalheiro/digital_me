from .models import Citation, DocumentSourceConfig, Source, SourceGroup, SourceGroupMember
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService

__all__ = [
    "SourcesService",
    "SourceGroupsService",
    "SourceGroupMembersService",
    "DocumentSourceConfigsService",
    "CitationsService",
]


class SourcesService(SqlService[Source]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Source, uow, auth_user=auth_user, **kwargs)


class SourceGroupsService(SqlService[SourceGroup]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(SourceGroup, uow, auth_user=auth_user, **kwargs)


class SourceGroupMembersService(SqlService[SourceGroupMember]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(SourceGroupMember, uow, auth_user=auth_user, **kwargs)


class DocumentSourceConfigsService(SqlService[DocumentSourceConfig]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(DocumentSourceConfig, uow, auth_user=auth_user, **kwargs)


class CitationsService(SqlService[Citation]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Citation, uow, auth_user=auth_user, **kwargs)
