import json
from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient
from httpx import Response


def generic_http_call(
    mocked_user_client: TestClient,
    endpoint: str,
    method: str,
    data: dict[str, Any] | None = None,
    expected_status_code: int = 201,
) -> Any | None:
    fn: Callable[..., Response] = getattr(mocked_user_client, method)

    if method in ("get", "delete"):
        response = fn(endpoint)
    else:
        response = fn(endpoint, json=data)

    response_data: Any | None = None
    if response.status_code == 204:
        response_data = None
    else:
        try:
            response_data = response.json()
        except json.decoder.JSONDecodeError:
            response_data = None

    assert (
        response.status_code == expected_status_code
    ), f"({method}, {endpoint}) Expected status code {expected_status_code}, got {response.status_code} with response: {response_data}"

    return response_data
