import pytest
from fastapi.testclient import TestClient

from tests.helpers.crud import create_collection


@pytest.mark.asyncio
async def test_create_collection_endpoint(test_org, isolated_client: TestClient):
    """Verify create_collection returns dict."""
    collection = await create_collection(isolated_client, name="Test Collection", external_id="test-collection-1")

    assert isinstance(collection, dict)
    assert collection["id"] is not None
    assert collection["name"] == "Test Collection"
    assert collection["externalId"] == "test-collection-1"
