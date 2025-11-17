from .models import Document, DocumentContent
from fury_api.lib.repository import GenericSqlExtendedRepository

__all__ = ["DocumentRepository", "DocumentContentRepository"]


class DocumentRepository(GenericSqlExtendedRepository[Document]):
    def __init__(self) -> None:
        super().__init__(model_cls=Document)


class DocumentContentRepository(GenericSqlExtendedRepository[DocumentContent]):
    def __init__(self) -> None:
        super().__init__(model_cls=DocumentContent)
