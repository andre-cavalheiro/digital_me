from .models import Plugin
from fury_api.lib.repository import GenericSqlExtendedRepository

__all__ = ["PluginRepository"]


class PluginRepository(GenericSqlExtendedRepository[Plugin]):
    def __init__(self) -> None:
        super().__init__(model_cls=Plugin)
