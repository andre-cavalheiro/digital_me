from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fury_api.lib.repository import GenericSqlExtendedRepository
from .models import Collection, ContentCollection

__all__ = ["CollectionsRepository", "ContentCollectionsRepository"]


class CollectionsRepository(GenericSqlExtendedRepository[Collection]):
    def __init__(self) -> None:
        super().__init__(model_cls=Collection)

    async def get_by_platform_name(
        self, session: AsyncSession, *, organization_id: int, platform: str, name: str
    ) -> Collection | None:
        q = select(self._model_cls).where(
            self._model_cls.organization_id == organization_id,
            self._model_cls.platform == platform,
            self._model_cls.name == name,
        )
        result = await session.exec(q)
        return result.scalar_one_or_none()


class ContentCollectionsRepository(GenericSqlExtendedRepository[ContentCollection]):
    def __init__(self) -> None:
        super().__init__(model_cls=ContentCollection)
