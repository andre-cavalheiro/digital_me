from typing import TYPE_CHECKING, Any
from collections.abc import Sequence

from sqlalchemy import select
from .models import Content, ContentSearchRequest
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService, with_uow

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
    async def get_by_ids(self, ids: Sequence[int], *, organization_id: int | None = None) -> list[Content]:
        if not ids:
            return []

        query = select(self._model_cls).where(self._model_cls.id.in_(ids))
        if organization_id is not None:
            query = query.where(self._model_cls.organization_id == organization_id)
        query = query.order_by(self._model_cls.id)
        return await self.repository.list(self.session, query=query)
