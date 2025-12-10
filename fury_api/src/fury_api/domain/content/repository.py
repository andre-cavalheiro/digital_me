from typing import TYPE_CHECKING

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Content
from fury_api.domain.authors.models import Author, AuthorRead
from fury_api.lib.repository import GenericSqlExtendedRepository
from fury_api.lib.model_filters import Filter, FilterOp
from fury_api.lib.model_filters.models import FilterCombineLogic

if TYPE_CHECKING:
    pass

__all__ = ["ContentRepository"]


class ContentRepository(GenericSqlExtendedRepository[Content]):
    def __init__(self) -> None:
        super().__init__(model_cls=Content)

    def _apply_custom_filters(
        self,
        query: select,
        filters: list[Filter],
        combine_logic: FilterCombineLogic = FilterCombineLogic.AND,
        *,
        filter_context: dict | None = None,
    ):
        """
        Handle virtual filters (collection_id) via the content_collection junction table.

        Returns the updated query and any remaining filters for the generic adapter.
        """
        from fury_api.domain.collections.models import ContentCollection

        organization_id = (filter_context or {}).get("organization_id")
        collection_filters = [f for f in filters if f.field == "collection_id"]
        remaining_filters = [f for f in filters if f.field != "collection_id"]

        if not collection_filters:
            return query, filters

        if organization_id is None:
            raise ValueError("organization_id is required to filter by collection_id")

        from fury_api.lib.repository.generic_sql_extended import SqlFilterAdapter

        def build_subquery(filter_: Filter):
            subquery = select(ContentCollection.content_id).where(ContentCollection.organization_id == organization_id)

            if filter_.op == FilterOp.EQ:
                value = int(filter_.value) if not isinstance(filter_.value, int) else filter_.value
                subquery = subquery.where(ContentCollection.collection_id == value)
            elif filter_.op == FilterOp.IN:
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
            else:
                raise NotImplementedError(f"collection_id does not support op {filter_.op}")

            return subquery

        def build_collection_condition(filter_: Filter):
            if filter_.op == FilterOp.NEQ:
                value = int(filter_.value) if not isinstance(filter_.value, int) else filter_.value
                excluded = select(ContentCollection.content_id).where(
                    ContentCollection.organization_id == organization_id,
                    ContentCollection.collection_id == value,
                )
                return ~self._model_cls.id.in_(excluded)

            if filter_.op == FilterOp.NOT_IN:
                raw_values = filter_.value if isinstance(filter_.value, list) else [filter_.value]
                values = [int(v) if not isinstance(v, int) else v for v in raw_values]
                excluded = select(ContentCollection.content_id).where(
                    ContentCollection.organization_id == organization_id,
                    ContentCollection.collection_id.in_(values),
                )
                return ~self._model_cls.id.in_(excluded)

            subquery = build_subquery(filter_)
            return self._model_cls.id.in_(subquery)

        if combine_logic == FilterCombineLogic.AND:
            for filter_ in collection_filters:
                query = query.where(build_collection_condition(filter_))
            return query, remaining_filters

        # OR combine logic: build one OR group across BOTH collection and remaining content filters
        conditions = [build_collection_condition(f) for f in collection_filters]
        if remaining_filters:
            conditions.extend(SqlFilterAdapter.build_condition(self, f) for f in remaining_filters)
        if conditions:
            query = query.where(or_(*conditions))
        # All OR-ed together already; nothing left for the generic adapter
        return query, []

    # FIXME: We shouldn't need this function! We should rely on the Author's domain service to load authors! Why are we duplicating logic?!
    async def load_authors_for_content(
        self,
        session: AsyncSession,
        author_ids,
    ) -> dict[int, AuthorRead]:
        """
        Bulk-load authors for a list of content items.

        Args:
            session: Database session
            content_items: List of content items to load authors for

        Returns:
            Dictionary mapping author_id to AuthorRead objects
        """
        if not author_ids:
            return {}

        # Bulk-load authors
        authors_query = select(Author).where(Author.id.in_(author_ids))
        authors_result = await session.execute(authors_query)
        authors = authors_result.scalars().all()

        # Return as mapping
        return {author.id: AuthorRead.model_validate(author, from_attributes=True) for author in authors}

    def apply_filters_to_semantic_query(
        self,
        query: select,
        filters: list[Filter],
        combine_logic: FilterCombineLogic = FilterCombineLogic.AND,
        organization_id: int | None = None,
    ) -> select:
        return self._apply_model_filters(
            query,
            filters,
            combine_logic,
            filter_context={"organization_id": organization_id},
        )
