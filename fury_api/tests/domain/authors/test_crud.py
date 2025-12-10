import pytest

from tests.helpers.crud import create_author


@pytest.mark.asyncio
async def test_create_author_service(test_org, isolated_authors_service):
    """Verify create_author returns normalized dict."""
    author = await create_author(isolated_authors_service, display_name="Test Author", external_id="test-author-1")

    # All assertions use dict access
    assert isinstance(author, dict)
    assert author["id"] is not None
    assert author["display_name"] == "Test Author"
    assert author["external_id"] == "test-author-1"
    assert author["handle"] == "@test_author"
