import pytest
from fastapi.testclient import TestClient

from tests.helpers.crud import create_author, create_content


@pytest.mark.asyncio
async def test_create_content_endpoint(bootstrap_org, mocked_user_client: TestClient, authors_service):
    """Verify create_content returns dict."""
    # Create author first
    author = await create_author(authors_service, display_name="Content Author", external_id="content-author-1")

    # Create content - normalized dict access
    content = await create_content(
        mocked_user_client,
        body="Test content body",
        title="Test Content",
        external_id="test-content-1",
        author_id=author["id"],  # Normalized dict access
    )

    assert isinstance(content, dict)
    assert content["id"] is not None
    assert content["body"] == "Test content body"
    assert content["authorId"] == author["id"]
