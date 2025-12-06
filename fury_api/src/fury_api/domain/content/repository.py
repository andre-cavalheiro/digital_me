from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Content
from fury_api.domain.authors.models import Author, AuthorRead
from fury_api.lib.repository import GenericSqlExtendedRepository
from fury_api.lib.model_filters import Filter
from fury_api.lib.model_filters.models import FilterCombineLogic

if TYPE_CHECKING:
    pass

__all__ = ["ContentRepository"]


class ContentRepository(GenericSqlExtendedRepository[Content]):
    def __init__(self) -> None:
        super().__init__(model_cls=Content)

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
        """
        Apply model filters to a semantic search query with combine logic support.

        Handles special case for collection_id which requires filtering
        via the ContentCollection junction table. Direct Content filters
        (like author_id) are applied using the repository's filter adapter.

        Args:
            query: Base SQLAlchemy select query
            filters: List of Filter objects to apply
            combine_logic: How to combine filters (AND or OR)
            organization_id: Organization ID for collection filtering

        Returns:
            Modified query with filters applied
        """
        from fury_api.domain.collections.models import ContentCollection
        from fury_api.lib.model_filters import FilterOp
        from fury_api.lib.repository.generic_sql_extended import SqlFilterAdapter
        from sqlalchemy import or_

        # Separate collection filters from direct Content filters
        collection_filters = [f for f in filters if f.field == "collection_id"]
        content_filters = [f for f in filters if f.field != "collection_id"]

        # For AND logic, use existing approach (works correctly)
        if combine_logic == FilterCombineLogic.AND:
            # Apply direct Content filters using repository's filter adapter
            if content_filters:
                query = self._apply_model_filters(query, content_filters, combine_logic)

            # Handle collection filters with subquery
            if collection_filters and organization_id is not None:
                for filter_ in collection_filters:
                    # Build subquery to find content_ids in matching collections
                    subquery = select(ContentCollection.content_id).where(
                        ContentCollection.organization_id == organization_id
                    )

                    # Apply filter operation to collection_id
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

                    # Apply condition with AND
                    query = query.where(self._model_cls.id.in_(subquery))

            return query

        # For OR logic, build all conditions first then combine
        all_conditions = []

        # Build content filter conditions using SqlFilterAdapter
        if content_filters:
            content_conditions = [SqlFilterAdapter.build_condition(self, f) for f in content_filters]
            if len(content_conditions) == 1:
                all_conditions.append(content_conditions[0])
            else:
                all_conditions.append(or_(*content_conditions))

        # Build collection filter conditions
        if collection_filters and organization_id is not None:
            collection_conditions = []
            for filter_ in collection_filters:
                # Build subquery to find content_ids in matching collections
                subquery = select(ContentCollection.content_id).where(
                    ContentCollection.organization_id == organization_id
                )

                # Apply filter operation to collection_id
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

                collection_conditions.append(self._model_cls.id.in_(subquery))

            if len(collection_conditions) == 1:
                all_conditions.append(collection_conditions[0])
            else:
                all_conditions.append(or_(*collection_conditions))

        # Combine all conditions with OR
        if all_conditions:
            if len(all_conditions) == 1:
                query = query.where(all_conditions[0])
            else:
                query = query.where(or_(*all_conditions))

        return query
