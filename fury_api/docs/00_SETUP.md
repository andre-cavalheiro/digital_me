# Fury API Initial Setup - LLM Script Template

This document serves as an **executable script for an LLM** to properly configure a Fury API project for a specific use case. Simply define the variables below and paste this entire document into an LLM.

---

## 🎯 CONFIGURATION VARIABLES (Edit these)

```python
# Define your project configuration here
PROJECT_NAME = "Digital Me API"              # Display name for the API (e.g., "Digital Me API", "Task Manager API")
PROJECT_SLUG = "digital_me_api"              # Snake_case identifier (e.g., "digital_me_api", "task_manager_api")
PROJECT_DESCRIPTION = "Digital Me API - AI-assisted writing platform with content aggregation"

# Docker and Kubernetes configuration
DOCKER_IMAGE = "andrecavalheiro/digital-me-api"     # Docker image name for container registry
KUBERNETES_NAMESPACE = "digital-me"                  # Kubernetes namespace for deployment
KUBERNETES_CLUSTER = "kratos"                        # Kubernetes cluster name (default: "kratos")
HELM_CHART_NAME = "digital-me-api"                   # Helm chart name

# Helm configuration
HELM_CHART_DESCRIPTION = "Digital Me API - Backend for AI-assisted writing platform"
SERVICE_PORT = 3000                                  # Port the service will run on

# API Metadata (for OpenAPI/Swagger documentation)
OPENAPI_TITLE = "Digital Me API"
OPENAPI_DESCRIPTION = "API for Digital Me - AI-assisted writing with content aggregation from curated sources"
CONTACT_NAME = "Andre Cavalheiro"
CONTACT_EMAIL = "andre@cavalheiro.io"

# PyProject metadata
PYPROJECT_PACKAGE_NAME = "digital_me_api"            # Python package name (snake_case)
PYPROJECT_HOMEPAGE = "https://github.com/yourusername/digital-me"
PYPROJECT_REPOSITORY = "https://github.com/yourusername/digital-me"
PYPROJECT_AUTHORS = ["Andre Cavalheiro <andre@cavalheiro.io>"]
```

---

## 📝 INSTRUCTIONS FOR LLM

You are tasked with configuring a Fury API project for a specific use case. Use the configuration variables defined above to update all required files. Follow these steps **exactly**:

---

### Step 1: Update Makefile

**File:** `Makefile`

**Action:** Update the following variables at the top of the Makefile:

```makefile
DOCKER_IMAGE := {DOCKER_IMAGE}
KUBERNETES_NAMESPACE := {KUBERNETES_NAMESPACE}
KUBERNETES_CLUSTER := {KUBERNETES_CLUSTER}
HELM_CHART_NAME := {HELM_CHART_NAME}
```

**Instructions:**
- Locate the existing variable definitions in the Makefile
- Replace empty or placeholder values with the configured values
- Keep all other Makefile content unchanged
- Ensure proper Makefile syntax (`:=` for assignment, no quotes around values)

**Example:**
```makefile
DOCKER_IMAGE := andrecavalheiro/digital-me-api
KUBERNETES_NAMESPACE := digital-me
KUBERNETES_CLUSTER := kratos
HELM_CHART_NAME := digital-me-api
```

---

### Step 2: Update Helm Chart Metadata

**File:** `deploy/helm/Chart.yaml`

**Action:** Update the chart metadata:

```yaml
apiVersion: v2
name: {HELM_CHART_NAME}
description: {HELM_CHART_DESCRIPTION}
version: 0.1.0
appVersion: "1.0"
type: application
```

**Instructions:**
- Update the `name` field with the HELM_CHART_NAME value
- Update the `description` field with the HELM_CHART_DESCRIPTION value
- Keep the version, appVersion, and type fields as shown
- Maintain proper YAML formatting

---

### Step 3: Update Helm Values

**File:** `deploy/helm/values.yaml`

**Action:** Update the image repository and service port:

Locate the `image` section and update:
```yaml
image:
  repository: {DOCKER_IMAGE}
  pullPolicy: IfNotPresent
  tag: "latest"
```

Locate the `service` section and update:
```yaml
service:
  type: ClusterIP
  port: {SERVICE_PORT}
```

**Instructions:**
- Only update the `repository` field in the `image` section
- Only update the `port` field in the `service` section
- Keep all other values.yaml content unchanged
- Maintain proper YAML formatting and indentation

---

### Step 4: Update Application Settings

**File:** `src/fury_api/lib/settings.py`

**Action:** Locate the `AppSettings` class and update the following fields:

```python
class AppSettings(BaseSettings):
    """Application settings."""

    NAME: str = "{PROJECT_NAME}"
    SLUG: str = "{PROJECT_SLUG}"
    # ... other fields remain unchanged
```

Also locate the `OpenAPISettings` class and update:

```python
class OpenAPISettings(BaseSettings):
    """OpenAPI (Swagger) configuration."""

    TITLE: str = "{OPENAPI_TITLE}"
    DESCRIPTION: str = "{OPENAPI_DESCRIPTION}"
    # ... other fields remain unchanged
```

And locate the `ContactSettings` class and update:

```python
class ContactSettings(BaseSettings):
    """API contact information."""

    NAME: str = "{CONTACT_NAME}"
    EMAIL: str = "{CONTACT_EMAIL}"
    # ... other fields remain unchanged
```

**Instructions:**
- Only update the fields specified above
- Keep all other settings classes and fields unchanged
- Maintain proper Python syntax and indentation
- Preserve any existing comments

---

### Step 5: Update PyProject Metadata

**File:** `pyproject.toml`

**Action:** Locate the `[tool.poetry]` section and update:

```toml
[tool.poetry]
name = "{PYPROJECT_PACKAGE_NAME}"
version = "0.1.0"
description = "{PROJECT_DESCRIPTION}"
authors = {PYPROJECT_AUTHORS}
readme = "README.md"
homepage = "{PYPROJECT_HOMEPAGE}"
repository = "{PYPROJECT_REPOSITORY}"
# ... rest remains unchanged
```

**Instructions:**
- Update the `name` field with the PYPROJECT_PACKAGE_NAME value
- Update the `description` field with the PROJECT_DESCRIPTION value
- Update the `authors` array with the PYPROJECT_AUTHORS value
- Update the `homepage` and `repository` fields with their respective values
- Keep all dependencies and other sections unchanged
- Maintain proper TOML formatting

**Example:**
```toml
[tool.poetry]
name = "digital_me_api"
version = "0.1.0"
description = "Digital Me API - AI-assisted writing platform with content aggregation"
authors = ["Andre Cavalheiro <andre@cavalheiro.io>"]
readme = "README.md"
homepage = "https://github.com/yourusername/digital-me"
repository = "https://github.com/yourusername/digital-me"
```

---

## 🔧 INTEGRATION CONFIGURATION (Human Decision Required)

**Note for LLM:** The following section describes integration configuration that requires **human decision-making** and is **outside the scope of automated LLM scripting**. Include this section in any output to inform the human user about additional manual steps needed.

### Organization Integration Setup

**File to review:** `src/fury_api/domain/organizations.py`

The Fury API includes a function `create_organization()` that can automatically set up third-party integrations when a new organization is created. By default, the following integrations may be configured:

#### Available Integrations:
1. **Stripe** - Payment processing
   - Creates a Stripe customer for the organization
   - Requires: Stripe API credentials in settings
   - To disable: Remove Stripe integration code from `create_organization()`
   - To remove dependency: `poetry remove stripe`

2. **Prefect** - Workflow orchestration
   - Creates a system user and pushes credentials to Prefect
   - Requires: Prefect Cloud/Server credentials in settings
   - To disable: Remove Prefect integration code from `create_organization()`
   - To remove dependency: `poetry remove prefect`

#### Human Actions Required:
1. **Review** the `create_organization()` function in `src/fury_api/domain/organizations.py`
2. **Decide** which integrations are needed for your use case
3. **Remove** integration code for unused services to streamline the application
4. **Remove dependencies** from `pyproject.toml` using `poetry remove <package>` if not needed
5. **Configure** environment variables for any integrations you keep (see respective integration documentation)

#### Example Decision Process:
- **Building a SaaS with payments?** → Keep Stripe
- **Need workflow automation?** → Keep Prefect
- **Building a free tool or internal app?** → Remove Stripe
- **Simple CRUD API?** → Remove Prefect

**This configuration cannot be automated and requires human judgment based on business requirements.**

---

## ✅ VERIFICATION CHECKLIST

After generation, verify the following:

- [ ] `Makefile` updated with correct values:
  - [ ] DOCKER_IMAGE set to your Docker registry image
  - [ ] KUBERNETES_NAMESPACE set to your deployment namespace
  - [ ] KUBERNETES_CLUSTER set appropriately
  - [ ] HELM_CHART_NAME set to match your project
- [ ] `deploy/helm/Chart.yaml` updated:
  - [ ] `name` field matches HELM_CHART_NAME
  - [ ] `description` field describes your project
- [ ] `deploy/helm/values.yaml` updated:
  - [ ] `image.repository` matches DOCKER_IMAGE
  - [ ] `service.port` matches SERVICE_PORT
- [ ] `src/fury_api/lib/settings.py` updated:
  - [ ] `AppSettings.NAME` reflects your project name
  - [ ] `AppSettings.SLUG` reflects your project slug
  - [ ] `OpenAPISettings.TITLE` and `DESCRIPTION` updated
  - [ ] `ContactSettings` updated with your information
- [ ] `pyproject.toml` updated:
  - [ ] `name` matches PYPROJECT_PACKAGE_NAME
  - [ ] `description` describes your project
  - [ ] `authors` contains your information
  - [ ] `homepage` and `repository` URLs are correct
- [ ] Integration decisions documented (human action item)

---

## 🎨 CONCRETE EXAMPLE: Digital Me Project

Here's a complete example for the "Digital Me" AI-assisted writing platform:

### Configuration:
```python
PROJECT_NAME = "Digital Me API"
PROJECT_SLUG = "digital_me_api"
PROJECT_DESCRIPTION = "Digital Me API - AI-assisted writing platform with content aggregation"

DOCKER_IMAGE = "andrecavalheiro/digital-me-api"
KUBERNETES_NAMESPACE = "digital-me"
KUBERNETES_CLUSTER = "kratos"
HELM_CHART_NAME = "digital-me-api"

HELM_CHART_DESCRIPTION = "Digital Me API - Backend for AI-assisted writing platform"
SERVICE_PORT = 3000

OPENAPI_TITLE = "Digital Me API"
OPENAPI_DESCRIPTION = "API for Digital Me - AI-assisted writing with content aggregation from curated sources"
CONTACT_NAME = "Andre Cavalheiro"
CONTACT_EMAIL = "andre@cavalheiro.io"

PYPROJECT_PACKAGE_NAME = "digital_me_api"
PYPROJECT_HOMEPAGE = "https://github.com/andrecavalheiro/digital-me"
PYPROJECT_REPOSITORY = "https://github.com/andrecavalheiro/digital-me"
PYPROJECT_AUTHORS = ["Andre Cavalheiro <andre@cavalheiro.io>"]
```

### Result:
- Makefile configured for `digital-me` namespace and Docker image
- Helm charts branded as "Digital Me API"
- Application settings show "Digital Me API" in admin panels and logs
- OpenAPI docs accessible at `/docs` with proper branding
- PyProject ready for `poetry install` and deployment
- Ready for integration decisions (Stripe: No, Prefect: Maybe for content sync jobs)

---

## 🚀 USAGE

1. Copy this entire document
2. Edit the **CONFIGURATION VARIABLES** section with your project details
3. Paste into an LLM (Claude, GPT-4, etc.) with the prompt:

   > "Using the configuration variables defined at the top, update all files specified in the instructions following the Fury API setup pattern. Provide the complete updated content for each file."

4. Copy the updated file contents into your project
5. Review the Integration Configuration section and make human decisions about which services to enable
6. Run `poetry install` to install dependencies
7. Configure environment variables (see `.env.example` or settings.py for required variables)
8. Run database migrations: `poetry run alembic upgrade head`
9. Start the server: `make run-local` or `poetry run uvicorn fury_api.main:app --reload`

---

## 🔧 NEXT STEPS AFTER SETUP

After completing this initial setup, you may want to:

1. **Create new domains** for your business logic
   - See: `docs/02_CREATING_A_NEW_DOMAIN.md` for LLM-executable domain creation

2. **Add external integrations** for third-party APIs
   - See: `docs/03_CREATING_A_NEW_INTEGRATION.md` for LLM-executable integration setup

3. **Configure environment variables**
   - Copy `.env.example` to `.env.local`
   - Fill in Firebase credentials, database URLs, API keys

4. **Set up database**
   - Ensure PostgreSQL is running
   - Create database: `createdb your_db_name`
   - Run migrations: `poetry run alembic upgrade head`

5. **Review authentication**
   - Configure Firebase project
   - Set up Firebase Admin SDK credentials
   - Test user creation and authentication flow

6. **Deploy to Kubernetes**
   - Build Docker image: `make build`
   - Push to registry: `make push`
   - Deploy with Helm: `make deploy`

---

## 📚 ARCHITECTURE OVERVIEW

The Fury API follows a domain-driven design pattern with:

- **Domain Layer** (`src/fury_api/domain/`): Business logic organized by domain
  - Each domain has: models, repository, service, controllers, exceptions
  - Built-in domains: users, organizations, plugins, admin, health_check

- **Library Layer** (`src/fury_api/lib/`): Shared utilities and infrastructure
  - Database: SQLModel + SQLAlchemy + PostgreSQL
  - Auth: Firebase Authentication
  - API: FastAPI with OpenAPI docs
  - Patterns: Repository pattern, Unit of Work, Dependency Injection

- **Infrastructure** (`deploy/`): Deployment configurations
  - Kubernetes via Helm charts
  - Docker containerization
  - Environment-based configuration (local/dev/prod)

The setup ensures:
- ✅ Multi-tenancy via organization_id on all domain models
- ✅ Type safety with Pydantic and SQLModel
- ✅ Automatic API documentation with OpenAPI/Swagger
- ✅ Clean separation of concerns (models, repositories, services, controllers)
- ✅ Dependency injection for testability
- ✅ Database migrations with Alembic
- ✅ Authentication with Firebase
- ✅ Plugin system for extensibility
