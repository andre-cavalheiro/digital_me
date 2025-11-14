# Project Structure

## Config Management

Configuration settings are managed in `src/fury_api/lib/settings.py`. The `.env` file provides runtime settings for local development, while Kubernetes secrets store sensitive information in production.


## Domains

The API follows **Domain-Driven Design (DDD)** with a layered architecture. Each domain (`src/fury_api/domain/`) represents a business concept (users, organizations, plugins) and is self-contained with minimal cross-domain dependencies.

```
HTTP Request → Controller → Service → Repository → Database
                    ↓           ↓          ↓
                 Routes    Business    Data Access
                           Logic
```

**`controller.py`** - HTTP endpoint handlers
- Maps HTTP requests to service method calls
- Handles request validation via Pydantic models
- Manages dependency injection (auth, services, UoW)
- Returns HTTP responses

**Example:**
```python
@router.get("/users/{id}", response_model=UserRead)
async def get_user(
    id: int,
    users_service: Annotated[UsersService, Depends(get_service(ServiceType.USERS))],
) -> User:
    return await users_service.get_item(id)
```

**`model.py`** - Data schemas
- Defines database table structure (via SQLModel/SQLAlchemy)
- Provides Pydantic validation for API input/output
- Auto-generates OpenAPI documentation
- Includes variants: `UserCreate` (input), `UserRead` (output), `User` (database model)

**`service.py`** - Business logic layer
- Orchestrates domain operations (create user, update organization, query plugins)
- Extends from `SqlService[T]` for database-backed services, which combined with our sqlalquemy pydantic models enabels standard CRUD operations out-of-the-box
- Enforces business rules and validation

**Example:**
```python
class UsersService(SqlService[User]):
    @with_uow
    async def get_item(self, id: int) -> User | None:
        return await self.repository.get_by_id(self.session, id)
```

**`repository.py`** - Data access layer
- Extends `GenericSqlExtendedRepository[T]`, which provides type-safe CRUD, pagination, filtering, and sorting out-of-the-box, allowing repositories to focus only on domain-specific queries.

**Example:**
```python
class UserRepository(GenericSqlExtendedRepository[User]):
    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        q = select(User).where(User.email == email)
        return (await session.exec(q)).scalar_one_or_none()
```

Repositories are accessed via **Unit of Work** (`lib/unit_of_work.py`), which manages database transactions (commit/rollback) thus prroviding session lifecycle management. They also enforce multi-tenancy via PostgreSQL Row-Level Security.

**Example Flow:**
```python
# In controller - UoW injected automatically
users_service: Annotated[UsersService, Depends(get_service(...))]

# In service - @with_uow manages transaction
@with_uow
async def create_user(self, user_data: UserCreate) -> User:
    user = User(**user_data.dict())
    return await self.repository.add(self.session, user)
    # Transaction commits automatically on successful exit
```

## Authentication & Security

**Authentication Flow:**
```
Request → Extract Bearer token → Validate (Firebase/System/Override) →
Extract user claims → Database lookup → Verify organization →
Inject auth_user into services
```

**Multi-Tenancy**: The authentication system extracts `organization_id` from the authenticated user and passes it to the Unit of Work, which enforces Row-Level Security (RLS) at the PostgreSQL level. This ensures data isolation between organizations without application-level filtering.

**Usage in Controllers:**
```python
@router.get("/users")
async def get_users(
    current_user: Annotated[User, Depends(get_current_user)]  # Auth required
) -> list[User]:
    # current_user is fully validated and includes organization_id
    ...
```

## Pagination & Filtering

**Pagination** (`lib/pagination.py`) uses cursor-based pagination (via fastapi-pagination) for stateless, scalable list endpoints.

**Model Filters** (`lib/ model_filters/`) provides type-safe, declarative query filtering made available to all domains.
- **Definition-based**: Each model defines allowed filter fields and operations in its controller (fields and operations are white-listed)
- **18+ operations**: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`, `like`, `ilike`, `is_null`, `is_not_null` (their applicability varies according to the target field's data type)
- **SQL injection prevention**: All values are parameterized and automaticly casted with validation (strings, numbers, booleans, dates, arrays)

**HTTP Query Format:**
```
GET /api/earthquakes?filters=magnitude:gte:5.0&filters=location:like:California&sorts=magnitude:desc
```

**Usage in Controllers:**
```python
@router.get("/earthquakes")
async def list_earthquakes(
    filters_parser: Annotated[
        FiltersAndSortsParser,
        Depends(get_models_filters_parser_factory(EARTHQUAKES_FILTERS_DEFINITION))
    ],
) -> CursorPage[Earthquake]:
    return await service.get_items_paginated(
        model_filters=filters_parser.filters,
        model_sorts=filters_parser.sorts
    )
```

The system transforms HTTP query parameters into type-safe SQLAlchemy filters, validated against a declarative schema.

## Dependencies, Factories

**Components:** `dependencies/`, `factories/`

This architecture implements Dependency Injection and Factory patterns:

**Factories** create instances dynamically:
- `ServiceFactory`: Uses reflection to instantiate services by type (e.g., `ServiceType.USERS` → `UsersService`)
- `UnitOfWorkFactory`: Creates UoW (unit of work) instances with appropriate session factories (read-only vs read-write)
- `ClientsFactory`: Creates external client instances (USGS API, etc.)

**Dependencies** compose FastAPI injectable functions:
- `get_uow_tenant()`: Creates UoW (unit of work) scoped to current user's organization (write access)
- `get_uow_tenant_ro()`: Read-only variant
- `get_uow_any_tenant()`: No tenant isolation
- `get_service()`: Creates services with UoW + auth context injected

Personal note on dependencies: leveraging dependency injection, whether it's for 3rd party clients, domain services, datbase clients helps maintain clean architecture and proper separation of concerns in FastAPI projects. That's why this project has so many of it.

**Request Flow Example:**
```
Controller endpoint → Depends(get_service(ServiceType.USERS, read_only=True))
  → get_uow_tenant_ro() → Creates UoW with organization_id
  → get_current_user() → Validates auth, extracts org_id
  → ServiceFactory.create_service() → Instantiates UsersService(uow, auth_user)
  → Service method → Repository CRUD → PostgreSQL (RLS enforced)
```
