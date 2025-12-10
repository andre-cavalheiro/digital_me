# Background Jobs with Celery

## Overview

The Fury API uses Celery + Redis for background job processing. This document explains how to:
- Queue background tasks from your domain
- Create new worker tasks
- Monitor job status
- Deploy workers to production

## Architecture

### Jobs Domain (Infrastructure)

The `jobs` domain is **infrastructure-only** - it provides task queueing capabilities to other domains:
- **No user-facing API** (no controllers.py)
- **No persistent storage** (no SQL models, no repository.py)
- **Service layer only** - `JobsService(GenericService)` with `push_task()` method
- **Worker definitions** - Task implementations in `jobs/tasks/`

### Queue Strategy

- **`ai` queue**: AI operations (conversation generation, research)
- **`datasync` queue**: Data sync operations (plugin installs, collection updates)
- **Auto-routing**: Tasks automatically route to queues based on name prefix (`ai.*`, `datasync.*`)

### Task Lifecycle

```
User Request → Domain Controller → JobsService.push_task()
                                         ↓
                                   Celery (Redis)
                                         ↓
                                   Worker picks task
                                         ↓
                                   Execute with UoW/Services
                                         ↓
                                   Update DB, return result
```

## Usage: Queueing Tasks from Your Domain

### Step 1: Import JobsService

```python
from fury_api.domain.jobs.services import JobsService
from fury_api.domain.jobs.models import TaskInfo
```

### Step 2: Add Async Endpoint to Your Controller

```python
@your_router.post("/your-resource/{id}/async", response_model=TaskInfo)
async def your_async_operation(
    id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Create any placeholder records with status=QUEUED
    # ...

    # Queue background task
    jobs_service = JobsService()
    task_info = jobs_service.push_task(
        task_name="your.task.name",
        organization_id=current_user.organization_id,
        resource_id=id,
        # ... other task-specific kwargs
    )

    return task_info  # Returns task_id for status tracking
```

### Step 3: (Not now, but maybe in the future) Add Status Check Endpoint

```python
@your_router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    jobs_service = JobsService()
    return jobs_service.get_task_status(task_id)
```

## Creating New Worker Tasks

### Step 1: Define Task in jobs/tasks/

Create your task in the appropriate file (`ai_tasks.py` or `datasync_tasks.py`):

```python
import asyncio
from fury_api.lib.celery_app import celery_app
from .base import FuryBaseTask

@celery_app.task(
    name="your.domain.operation",  # Must match push_task() name
    bind=True,
    base=FuryBaseTask,
    queue="ai",  # or "datasync"
    time_limit=900,
    soft_time_limit=870
)
def your_task_name(
    self,
    organization_id: int,
    resource_id: int,
    **kwargs
):
    """Task description."""
    return asyncio.run(_your_task_async(
        organization_id=organization_id,
        resource_id=resource_id,
        **kwargs
    ))

async def _your_task_async(organization_id: int, resource_id: int, **kwargs):
    """Async implementation."""
    from fury_api.lib.factories import UnitOfWorkFactory, ServiceFactory
    from fury_api.lib.factories.service_factory import ServiceType

    async with UnitOfWorkFactory.get_uow(organization_id=organization_id) as uow:
        service = ServiceFactory.create_service(
            ServiceType.YOUR_SERVICE, uow, has_system_access=True
        )

        # Your business logic here
        result = await service.do_something(resource_id)

        return {"success": True, "result": result}
```

### Step 2: Register Task in celery_app.py

Ensure your tasks module is included in celery_app.py:

```python
celery_app = Celery(
    "fury_api",
    broker=config.celery.BROKER_URL,
    backend=config.celery.RESULT_BACKEND_URL,
    include=[
        "fury_api.domain.jobs.tasks.ai_tasks",
        "fury_api.domain.jobs.tasks.datasync_tasks",
        # Add your tasks module if separate
    ]
)
```

## Local Development

### Start Services

```bash
# Terminal 1: Start Redis
docker-compose up redis

# Terminal 2: Start API
poetry run uvicorn fury_api.main:app --reload

# Terminal 3: Start Celery worker
poetry run celery -A fury_api.lib.celery_app worker --loglevel=info --queues=ai,datasync
```

### Monitor Tasks

```bash
# Check Redis queue depth
redis-cli -h localhost -p 6379
> LLEN celery  # Main queue
> KEYS celery-task-meta-*  # Task results

# View worker logs
# Check Terminal 3 for task execution logs
```

## Production Deployment

### Kubernetes

Workers are deployed as separate pods with autoscaling (HPA):

```yaml
# deploy/helm/values.yaml
celeryWorker:
  enabled: true
  replicaCount: 2
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
```

### Environment Variables

```bash
FURY_CELERY_BROKER_URL=redis://redis:6379/0
FURY_CELERY_RESULT_BACKEND_URL=redis://redis:6379/1
```

## Monitoring & Debugging

### Task States (Celery)

- **PENDING**: Task queued, not yet picked up
- **STARTED**: Worker processing task
- **SUCCESS**: Task completed successfully
- **FAILURE**: Task failed
- **RETRY**: Task retrying after failure

### Checking Task Status

```python
from fury_api.domain.jobs.services import JobsService

jobs_service = JobsService()
status = jobs_service.get_task_status(task_id)
# {"state": "SUCCESS", "result": {...}, "error": None}
```

### Common Issues

**Problem**: Tasks not being picked up
- Check worker is running: `celery -A fury_api.lib.celery_app inspect active`
- Check Redis connection: `redis-cli PING`
- Verify queue routing in celery_app.py

**Problem**: Task fails immediately
- Check worker logs for exceptions
- Verify organization_id is passed correctly
- Ensure UoW has access to organization's data

## Best Practices

1. **Always pass organization_id**: Required for multi-tenancy
2. **Use asyncio.run() wrapper**: Workers run sync, so wrap async logic
3. **Keep tasks idempotent**: Tasks may retry, design for multiple executions
4. **Set reasonable timeouts**: Default 15 minutes, adjust per task
5. **Log generously**: Worker logs are your debugging tool
6. **Create placeholder records**: Set status=QUEUED before queueing task
7. **Update records on completion**: Workers update status to COMPLETED/FAILED

## Examples

See implementation examples:
- AI conversation generation: `jobs/tasks/ai_tasks.py`
- X bookmarks sync: `jobs/tasks/datasync_tasks.py`
- Async endpoint integration: `conversations/controllers.py`
