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
    ) -> list[Content]:
        limit = search.limit or 20

        async def _run(client: BaseAIClient) -> list[Content]:
            query_vector = await client.embed(search.query)
            vector_literal = sa.literal(query_vector, type_=Vector(len(query_vector)))

            q = select(self._model_cls).where(self._model_cls.embedding.is_not(None))

            q = q.order_by(self._model_cls.embedding.op("<->")(vector_literal)).limit(limit)

            result = await self.session.exec(q)
            return result.scalars().all()

        if ai_client is not None:
            return await _run(ai_client)

        async with IntegrationsFactory.get_ai_client() as client:
            return await _run(client)

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
