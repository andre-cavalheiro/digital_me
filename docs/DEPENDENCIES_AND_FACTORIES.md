# Dependencies and Factories Guide

This document explains the purpose and proper usage of the `lib/dependencies` and `lib/factories` modules in the Fury API codebase.

## Table of Contents
- [FastAPI's Dependency Injection Overview](#fastapi-dependency-injection-overview)
- [The Dependencies Module](#the-dependencies-module)
- [The Factories Module](#the-factories-module)
- [How They Work Together](#how-they-work-together)
- [Common Patterns](#common-patterns)
- [Quick Decision Tree](#quick-decision-tree)
- [Creating New Integrations Guide](#creating-new-integrations-guide)

## FastAPI Dependency Injection Overview

FastAPI has a built-in dependency injection system that allows you to declare what your endpoint functions need, and the framework handles the creation and lifecycle of those objects.

### Without Dependency Injection
```python
@app.get("/users")
async def get_users():
    db = Database()                         # Create manually
    user = authenticate()                   # Create manually
    service = UserService(db, user)   # Create manually
    return service.get_all()
```

### With Dependency Injection
```python
@app.get("/users")
async def get_users(
    service: Annotated[UserService, Depends(get_service(ServiceType.USERS))]
):
    return service.get_all()
```

### Benefits
- **DRY (Don't Repeat Yourself):** Setup code is centralized, not repeated in every endpoint
- **Testability:** Easy to swap implementations for testing
- **Clarity:** Explicit declaration of what each endpoint needs
- **Lifecycle Management:** Automatic setup and teardown of resources

## The Dependencies Module

**Location:** `lib/dependencies/`

**Purpose:** Provide FastAPI-compatible dependency functions that integrate with the framework's `Depends()` system.

### What Dependency Functions Do
1. Extract and provide objects from FastAPI request context (user, headers, etc.)
2. Manage object lifecycle with setup/teardown (using generators)
3. Coordinate multiple dependencies that need to work together
4. Adapt complex object creation to FastAPI's expectations

### Key Characteristics
- Must be callable (functions or classes with `__call__`)
- Can be sync or async
- Can use `Depends()` to declare their own dependencies
- Can yield (for cleanup) or return values
- Have access to FastAPI request context

### Example: UnitOfWork Dependency
```python
# lib/dependencies/unit_of_work.py
async def get_uow(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)]
) -> AsyncGenerator[UnitOfWork, None]:
    """Provides a UnitOfWork with proper lifecycle management."""
    uow = UnitOfWorkFactory.get_uow(
        organization_id=current_user.organization_id,
        read_only=False
    )
    try:
        yield uow
    finally:
        await uow.close()  # Cleanup
```

**Why this needs a dependency function:**
- Needs the current user from request context
- Needs lifecycle management (cleanup on request end)
- UoW setup depends on request-specific data

## The Factories Module

**Location:** `lib/factories/`

**Purpose:** Encapsulate complex object creation logic that can be reused across different contexts (endpoints, background jobs, tests, scripts).

### What Factory Classes Do
1. Handle complex configuration logic
2. Resolve dependencies between objects
3. Perform dynamic imports or runtime decisions
4. Centralize creation logic that's used in multiple places

### Key Characteristics
- Framework-agnostic (not tied to FastAPI)
- Can be used anywhere in the codebase
- Typically static methods or class methods
- Focus on "how to build" rather than "when to build"

### Example: ServiceFactory
```python
# lib/factories/service_factory.py
class ServiceFactory:
    @classmethod
    def create_service(
        cls,
        service_type: ServiceType,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs: Any,
    ) -> SqlService:
        """
        Creates services with complex dependency resolution.
        """
        config = cls._get_config(service_type)

        # Dynamic import based on service type
        service_class = cls._get_service_class(config.domain, config.class_name)

        # Resolve service dependencies (services that need other services)
        dependencies = cls._create_dependencies(config.dependencies, uow, **kwargs)

        # Instantiate with all resolved dependencies
        return service_class(uow, auth_user=auth_user, **dependencies, **kwargs)
```

**Why this justifies a factory:**
- Complex logic: Dynamic imports based on service type
- Dependency resolution: Services can depend on other services
- Reusable: Can be called from endpoints, scripts, background jobs
- Configuration: Handles different service configurations

### Example: UnitOfWorkFactory
```python
# lib/factories/uow_factory.py
class UnitOfWorkFactory:
    @staticmethod
    def get_uow(
        *,
        organization_id: int | None = None,
        read_only: bool = False,
        query_user: bool = False
    ) -> UnitOfWork:
        """Creates a UnitOfWork with proper session configuration."""
        session_factory = async_session_ro if read_only else async_session

        # Determine if session is actually read-only
        if session_factory.kw.get("info", {}).get("read_only"):
            read_only = True

        return UnitOfWork(
            session_factory=session_factory,
            autocommit=config.api.SERVICES_AUTOCOMMIT,
            organization_id=organization_id,
            read_only=read_only,
            query_user=query_user,
        )
```

**Why this justifies a factory:**
- Configuration logic: Read-only session selection
- Multiple parameters with interdependencies
- Used in multiple contexts (dependency functions, tests, scripts)

## How They Work Together

The ideal flow combines both modules:

```
Controller/Endpoint
      ↓ (needs via Depends)
Dependencies Module (FastAPI-specific wrappers)
      ↓ (calls)
Factories Module (reusable creation logic)
      ↓ (creates)
Actual Objects (Services, Clients, etc.)
```

### Real Example: Service Dependency Flow

**Step 1 - Controller declares need:**
```python
# domain/users/controllers.py
@earthquake_router.get("/users")
async def get_users(
    service: Annotated[
        UsersService,
        Depends(get_service(ServiceType.USERS, read_only=True, uow=Depends(get_uow_ro)))
    ],
):
    return await service.get_items()
```

**Step 2 - Dependency function coordinates:**
```python
# lib/dependencies/services.py
def get_service(service_type: ServiceType, read_only: bool = False, *, uow=None):
    def dependency(
        uow: Annotated[UnitOfWork, uow or Depends(get_uow_ro if read_only else get_uow)],
        auth_user: Annotated[User, Depends(get_current_user)],
    ) -> SqlService:
        # Delegates to factory with request-specific data
        return ServiceFactory.create_service(
            service_type,
            uow,
            auth_user=auth_user,
        )
    return dependency
```

**Step 3 - Factory handles complexity:**
```python
# lib/factories/service_factory.py
class ServiceFactory:
    @classmethod
    def create_service(cls, service_type, uow, *, auth_user=None, **kwargs):
        # Dynamic import
        service_class = cls._get_service_class(domain, class_name)

        # Dependency resolution
        dependencies = cls._create_dependencies(...)

        # Instantiation
        return service_class(uow, auth_user=auth_user, **dependencies)
```

**What each layer contributes:**
- **Dependencies:** Extracts request context (UoW, current user), provides FastAPI integration
- **Factory:** Complex creation logic (dynamic imports, dependency resolution)
- **Controller:** Just declares what it needs

## Common Patterns

### Pattern 1: Simple Dependency (No Factory Needed)

When object creation is straightforward:

**Example 1: Simple client creation**
```python
# lib/dependencies/clients.py
def get_prefect_client() -> PrefectClient:
    """Provides a Prefect API client configured for the current environment."""
    return PrefectClient(
        base_url=config.prefect.API_URL,
        headers=config.prefect.HEADERS
    )

# Usage in controller
@app.post("/deployments")
async def create_deployment(
    prefect: Annotated[PrefectClient, Depends(get_prefect_client)],
    payload: DeploymentPayload,
):
    return await prefect.create_deployment(...)
```

**Example 2: Client with lifecycle management**
```python
# lib/dependencies/clients.py
async def get_usgs_client() -> AsyncGenerator[USGSEarthquakeClient, None]:
    """Provides a USGS client with automatic lifecycle management."""
    # Handle __aenter__/__aexit__ here, so callers receive a ready-to-use instance
    async with USGSEarthquakeClient() as client:
        yield client

# Usage in controller
@app.post("/ingest")
async def ingest(
    client: Annotated[USGSEarthquakeClient, Depends(get_usgs_client)]
):
    # No need for `async with` - dependency handles it
    return await client.fetch_users(...)
```

### Pattern 2: Dependency with Lifecycle

When cleanup is needed:

```python
# lib/dependencies/database.py
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a database session with automatic cleanup."""
    session = async_session()
    try:
        yield session
    finally:
        await session.close()
```

### Pattern 3: Dependency Using Factory

When creation is complex but request context is needed:

```python
# lib/dependencies/services.py
def get_service(service_type: ServiceType):
    def dependency(
        uow: Annotated[UnitOfWork, Depends(get_uow)],
        user: Annotated[User, Depends(get_current_user)],
    ) -> SqlService:
        # Delegate to factory with request-specific data
        return ServiceFactory.create_service(service_type, uow, auth_user=user)
    return dependency
```

### Pattern 4: Reusable Creation Logic

When the same creation logic is needed in multiple contexts:

**Example 1: Using a Factory (Complex Creation)**
```python
# Use in FastAPI endpoint via dependency
@app.get("/items")
async def get_items(
    service: Annotated[Service, Depends(get_service(ServiceType.ITEMS))]
):
    return await service.get_all()

# Use in background job (no FastAPI context)
async def background_sync_job():
    uow = UnitOfWorkFactory.get_uow(read_only=False)
    service = ServiceFactory.create_service(ServiceType.ITEMS, uow)
    await service.sync_all()

# Use in test
def test_service():
    uow = UnitOfWorkFactory.get_uow(organization_id=1)
    service = ServiceFactory.create_service(ServiceType.ITEMS, uow)
    assert service.get_item(1) is not None
```

**Example 2: Direct Creation Function (Simple Creation)**
```python
# lib/integrations/prefect/client.py - Creation logic
def get_prefect_client() -> PrefectClient:
    """Create a Prefect client configured for current environment."""
    return PrefectClient(
        base_url=config.prefect.API_URL,
        headers=config.prefect.HEADERS
    )

# lib/dependencies/clients.py - Wrap for FastAPI
from fury_api.lib.clients.prefect import get_prefect_client

# Re-export directly - no additional logic needed
__all__ = ["get_prefect_client"]

# Use in FastAPI endpoint
@app.post("/deployments")
async def create_deployment(
    prefect: Annotated[PrefectClient, Depends(get_prefect_client)]
):
    return await prefect.create_deployment(...)

# Use in script (no FastAPI context)
async def push_secret_to_prefect(org_id: int, token: str):
    prefect = get_prefect_client()  # Same function!
    secret_name = f"api-token-org-{org_id}"
    await prefect.create_secret(secret_name, {"value": token})

# Use in test
async def test_prefect_secret():
    prefect = get_prefect_client()  # Same function!
    assert await prefect.secret_exists("test-secret")
```

**Why Example 2 doesn't need a factory:**
- Creation logic is simple (just pass config values)
- No complex dependency resolution
- The function itself is reusable across contexts
- Adding a factory layer would just add indirection without value

## Quick Decision Tree

```
Need to create an object?
│
├─ Is creation trivial (just call constructor with defaults)?
│  └─ YES → Use constructor directly or simple function
│
├─ Does it need FastAPI request context?
│  └─ YES → Create dependency function in lib/dependencies/
│     Example: get_current_user() (needs auth headers)
│
├─ Does it need lifecycle management (setup/cleanup)?
│  └─ YES → Use async generator dependency
│
├─ Is creation complex (dynamic imports, dependency graphs, etc.)?
│  └─ YES → Create factory in lib/factories/
│
└─ Will it be used in multiple contexts (endpoints, scripts, tests)?
   └─ YES → Put creation logic in the module itself, re-export in dependencies/
```
