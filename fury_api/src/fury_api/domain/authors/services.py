from .models import Author
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User
from fury_api.lib.service import SqlService, with_uow

__all__ = [
    "AuthorsService",
]


class AuthorsService(SqlService[Author]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Author, uow, auth_user=auth_user, **kwargs)

    @with_uow
    async def get_by_platform_id(
        self,
        *,
        platform: str,
        external_id: str,
    ) -> Author | None:
        return await self.repository.get_by_platform_id(self.session, platform=platform, external_id=external_id)
