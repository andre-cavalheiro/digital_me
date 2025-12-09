import pytest
from fastapi.testclient import TestClient

from tests.helpers.dataset_basic import (
    create_test_dataset,
    # Dataset constants
    ALL_AUTHORS,
    ALL_COLLECTIONS,
    ALL_CONTENT,
    # Author constants
    AUTHOR_ALICE,
    AUTHOR_BOB,
    AUTHOR_ALICE_IDX,
    AUTHOR_BOB_IDX,
    # Collection constants
    COLLECTION_TECH,
    COLLECTION_SCIENCE,
    COLLECTION_ART,
    COLLECTION_TECH_IDX,
    COLLECTION_SCIENCE_IDX,
    COLLECTION_ART_IDX,
    # Content constants
    CONTENT_TECH_ALICE,
    CONTENT_ART_ANONYMOUS,
    CONTENT_TECH_ALICE_IDX,
)


@pytest.mark.asyncio
async def test_create_test_dataset(
    bootstrap_org,
    mocked_user_client: TestClient,
    authors_service,
):
    """Verify create_test_dataset creates normalized dataset using constants."""
    dataset = await create_test_dataset(
        mocked_user_client,
        authors_service,
    )

    # Validate counts match constants
    assert len(dataset["authors"]) == len(ALL_AUTHORS)
    assert len(dataset["collections"]) == len(ALL_COLLECTIONS)
    assert len(dataset["content"]) == len(ALL_CONTENT)

    # All data types are dicts - normalized interface
    assert all(isinstance(a, dict) for a in dataset["authors"])
    assert all(isinstance(c, dict) for c in dataset["collections"])
    assert all(isinstance(c, dict) for c in dataset["content"])

    # Verify authors match constants
    alice = dataset["authors"][AUTHOR_ALICE_IDX]
    bob = dataset["authors"][AUTHOR_BOB_IDX]
    assert alice["display_name"] == AUTHOR_ALICE["display_name"]
    assert alice["external_id"] == AUTHOR_ALICE["external_id"]
    assert bob["display_name"] == AUTHOR_BOB["display_name"]
    assert bob["external_id"] == AUTHOR_BOB["external_id"]

    # Verify collections match constants
    tech = dataset["collections"][COLLECTION_TECH_IDX]
    science = dataset["collections"][COLLECTION_SCIENCE_IDX]
    art = dataset["collections"][COLLECTION_ART_IDX]
    assert tech["name"] == COLLECTION_TECH["name"]
    assert science["name"] == COLLECTION_SCIENCE["name"]
    assert art["name"] == COLLECTION_ART["name"]

    # Verify content matches constants
    content_tech_alice = dataset["content"][CONTENT_TECH_ALICE_IDX]
    assert content_tech_alice["body"] == CONTENT_TECH_ALICE["body"]
    assert content_tech_alice["title"] == CONTENT_TECH_ALICE["title"]

    # Verify relationships using constant indices
    assert content_tech_alice["authorId"] == alice["id"]

    # Verify anonymous content has no author
    content_art_anon = dataset["content"][ALL_CONTENT.index(CONTENT_ART_ANONYMOUS)]
    assert content_art_anon["authorId"] is None
    assert content_art_anon["body"] == CONTENT_ART_ANONYMOUS["body"]
