from typing import Any

from fastapi.testclient import TestClient

from .crud import (
    create_author,
    create_collection,
    create_content,
    associate_content_with_collection,
)


# =============================================================================
# DATASET CONSTANTS - Test Data Definitions
# =============================================================================

# -----------------------------------------------------------------------------
# Authors
# -----------------------------------------------------------------------------
AUTHOR_ALICE = {
    "display_name": "Alice",
    "handle": "@alice",
    "external_id": "author-alice",
}

AUTHOR_BOB = {
    "display_name": "Bob",
    "handle": "@bob",
    "external_id": "author-bob",
}

ALL_AUTHORS = [AUTHOR_ALICE, AUTHOR_BOB]

# Index references for author lookups
AUTHOR_ALICE_IDX = 0
AUTHOR_BOB_IDX = 1

# -----------------------------------------------------------------------------
# Collections
# -----------------------------------------------------------------------------
COLLECTION_TECH = {
    "name": "Tech",
    "external_id": "collection-tech",
}

COLLECTION_SCIENCE = {
    "name": "Science",
    "external_id": "collection-science",
}

COLLECTION_ART = {
    "name": "Art",
    "external_id": "collection-art",
}

ALL_COLLECTIONS = [COLLECTION_TECH, COLLECTION_SCIENCE, COLLECTION_ART]

# Index references for collection lookups
COLLECTION_TECH_IDX = 0
COLLECTION_SCIENCE_IDX = 1
COLLECTION_ART_IDX = 2

# -----------------------------------------------------------------------------
# Content
# -----------------------------------------------------------------------------
# author_idx: index into ALL_AUTHORS (None for anonymous)
# collection_idxs: list of indices into ALL_COLLECTIONS

CONTENT_TECH_ALICE = {
    "body": "Tech article by Alice",
    "title": "Tech Article",
    "external_id": "content-1",
    "author_idx": AUTHOR_ALICE_IDX,
    "collection_idxs": [COLLECTION_TECH_IDX],
}

CONTENT_TECH_BOB = {
    "body": "Tech article by Bob",
    "title": "Tech Article 2",
    "external_id": "content-2",
    "author_idx": AUTHOR_BOB_IDX,
    "collection_idxs": [COLLECTION_TECH_IDX],
}

CONTENT_SCIENCE_ALICE = {
    "body": "Science article by Alice",
    "title": "Science Article",
    "external_id": "content-3",
    "author_idx": AUTHOR_ALICE_IDX,
    "collection_idxs": [COLLECTION_SCIENCE_IDX],
}

CONTENT_CROSS_CATEGORY_ALICE = {
    "body": "Cross-category by Alice",
    "title": "Cross-category",
    "external_id": "content-4",
    "author_idx": AUTHOR_ALICE_IDX,
    "collection_idxs": [COLLECTION_TECH_IDX, COLLECTION_SCIENCE_IDX],
}

CONTENT_ART_ANONYMOUS = {
    "body": "Anonymous art article",
    "title": "Art Article",
    "external_id": "content-5",
    "author_idx": None,  # Anonymous content
    "collection_idxs": [COLLECTION_ART_IDX],
}

CONTENT_UNCATEGORIZED_BOB = {
    "body": "Uncategorized by Bob",
    "title": "Uncategorized",
    "external_id": "content-6",
    "author_idx": AUTHOR_BOB_IDX,
    "collection_idxs": [],  # No collections
}

ALL_CONTENT = [
    CONTENT_TECH_ALICE,
    CONTENT_TECH_BOB,
    CONTENT_SCIENCE_ALICE,
    CONTENT_CROSS_CATEGORY_ALICE,
    CONTENT_ART_ANONYMOUS,
    CONTENT_UNCATEGORIZED_BOB,
]

# Index references for content lookups
CONTENT_TECH_ALICE_IDX = 0
CONTENT_TECH_BOB_IDX = 1
CONTENT_SCIENCE_ALICE_IDX = 2
CONTENT_CROSS_CATEGORY_ALICE_IDX = 3
CONTENT_ART_ANONYMOUS_IDX = 4
CONTENT_UNCATEGORIZED_BOB_IDX = 5


# =============================================================================
# Dataset Creation
# =============================================================================


async def create_test_dataset(
    client: TestClient,
    authors_service,
) -> dict[str, Any]:
    """
    Create complete test dataset with normalized return types.

    Uses module-level constants for all entity definitions.
    All entities returned as dicts for consistency.

    Args:
        client: TestClient for HTTP calls
        authors_service: AuthorsService for author creation

    Returns:
        {
            "authors": [dict, ...],      # TOTAL_AUTHORS authors
            "collections": [dict, ...],  # TOTAL_COLLECTIONS collections
            "content": [dict, ...],      # TOTAL_CONTENT content items
        }

        All items are dicts with consistent access patterns.

    Example:
        dataset = await create_test_dataset(
            mocked_user_client,
            authors_service
        )

        # Access using index constants
        alice = dataset["authors"][AUTHOR_ALICE_IDX]
        tech = dataset["collections"][COLLECTION_TECH_IDX]
        first_content = dataset["content"][CONTENT_TECH_ALICE_IDX]
    """
    # Create authors from constants
    authors = []
    for author_def in ALL_AUTHORS:
        author = await create_author(
            authors_service,
            display_name=author_def["display_name"],
            handle=author_def["handle"],
            external_id=author_def["external_id"],
        )
        authors.append(author)

    # Create collections from constants
    collections = []
    for collection_def in ALL_COLLECTIONS:
        collection = await create_collection(
            client,
            name=collection_def["name"],
            external_id=collection_def["external_id"],
        )
        collections.append(collection)

    # Create content from constants
    content_items = []
    for content_def in ALL_CONTENT:
        # Resolve author_id from index
        author_idx = content_def["author_idx"]
        author_id = authors[author_idx]["id"] if author_idx is not None else None

        content = await create_content(
            client,
            body=content_def["body"],
            title=content_def["title"],
            author_id=author_id,
            external_id=content_def["external_id"],
        )
        content_items.append(content)

        # Associate content with collections
        for collection_idx in content_def["collection_idxs"]:
            await associate_content_with_collection(
                client,
                content["id"],
                collections[collection_idx]["id"],
            )

    return {
        "authors": authors,
        "collections": collections,
        "content": content_items,
    }
