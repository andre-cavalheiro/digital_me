from typing import TYPE_CHECKING
from collections.abc import Sequence

from sqlalchemy import select

from .models import Document, DocumentContent, DocumentContentCreate
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService
from fury_api.lib.service import with_uow

if TYPE_CHECKING:
    pass

__all__ = ["DocumentsService", "DocumentContentsService"]


class DocumentsService(SqlService[Document]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(Document, uow, auth_user=auth_user, **kwargs)


class DocumentContentsService(SqlService[DocumentContent]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__(DocumentContent, uow, auth_user=auth_user, **kwargs)

    @with_uow
    async def get_sections(self, document_id: int) -> list[DocumentContent]:
        query = (
            select(self._model_cls)
            .where(self._model_cls.document_id == document_id)
            .order_by(self._model_cls.order_index, self._model_cls.id)
        )
        return await self.repository.list(self.session, query=query)

    @with_uow
    async def replace_sections(
        self, document_id: int, sections: Sequence[DocumentContentCreate]
    ) -> list[DocumentContent]:
        # Normalize and rebuild sections for the document
        ordered_sections = []
        for idx, section in enumerate(sections):
            data = section.model_dump(exclude_unset=False)
            data["document_id"] = document_id
            data["order_index"] = idx
            # Preserve provided word_count; could compute here if needed.
            ordered_sections.append(DocumentContent(**data))

        await self.repository.delete_by_document_id(self.session, document_id)
        for section in ordered_sections:
            await self.repository.add(self.session, section)

        await self.session.commit()
        return ordered_sections
