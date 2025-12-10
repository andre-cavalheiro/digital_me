from typing import Any
from celery.result import AsyncResult
from fury_api.lib.settings import config
from fury_api.lib.service import GenericService
from fury_api.lib.celery_app import celery_app
from fury_api.lib.logging import get_logger
from .models import TaskInfo

logger = get_logger(__name__)

__all__ = ["JobsService"]


class JobsService(GenericService):
    """
    Infrastructure service for queueing and managing background jobs.

    This service does NOT interact with a database. It queues tasks to Celery
    and retrieves status from Redis (Celery's result backend).

    Usage by other domains:
        jobs_service = JobsService()
        task_info = jobs_service.push_task(
            task_name="ai.conversation.generate_response",
            organization_id=user.organization_id,
            conversation_id=123,
            message_id=456,
            ...
        )
    """

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

    def push_task(self, task_name: str, organization_id: int, queue: str | None = None, **task_kwargs: Any) -> TaskInfo:
        """
        Queue a background task.

        Args:
            task_name: Celery task name (e.g., "ai.conversation.generate_response")
            organization_id: Organization ID for tenant scoping
            queue: Optional queue override (defaults to auto-routing)
            **task_kwargs: Task-specific arguments

        Returns:
            TaskInfo with task_id for status tracking

        Example:
            task_info = jobs_service.push_task(
                task_name="datasync.x.bookmarks.sync",
                organization_id=user.organization_id,
                plugin_id=123,
                max_results=100
            )
        """
        task_kwargs["organization_id"] = organization_id

        # Determine queue from task name if not specified
        if queue is None:
            queue = self._route_task_to_queue(task_name)

        # Queue task
        result = celery_app.send_task(task_name, kwargs=task_kwargs, queue=queue)

        logger.info("Task queued", task_id=result.id, task_name=task_name, queue=queue, organization_id=organization_id)

        return TaskInfo(task_id=result.id, task_name=task_name, organization_id=organization_id, queue=queue)

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        """
        Get task status from Celery result backend (Redis).

        Args:
            task_id: Celery task ID

        Returns:
            Dict with status, result, error (if available)

        Example:
            status = jobs_service.get_task_status("abc-123-def")
            # {"state": "SUCCESS", "result": {...}, "error": None}
        """
        result = AsyncResult(task_id, app=celery_app)

        return {
            "state": result.state,  # PENDING, STARTED, SUCCESS, FAILURE, RETRY
            "result": result.result if result.successful() else None,
            "error": str(result.info) if result.failed() else None,
            "ready": result.ready(),
        }

    def _route_task_to_queue(self, task_name: str) -> str:
        """Auto-route task to queue based on naming convention."""
        if task_name.startswith("ai."):
            return config.celery.QUEUE_ROUTE_AI
        elif task_name.startswith("datasync."):
            return config.celery.QUEUE_ROUTE_DATA_SYNC
        else:
            return "default"
