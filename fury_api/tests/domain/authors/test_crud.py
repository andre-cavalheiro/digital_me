import pytest

from tests.helpers.crud import create_author


@pytest.mark.asyncio
async def test_create_author_service(bootstrap_org, authors_service):
    """Verify create_author returns normalized dict."""
    author = await create_author(authors_service, display_name="Test Author", external_id="test-author-1")

    # All assertions use dict access
    assert isinstance(author, dict)
    assert author["id"] is not None
    assert author["display_name"] == "Test Author"
    assert author["external_id"] == "test-author-1"
    assert author["handle"] == "@test_author"
