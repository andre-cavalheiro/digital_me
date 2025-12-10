from sqlalchemy import select

from fury_api.lib.service import SqlService, with_uow
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User
from .models import Collection, ContentCollection, CollectionAuthorStatistics
from .repository import CollectionsRepository, ContentCollectionsRepository

__all__ = ["CollectionsService", "ContentCollectionsService"]


class CollectionsService(SqlService[Collection]):
    """Service for managing collections."""

    repository_class = CollectionsRepository

    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Collection, uow, auth_user=auth_user, **kwargs)

    @with_uow
    async def get_by_platform_name(
        self,
        *,
        platform: str,
        name: str,
    ) -> Collection | None:
        return await self.repository.get_by_platform_name(
            self.session, organization_id=self.organization_id, platform=platform, name=name
        )

    @with_uow
    async def get_by_platform_external_id(
        self,
        *,
        platform: str,
        external_id: str,
    ) -> Collection | None:
        return await self.repository.get_by_platform_external_id(
            self.session, organization_id=self.organization_id, platform=platform, external_id=external_id
        )

    @with_uow
    async def get_author_statistics(self, collection_id: int) -> CollectionAuthorStatistics:
        """
        Get author contribution statistics for a collection.

        Args:
            collection_id: ID of the collection

        Returns:
            CollectionAuthorStatistics with contributor information
        """
        total_count, contributors = await self.repository.get_author_statistics(
            self.session, organization_id=self.organization_id, collection_id=collection_id
        )

        return CollectionAuthorStatistics(
            collection_id=collection_id,
            total_content_count=total_count,
            unique_author_count=len(contributors),
            contributors=contributors,
        )


class ContentCollectionsService(SqlService[ContentCollection]):
    """Service for managing content-collection relationships."""

    repository_class = ContentCollectionsRepository

    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(ContentCollection, uow, auth_user=auth_user, **kwargs)

    @with_uow
    async def link_content_to_collection(
        self,
        *,
        content_id: int,
        collection_id: int,
    ) -> ContentCollection:
        """
        Link a piece of content to a collection.

        This method is idempotent - it will not create duplicates if the link already exists.

        Args:
            content_id: ID of the content
            collection_id: ID of the collection

        Returns:
            The existing or newly created ContentCollection link
        """
        if self.organization_id is None:
            raise ValueError("organization_id is required to link content to a collection")

        collection = await self.uow.collections.get_by_id(self.session, collection_id)
        if collection is None or collection.organization_id != self.organization_id:
            raise ValueError(f"Collection {collection_id} not found for organization {self.organization_id}")

        content = await self.uow.contents.get_by_id(self.session, content_id)
        if content is None:
            raise ValueError(f"Content {content_id} not found")

        query = select(ContentCollection).where(
            ContentCollection.organization_id == self.organization_id,
            ContentCollection.content_id == content_id,
            ContentCollection.collection_id == collection_id,
        )

        result = await self.session.execute(query)
        existing_link = result.scalar_one_or_none()
        if existing_link:
            return existing_link

        link_data = ContentCollection(
            organization_id=self.organization_id,
            content_id=content_id,
            collection_id=collection_id,
        )

        return await self.repository.add(self.session, link_data)

    @with_uow
    async def unlink_content_from_collection(
        self,
        *,
        content_id: int,
        collection_id: int,
    ) -> bool:
        """
        Unlink a piece of content from a collection.

        Args:
            content_id: ID of the content
            collection_id: ID of the collection

        Returns:
            True if the link was removed, False if it didn't exist
        """
        if self.organization_id is None:
            raise ValueError("organization_id is required to unlink content from a collection")

        query = select(ContentCollection).where(
            ContentCollection.organization_id == self.organization_id,
            ContentCollection.content_id == content_id,
            ContentCollection.collection_id == collection_id,
        )

        result = await self.session.execute(query)
        link = result.scalar_one_or_none()

        if not link:
            return False

        await self.repository.delete(self.session, link.id)
        return True

    @with_uow
    async def get_collections_for_content(self, content_id: int) -> list[int]:
        """
        Get all collection IDs that a piece of content belongs to.

        Args:
            content_id: ID of the content

        Returns:
            List of collection IDs
        """
        query = select(ContentCollection.collection_id).where(
            ContentCollection.organization_id == self.organization_id,
            ContentCollection.content_id == content_id,
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    @with_uow
    async def get_content_for_collection(self, collection_id: int) -> list[int]:
        """
        Get all content IDs that belong to a collection.

        Args:
            collection_id: ID of the collection

        Returns:
            List of content IDs
        """
        query = select(ContentCollection.content_id).where(
            ContentCollection.organization_id == self.organization_id,
            ContentCollection.collection_id == collection_id,
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())
