from .models import Citation, DocumentSourceConfig, Source, SourceGroup, SourceGroupMember
from fury_api.lib.repository import GenericSqlExtendedRepository

__all__ = [
    "SourceRepository",
    "SourceGroupRepository",
    "SourceGroupMemberRepository",
    "DocumentSourceConfigRepository",
    "CitationRepository",
]


class SourceRepository(GenericSqlExtendedRepository[Source]):
    def __init__(self) -> None:
        super().__init__(model_cls=Source)


class SourceGroupRepository(GenericSqlExtendedRepository[SourceGroup]):
    def __init__(self) -> None:
        super().__init__(model_cls=SourceGroup)


class SourceGroupMemberRepository(GenericSqlExtendedRepository[SourceGroupMember]):
    def __init__(self) -> None:
        super().__init__(model_cls=SourceGroupMember)


class DocumentSourceConfigRepository(GenericSqlExtendedRepository[DocumentSourceConfig]):
    def __init__(self) -> None:
        super().__init__(model_cls=DocumentSourceConfig)


class CitationRepository(GenericSqlExtendedRepository[Citation]):
    def __init__(self) -> None:
        super().__init__(model_cls=Citation)
