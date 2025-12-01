from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fury_api.lib.repository import GenericSqlExtendedRepository
from .models import Author

__all__ = ["AuthorsRepository"]


class AuthorsRepository(GenericSqlExtendedRepository[Author]):
    def __init__(self) -> None:
        super().__init__(model_cls=Author)

    async def get_by_platform_id(self, session: AsyncSession, *, platform: str, external_id: str) -> Author | None:
        q = select(self._model_cls).where(
            self._model_cls.platform == platform,
            self._model_cls.external_id == external_id,
        )
        result = await session.exec(q)
        return result.scalar_one_or_none()

    async def get_by_platform_handle(self, session: AsyncSession, *, platform: str, handle: str) -> Author | None:
        """Get author by platform and handle (username)."""
        q = select(self._model_cls).where(
            self._model_cls.platform == platform,
            self._model_cls.handle == handle,
        )
        result = await session.exec(q)
        return result.scalar_one_or_none()
