# Fury API

## Overview

Fury API is built with **Domain-Driven Design (DDD)** and **Unit of Work (UoW)** patterns, tightly integrating with its data model to centrally manage schemas, migrations, and transactional integrity. It's cloud-native and ready for **containerized deployments** with Docker, Helm, and Kubernetes configurations. Operations are streamlined via `make` commands to minimize manual intervention.

**Tech Stack:** FastAPI, PostgreSQL, SQLAlchemy, Firebase Auth, Docker, Kubernetes

---

## Getting Started (Local Development)

### Prerequisites
- Python 3.11+, Docker, Make

### Run Locally (5 minutes)
1. `make install` (install poetry and project dependencies)
2. Create `.env` (copy from `.env.example`) see how to configure firebase [here](doc/CONFIGURING_FIREBASE.md).
3. `docker-compose up postgres -d` (launch database in the background)
4. `make db-migrate` (run database migrations)
4. `make start`
5. Visit http://localhost:3000/docs

Alternatively, you can just use docker-compose - you'll still need to perform step 2 (create `.env`) for it to work.

```bash
docker-compose up fury-api -d
```

### Authentication

The API requires Firebase authentication for all endpoints. For local development, you have two options:

#### Option 1: Skip Authentication (Recommended for Local Dev)

Bypass token validation entirely by setting a mock user identity in `.env`:

```bash
FURY_API_DEVEX_ENABLED=true
FURY_API_DEVEX_AUTH_OVERRIDE_ENABLED=true
FURY_API_DEVEX_AUTH_OVERRIDE_USER_NAME=Test User
FURY_API_DEVEX_AUTH_OVERRIDE_USER_EMAIL=test@example.com
FURY_API_DEVEX_AUTH_OVERRIDE_ORGANIZATION_ID=org_123
FURY_API_DEVEX_AUTH_OVERRIDE_USER_ID=user_123
FURY_API_DEVEX_AUTH_OVERRIDE_FIREBASE_USER_ID=firebase_123
```

All requests will be authenticated as this mock user. Use this for rapid development.

#### Option 2: Generate Real Firebase Tokens
Test actual authentication flows using a Firebase user:

```bash
# In .env
FURY_API_DEVEX_ENABLED=true
FURY_API_DEVEX_TOKEN_GENERATION_FIREBASE_USER_ID=your_firebase_user_id

# Generate token (valid for 1 hour)
make get-token
```

Use this to better mimick real production scenarios.

---

## Documentation

### 📚 Learn More

**Want to instantiate a new fury version for a dedicated use-case?**
→ Read [SETUP](docs/01_PROJECT_STRUCTURE.md).

**Want to understand how the codebase is organized?**
→ Read [Project Structure](docs/01_PROJECT_STRUCTURE.md) to learn about domains, services, repositories, authentication, pagination, filtering, and the dependency injection system.

**Need to add a new business domain (e.g., `invoices`, `projects`)?**
→ Follow [Creating a New Domain](docs/02_CREATING_A_NEW_DOMAIN.md) for step-by-step guidance on building controllers, models, services, and repositories.

**Integrating with an external API (e.g., Stripe, SendGrid)?**
→ See [Creating a New Integration](docs/03_CREATING_A_NEW_INTEGRATION.md) to set up clients with proper factory and dependency injection support.

**Working with the database or migrations?**
→ Check [Default Data Model](docs/DEFAULT_DATA_MODEL.md) for details on the key tables that are configure out-of-the-box.
→ Check [Database & Migrations](docs/DATABASE_AND_MIGRATIONS.md) for details on Alembic, creating/applying migrations, and rollback procedures.

**Understanding dependencies and factories?**
→ Dive into [Dependencies and Factories](docs/DEPENDENCIES_AND_FACTORIES.md) for an in-depth guide on FastAPI dependency injection, factory patterns, and when to use each.

**Ready to deploy to Kubernetes?**
→ Follow [Deployment](docs/04_DEPLOYING.md) for instructions on building Docker images, pushing Helm charts, and running production migrations.
