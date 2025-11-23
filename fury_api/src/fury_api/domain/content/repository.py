from .models import Content
from fury_api.lib.repository import GenericSqlExtendedRepository

__all__ = ["ContentRepository"]


class ContentRepository(GenericSqlExtendedRepository[Content]):
    def __init__(self) -> None:
        super().__init__(model_cls=Content)
