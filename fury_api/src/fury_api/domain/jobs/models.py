from enum import Enum
from pydantic import BaseModel

__all__ = ["JobType", "TaskInfo"]


class JobType(str, Enum):
    """Job type identifiers for task routing."""

    AI_CONVERSATION = "ai.conversation"
    AI_RESEARCH = "ai.research"
    DATASYNC_PLUGIN_INSTALL = "datasync.plugin.install"
    DATASYNC_COLLECTION_SYNC = "datasync.collection.sync"
    DATASYNC_X_BOOKMARKS = "datasync.x.bookmarks"


class TaskInfo(BaseModel):
    """Metadata about a queued task (returned from push_task)."""

    task_id: str
    task_name: str
    organization_id: int
    queue: str

    class Config:
        frozen = True
