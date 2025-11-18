from .models import Document, DocumentContent
from fury_api.lib.repository import GenericSqlExtendedRepository
from sqlalchemy import delete
from sqlmodel.ext.asyncio.session import AsyncSession

__all__ = ["DocumentRepository", "DocumentContentRepository"]


class DocumentRepository(GenericSqlExtendedRepository[Document]):
    def __init__(self) -> None:
        super().__init__(model_cls=Document)


class DocumentContentRepository(GenericSqlExtendedRepository[DocumentContent]):
    def __init__(self) -> None:
        super().__init__(model_cls=DocumentContent)

    async def delete_by_document_id(self, session: AsyncSession, document_id: int) -> None:
        stmt = delete(self._model_cls).where(self._model_cls.document_id == document_id)
        await session.exec(stmt)
