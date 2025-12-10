from celery import Task
from fury_api.lib.logging import get_logger

logger = get_logger(__name__)


class FuryBaseTask(Task):
    """
    Base task for Fury API background jobs.

    Features:
    - Automatic retries with exponential backoff
    - Organization-scoped execution
    - Logging and error handling

    Note: Job status tracking is handled by Celery's result backend (Redis).
    """

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True

    def before_start(self, task_id, args, kwargs):
        """Called before task execution."""
        organization_id = kwargs.get("organization_id")
        task_name = self.name
        logger.info("Starting task", task_id=task_id, task_name=task_name, organization_id=organization_id)

    def on_success(self, retval, task_id, args, kwargs):
        """Called on successful task completion."""
        logger.info("Task completed successfully", task_id=task_id, result=retval)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called on task failure."""
        logger.error("Task failed", task_id=task_id, error=str(exc), traceback=str(einfo))

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning("Task retry", task_id=task_id, error=str(exc), retry_count=self.request.retries)
