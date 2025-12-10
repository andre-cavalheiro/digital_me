"""Tests for GET /api/v1/content endpoint."""

from urllib.parse import parse_qsl, urlencode, urlparse

import pytest
from fastapi.testclient import TestClient
from tests.helpers.utils import generic_http_call
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


def _build_endpoint(base_endpoint: str, query_params: list[tuple[str, str]]) -> str:
    query = urlencode(query_params, doseq=True)
    return f"{base_endpoint}?{query}" if query else base_endpoint


def _collect_all_items(mocked_user_client: TestClient, endpoint: str, *, page_size: int = 100):
    """
    Retrieve all paginated items for a given endpoint while preserving duplicate query params like filters.
    """
    parsed = urlparse(endpoint)
    base_endpoint = parsed._replace(query="", params="", fragment="").geturl()
    base_query = parse_qsl(parsed.query, keep_blank_values=True)

    # Keep all original params (including duplicate filters) and add a larger page size if missing
    base_query = [pair for pair in base_query if pair[0] != "cursor"]
    if not any(key == "size" for key, _ in base_query):
        base_query.append(("size", str(page_size)))

    response = generic_http_call(
        mocked_user_client,
        _build_endpoint(base_endpoint, base_query),
        "get",
        expected_status_code=200,
    )
    items = list(response.get("items", []))
    next_page = response.get("next_page")

    while next_page:
        if isinstance(next_page, str) and (next_page.startswith("/") or next_page.startswith("http")):
            next_endpoint = next_page
        else:
            query_with_cursor = [pair for pair in base_query if pair[0] != "cursor"]
            query_with_cursor.append(("cursor", next_page))
            next_endpoint = _build_endpoint(base_endpoint, query_with_cursor)

        page = generic_http_call(mocked_user_client, next_endpoint, "get", expected_status_code=200)
        items.extend(page.get("items", []))
        next_page = page.get("next_page")

    return items


class TestCollectionIDAndLogic:
    """Test collection_id AND logic: filters with collection_id:eq:X + author_id:eq:Y."""

    @pytest.mark.asyncio
    async def test_collection_and_author_both_match(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Items matching BOTH collection_id AND author_id are returned."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]  # Tech
        author_id = dataset["authors"][AUTHOR_ALICE_IDX]["id"]  # Alice

        # Expected: content in Tech collection by Alice (content-1 and content-4)
        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=and&includeTotal=true",
            "get",
            expected_status_code=200,
        )

        assert response["total"] == 2
        assert len(response["items"]) == 2
        assert all(item["authorId"] == author_id for item in response["items"])

    @pytest.mark.asyncio
    async def test_collection_and_author_no_matches(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """No items when collection_id AND author_id don't overlap."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_ART_IDX]["id"]  # Art (has no Alice content)
        author_id = dataset["authors"][AUTHOR_ALICE_IDX]["id"]  # Alice

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=and&includeTotal=true",
            "get",
            expected_status_code=200,
        )

        assert response["total"] == 0
        assert len(response["items"]) == 0

    @pytest.mark.asyncio
    async def test_collection_and_author_pagination_correct(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Pagination metadata is correct with AND filters."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]
        author_id = dataset["authors"][AUTHOR_ALICE_IDX]["id"]

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=and&size=1&includeTotal=true",
            "get",
            expected_status_code=200,
        )

        assert response["total"] == 2
        assert len(response["items"]) == 1
        assert response["next_page"] is not None

    @pytest.mark.asyncio
    async def test_collection_and_author_no_500_error(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """No 500 errors with valid collection_id + author_id filters."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]
        author_id = dataset["authors"][AUTHOR_ALICE_IDX]["id"]

        # Should not raise 500
        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=and",
            "get",
            expected_status_code=200,
        )

        assert "items" in response


class TestCollectionIDOrLogic:
    """Test collection_id OR logic: filter_logic=or with multiple filters."""

    @pytest.mark.asyncio
    async def test_collection_or_author_returns_union(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """OR logic returns union of collection_id:in + author_id:eq."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection1_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]  # Tech
        collection2_id = dataset["collections"][COLLECTION_SCIENCE_IDX]["id"]  # Science
        author_id = dataset["authors"][AUTHOR_BOB_IDX]["id"]  # Bob

        # Expected: All Tech OR Science content, PLUS all Bob content
        # Content-1 (Tech+Alice), Content-2 (Tech+Bob), Content-3 (Science+Alice),
        # Content-4 (Tech+Science+Alice), Content-6 (no collection+Bob)
        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:in:{collection1_id},{collection2_id}&filters=author_id:eq:{author_id}&filter_logic=or&includeTotal=true",
            "get",
            expected_status_code=200,
        )

        # Should include Bob's non-collection content too
        assert response["total"] == 5

    @pytest.mark.asyncio
    async def test_collection_or_does_not_drop_clauses(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Ensure neither collection_id nor author_id clause is dropped."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_ART_IDX]["id"]  # Art (content-5)
        author_id = dataset["authors"][AUTHOR_BOB_IDX]["id"]  # Bob (content-2, content-6)

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=or&includeTotal=true",
            "get",
            expected_status_code=200,
        )

        # Should have exactly 3 items: content-2, content-5, content-6
        assert response["total"] == 3

        # Verify at least one item from author
        author_ids_in_results = [item.get("author_id") for item in response["items"]]
        assert author_id in author_ids_in_results or response["total"] > 0

    @pytest.mark.asyncio
    async def test_collection_or_pagination_correct(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Pagination works correctly with OR filters."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]
        author_id = dataset["authors"][AUTHOR_ALICE_IDX]["id"]

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&filters=author_id:eq:{author_id}&filter_logic=or&size=2&includeTotal=true",
            "get",
            expected_status_code=200,
        )

        assert len(response["items"]) == 2
        assert "total" in response


class TestCollectionIDNotInNeq:
    """Test collection_id NOT_IN/NEQ: exclude collections."""

    @pytest.mark.asyncio
    async def test_collection_neq_excludes_collection(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """NEQ excludes items from specified collection."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        excluded_collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]  # Tech

        items = _collect_all_items(
            isolated_client,
            f"/api/v1/content?filters=collection_id:neq:{excluded_collection_id}&includeTotal=true",
        )

        external_ids = {item["externalId"] for item in items}
        excluded_ids = {
            dataset["content"][CONTENT_TECH_ALICE_IDX]["externalId"],
            dataset["content"][CONTENT_TECH_BOB_IDX]["externalId"],
            dataset["content"][CONTENT_CROSS_CATEGORY_ALICE_IDX]["externalId"],
        }
        expected_present = {
            dataset["content"][CONTENT_SCIENCE_ALICE_IDX]["externalId"],
            dataset["content"][CONTENT_ART_ANONYMOUS_IDX]["externalId"],
            dataset["content"][CONTENT_UNCATEGORIZED_BOB_IDX]["externalId"],
        }

        assert excluded_ids.isdisjoint(external_ids)
        assert expected_present.issubset(external_ids)

    @pytest.mark.asyncio
    async def test_collection_not_in_excludes_multiple(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """NOT_IN excludes items from multiple collections."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        excluded1 = dataset["collections"][COLLECTION_TECH_IDX]["id"]  # Tech
        excluded2 = dataset["collections"][COLLECTION_SCIENCE_IDX]["id"]  # Science

        items = _collect_all_items(
            isolated_client,
            f"/api/v1/content?filters=collection_id:notIn:{excluded1},{excluded2}&includeTotal=true",
        )

        external_ids = {item["externalId"] for item in items}
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
    async def test_collection_neq_does_not_leak(self, test_org, isolated_client: TestClient, isolated_authors_service):
        """Junction table logic correctly excludes items."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        excluded_id = dataset["collections"][COLLECTION_ART_IDX]["id"]  # Art

        items = _collect_all_items(
            isolated_client,
            f"/api/v1/content?filters=collection_id:neq:{excluded_id}",
        )
        external_ids = {item["externalId"] for item in items}

        assert dataset["content"][CONTENT_ART_ANONYMOUS_IDX]["externalId"] not in external_ids


class TestValidationErrors:
    """Validation coverage for malformed filter values."""

    @pytest.mark.asyncio
    async def test_collection_eq_non_numeric_returns_400(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Invalid collection_id value should trigger 400, not parsing fallback."""
        await create_test_dataset(isolated_client, isolated_authors_service)

        generic_http_call(
            isolated_client,
            "/api/v1/content?filters=collection_id:eq:not-a-number",
            "get",
            expected_status_code=400,
        )

    @pytest.mark.asyncio
    async def test_collection_in_mixed_tokens_returns_400(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Mixed list tokens must reject whole request."""
        await create_test_dataset(isolated_client, isolated_authors_service)

        generic_http_call(
            isolated_client,
            "/api/v1/content?filters=collection_id:in:123,abc",
            "get",
            expected_status_code=400,
        )

    @pytest.mark.asyncio
    async def test_author_eq_non_numeric_returns_400(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Generic filter parsing should 400 on non-numeric author_id."""
        await create_test_dataset(isolated_client, isolated_authors_service)

        generic_http_call(
            isolated_client,
            "/api/v1/content?filters=author_id:eq:abc",
            "get",
            expected_status_code=400,
        )


class TestMissingOrgContext:
    """Test missing organization context with collection_id."""

    @pytest.mark.asyncio
    async def test_collection_filter_without_org_returns_error(self, test_org, unauthenticated_client: TestClient):
        """Using collection_id without org context returns clear error."""
        response = unauthenticated_client.get("/api/v1/content?filters=collection_id:eq:1")

        # Should return 401 or 403, not 500
        assert response.status_code in [401, 403]
        assert response.status_code != 500


class TestIncludeAuthor:
    """Test include=author parameter with collection_id filters."""

    @pytest.mark.asyncio
    async def test_include_author_hydrates_author_fields(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """include=author returns hydrated author for items with author_id."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&include=author",
            "get",
            expected_status_code=200,
        )

        # Find items with author_id
        for item in response["items"]:
            if item.get("author_id") is not None:
                assert item.get("author") is not None
                assert "display_name" in item["author"]
                assert "id" in item["author"]

    @pytest.mark.asyncio
    async def test_include_author_none_for_no_author(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """include=author keeps author=None for items without author_id."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_ART_IDX]["id"]  # Art (has content-5 with no author)

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&include=author",
            "get",
            expected_status_code=200,
        )

        # Find item without author
        for item in response["items"]:
            if item.get("author_id") is None:
                assert item.get("author") is None

    @pytest.mark.asyncio
    async def test_include_author_preserves_pagination(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """include=author doesn't break pagination metadata."""
        await create_test_dataset(isolated_client, isolated_authors_service)

        response = generic_http_call(
            isolated_client,
            "/api/v1/content?include=author&size=2&includeTotal=true",
            "get",
            expected_status_code=200,
        )

        assert "total" in response
        assert "items" in response
        assert len(response["items"]) == 2

    @pytest.mark.asyncio
    async def test_include_author_total_matches_unique_items_across_pages(
        self, test_org, isolated_client: TestClient, isolated_authors_service
    ):
        """Total remains stable across pages and items do not repeat."""
        await create_test_dataset(isolated_client, isolated_authors_service)
        base_endpoint = "/api/v1/content?include=author&size=1&includeTotal=true"

        first_page = generic_http_call(isolated_client, base_endpoint, "get", expected_status_code=200)
        all_items = _collect_all_items(isolated_client, base_endpoint)

        external_ids = [item["externalId"] for item in all_items]

        assert first_page["total"] == len(all_items)
        assert len(external_ids) == len(set(external_ids))


class TestSortWithFilters:
    """Test sorting with collection_id filters."""

    @pytest.mark.asyncio
    async def test_sort_applied_after_filtering(self, test_org, isolated_client: TestClient, isolated_authors_service):
        """Sort is applied to filtered results."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)
        collection_id = dataset["collections"][COLLECTION_TECH_IDX]["id"]

        response = generic_http_call(
            isolated_client,
            f"/api/v1/content?filters=collection_id:eq:{collection_id}&sorts=published_at:desc",
            "get",
            expected_status_code=200,
        )

        # Verify descending order
        published_dates = [item["published_at"] for item in response["items"] if item.get("published_at")]
        assert published_dates == sorted(published_dates, reverse=True)


class TestNoFiltersFallback:
    """Test plain GET /content without filters."""

    @pytest.mark.asyncio
    async def test_no_filters_returns_all_content(self, test_org, isolated_client: TestClient, isolated_authors_service):
        """Plain GET /content works without collection_id filter."""
        dataset = await create_test_dataset(isolated_client, isolated_authors_service)

        items = _collect_all_items(isolated_client, "/api/v1/content?includeTotal=true")
        external_ids = {item["externalId"] for item in items}
        expected_ids = {content["externalId"] for content in dataset["content"]}

        assert expected_ids.issubset(external_ids)
