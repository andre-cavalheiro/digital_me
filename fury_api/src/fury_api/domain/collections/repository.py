from sqlalchemy import select, func, cast, Float
from sqlmodel.ext.asyncio.session import AsyncSession

from fury_api.lib.repository import GenericSqlExtendedRepository
from fury_api.domain.authors.models import Author
from fury_api.domain.content.models import Content
from .models import Collection, ContentCollection, AuthorContribution

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

    async def get_by_platform_external_id(
        self, session: AsyncSession, *, organization_id: int, platform: str, external_id: str
    ) -> Collection | None:
        q = select(self._model_cls).where(
            self._model_cls.organization_id == organization_id,
            self._model_cls.platform == platform,
            self._model_cls.external_id == external_id,
        )
        result = await session.exec(q)
        return result.scalar_one_or_none()

    async def get_author_statistics(
        self, session: AsyncSession, *, organization_id: int, collection_id: int
    ) -> tuple[int, list[AuthorContribution]]:
        """
        Get author contribution statistics for a collection.

        Returns:
            Tuple of (total_content_count, list of author contributions)
        """
        # Subquery to get total count
        total_count_subquery = (
            select(func.count(Content.id))
            .select_from(ContentCollection)
            .join(Content, ContentCollection.content_id == Content.id)
            .where(
                ContentCollection.organization_id == organization_id,
                ContentCollection.collection_id == collection_id,
            )
        )

        total_result = await session.exec(total_count_subquery)
        total_count = total_result.scalar_one() or 0

        if total_count == 0:
            return 0, []

        # Main query to get author statistics
        q = (
            select(
                Author.id.label("author_id"),
                Author.display_name,
                Author.handle,
                Author.avatar_url,
                func.count(Content.id).label("content_count"),
                cast(func.count(Content.id) * 100.0 / total_count, Float).label("percentage"),
            )
            .select_from(ContentCollection)
            .join(Content, ContentCollection.content_id == Content.id)
            .join(Author, Content.author_id == Author.id)
            .where(
                ContentCollection.organization_id == organization_id,
                ContentCollection.collection_id == collection_id,
            )
            .group_by(Author.id, Author.display_name, Author.handle, Author.avatar_url)
            .order_by(func.count(Content.id).desc())
        )

        result = await session.exec(q)
        rows = result.all()

        contributors = [
            AuthorContribution(
                author_id=row.author_id,
                display_name=row.display_name,
                handle=row.handle,
                avatar_url=row.avatar_url,
                content_count=row.content_count,
                percentage=row.percentage,
            )
            for row in rows
        ]

        return total_count, contributors


class ContentCollectionsRepository(GenericSqlExtendedRepository[ContentCollection]):
    def __init__(self) -> None:
        super().__init__(model_cls=ContentCollection)
