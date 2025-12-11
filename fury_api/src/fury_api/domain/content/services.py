from typing import TYPE_CHECKING, Any
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import select
from pgvector.sqlalchemy import Vector
from .models import Content, ContentBulkResult, ContentSearchRequest, FailedContent, ContentRead
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User
from fury_api.lib.pagination import CursorPage

from fury_api.lib.service import SqlService, with_uow
from fury_api.lib.integrations.base_ai import BaseAIClient
from fury_api.lib.factories.integrations_factory import IntegrationsFactory
from fury_api.lib.model_filters import Filter
from fury_api.lib.model_filters.models import FilterCombineLogic

if TYPE_CHECKING:
    pass

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

    @with_uow
    async def get_items_paginated(
        self,
        *,
        model_filters: list[Filter] | None = None,
        model_sorts: list[Filter] | None = None,
        filter_combine_logic: FilterCombineLogic = FilterCombineLogic.AND,
        include_author: bool = False,
        **kwargs: Any,
    ) -> CursorPage[ContentRead]:
        """Get paginated content with optional author join."""

        if include_author:
            # Step 1: Paginate Content using existing infrastructure
            content_page = await self.repository.list_with_pagination(
                self.session,
                model_filters=model_filters,
                model_sorts=model_sorts,
                filter_combine_logic=filter_combine_logic,
                filter_context={"organization_id": self.organization_id},
                **kwargs,
            )

            # Step 2: Bulk-load authors for paginated results
            authors_map = await self.repository.load_authors_for_content(
                self.session,
                {item.author_id for item in content_page.items if item.author_id},
            )

            # Step 3: Transform results to include authors
            items_with_authors = [
                ContentRead.model_validate(
                    {
                        **item.model_dump(),
                        "author": authors_map.get(item.author_id) if item.author_id else None,
                    },
                    from_attributes=True,
                )
                for item in content_page.items
            ]

            # Return properly paginated response
            return CursorPage(
                items=items_with_authors,
                total=content_page.total,
                current_page=content_page.current_page,
                current_page_backwards=content_page.current_page_backwards,
                previous_page=content_page.previous_page,
                next_page=content_page.next_page,
            )

        # Without author, use existing generic pagination
        return await self.repository.list_with_pagination(
            self.session,
            model_filters=model_filters,
            model_sorts=model_sorts,
            filter_combine_logic=filter_combine_logic,
            filter_context={"organization_id": self.organization_id},
            **kwargs,
        )

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
        include_author: bool = False,
    ) -> list[ContentRead]:
        limit = search.limit or 20

        async def _run(client: BaseAIClient) -> list[Content]:
            query_vector = await client.embed(search.query)
            vector_literal = sa.literal(query_vector, type_=Vector(len(query_vector)))

            q = select(self._model_cls).where(self._model_cls.embedding.is_not(None))

            # Apply filters if provided
            if model_filters:
                q = self.repository.apply_filters_to_semantic_query(
                    q,
                    model_filters,
                    filter_combine_logic,
                    organization_id=self.organization_id,
                )

            q = q.order_by(self._model_cls.embedding.op("<->")(vector_literal)).limit(limit)

            result = await self.session.exec(q)
            return result.scalars().all()

        # Get search results
        if ai_client is not None:
            content_items = await _run(ai_client)
        else:
            async with IntegrationsFactory.get_ai_client() as client:
                content_items = await _run(client)

        # If not including author, return as-is
        if not include_author:
            return [ContentRead.model_validate(item, from_attributes=True) for item in content_items]

        # Bulk-load authors for search results
        author_ids = {item.author_id for item in content_items if item.author_id}
        authors_map = await self.repository.load_authors_for_content(
            self.session,
            author_ids,
        )

        # Transform results to include authors
        return [
            ContentRead.model_validate(
                {
                    **item.model_dump(exclude={"embedding"}),
                    "author": authors_map.get(item.author_id) if item.author_id else None,
                }
            )
            for item in content_items
        ]

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
        result = await self.create_items_with_insertion_results(items, ai_client=ai_client)
        return len(result.created)

    @with_uow
    async def create_items_with_insertion_results(
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

    def convert_x_content_payload(
        self,
        post: Any,
        author_id: int,
    ) -> Content:
        """Convert X post object to Content model."""
        # For long-form tweets (>280 chars), use note_tweet.text; otherwise use text
        # Handle case where note_tweet might be None or attribute missing if dict passed
        if hasattr(post, "note_tweet") and post.note_tweet:
            body = post.note_tweet.text
        else:
            body = post.text

        body = body or ""

        # Excerpt should be truncated for display (limit to 280 chars)
        excerpt = body[:280] + "..." if len(body) > 280 else body

        # Extract quoted tweet data if this is a quote tweet
        extra_fields = None
        if getattr(post, "is_quote", False) and getattr(post, "quoted_tweet", None):
            qt = post.quoted_tweet

            if hasattr(qt, "note_tweet") and qt.note_tweet:
                quoted_text = qt.note_tweet.text
            else:
                quoted_text = qt.text
            quoted_text = quoted_text or ""

            qt_author = getattr(qt, "author", None)

            extra_fields = {
                "quoted_tweet": {
                    "id": qt.id,
                    "text": quoted_text,
                    "author": {
                        "id": qt_author.id if qt_author else None,
                        "name": qt_author.name if qt_author else None,
                        "username": qt_author.username if qt_author else None,
                        "avatar_url": qt_author.profile_image_url if qt_author else None,
                    }
                    if qt_author
                    else None,
                    "created_at": qt.created_at.isoformat() if qt.created_at else None,
                    "url": qt.tweet_url if hasattr(qt, "tweet_url") else None,
                }
            }

        # Store platform metadata (keep quoted_tweet_id for reference)
        # Clean up redundant fields to avoid duplication/bloat
        platform_metadata = post.model_dump() if hasattr(post, "model_dump") else {}

        # Remove fields that are already mapped to the Content model or Author model
        platform_metadata.pop("author", None)  # Stored in Author table
        platform_metadata.pop("text", None)  # Stored in body
        platform_metadata.pop("note_tweet", None)  # Stored in body

        referenced_tweets = getattr(post, "referenced_tweets", []) or []
        if getattr(post, "is_quote", False) and referenced_tweets:
            quoted_ref = next((ref for ref in referenced_tweets if ref.type == "quoted"), None)
            if quoted_ref:
                platform_metadata["quoted_tweet_id"] = quoted_ref.id

        return Content(
            organization_id=self.organization_id,
            author_id=author_id,
            external_id=post.id,
            external_url=getattr(post, "tweet_url", None),
            title=None,
            body=body,
            excerpt=excerpt,
            published_at=post.created_at,
            synced_at=datetime.now(timezone.utc),
            platform_metadata=platform_metadata,
            extra_fields=extra_fields,
        )
