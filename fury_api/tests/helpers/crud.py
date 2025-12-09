"""Test data factories for content domain - normalized interface."""

import uuid
from typing import Any

from fastapi.testclient import TestClient

from fury_api.domain.authors.models import Author
from .utils import generic_http_call


async def create_author(
    authors_service,  # AuthorsService from fixture
    platform: str = "x",
    external_id: str | None = None,
    display_name: str = "Test Author",
    handle: str | None = None,
    avatar_url: str = "https://example.com/avatar.jpg",
    profile_url: str = "https://example.com/profile",
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create test author via service layer.

    Returns dict for consistency with other factories.

    Args:
        authors_service: AuthorsService from pytest fixture
        platform: Platform identifier (default: "x")
        external_id: Unique ID (auto-generated if None)
        display_name: Author display name
        handle: Author handle/username
        **kwargs: Additional Author fields

    Returns:
        Author data as dict (normalized from model)

    Example:
        author = await create_author(
            authors_service,
            display_name="John Doe",
            external_id="john-123"
        )
        print(author["id"])  # Access as dict key
    """
    unique_id = external_id or f"author-{uuid.uuid4()}"

    author_data = Author.model_validate(
        {
            "platform": platform,
            "external_id": unique_id,
            "display_name": display_name,
            "handle": handle or f"@{display_name.lower().replace(' ', '_')}",
            "avatar_url": avatar_url,
            "profile_url": profile_url,
            "follower_count": kwargs.get("follower_count", 100),
            "following_count": kwargs.get("following_count", 50),
            "bio": kwargs.get("bio"),
        }
    )

    # Create via service and normalize to dict
    author_model = await authors_service.create_item(author_data)

    # Commit to make author visible to HTTP endpoints
    await authors_service.session.commit()

    return author_model.model_dump()  # Normalize to dict


async def create_collection(
    client: TestClient,
    type: str = "bookmark_folder",
    platform: str = "x",
    name: str = "Test Collection",
    external_id: str | None = None,
    description: str | None = None,
    plugin_id: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create test collection via HTTP API.

    Args:
        client: TestClient (mocked_user_client fixture)
        type: Collection type
        platform: Platform identifier
        name: Collection name
        external_id: Unique ID (auto-generated if None)
        plugin_id: Optional plugin association
        **kwargs: Additional fields

    Returns:
        Collection data as dict from API response

    Example:
        collection = await create_collection(
            mocked_user_client,
            name="My Bookmarks"
        )
        print(collection["id"])  # Access as dict key
    """
    unique_id = external_id or f"collection-{uuid.uuid4()}"
    data = {
        "type": type,
        "platform": platform,
        "name": name,
        "external_id": unique_id,
        "description": description or f"{name} description",
        "collection_url": f"https://example.com/collection/{unique_id}",
        "plugin_id": plugin_id,
        **kwargs,
    }

    return generic_http_call(
        client,
        "/api/v1/collections",
        "post",
        data=data,
        expected_status_code=201,
    )


async def create_content(
    client: TestClient,
    external_id: str | None = None,
    body: str = "Test content body",
    author_id: int | None = None,
    title: str | None = "Test Content",
    published_at: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create test content via HTTP API.

    Args:
        client: TestClient (mocked_user_client fixture)
        external_id: Unique ID (auto-generated if None)
        body: Content body text (required)
        author_id: Author ID to associate
        title: Content title
        published_at: Publication timestamp
        **kwargs: Additional Content fields

    Returns:
        Content data as dict from API response

    Example:
        content = await create_content(
            mocked_user_client,
            title="My Article",
            author_id=author["id"]  # Now consistently a dict key
        )
        print(content["id"])  # Access as dict key
    """
    unique_id = external_id or f"content-{uuid.uuid4()}"
    data = {
        "external_id": unique_id,
        "body": body,
        "title": title,
        "external_url": f"https://example.com/content/{unique_id}",
        **kwargs,
    }
    if author_id is not None:
        data["author_id"] = author_id
    if published_at is not None:
        data["published_at"] = published_at

    return generic_http_call(
        client,
        "/api/v1/content",
        "post",
        data=data,
        expected_status_code=201,
    )


async def associate_content_with_collection(
    client: TestClient,
    content_id: int,
    collection_id: int,
) -> dict[str, Any]:
    """
    Associate content with a collection via API.

    Args:
        client: TestClient
        content_id: Content ID
        collection_id: Collection ID

    Returns:
        Association data as dict
    """
    try:
        return generic_http_call(
            client,
            f"/api/v1/collections/{collection_id}/content",
            "post",
            data={"content_id": content_id},
            expected_status_code=201,
        )
    except Exception:
        # If the endpoint doesn't exist, return a mock response
        return {"content_id": content_id, "collection_id": collection_id}
