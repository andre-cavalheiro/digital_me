from celery import Celery
from fury_api.lib.settings import config

celery_app = Celery(
    "fury_api",
    broker=config.celery.BROKER_URL,
    backend=config.celery.RESULT_BACKEND_URL,
    include=[
        "fury_api.domain.jobs.tasks.ai.generate_assistant_response",
        "fury_api.domain.jobs.tasks.datasync.fetch_all_x_bookmarks",
        "fury_api.domain.jobs.tasks.datasync.sync_x_bookmark_folders",
        "fury_api.domain.jobs.tasks.datasync.fetch_x_bookmark_folder_content",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_time_limit=config.celery.TASK_TIME_LIMIT_SECONDS,
    task_soft_time_limit=config.celery.TASK_SOFT_TIME_LIMIT_SECONDS,
    # Retries
    task_default_retry_delay=config.celery.TASK_DEFAULT_RETRY_DELAY,
    task_max_retries=config.celery.TASK_MAX_RETRIES,
    # Queue routing
    task_routes={
        "ai.*": {"queue": config.celery.QUEUE_ROUTE_AI},
        "datasync.*": {"queue": config.celery.QUEUE_ROUTE_DATA_SYNC},
    },
    worker_max_tasks_per_child=config.celery.WORKER_MAX_TASKS_PER_CHILD,
    worker_disable_rate_limits=config.celery.WORKER_DISABLE_RATE_LIMITS,
)

# Import tasks to register them
from fury_api.domain.jobs.tasks import ai, datasync  # noqa: E402, F401
