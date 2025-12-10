# ruff: noqa: E402
import os

# import subprocess
import pytest
from fastapi_pagination import add_pagination

os.environ["FURY_API_APP_ENVIRONMENT"] = "test"
os.environ["FURY_DB_TENANT_ROLE_ENABLED"] = "false"
os.environ["FURY_API_DEVEX_ENABLED"] = "true"
os.environ["FURY_API_DEVEX_ON_CREATE_ORGANIZATION_SKIP_AUTH0_USER_CREATE"] = "true"
os.environ["FURY_API_DEVEX_SKIP_AUTH0_USER_CREATE"] = "true"
os.environ["FURY_API_DEVEX_ON_CREATE_ORGANIZATION_SKIP_DEFAULT_INTERNAL_USERS_VAULT_CREATION"] = "true"
os.environ["FURY_API_EVENTS_API_USE_BACKGROUND_TASKS"] = "false"

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import create_engine


@pytest.fixture(scope="session")
async def db_init() -> None:
    from fury_api.lib.settings import config

    engine = create_engine(config.database.URL, echo=False)

    # Since Makefile runs migrations before tests, tables already exist with vector extension
    # We just need to ensure the entities view is dropped if it exists
    with engine.connect() as connection:
        connection.execute(text("DROP VIEW IF EXISTS entities;"))
        connection.commit()

    # Note: We rely on Alembic migrations (run by Makefile) to create tables
    # This avoids the vector extension issues with metadata.create_all()
    # TODO: Add fixture to clean up test data between test runs if needed


@pytest.fixture(scope="session")
async def app() -> FastAPI:
    from fury_api.lib.lifecycle import on_shutdown, on_startup
    from fury_api.main import app

    await on_startup()
    yield app
    await on_shutdown()


@pytest.fixture(scope="session")
def mocked_user_client(app: FastAPI) -> TestClient:
    from fury_api.domain.users.models import User
    from fury_api.lib.security import get_current_user, get_current_user_new_organization, validate_api_key

    app.dependency_overrides[get_current_user] = lambda: User(
        source_id="1", name="test", email="test@test.com", organization_id=1, user_id=1, firebase_id="test-firebase-id"
    )
    app.dependency_overrides[get_current_user_new_organization] = lambda: User(
        source_id="1",
        name="test",
        email="test@test.com",
        organization_id=None,
        user_id=None,
        firebase_id="test-firebase-id",
    )
    app.dependency_overrides[validate_api_key] = lambda: None

    class VaultClient:
        def read(self, secret: str):
            return None

        def create(self, secret: str, data: dict):
            return None

        def decrypt(self, secret: str):
            return None

    add_pagination(app)

    return TestClient(app)


@pytest.fixture(scope="session")
def client(app: FastAPI) -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="function")
def unauthenticated_client(app: FastAPI) -> TestClient:
    """
    Provide a client without auth/org context by temporarily clearing auth overrides.
    """
    from fury_api.lib.security import get_current_user, get_current_user_new_organization, validate_api_key

    overrides_backup = dict(app.dependency_overrides)
    for dep in (get_current_user, get_current_user_new_organization, validate_api_key):
        app.dependency_overrides.pop(dep, None)
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides = overrides_backup


@pytest.fixture(scope="session")
async def bootstrap_org(db_init: None, mocked_user_client: TestClient) -> None:
    response = mocked_user_client.post("/api/v1/organizations", json={"name": "test-org"})
    # Assuming the function is imported and ready to be used
    # Retrieve the UnitOfWork dependency
    # Allow 201 (created) or 409 (already exists)
    assert response.status_code in [201, 409], f"Unexpected status {response.status_code}: {response.json()}"


@pytest.fixture(scope="function")
def use_system_user(mocked_user_client: TestClient) -> None:
    from fury_api.lib.dependencies import is_system_user

    mocked_user_client.app.dependency_overrides[is_system_user] = lambda: True
    yield
    del mocked_user_client.app.dependency_overrides[is_system_user]


# Service layer fixtures for test data factories
from fury_api.lib.factories import UnitOfWorkFactory, ServiceFactory
from fury_api.lib.factories.service_factory import ServiceType


@pytest.fixture(scope="function")
async def test_uow(bootstrap_org):
    """Provide UnitOfWork for test organization (ID=1)."""
    async with UnitOfWorkFactory.get_uow(organization_id=1) as uow:
        yield uow


@pytest.fixture(scope="function")
def test_auth_user(bootstrap_org):
    """Provide test User for service authentication."""
    from fury_api.domain.users.models import User

    return User(
        source_id="1", name="test", email="test@test.com", organization_id=1, user_id=1, firebase_id="test-firebase-id"
    )


@pytest.fixture(scope="function")
async def authors_service(test_uow, test_auth_user):
    """Provide AuthorsService for direct service access."""
    return ServiceFactory.create_service(
        ServiceType.AUTHORS, test_uow, auth_user=test_auth_user, has_system_access=True
    )


@pytest.fixture(scope="function")
async def collections_service(test_uow, test_auth_user):
    """Provide CollectionsService for direct service access."""
    return ServiceFactory.create_service(
        ServiceType.COLLECTIONS, test_uow, auth_user=test_auth_user, has_system_access=True
    )


@pytest.fixture(scope="function")
async def contents_service(test_uow, test_auth_user):
    """Provide ContentsService for direct service access."""
    return ServiceFactory.create_service(
        ServiceType.CONTENTS, test_uow, auth_user=test_auth_user, has_system_access=True
    )


# =============================================================================
# Isolated Test Fixtures - Per-Test Organization for Complete Data Isolation
# =============================================================================


@pytest.fixture(scope="function")
async def test_org(db_init: None) -> dict:
    """Create a unique organization for each test function.

    Provides complete data isolation by giving each test its own tenant.
    Data is automatically cleaned up after the test completes.
    """
    import uuid
    from fury_api.domain.organizations.models import Organization

    org_name = f"test-org-{uuid.uuid4()}"

    # Create organization directly in database to avoid user creation issues
    async with UnitOfWorkFactory.get_uow() as uow:
        org = Organization(name=org_name)
        uow.session.add(org)
        await uow.session.flush()
        await uow.session.refresh(org)
        org_id = org.id
        org_name_saved = org.name
        await uow.session.commit()

    org_data = {"id": org_id, "name": org_name_saved}
    yield org_data

    # Cleanup on teardown - delete in order to respect foreign key constraints
    async with UnitOfWorkFactory.get_uow() as uow:
        org_id = org_data["id"]

        # Delete in order to respect foreign key constraints
        await uow.session.execute(
            text("DELETE FROM content_collection WHERE organization_id = :id"), {"id": org_id}
        )
        await uow.session.execute(text("DELETE FROM collection WHERE organization_id = :id"), {"id": org_id})
        await uow.session.execute(
            text(
                "DELETE FROM document_content WHERE document_id IN (SELECT id FROM document WHERE organization_id = :id)"
            ),
            {"id": org_id},
        )
        await uow.session.execute(text("DELETE FROM conversation WHERE organization_id = :id"), {"id": org_id})
        await uow.session.execute(text("DELETE FROM document WHERE organization_id = :id"), {"id": org_id})
        await uow.session.execute(text("DELETE FROM organization WHERE id = :id"), {"id": org_id})
        await uow.session.commit()


@pytest.fixture(scope="function")
def isolated_client(app: FastAPI, test_org: dict) -> TestClient:
    """Test client with isolated organization context.

    Overrides the current user dependency to use the test org's ID,
    providing complete isolation from other tests.
    """
    from fury_api.domain.users.models import User
    from fury_api.lib.security import get_current_user

    # Ensure pagination is set up (idempotent)
    add_pagination(app)

    # Save the original override
    original_override = app.dependency_overrides.get(get_current_user)

    # Override dependency with test org's ID
    app.dependency_overrides[get_current_user] = lambda: User(
        source_id="1",
        name="test",
        email="test@test.com",
        organization_id=test_org["id"],  # Dynamic org ID per test
        user_id=1,
        firebase_id="test-firebase-id",
    )

    client = TestClient(app)
    yield client

    # Restore original override after test
    if original_override is not None:
        app.dependency_overrides[get_current_user] = original_override
    else:
        # If there was no original override, remove it
        app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="function")
async def isolated_uow(test_org: dict):
    """UnitOfWork scoped to test's isolated organization."""
    async with UnitOfWorkFactory.get_uow(organization_id=test_org["id"]) as uow:
        yield uow


@pytest.fixture(scope="function")
def isolated_test_auth_user(test_org: dict):
    """Provide test User for isolated organization service authentication."""
    from fury_api.domain.users.models import User

    return User(
        source_id="1",
        name="test",
        email="test@test.com",
        organization_id=test_org["id"],
        user_id=1,
        firebase_id="test-firebase-id",
    )


@pytest.fixture(scope="function")
async def isolated_authors_service(isolated_uow, isolated_test_auth_user):
    """AuthorsService for isolated organization."""
    return ServiceFactory.create_service(
        ServiceType.AUTHORS, isolated_uow, auth_user=isolated_test_auth_user, has_system_access=True
    )


@pytest.fixture(scope="function")
async def isolated_collections_service(isolated_uow, isolated_test_auth_user):
    """CollectionsService for isolated organization."""
    return ServiceFactory.create_service(
        ServiceType.COLLECTIONS, isolated_uow, auth_user=isolated_test_auth_user, has_system_access=True
    )


@pytest.fixture(scope="function")
async def isolated_contents_service(isolated_uow, isolated_test_auth_user):
    """ContentsService for isolated organization."""
    return ServiceFactory.create_service(
        ServiceType.CONTENTS, isolated_uow, auth_user=isolated_test_auth_user, has_system_access=True
    )
