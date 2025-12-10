"""Tests for POST /api/v1/content/search endpoint."""

import pytest
from fastapi.testclient import TestClient

from fury_api.lib.dependencies.integrations import get_ai_client
from fury_api.domain.content.models import Content
from tests.helpers.dataset_basic import (
    AUTHOR_ALICE_IDX,
    AUTHOR_BOB_IDX,
    COLLECTION_ART_IDX,
    COLLECTION_SCIENCE_IDX,
    COLLECTION_TECH_IDX,
    CONTENT_ART_ANONYMOUS_IDX,
    CONTENT_CROSS_CATEGORY_ALICE_IDX,
    CONTENT_SCIENCE_ALICE_IDX,
    CONTENT_TECH_ALICE_IDX,
    CONTENT_TECH_BOB_IDX,
    CONTENT_UNCATEGORIZED_BOB_IDX,
    create_test_dataset,
)
from tests.helpers.utils import generic_http_call

EMBEDDING_DIM = 1536


def _make_embedding(value: float = 0.01, dim: int = EMBEDDING_DIM) -> list[float]:
    return [value] * dim


async def _seed_embeddings(contents_service, content_ids: list[int], vector: list[float]) -> None:
    """Populate embeddings so semantic search returns the inserted content."""
    import sqlalchemy as sa

    # Clear embeddings to avoid cross-test contamination
    await contents_service.session.exec(sa.update(Content).values(embedding=None))

    if content_ids:
        await contents_service.session.exec(
            sa.update(Content).where(Content.id.in_(content_ids)).values(embedding=vector)
        )

    await contents_service.session.commit()


@pytest.fixture()
def fake_ai_client(isolated_client: TestClient):
    """Override AI client dependency to avoid real vector calls."""

    class FakeAIClient:
        def __init__(self, vector: list[float]):
            self._vector = vector

        async def embed(self, _: str) -> list[float]:
            return self._vector

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    vector = _make_embedding()
    app = isolated_client.app
    original_override = app.dependency_overrides.get(get_ai_client)

    async def _override():
        yield FakeAIClient(vector)

    app.dependency_overrides[get_ai_client] = _override
    try:
        yield vector
    finally:
        if original_override is not None:
            app.dependency_overrides[get_ai_client] = original_override
        else:
            app.dependency_overrides.pop(get_ai_client, None)


class TestSearchFilters:
    """Filters behavior mirrors GET /content."""

    @pytest.mark.asyncio
    async def test_collection_eq_limits_results(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]
        response = generic_http_call(
            isolated_client,
            f"/api/v1/content/search?filters=collection_id:eq:{collection_id}",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        external_ids = {item["externalId"] for item in response}
        expected_ids = {
            dataset["content"][CONTENT_TECH_ALICE_IDX]["externalId"],
            dataset["content"][CONTENT_TECH_BOB_IDX]["externalId"],
            dataset["content"][CONTENT_CROSS_CATEGORY_ALICE_IDX]["externalId"],
        }
        assert expected_ids.issubset(external_ids)

    @pytest.mark.asyncio
    async def test_collection_not_in_excludes_multiple(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        excluded1 = dataset["collections"][COLLECTION_TECH_IDX]["id"]
        excluded2 = dataset["collections"][COLLECTION_SCIENCE_IDX]["id"]

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content/search?filters=collection_id:notIn:{excluded1},{excluded2}",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        external_ids = {item["externalId"] for item in response}
        excluded_ids = {
            dataset["content"][CONTENT_TECH_ALICE_IDX]["externalId"],
            dataset["content"][CONTENT_TECH_BOB_IDX]["externalId"],
            dataset["content"][CONTENT_SCIENCE_ALICE_IDX]["externalId"],
            dataset["content"][CONTENT_CROSS_CATEGORY_ALICE_IDX]["externalId"],
        }
        expected_present = {
            dataset["content"][CONTENT_ART_ANONYMOUS_IDX]["externalId"],
            dataset["content"][CONTENT_UNCATEGORIZED_BOB_IDX]["externalId"],
        }

        assert excluded_ids.isdisjoint(external_ids)
        assert expected_present.issubset(external_ids)

    @pytest.mark.asyncio
    async def test_author_eq_limits_results(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        author_id = dataset["authors"][AUTHOR_BOB_IDX]["id"]
        response = generic_http_call(
            isolated_client,
            f"/api/v1/content/search?filters=author_id:eq:{author_id}",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        assert all(item["authorId"] == author_id for item in response)

    @pytest.mark.asyncio
    async def test_collection_and_author_and_logic(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]
        author_id = dataset["authors"][AUTHOR_ALICE_IDX]["id"]
        response = generic_http_call(
            isolated_client,
            f"/api/v1/content/search?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=and",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        external_ids = {item["externalId"] for item in response}
        expected_ids = {
            dataset["content"][CONTENT_TECH_ALICE_IDX]["externalId"],
            dataset["content"][CONTENT_CROSS_CATEGORY_ALICE_IDX]["externalId"],
        }
        assert external_ids == expected_ids

    @pytest.mark.asyncio
    async def test_collection_or_author_union(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        collection_id = dataset["collections"][COLLECTION_ART_IDX]["id"]
        author_id = dataset["authors"][AUTHOR_BOB_IDX]["id"]
        response = generic_http_call(
            isolated_client,
            f"/api/v1/content/search?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=or",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        external_ids = {item["externalId"] for item in response}
        expected_ids = {
            dataset["content"][CONTENT_TECH_BOB_IDX]["externalId"],
            dataset["content"][CONTENT_UNCATEGORIZED_BOB_IDX]["externalId"],
            dataset["content"][CONTENT_ART_ANONYMOUS_IDX]["externalId"],
        }
        assert expected_ids == external_ids


class TestSearchIncludeAuthor:
    """Hydration behavior mirrors GET /content."""

    @pytest.mark.asyncio
    async def test_include_author_hydrates_when_present(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        response = generic_http_call(
            isolated_client,
            "/api/v1/content/search?include=author",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        for item in response:
            if item.get("authorId") is not None:
                assert item.get("author") is not None
                assert "id" in item["author"]
                assert "displayName" in item["author"]

    @pytest.mark.asyncio
    async def test_include_author_none_when_missing(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        response = generic_http_call(
            isolated_client,
            "/api/v1/content/search?include=author",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        anon_external_id = dataset["content"][CONTENT_ART_ANONYMOUS_IDX]["externalId"]
        anon_item = next(item for item in response if item["externalId"] == anon_external_id)
        assert anon_item["authorId"] is None
        assert anon_item["author"] is None


class TestSearchValidation:
    """Validation should match GET behavior."""

    @pytest.mark.asyncio
    async def test_collection_eq_non_numeric_returns_400(
        self, test_org, isolated_client: TestClient, isolated_authors_service, isolated_contents_service, fake_ai_client
    ):
        await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [], fake_ai_client)

        generic_http_call(
            isolated_client,
            "/api/v1/content/search?filters=collection_id:eq:not-a-number",
            "post",
            data={"query": "anything"},
            expected_status_code=400,
        )

    @pytest.mark.asyncio
    async def test_collection_in_mixed_tokens_returns_400(
        self, test_org, isolated_client: TestClient, isolated_authors_service, isolated_contents_service, fake_ai_client
    ):
        await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [], fake_ai_client)

        generic_http_call(
            isolated_client,
            "/api/v1/content/search?filters=collection_id:in:123,abc",
            "post",
            data={"query": "anything"},
            expected_status_code=400,
        )

    @pytest.mark.asyncio
    async def test_author_eq_non_numeric_returns_400(
        self, test_org, isolated_client: TestClient, isolated_authors_service, isolated_contents_service, fake_ai_client
    ):
        await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [], fake_ai_client)

        generic_http_call(
            isolated_client,
            "/api/v1/content/search?filters=author_id:eq:abc",
            "post",
            data={"query": "anything"},
            expected_status_code=400,
        )


class TestSearchBaseline:
    """Baseline search without filters."""

    @pytest.mark.asyncio
    async def test_search_without_filters_returns_items(
        self,
        test_org,
        isolated_client: TestClient,
        isolated_authors_service,
        isolated_contents_service,
        fake_ai_client,
    ):
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        await _seed_embeddings(isolated_contents_service, [c["id"] for c in dataset["content"]], fake_ai_client)

        response = generic_http_call(
            isolated_client,
            "/api/v1/content/search",
            "post",
            data={"query": "anything", "limit": 10},
            expected_status_code=200,
        )

        external_ids = {item["externalId"] for item in response}
        expected_ids = {content["externalId"] for content in dataset["content"]}
        assert expected_ids.issubset(external_ids)
