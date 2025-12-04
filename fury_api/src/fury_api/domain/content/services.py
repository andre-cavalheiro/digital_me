from typing import TYPE_CHECKING, Any
from collections.abc import Iterable, Sequence

import sqlalchemy as sa
from sqlalchemy import select
from pgvector.sqlalchemy import Vector
from .models import Content, ContentBulkResult, ContentSearchRequest, FailedContent
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService, with_uow
from fury_api.lib.integrations.base_ai import BaseAIClient
from fury_api.lib.factories.integrations_factory import IntegrationsFactory
from fury_api.lib.model_filters import Filter
from fury_api.lib.model_filters.models import FilterCombineLogic

if TYPE_CHECKING:
    from fury_api.lib.integrations import XAppClient

__all__ = ["ContentsService"]


class ContentsService(SqlService[Content]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs: Any,
    ):
        super().__init__(Content, uow, auth_user=auth_user, **kwargs)

    async def search_external_sources(
        self,
        search: ContentSearchRequest,
        *,
        x_client: "XAppClient",
    ) -> list[dict[str, Any]]:
        """
        Perform a basic external search using the X App integration.

        Args:
            search: Search payload containing query and optional limit.
            x_client: Configured X client used to execute the search.

        Returns:
            List of post dictionaries from X (raw response data or empty list).
        """
        response = x_client.search_all(query=search.query, max_results=search.limit)
        return [post.model_dump() for post in response.data] if response and response.data else []

    @with_uow
    async def get_by_ids(self, ids: Sequence[int]) -> list[Content]:
        if not ids:
            return []

        query = select(self._model_cls).where(self._model_cls.id.in_(ids)).order_by(self._model_cls.id)
        return await self.repository.list(self.session, query=query)

    @with_uow
    async def semantic_search(
        self,
        search: ContentSearchRequest,
        *,
        ai_client: BaseAIClient | None = None,
        model_filters: list[Filter] | None = None,
        filter_combine_logic: FilterCombineLogic = FilterCombineLogic.AND,
    ) -> list[Content]:
        limit = search.limit or 20

        async def _run(client: BaseAIClient) -> list[Content]:
            query_vector = await client.embed(search.query)
            vector_literal = sa.literal(query_vector, type_=Vector(len(query_vector)))

            q = select(self._model_cls).where(self._model_cls.embedding.is_not(None))

            # Apply filters if provided
            if model_filters:
                q = self._apply_filters_to_semantic_query(q, model_filters, filter_combine_logic)

            q = q.order_by(self._model_cls.embedding.op("<->")(vector_literal)).limit(limit)

            result = await self.session.exec(q)
            return result.scalars().all()

        if ai_client is not None:
            return await _run(ai_client)

        async with IntegrationsFactory.get_ai_client() as client:
            return await _run(client)

    def _apply_filters_to_semantic_query(
        self,
        query: select,
        filters: list[Filter],
        combine_logic: FilterCombineLogic = FilterCombineLogic.AND,
    ) -> select:
        """
        Apply model filters to the semantic search query with combine logic support.

        Handles special case for collection_id which requires filtering
        via the ContentCollection junction table. Direct Content filters
        (like author_id) are applied using the repository's filter adapter.

        Args:
            query: Base SQLAlchemy select query
            filters: List of Filter objects to apply
            combine_logic: How to combine filters (AND or OR)

        Returns:
            Modified query with filters applied
        """
        from fury_api.domain.collections.models import ContentCollection
        from fury_api.lib.model_filters import FilterOp
        from sqlalchemy import or_

        # Separate collection filters from direct Content filters
        collection_filters = []
        content_filters = []

        for filter_ in filters:
            if filter_.field == "collection_id":
                collection_filters.append(filter_)
            else:
                content_filters.append(filter_)

        # Apply direct Content filters using repository's filter adapter
        if content_filters:
            query = self.repository._apply_model_filters(query, content_filters, combine_logic)

        # Handle collection filters with subquery
        if collection_filters:
            collection_conditions = []
            for filter_ in collection_filters:
                # Build subquery to find content_ids in matching collections
                subquery = (
                    select(ContentCollection.content_id)
                    .where(ContentCollection.organization_id == self.organization_id)
                )

                # Apply filter operation to collection_id
                if filter_.op == FilterOp.EQ:
                    # Ensure value is integer
                    value = int(filter_.value) if not isinstance(filter_.value, int) else filter_.value
                    subquery = subquery.where(ContentCollection.collection_id == value)
                elif filter_.op == FilterOp.IN:
                    # Ensure all values are integers
                    raw_values = filter_.value if isinstance(filter_.value, list) else [filter_.value]
                    values = [int(v) if not isinstance(v, int) else v for v in raw_values]
                    subquery = subquery.where(ContentCollection.collection_id.in_(values))
                elif filter_.op == FilterOp.NEQ:
                    value = int(filter_.value) if not isinstance(filter_.value, int) else filter_.value
                    subquery = subquery.where(ContentCollection.collection_id != value)
                elif filter_.op == FilterOp.NOT_IN:
                    raw_values = filter_.value if isinstance(filter_.value, list) else [filter_.value]
                    values = [int(v) if not isinstance(v, int) else v for v in raw_values]
                    subquery = subquery.where(~ContentCollection.collection_id.in_(values))

                # Build condition for this collection filter
                collection_conditions.append(self._model_cls.id.in_(subquery))

            # Apply collection conditions based on combine_logic
            if combine_logic == FilterCombineLogic.OR:
                query = query.where(or_(*collection_conditions))
            else:
                # AND logic: apply each condition separately
                for condition in collection_conditions:
                    query = query.where(condition)

        return query

    def _prepare_embedding_text(self, content: Content) -> str:
        """
        Prepare text for embedding generation.

        For quote tweets, combines main tweet text with quoted tweet text
        to enable semantic search across both.
        """
        text = content.body

        # If this is a quote tweet, append the quoted tweet text
        if content.extra_fields and "quoted_tweet" in content.extra_fields:
            quoted_text = content.extra_fields["quoted_tweet"].get("text")
            if quoted_text:
                text = f"{text}\n\n[Quoted: {quoted_text}]"

        return text

    async def _embed_contents(
        self,
        contents: Iterable[Content],
        *,
        ai_client: BaseAIClient | None = None,
    ) -> None:
        targets = [content for content in contents if content.embedding is None and content.body]
        if not targets:
            return

        async def apply(client: BaseAIClient) -> None:
            embedding_texts = [self._prepare_embedding_text(c) for c in targets]
            embeddings = await client.embed_batch(embedding_texts)
            for content, embedding in zip(targets, embeddings, strict=False):
                content.embedding = embedding

        if ai_client is not None:
            await apply(ai_client)
            return

        async with IntegrationsFactory.get_ai_client() as client:
            await apply(client)

    @with_uow
    async def create_item(self, item: Content, *, ai_client: BaseAIClient | None = None) -> Content:
        await self._embed_contents([item], ai_client=ai_client)
        return await self.repository.add(self.session, item)

    async def create_items(
        self,
        items: list[Content],
        *,
        ai_client: BaseAIClient | None = None,
    ) -> int:
        result = await self.create_items_with_results(items, ai_client=ai_client)
        return len(result.created)

    @with_uow
    async def create_items_with_results(
        self,
        items: list[Content],
        *,
        ai_client: BaseAIClient | None = None,
    ) -> ContentBulkResult:
        await self._embed_contents(items, ai_client=ai_client)

        created: list[Content] = []
        failed: list[FailedContent] = []
        for item in items:
            try:
                created_item = await self.repository.add(self.session, item)
                created.append(created_item)
            except Exception as e:  # pragma: no cover - defensive
                if self.session is not None:
                    await self.session.rollback()
                failed.append(
                    FailedContent(
                        error=str(e),
                        external_id=getattr(item, "external_id", None),
                        title=getattr(item, "title", None),
                    )
                )
                continue

        return ContentBulkResult(
            created=created,
            failed=failed,
        )

    @with_uow
    async def get_by_external_ids(self, external_ids: Sequence[str]) -> list[Content]:
        """Fetch contents by external IDs."""
        if not external_ids:
            return []

        query = select(self._model_cls).where(self._model_cls.external_id.in_(external_ids))
        return await self.repository.list(self.session, query=query)
