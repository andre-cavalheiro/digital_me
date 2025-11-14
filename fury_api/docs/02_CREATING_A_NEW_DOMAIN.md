# Creating a New Domain - LLM Script Template

This document serves as an **executable script for an LLM** to create a new domain with full CRUD operations. Simply define the variables below and paste this entire document into an LLM.

---

## 🎯 CONFIGURATION VARIABLES (Edit these)

```python
# Define your domain configuration here
DOMAIN_NAME = "tasks"                    # Singular, lowercase (e.g., "task", "project", "comment")
DOMAIN_NAME_PLURAL = "tasks"            # Plural form for routes and collection names
DISPLAY_NAME = "Task"                    # Singular, PascalCase for classes
DISPLAY_NAME_PLURAL = "Tasks"           # Plural, PascalCase for service class

# Define your model fields (excluding id, timestamps, and organization_id which are handled automatically)
MODEL_FIELDS = {
    "title": {"type": "str", "required": True, "nullable": False},
    "description": {"type": "str", "required": False, "nullable": True},
    "status": {"type": "str", "required": True, "nullable": False},
    "priority": {"type": "int", "required": False, "nullable": True},
}

# Fields to include in the Read model (subset of MODEL_FIELDS)
READ_MODEL_FIELDS = ["id", "title", "description", "status", "priority"]

# Fields to include in the Create model (subset of MODEL_FIELDS, excluding auto-generated fields)
CREATE_MODEL_FIELDS = ["title", "description", "status", "priority"]

# Fields to include in the Update model (subset of MODEL_FIELDS, excluding id and non-updatable fields)
# All fields should be optional in Update model
UPDATE_MODEL_FIELDS = ["title", "description", "status", "priority"]

# Fields to enable filtering on in the API
FILTERABLE_FIELDS = ["title", "status", "priority"]

# Fields to enable sorting on in the API
SORTABLE_FIELDS = ["id", "title", "status", "created_at"]
```

---

## 📝 INSTRUCTIONS FOR LLM

You are tasked with creating a complete domain module following the Fury API architectural pattern. Use the configuration variables defined above to generate all required files. Follow these steps **exactly**:

---

### Step 1: Create the Models File

**File:** `src/fury_api/domain/{DOMAIN_NAME_PLURAL}/models.py`

**Template:**

```python
from __future__ import annotations

import sqlalchemy as sa
from datetime import datetime
from typing import Any, Optional

from pydantic import ConfigDict
from sqlmodel import Field
from fury_api.lib.db.base import BaseSQLModel, BigIntIDModel

__all__ = ["{DISPLAY_NAME}", "{DISPLAY_NAME}Create", "{DISPLAY_NAME}Read", "{DISPLAY_NAME}Update"]


class {DISPLAY_NAME}Base(BaseSQLModel):
    # Add base fields that are common across Create/Read models
    {GENERATE_BASE_FIELDS}


class {DISPLAY_NAME}({DISPLAY_NAME}Base, BigIntIDModel, table=True):
    __tablename__: str = "{DOMAIN_NAME}"
    __id_attr__ = "id"

    id: int | None = Field(
        default=None, primary_key=True, sa_type=sa.BigInteger, sa_column_kwargs={"autoincrement": True}
    )
    organization_id: int = Field(sa_type=sa.BigInteger, foreign_key="organization.id", nullable=False)
    {GENERATE_TABLE_FIELDS}
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class {DISPLAY_NAME}Read({DISPLAY_NAME}Base):
    # Ignore extra fields to allow direct SQLA model usage in responses.
    model_config = ConfigDict(extra="ignore")

    {GENERATE_READ_FIELDS}


class {DISPLAY_NAME}Create({DISPLAY_NAME}Base):
    {GENERATE_CREATE_FIELDS}


class {DISPLAY_NAME}Update(BaseSQLModel):
    {GENERATE_UPDATE_FIELDS}
```

**Instructions:**
- Use the `MODEL_FIELDS` dictionary to generate field definitions
- For `{DISPLAY_NAME}Base`: Include only **required** fields that appear in both Create and Read
- For `{DISPLAY_NAME}` (table model): Include **all** fields from `MODEL_FIELDS` with appropriate SQLAlchemy types
- For `{DISPLAY_NAME}Read`: Include only fields listed in `READ_MODEL_FIELDS`
- For `{DISPLAY_NAME}Create`: Include only fields listed in `CREATE_MODEL_FIELDS`
- For `{DISPLAY_NAME}Update`: Include only fields listed in `UPDATE_MODEL_FIELDS`, **all fields must be optional** (use `| None` type union)
- Map Python types to SQLAlchemy types appropriately (str → String, int → BigInteger, dict → JSON, etc.)

---

### Step 2: Create the Repository File

**File:** `src/fury_api/domain/{DOMAIN_NAME_PLURAL}/repository.py`

**Template:**

```python
from .models import {DISPLAY_NAME}
from fury_api.lib.repository import GenericSqlExtendedRepository

__all__ = ["{DISPLAY_NAME}Repository"]


class {DISPLAY_NAME}Repository(GenericSqlExtendedRepository[{DISPLAY_NAME}]):
    def __init__(self) -> None:
        super().__init__(model_cls={DISPLAY_NAME})
```

**Instructions:**
- This is a minimal repository that inherits all CRUD operations from `GenericSqlExtendedRepository`
- Only add custom methods if domain-specific queries are needed (e.g., `get_by_email`, `get_by_status`)

---

### Step 3: Create the Exceptions File

**File:** `src/fury_api/domain/{DOMAIN_NAME_PLURAL}/exceptions.py`

**Template:**

```python
from fury_api.lib.exceptions import FuryAPIError

__all__ = [
    "{DISPLAY_NAME}Error",
]


class {DISPLAY_NAME}Error(FuryAPIError):
    pass
```

**Instructions:**
- Create a base exception class for the domain
- Add specific exception subclasses as needed for domain logic

---

### Step 4: Create the Service File

**File:** `src/fury_api/domain/{DOMAIN_NAME_PLURAL}/services.py`

**Template:**

```python
from typing import TYPE_CHECKING, Any
from collections.abc import AsyncGenerator

from .models import {DISPLAY_NAME}
from fury_api.lib.unit_of_work import UnitOfWork
from fury_api.lib.model_filters import Filter, Sort
from fury_api.domain.users.models import User

from fury_api.lib.service import SqlService, with_uow
from fury_api.lib.pagination import CursorPage

if TYPE_CHECKING:
    pass

__all__ = ["{DISPLAY_NAME_PLURAL}Service"]


class {DISPLAY_NAME_PLURAL}Service(SqlService[{DISPLAY_NAME}]):
    def __init__(
        self,
        uow: UnitOfWork,
        *,
        auth_user: User | None = None,
        **kwargs,
    ):
        super().__init__({DISPLAY_NAME}, uow, auth_user=auth_user, **kwargs)

    # Add custom domain-specific methods here using the @with_uow decorator
    # Example:
    # @with_uow
    # async def get_by_status(self, status: str) -> list[{DISPLAY_NAME}]:
    #     return await self.repository.list(self.session, filters={"status": status})
```

**Instructions:**
- The service inherits from `SqlService[{DISPLAY_NAME}]` which provides:
  - `get_item(id)` - Get single item by ID
  - `create_item(item)` - Create a new item
  - `delete_item(item)` - Delete an item
  - `update_item(item_id, item)` - Update an item
  - `get_items_paginated(model_filters, model_sorts)` - Get paginated list
  - `get_items(model_filters, model_sorts)` - Get all items as generator
- Add domain-specific methods decorated with `@with_uow`

---

### Step 5: Create the Controllers File

**File:** `src/fury_api/domain/{DOMAIN_NAME_PLURAL}/controllers.py`

**Template:**

```python
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from fury_api.domain import paths
from fury_api.domain.users.models import User
from fury_api.lib.dependencies import (
    FiltersAndSortsParser,
    ServiceType,
    get_models_filters_parser_factory,
    get_service,
    get_uow_tenant,
    get_uow_tenant_ro,
)
from . import exceptions
from .models import (
    {DISPLAY_NAME},
    {DISPLAY_NAME}Create,
    {DISPLAY_NAME}Read,
    {DISPLAY_NAME}Update,
)
from fury_api.lib.security import get_current_user
from fury_api.lib.db.base import Identifier
from fury_api.lib.pagination import CursorPage
from .services import {DISPLAY_NAME_PLURAL}Service
from fury_api.lib.model_filters import ModelFilterAndSortDefinition, get_default_ops_for_type

{DOMAIN_NAME}_router = APIRouter()

{DOMAIN_NAME_UPPER}_FILTERS_DEFINITION = ModelFilterAndSortDefinition(
    model={DISPLAY_NAME},
    allowed_filters={
        {GENERATE_FILTER_DEFINITION}
    },
    allowed_sorts={GENERATE_SORT_DEFINITION},
)


@{DOMAIN_NAME}_router.post(paths.{DOMAIN_NAME_UPPER}, response_model={DISPLAY_NAME}Read, status_code=status.HTTP_201_CREATED)
async def create_{DOMAIN_NAME}(
    {DOMAIN_NAME}: {DISPLAY_NAME}Create,
    {DOMAIN_NAME}_service: Annotated[
        {DISPLAY_NAME_PLURAL}Service,
        Depends(
            get_service(
                ServiceType.{DOMAIN_NAME_UPPER},
                read_only=False,
                uow=Depends(get_uow_tenant),
            )
        ),
    ],
    current_user: Annotated[User, Depends(get_current_user)],
) -> {DISPLAY_NAME}:
    converted_{DOMAIN_NAME} = {DISPLAY_NAME}.model_validate({DOMAIN_NAME})
    converted_{DOMAIN_NAME}.organization_id = current_user.organization_id
    return await {DOMAIN_NAME}_service.create_item(converted_{DOMAIN_NAME})


@{DOMAIN_NAME}_router.get(paths.{DOMAIN_NAME_UPPER}, response_model=CursorPage[{DISPLAY_NAME}Read])
async def get_{DOMAIN_NAME_PLURAL}(
    {DOMAIN_NAME}_service: Annotated[
        {DISPLAY_NAME_PLURAL}Service,
        Depends(
            get_service(
                ServiceType.{DOMAIN_NAME_UPPER},
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
    filters_parser: Annotated[
        FiltersAndSortsParser, Depends(get_models_filters_parser_factory({DOMAIN_NAME_UPPER}_FILTERS_DEFINITION))
    ],
) -> CursorPage[{DISPLAY_NAME}Read]:
    return await {DOMAIN_NAME}_service.get_items_paginated(
        model_filters=filters_parser.filters, model_sorts=filters_parser.sorts
    )


@{DOMAIN_NAME}_router.get(paths.{DOMAIN_NAME_UPPER}_ID, response_model={DISPLAY_NAME}Read)
async def get_{DOMAIN_NAME}(
    id_: int,
    {DOMAIN_NAME}_service: Annotated[
        {DISPLAY_NAME_PLURAL}Service,
        Depends(
            get_service(
                ServiceType.{DOMAIN_NAME_UPPER},
                read_only=True,
                uow=Depends(get_uow_tenant_ro),
            )
        ),
    ],
) -> {DISPLAY_NAME}Read:
    {DOMAIN_NAME} = await {DOMAIN_NAME}_service.get_item(id_)
    if not {DOMAIN_NAME}:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{DISPLAY_NAME} not found")
    return {DOMAIN_NAME}


@{DOMAIN_NAME}_router.put(paths.{DOMAIN_NAME_UPPER}_ID, response_model={DISPLAY_NAME}Read)
async def update_{DOMAIN_NAME}(
    id_: int,
    {DOMAIN_NAME}_update: {DISPLAY_NAME}Update,
    {DOMAIN_NAME}_service: Annotated[
        {DISPLAY_NAME_PLURAL}Service,
        Depends(get_service(ServiceType.{DOMAIN_NAME_UPPER})),
    ],
) -> {DISPLAY_NAME}:
    {DOMAIN_NAME} = await {DOMAIN_NAME}_service.get_item(id_)
    if {DOMAIN_NAME} is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{DISPLAY_NAME} not found")

    try:
        updated_{DOMAIN_NAME} = await {DOMAIN_NAME}_service.update_item(id_, {DOMAIN_NAME}_update)
        return updated_{DOMAIN_NAME}
    except exceptions.{DISPLAY_NAME}Error as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@{DOMAIN_NAME}_router.delete(paths.{DOMAIN_NAME_UPPER}_ID, status_code=status.HTTP_204_NO_CONTENT)
async def delete_{DOMAIN_NAME}(
    id_: int,
    {DOMAIN_NAME}_service: Annotated[
        {DISPLAY_NAME_PLURAL}Service,
        Depends(get_service(ServiceType.{DOMAIN_NAME_UPPER})),
    ],
) -> None:
    {DOMAIN_NAME} = await {DOMAIN_NAME}_service.get_item(id_)
    if {DOMAIN_NAME} is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="{DISPLAY_NAME} not found")

    try:
        await {DOMAIN_NAME}_service.delete_item({DOMAIN_NAME})
    except exceptions.{DISPLAY_NAME}Error as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
```

**Instructions:**
- Replace `{DOMAIN_NAME_UPPER}` with the uppercase version of `DOMAIN_NAME` (e.g., "TASKS")
- Generate filter definitions from `FILTERABLE_FIELDS`:
  ```python
  "field_name": get_default_ops_for_type(field_type),
  ```
- Generate sort definitions from `SORTABLE_FIELDS` as a set:
  ```python
  {"field1", "field2", "field3"}
  ```
- Ensure path constants match the pattern in `fury_api.domain.paths`

---

### Step 6: Create the __init__.py File

**File:** `src/fury_api/domain/{DOMAIN_NAME_PLURAL}/__init__.py`

**Template:**

```python
"""
{DISPLAY_NAME_PLURAL} domain module.
"""
```

---

### Step 7: Register the Domain in ServiceType Enum

**File:** `src/fury_api/lib/factories/service_factory.py`

**Action:** Add to the `ServiceType` enum:

```python
class ServiceType(Enum):
    USERS = "users"
    PLUGINS = "plugins"
    ORGANIZATIONS = "organizations"
    {DOMAIN_NAME_UPPER} = "{DOMAIN_NAME_PLURAL}"  # Add this line
```

---

### Step 8: Add API Paths

**File:** `src/fury_api/domain/paths.py`

**Action:** Add path constants:

```python
# {DISPLAY_NAME_PLURAL} paths
{DOMAIN_NAME_UPPER} = "/{DOMAIN_NAME_PLURAL}"
{DOMAIN_NAME_UPPER}_ID = "/{DOMAIN_NAME_PLURAL}/{id_}"
```

---

### Step 9: Register Routes in Main Router

**File:** `src/fury_api/domain/routes.py`

**Action:** Add import and include router:

```python
from fury_api.domain.{DOMAIN_NAME_PLURAL}.controllers import {DOMAIN_NAME}_router

# ... existing code ...

api_router.include_router({DOMAIN_NAME}_router, prefix="/{DOMAIN_NAME_PLURAL}", tags=["{DOMAIN_NAME_PLURAL}"])
```

---

### Step 10: Register Repository in Unit of Work

**File:** Search for the file that contains the `UnitOfWork` class and its repository mappings (likely `src/fury_api/lib/unit_of_work.py` or similar)

**Action:** Add the repository to the `_repos` mapper:

```python
from fury_api.domain.{DOMAIN_NAME_PLURAL}.repository import {DISPLAY_NAME}Repository
from fury_api.domain.{DOMAIN_NAME_PLURAL}.models import {DISPLAY_NAME}

# In the _repos dictionary or initialization:
{DISPLAY_NAME}: {DISPLAY_NAME}Repository()
```

---

## ✅ VERIFICATION CHECKLIST

After generation, verify the following:

- [ ] All files are created in `src/fury_api/domain/{DOMAIN_NAME_PLURAL}/`
- [ ] Models include proper type hints and SQLAlchemy configurations
  - [ ] Base model with shared fields
  - [ ] Table model with all database fields
  - [ ] Create model for POST requests
  - [ ] Read model for GET responses
  - [ ] Update model for PUT requests (all fields optional)
- [ ] Service inherits from `SqlService[{DISPLAY_NAME}]`
- [ ] Repository inherits from `GenericSqlExtendedRepository[{DISPLAY_NAME}]`
- [ ] Controllers use dependency injection with `get_service()`
  - [ ] POST endpoint for creating items
  - [ ] GET endpoint for listing items (paginated)
  - [ ] GET endpoint for retrieving single item
  - [ ] PUT endpoint for updating items
  - [ ] DELETE endpoint for removing items
- [ ] ServiceType enum includes `{DOMAIN_NAME_UPPER}`
- [ ] Paths are defined in `paths.py`
- [ ] Router is registered in `routes.py`
- [ ] Repository is registered in Unit of Work

---

## 🎨 EXAMPLE GENERATION

Here's a concrete example for a "tasks" domain:

### Configuration:
```python
DOMAIN_NAME = "task"
DOMAIN_NAME_PLURAL = "tasks"
DISPLAY_NAME = "Task"
DISPLAY_NAME_PLURAL = "Tasks"

MODEL_FIELDS = {
    "title": {"type": "str", "required": True, "nullable": False},
    "description": {"type": "str", "required": False, "nullable": True},
    "status": {"type": "str", "required": True, "nullable": False},
}

READ_MODEL_FIELDS = ["id", "title", "description", "status"]
CREATE_MODEL_FIELDS = ["title", "description", "status"]
UPDATE_MODEL_FIELDS = ["title", "description", "status"]
FILTERABLE_FIELDS = ["title", "status"]
SORTABLE_FIELDS = ["id", "title", "status", "created_at"]
```

### Generated Field Examples:

**Base Model:**
```python
class TaskBase(BaseSQLModel):
    title: str
    status: str
```

**Table Model:**
```python
title: str = Field(nullable=False)
description: str | None = Field(None, nullable=True)
status: str = Field(nullable=False)
```

**Read Model:**
```python
id: int
title: str
description: str | None = None
status: str
```

**Create Model:**
```python
title: str = Field()
description: str | None = None
status: str = Field()
```

**Update Model:**
```python
title: str | None = None
description: str | None = None
status: str | None = None
```

**Filter Definition:**
```python
allowed_filters={
    "id": get_default_ops_for_type(Identifier),
    "title": get_default_ops_for_type(str),
    "status": get_default_ops_for_type(str),
},
allowed_sorts={"id", "title", "status", "created_at"},
```

---

## 🚀 USAGE

1. Copy this entire document
2. Edit the **CONFIGURATION VARIABLES** section with your domain details
3. Paste into an LLM (Claude, GPT-4, etc.) with the prompt:

   > "Using the configuration variables defined at the top, generate all the files specified in the instructions following the Fury API architectural pattern. Provide each file's complete content with full CRUD operations (Create, Read, Update, Delete)."

4. Copy the generated files into your project
5. Run tests and verify functionality

---

## 📚 ARCHITECTURE REFERENCE

This template follows the Fury API domain-driven design pattern:

- **Models:** Define database schema and API contracts (Base, Table, Create, Read, Update)
- **Repository:** Data access layer (inherits CRUD from `GenericSqlExtendedRepository`)
- **Service:** Business logic layer (inherits CRUD from `SqlService`, add domain logic)
- **Controllers:** API endpoint definitions using FastAPI
- **Exceptions:** Domain-specific error handling

The pattern ensures:
- ✅ Consistent structure across all domains
- ✅ Complete CRUD operations (Create, Read, Update, Delete)
- ✅ Type safety with Pydantic and SQLModel
- ✅ Automatic dependency injection
- ✅ Built-in pagination, filtering, and sorting
- ✅ Multi-tenancy support via `organization_id`
- ✅ Transaction management via Unit of Work pattern
