# Creating a New Integration - LLM Script Template

This document serves as an **executable script for an LLM** to create a new external integration with full factory and dependency injection support. Simply define the variables below and paste this entire document into an LLM.

Learn more about the dependencies and factories concepts [here](DEPENDENCIES_AND_FACTORIES.md).

---

## 🎯 CONFIGURATION VARIABLES (Edit these)

```python
# Define your integration configuration here
INTEGRATION_NAME = "acme"                      # Lowercase, snake_case (e.g., "datadog", "github")
INTEGRATION_DISPLAY_NAME = "Acme"             # PascalCase for class names (e.g., "Datadog", "GitHub")
INTEGRATION_TYPE = "http"                      # "http" or "sdk"

# For HTTP-based integrations (REST APIs)
BASE_URL_CONFIG_PATH = "config.acme.API_URL"   # Path to base URL in config (e.g., "config.acme.API_URL")
AUTH_TYPE = "bearer"                            # "bearer", "api_key", "basic", "custom", or "none"
API_KEY_CONFIG_PATH = "config.acme.API_KEY"    # Path to API key in config (if applicable)
DEFAULT_TIMEOUT = 30.0                         # Default request timeout in seconds

# For SDK-based integrations (e.g., stripe, datadog)
SDK_PACKAGE = "acme-sdk"                       # PyPI package name (e.g., "stripe", "datadog")
SDK_INIT_PARAMS = {                            # Parameters needed to initialize the SDK
    "api_key": "config.acme.API_KEY",
    "app_key": "config.acme.APP_KEY",
}

# Example methods for your integration (define the key operations)
EXAMPLE_METHODS = [
    {
        "name": "get_resource",
        "description": "Get a resource by ID",
        "params": [{"name": "resource_id", "type": "str"}],
        "return_type": "dict[str, Any]",
        "is_async": True,  # True for HTTP, varies for SDK
    },
    {
        "name": "create_resource",
        "description": "Create a new resource",
        "params": [
            {"name": "name", "type": "str"},
            {"name": "description", "type": "str | None", "default": "None"},
        ],
        "return_type": "dict[str, Any]",
        "is_async": True,
    },
]
```

---

## 📝 INSTRUCTIONS FOR LLM

You are tasked with creating a complete external API integration following the Fury API architectural pattern. Use the configuration variables defined above to generate all required files. Follow these steps **exactly**:

---

## STEP-BY-STEP GUIDE

### Step 1: Create the Client Class

**File:** `src/fury_api/lib/integrations/{INTEGRATION_NAME}.py`

#### For HTTP-based Integrations (INTEGRATION_TYPE = "http")

Inherit from `BaseHTTPClient` to get automatic connection management.

**Template:**

```python
"""
{INTEGRATION_DISPLAY_NAME} API integration client.

This client provides a typed interface to the {INTEGRATION_DISPLAY_NAME} API,
inheriting from BaseHTTPClient for proper HTTP connection lifecycle management.
"""

from typing import Any, Optional

import httpx

from fury_api.lib.settings import config
from fury_api.lib.integrations.base import BaseHTTPClient


class {INTEGRATION_DISPLAY_NAME}Client(BaseHTTPClient):
    """
    Client for interacting with the {INTEGRATION_DISPLAY_NAME} API.

    Inherits from BaseHTTPClient to get:
    - Long-lived HTTP connection management
    - Async context manager lifecycle
    - Automatic connection cleanup
    - Connection pooling for better performance

    Must be used with `async with` or via FastAPI Depends().

    Example:
        async with {INTEGRATION_DISPLAY_NAME}Client(...) as client:
            result = await client.some_method()
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,  # Adjust based on AUTH_TYPE
        timeout: float = {DEFAULT_TIMEOUT},
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize {INTEGRATION_DISPLAY_NAME} API client.

        Args:
            base_url: {INTEGRATION_DISPLAY_NAME} API endpoint URL
            api_key: API key for authentication
            timeout: Request timeout in seconds
            http_client: Optional pre-configured httpx client (for testing)
        """
        {GENERATE_HEADERS_BASED_ON_AUTH_TYPE}
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            http_client=http_client,
        )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the {INTEGRATION_DISPLAY_NAME} API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            endpoint: API endpoint path (relative to base_url)
            params: Query parameters
            json: JSON body for request

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        url = f"{self._base_url}/{endpoint}"
        response = await self._http_client.request(
            method, url, params=params, json=json, follow_redirects=True
        )
        response.raise_for_status()
        return response.json()

    {GENERATE_METHODS_FROM_EXAMPLE_METHODS}
```

**Instructions for HTTP-based integrations:**

1. **Headers generation based on AUTH_TYPE:**
   - `bearer`: `headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}`
   - `api_key`: `headers = {"X-API-Key": api_key, "Content-Type": "application/json"}`
   - `basic`: `headers = {"Authorization": f"Basic {base64_encode(username:password)}", "Content-Type": "application/json"}`
   - `none`: `headers = {"Content-Type": "application/json"}`
   - `custom`: Leave comment for user to customize

2. **Generate methods from EXAMPLE_METHODS:**
   For each method in EXAMPLE_METHODS:
   ```python
   async def {method_name}(self, {generate_params}) -> {return_type}:
       """{description}"""
       # Implement using self._make_request()
       response = await self._make_request("GET", f"endpoint/{param_value}")
       return response
   ```

#### For SDK-based Integrations (INTEGRATION_TYPE = "sdk")

Just wrap the SDK - no inheritance needed.

**Template:**

```python
"""
{INTEGRATION_DISPLAY_NAME} API integration client.

This client wraps the {INTEGRATION_DISPLAY_NAME} Python SDK to provide a cleaner
interface and proper initialization. The SDK manages HTTP connections internally.
"""

from typing import Any

import {SDK_PACKAGE}

from fury_api.lib.settings import config


class {INTEGRATION_DISPLAY_NAME}Client:
    """
    Client for interacting with the {INTEGRATION_DISPLAY_NAME} API.

    This client configures and wraps the {INTEGRATION_DISPLAY_NAME} SDK,
    providing a cleaner interface for operations.

    Unlike HTTP integrations, this doesn't use async context managers
    because the SDK manages connections internally.

    Example:
        client = {INTEGRATION_DISPLAY_NAME}Client()
        result = client.some_method(param="value")
    """

    def __init__(self, {GENERATE_INIT_PARAMS_FROM_SDK_INIT_PARAMS}):
        """
        Initialize the {INTEGRATION_DISPLAY_NAME} client.

        Args:
            {GENERATE_PARAM_DOCS}
        """
        {GENERATE_ASSIGNMENTS}
        # Initialize the SDK
        {GENERATE_SDK_INITIALIZATION}

    {GENERATE_METHODS_FROM_EXAMPLE_METHODS}
```

**Instructions for SDK-based integrations:**

1. **Generate init params from SDK_INIT_PARAMS:**
   ```python
   def __init__(self, api_key: str, app_key: str):
   ```

2. **Generate SDK initialization:**
   - For `stripe`: `stripe.api_key = self.api_key`
   - For `datadog`: `initialize(api_key=api_key, app_key=app_key)`
   - Generic: Follow SDK documentation

3. **Generate methods from EXAMPLE_METHODS:**
   For SDK-based methods, wrap the SDK's API:
   ```python
   def {method_name}(self, {generate_params}) -> {return_type}:
       """{description}"""
       return {SDK_PACKAGE}.Resource.operation(...)
   ```

---

### Step 2: Export from Integrations Module

**File:** `src/fury_api/lib/integrations/__init__.py`

**Action:** Add your client to the exports:

```python
from .{INTEGRATION_NAME} import {INTEGRATION_DISPLAY_NAME}Client

__all__ = [
    "{INTEGRATION_DISPLAY_NAME}Client",
    # ... other clients
]
```

---

### Step 3: Create Factory Method

**File:** `src/fury_api/lib/factories/integrations_factory.py`

**Action:** Add a factory method to the `IntegrationsFactory` class:

#### For HTTP-based Integrations:

```python
from fury_api.lib.integrations import {INTEGRATION_DISPLAY_NAME}Client

class IntegrationsFactory:

    @staticmethod
    def get_{INTEGRATION_NAME}_client() -> {INTEGRATION_DISPLAY_NAME}Client:
        """Get a new {INTEGRATION_DISPLAY_NAME} API client."""
        return {INTEGRATION_DISPLAY_NAME}Client(
            base_url={BASE_URL_CONFIG_PATH},
            api_key={API_KEY_CONFIG_PATH}.get_secret_value(),
            {GENERATE_ADDITIONAL_PARAMS}
        )

    # ... other factory methods
```

#### For SDK-based Integrations:

```python
from fury_api.lib.integrations import {INTEGRATION_DISPLAY_NAME}Client

class IntegrationsFactory:

    @staticmethod
    def get_{INTEGRATION_NAME}_client() -> {INTEGRATION_DISPLAY_NAME}Client:
        """Get a new {INTEGRATION_DISPLAY_NAME} API client."""
        return {INTEGRATION_DISPLAY_NAME}Client(
            {GENERATE_SDK_INIT_ARGS}
        )

    # ... other factory methods
```

**Instructions:**
- Use `config.path.to.value.get_secret_value()` for secrets (API keys, tokens)
- Use `config.path.to.value` for non-secret values (URLs, timeouts)

---

### Step 4: Create Dependency Function

**File:** `src/fury_api/lib/dependencies/integrations.py`

#### For HTTP-based Integrations:

Use `async def` with `yield` to manage the connection lifecycle:

```python
from collections.abc import AsyncGenerator
from fury_api.lib.integrations import {INTEGRATION_DISPLAY_NAME}Client
from fury_api.lib.factories import IntegrationsFactory


async def get_{INTEGRATION_NAME}_client() -> AsyncGenerator[{INTEGRATION_DISPLAY_NAME}Client, None]:
    """
    Get a {INTEGRATION_DISPLAY_NAME} API client with automatic lifecycle management.

    The client is configured from settings and manages a long-lived HTTP connection
    that's automatically cleaned up when the request completes.

    Yields:
        {INTEGRATION_DISPLAY_NAME}Client: Ready-to-use client with open connection

    Example:
        @app.post("/resources")
        async def create_resource(
            {INTEGRATION_NAME}: Annotated[{INTEGRATION_DISPLAY_NAME}Client, Depends(get_{INTEGRATION_NAME}_client)],
            payload: ResourcePayload,
        ):
            resource = await {INTEGRATION_NAME}.create_resource(...)
            return resource
    """
    async with IntegrationsFactory.get_{INTEGRATION_NAME}_client() as client:
        yield client
```

#### For SDK-based Integrations:

Use a simple `def` with `return`:

```python
from fury_api.lib.integrations import {INTEGRATION_DISPLAY_NAME}Client
from fury_api.lib.factories import IntegrationsFactory


def get_{INTEGRATION_NAME}_client() -> {INTEGRATION_DISPLAY_NAME}Client:
    """
    Get a {INTEGRATION_DISPLAY_NAME} API client.

    The {INTEGRATION_DISPLAY_NAME} SDK manages its own connections internally, so no
    async context manager is needed. The client is configured from settings.

    Returns:
        {INTEGRATION_DISPLAY_NAME}Client: Ready-to-use {INTEGRATION_DISPLAY_NAME} client

    Example:
        @app.post("/resources")
        def create_resource(
            {INTEGRATION_NAME}: Annotated[{INTEGRATION_DISPLAY_NAME}Client, Depends(get_{INTEGRATION_NAME}_client)],
            payload: ResourcePayload,
        ):
            resource = {INTEGRATION_NAME}.create_resource(...)
            return resource
    """
    return IntegrationsFactory.get_{INTEGRATION_NAME}_client()
```

**Key Difference:**
- **HTTP-based**: `async def` + `yield` + `async with` → FastAPI manages lifecycle
- **SDK-based**: `def` + `return` → SDK manages lifecycle

---

### Step 5: Export Dependency Function

**File:** `src/fury_api/lib/dependencies/__init__.py`

**Action:** Export the dependency:

```python
from .integrations import get_{INTEGRATION_NAME}_client

__all__ = [
    "get_{INTEGRATION_NAME}_client",
    # ... other exports
]
```

---

### Step 6: Add Configuration Settings

**File:** `src/fury_api/lib/settings.py` (or appropriate config file)

**Action:** Add configuration for the integration:

```python
class {INTEGRATION_DISPLAY_NAME}Settings(BaseSettings):
    """Settings for {INTEGRATION_DISPLAY_NAME} API integration."""

    API_URL: str = Field(..., description="{INTEGRATION_DISPLAY_NAME} API base URL")
    API_KEY: SecretStr = Field(..., description="{INTEGRATION_DISPLAY_NAME} API key")
    {GENERATE_ADDITIONAL_CONFIG_FIELDS}

    class Config:
        env_prefix = "{INTEGRATION_NAME_UPPER}_"


class Settings(BaseSettings):
    # ... existing settings
    {INTEGRATION_NAME}: {INTEGRATION_DISPLAY_NAME}Settings
```

**Environment Variables:**
```bash
{INTEGRATION_NAME_UPPER}_API_URL=https://api.{INTEGRATION_NAME}.com
{INTEGRATION_NAME_UPPER}_API_KEY=your_api_key_here
```

---

### Step 7: Use in Controllers (Example)

**File:** `src/fury_api/domain/{some_domain}/controllers.py`

**Example usage:**

```python
from typing import Annotated
from fastapi import APIRouter, Depends
from fury_api.lib.dependencies import get_{INTEGRATION_NAME}_client
from fury_api.lib.integrations import {INTEGRATION_DISPLAY_NAME}Client

router = APIRouter()


@router.get("/resources/{resource_id}")
async def get_resource(
    resource_id: str,
    {INTEGRATION_NAME}: Annotated[{INTEGRATION_DISPLAY_NAME}Client, Depends(get_{INTEGRATION_NAME}_client)],
):
    """Fetch a resource from {INTEGRATION_DISPLAY_NAME} API."""
    return await {INTEGRATION_NAME}.get_resource(resource_id)


@router.post("/resources")
async def create_resource(
    name: str,
    {INTEGRATION_NAME}: Annotated[{INTEGRATION_DISPLAY_NAME}Client, Depends(get_{INTEGRATION_NAME}_client)],
):
    """Create a new resource in {INTEGRATION_DISPLAY_NAME}."""
    return await {INTEGRATION_NAME}.create_resource(name=name)
```

---

## ✅ VERIFICATION CHECKLIST

After generation, verify the following:

- [ ] Client created in `src/fury_api/lib/integrations/{INTEGRATION_NAME}.py`
  - [ ] HTTP-based: Inherits from `BaseHTTPClient`
  - [ ] SDK-based: No inheritance, wraps SDK
- [ ] Client exported from `src/fury_api/lib/integrations/__init__.py`
- [ ] Factory method added to `src/fury_api/lib/factories/integrations_factory.py`
- [ ] Dependency function added in `src/fury_api/lib/dependencies/integrations.py`
  - [ ] HTTP-based: Uses `async def` with `yield` and `async with`
  - [ ] SDK-based: Uses `def` with `return`
- [ ] Dependency exported from `src/fury_api/lib/dependencies/__init__.py`
- [ ] Configuration settings added to settings file
- [ ] Environment variables documented
- [ ] Example controller usage provided

---

## 🎨 CONCRETE EXAMPLES

### Example 1: HTTP-based Integration (Acme API)

#### Configuration:
```python
INTEGRATION_NAME = "acme"
INTEGRATION_DISPLAY_NAME = "Acme"
INTEGRATION_TYPE = "http"
BASE_URL_CONFIG_PATH = "config.acme.API_URL"
AUTH_TYPE = "bearer"
API_KEY_CONFIG_PATH = "config.acme.API_KEY"
DEFAULT_TIMEOUT = 30.0

EXAMPLE_METHODS = [
    {
        "name": "get_resource",
        "description": "Get a resource by ID",
        "params": [{"name": "resource_id", "type": "str"}],
        "return_type": "dict[str, Any]",
        "is_async": True,
    },
]
```

#### Generated Client:
```python
# lib/integrations/acme.py
from typing import Any, Optional
import httpx
from fury_api.lib.settings import config
from fury_api.lib.integrations.base import BaseHTTPClient


class AcmeClient(BaseHTTPClient):
    """Client for interacting with the Acme API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            http_client=http_client,
        )

    async def _make_request(
        self, method: str, endpoint: str, params: dict[str, Any] | None = None, json: Any = None
    ) -> dict[str, Any]:
        """Make an HTTP request to the Acme API."""
        url = f"{self._base_url}/{endpoint}"
        response = await self._http_client.request(method, url, params=params, json=json)
        response.raise_for_status()
        return response.json()

    async def get_resource(self, resource_id: str) -> dict[str, Any]:
        """Get a resource by ID."""
        return await self._make_request("GET", f"resources/{resource_id}")
```

#### Generated Dependency:
```python
# lib/dependencies/integrations.py
async def get_acme_client() -> AsyncGenerator[AcmeClient, None]:
    """Get an Acme API client with automatic lifecycle management."""
    async with IntegrationsFactory.get_acme_client() as client:
        yield client
```

---

### Example 2: SDK-based Integration (Datadog)

#### Configuration:
```python
INTEGRATION_NAME = "datadog"
INTEGRATION_DISPLAY_NAME = "Datadog"
INTEGRATION_TYPE = "sdk"
SDK_PACKAGE = "datadog"
SDK_INIT_PARAMS = {
    "api_key": "config.datadog.API_KEY",
    "app_key": "config.datadog.APP_KEY",
}

EXAMPLE_METHODS = [
    {
        "name": "send_event",
        "description": "Send an event to Datadog",
        "params": [
            {"name": "title", "type": "str"},
            {"name": "text", "type": "str"},
            {"name": "tags", "type": "list[str] | None", "default": "None"},
        ],
        "return_type": "dict[str, Any]",
        "is_async": False,
    },
]
```

#### Generated Client:
```python
# lib/integrations/datadog.py
from typing import Any
from datadog import api, initialize
from fury_api.lib.settings import config


class DatadogClient:
    """Client for interacting with the Datadog API."""

    def __init__(self, api_key: str, app_key: str):
        self.api_key = api_key
        self.app_key = app_key
        initialize(api_key=api_key, app_key=app_key)

    def send_event(self, title: str, text: str, tags: list[str] | None = None) -> dict[str, Any]:
        """Send an event to Datadog."""
        return api.Event.create(title=title, text=text, tags=tags or [])
```

#### Generated Dependency:
```python
# lib/dependencies/integrations.py
def get_datadog_client() -> DatadogClient:
    """Get a Datadog API client."""
    return IntegrationsFactory.get_datadog_client()
```

---

## 🚀 USAGE

1. Copy this entire document
2. Edit the **CONFIGURATION VARIABLES** section with your integration details
3. Paste into an LLM (Claude, GPT-4, etc.) with the prompt:

   > "Using the configuration variables defined at the top, generate all the files specified in the instructions following the Fury API integration pattern. Provide each file's complete content, properly handling HTTP-based vs SDK-based differences."

4. Copy the generated files into your project
5. Add required dependencies to `requirements.txt` or `pyproject.toml`
6. Set environment variables
7. Test the integration

---

## 📚 ARCHITECTURE REFERENCE

This template follows the Fury API integration pattern:

### **HTTP-based Integrations (REST APIs)**
- **Client:** Inherits from `BaseHTTPClient`
- **Lifecycle:** Async context manager (`async with`)
- **Dependency:** `async def` with `yield`
- **Benefits:** Automatic connection pooling, proper cleanup, error handling

### **SDK-based Integrations**
- **Client:** Wraps third-party SDK
- **Lifecycle:** Managed by SDK
- **Dependency:** `def` with `return`
- **Benefits:** Simpler code, leverages SDK's features

### **Factory Pattern**
- Centralizes client configuration
- Reads from settings/config
- Handles secrets properly
- Enables testing with mocks

### **Dependency Injection**
- FastAPI `Depends()` pattern
- Automatic lifecycle management
- Type-safe with `Annotated`
- Clean separation of concerns

The pattern ensures:
- ✅ Consistent structure across all integrations
- ✅ Proper resource cleanup (connections, sessions)
- ✅ Type safety and IDE autocomplete
- ✅ Easy testing with dependency overrides
- ✅ Configuration from environment variables
- ✅ Secrets management with `SecretStr`
