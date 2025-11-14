from typing import Any, Optional

import httpx

from fury_api.lib.settings import config
from fury_api.lib.utils.datetime import utcnow
from fury_api.lib.integrations.base import BaseHTTPClient


class PrefectClient(BaseHTTPClient):
    """
    Client for interacting with the Prefect API.

    Inherits from BaseHTTPClient to get:
    - Long-lived HTTP connection management
    - Async context manager lifecycle
    - Automatic connection cleanup
    - Connection pooling for better performance

    Must be used with `async with` or via FastAPI Depends().
    """

    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize Prefect API client.

        Args:
            base_url: Prefect API endpoint URL
            headers: HTTP headers for requests (default: {"Content-Type": "application/json"})
            timeout: Request timeout in seconds
            http_client: Optional pre-configured httpx client
        """
        headers = headers or {"Content-Type": "application/json"}
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            http_client=http_client,
        )

    async def _make_request(
        self, method: str, endpoint: str, params: dict[str, Any] | None = None, json: Any = None
    ) -> dict[str, Any]:
        """
        Make an HTTP request to the Prefect API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path (relative to base_url)
            params: Query parameters
            json: JSON body for request

        Returns:
            Response JSON as dict

        Raises:
            httpx.HTTPStatusError: If request fails
        """
        url = f"{self._base_url}/{endpoint}"
        # Avoid redirects due to trailing slashes
        response = await self._http_client.request(method, url, params=params, json=json, follow_redirects=True)
        response.raise_for_status()
        try:
            return response.json()
        except Exception:
            if response.status_code == 204:
                return {}
            raise

    async def create_flow(self, name: str, tags: list[str]) -> dict[str, Any]:
        post_data = self._flow_post_data(name, tags)
        return await self._make_request("POST", "flows", json=post_data)

    async def get_flow_id_by_name(self, flow_name: str) -> str:
        response = await self._make_request("GET", f"flows/name/{flow_name}")
        return response["id"]

    async def get_deployment_id_by_name(self, deployment_name: str) -> str | None:
        response = await self._make_request(
            "POST", "deployments/filter", json={"deployments": {"name": {"any_": [deployment_name]}}}
        )
        if not response:
            return None
        return response[0]["id"]

    async def get_deployment_ids_by_name(self, deployment_name: str) -> list[str]:
        response = await self._make_request(
            "POST", "deployments/filter", json={"deployments": {"name": {"any_": [deployment_name]}}}
        )
        return [deployment["id"] for deployment in response]

    async def create_deployment(
        self,
        flow_id: str,
        flow_name: str,
        parameters: dict[str, Any],
        tags: list[str],
        entrypoint: str,
        integration_name: str,
        interval: int | None = None,
        schedule: dict | None = None,
        max_retries: int = 3,  # Number of retries
        retry_delay_seconds: int = 300,  # Delay between retries in seconds
        galaxy: bool = False,
    ) -> dict[str, Any]:
        post_data = self._deployment_post_data(
            flow_id,
            flow_name=flow_name,
            parameters=parameters,
            tags=tags,
            entrypoint=entrypoint,
            schedule=schedule,
            max_retries=max_retries,
            retry_delay_seconds=retry_delay_seconds,
            interval=interval,
            galaxy=galaxy,
            integration_name=integration_name,
        )
        return await self._make_request("POST", "deployments/", json=post_data)

    async def delete_deployment(self, deployment_id: str) -> None:
        await self._make_request("DELETE", f"deployments/{deployment_id}")

    async def delete_deployments_by_name(self, deployment_name: str) -> None:
        deployment_ids = await self.get_deployment_ids_by_name(deployment_name)
        for deployment_id in deployment_ids:
            await self.delete_deployment(deployment_id)

    async def pause_deployment(self, deployment_id: str) -> None:
        await self._make_request("POST", f"deployments/{deployment_id}/pause_deployment")

    async def resume_deployment(self, deployment_id: str) -> None:
        await self._make_request("POST", f"deployments/{deployment_id}/resume_deployment")

    async def create_flow_run(
        self,
        deployment_id: str,
        organization_id: int,
        parameters: dict[str, Any],
        *,
        run_name: str | None = None,
        message: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        post_data = self._flow_run_post_data(organization_id, parameters, run_name=run_name, message=message, tags=tags)
        return await self._make_request("POST", f"deployments/{deployment_id}/create_flow_run/", json=post_data)

    async def get_block(self, block_type: str, block_name: str) -> dict[str, Any]:
        return await self._make_request("GET", f"block_types/slug/{block_type}/block_documents/name/{block_name}")

    async def create_block(
        self,
        block_name: str,
        block_data: dict[str, Any],
        block_schema_id: str,
        block_type_id: str,
        is_anonymous: bool = False,
    ) -> dict[str, Any]:
        post_data = {
            "name": block_name,
            "data": block_data,
            "block_schema_id": block_schema_id,
            "block_type_id": block_type_id,
            "is_anonymous": is_anonymous,
        }
        return await self._make_request("POST", "block_documents/", json=post_data)

    async def read_block_type_by_slug(self, slug: str) -> dict[str, Any]:
        return await self._make_request("GET", f"block_types/slug/{slug}")

    async def read_block_schemas(self, block_type_id: str) -> dict[str, Any]:
        return await self._make_request(
            "POST", "block_schemas/filter", json={"block_schemas": {"block_type_id": {"any_": [block_type_id]}}}
        )

    async def create_block_schema(self, block_type_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        post_data = {"block_type_id": block_type_id, "fields": fields}
        return await self._make_request("POST", "block_schemas/", json=post_data)

    async def secret_exists(self, secret_name: str) -> bool:
        try:
            block = await self.get_block("secret", secret_name)
        except httpx.HTTPError as e:
            if e.response.status_code == 404:
                return False
            raise
        else:
            return block is not None

    async def create_secret(self, secret_name: str, secret_value: dict[str, Any]) -> dict[str, Any]:
        type_id = (await self.read_block_type_by_slug("secret"))["id"]
        schemas = await self.read_block_schemas(type_id)
        if not schemas:
            schema = await self.create_block_schema(
                block_type_id=type_id,
                fields={
                    "type": "object",
                    "title": "Secret",
                    "properties": {
                        "value": {
                            "type": "string",
                            "format": "password",
                            "title": "Value",
                            "writeOnly": True,
                            "description": "A string value that should be kept secret.",
                        }
                    },
                },
            )
        else:
            schema = schemas[-1]
        return await self.create_block(
            block_name=secret_name, block_data=secret_value, block_schema_id=schema["id"], block_type_id=type_id
        )

    async def delete_secret(self, secret_name: str) -> None:
        block = await self.get_block("secret", secret_name)
        await self._make_request("DELETE", f"block_documents/{block['id']}")

    @staticmethod
    def _flow_post_data(name: str, tags: list[str]) -> dict[str, Any]:
        return {"name": name, "tags": tags}

    @staticmethod
    def _deployment_post_data(
        flow_id: str,
        flow_name: str,
        parameters: dict[str, Any],
        tags: list[str],
        entrypoint: str,
        integration_name: str,
        schedule: dict | None,
        interval: int | None,
        max_retries: int = 3,  # Number of retries
        retry_delay_seconds: int = 300,  # Delay between retries in seconds
        galaxy: bool = False,
    ) -> dict[str, Any]:
        tags = list(set((tags or []) + [f"environment:{config.app.ENVIRONMENT}"]))

        if not interval:
            interval = config.plugins.DEFAULT_SCHEDULE_INTERVAL_SECONDS

        if not schedule:
            schedule = {"interval": interval, "anchor_date": str(utcnow()), "timezone": "UTC"}

        if galaxy:
            environment = {
                "ENVIRONMENT": config.app.ENVIRONMENT,
                "RELY_API_URL": config.api.API_URL_INTERNAL,
                "RELY_INTEGRATION_TYPE": integration_name,
                "PREFECT_LOGGING_EXTRA_LOGGERS": "galaxy",
            }
            if integration_name == "github":
                github_config = {
                    "RELY_INTEGRATION_GITHUB_APP_ID": (
                        f"{{{{ prefect.blocks.secret.github-app-id-{config.app.ENVIRONMENT} }}}}"
                    ),
                    "RELY_INTEGRATION_GITHUB_APP_PRIVATE_KEY": (
                        f"{{{{ prefect.blocks.secret.github-app-private-key-{config.app.ENVIRONMENT} }}}}"
                    ),
                }
                environment.update(github_config)
            elif integration_name == "bitbucket":
                github_config = {
                    "RELY_BITBUCKET_APP_CLIENT_ID": (
                        f"{{{{ prefect.blocks.secret.bitbucket-app-client-id-{config.app.ENVIRONMENT} }}}}"
                    ),
                    "RELY_BITBUCKET_APP_CLIENT_SECRET": (
                        f"{{{{ prefect.blocks.secret.bitbucket-app-client-secret-{config.app.ENVIRONMENT} }}}}"
                    ),
                }
                environment.update(github_config)

            return {
                "name": flow_name,
                "flow_id": flow_id,
                "is_schedule_active": True,
                "enforce_parameter_schema": False,
                "parameter_openapi_schema": {},
                "parameters": parameters,
                "tags": tags,
                "pull_steps": [
                    {
                        "prefect_aws.deployments.steps.pull_from_s3": {
                            "bucket": "prefect-flows-rely-dev",
                            "folder": f"{config.app.ENVIRONMENT}/galaxy",
                            "requires": "prefect-aws>=0.3.0",
                            "credentials": "{{ prefect.blocks.aws-credentials.aws-credentials }}",
                        }
                    }
                ],
                "work_queue_name": "default",
                "work_pool_name": "kubernetes-pool",
                "schedule": schedule,
                "entrypoint": entrypoint,
                "infra_overrides": {
                    "image": "{{ prefect.variables.galaxy_image }}",
                    "env": environment,
                    "retry_policy": {"max_retries": max_retries, "retry_delay_seconds": retry_delay_seconds},
                },
            }

        return {
            "name": flow_name,
            "flow_id": flow_id,
            "is_schedule_active": True,
            "enforce_parameter_schema": False,
            "parameter_openapi_schema": {},
            "parameters": parameters,
            "tags": tags,
            "pull_steps": [
                {
                    "prefect_aws.deployments.steps.pull_from_s3": {
                        "bucket": "prefect-flows-rely-dev",
                        "folder": f"{config.app.ENVIRONMENT}/integrations",
                        "requires": "prefect-aws>=0.3.0",
                        "credentials": "{{ prefect.blocks.aws-credentials.aws-credentials }}",
                    }
                }
            ],
            "work_queue_name": "default",
            "work_pool_name": "kubernetes-pool",
            "schedule": schedule,
            "entrypoint": entrypoint,
            "infra_overrides": {
                "image": "{{ prefect.variables.deployment_image }}",
                "env": {
                    "ENVIRONMENT": config.app.ENVIRONMENT,
                    "MAGNETO_API_URL": config.api.API_URL_INTERNAL,
                    "AUTH_TOKEN_URL": config.auth0.USER_MANAGEMENT_API_URL,
                    "INFLUXDB_URL": config.influxdb.URL,
                },
                "retry_policy": {"max_retries": max_retries, "retry_delay_seconds": retry_delay_seconds},
            },
        }

    @staticmethod
    def _flow_run_post_data(
        organization_id: int,
        parameters: dict[str, Any],
        *,
        run_name: str | None = None,
        message: str | None = None,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        tags = list(set((tags or []) + [f"organization:{organization_id}", f"environment:{config.app.ENVIRONMENT}"]))
        return {
            "state": {
                "type": "SCHEDULED",
                "name": "Scheduled",
                "message": message,
                "data": None,
                "state_details": {},
                "timestamp": None,
                "id": None,
            },
            "name": run_name or f"run-org-{organization_id}-{utcnow().isoformat()}",
            "parameters": parameters,
            "context": {},
            "empirical_policy": {
                "max_retries": 0,
                "retry_delay_seconds": 0,
                "retries": 0,
                "retry_delay": 0,
                "pause_keys": [None],
                "resuming": False,
            },
            "tags": tags,
            "idempotency_key": None,
        }


def get_prefect_client() -> PrefectClient:
    return PrefectClient(base_url=config.prefect.API_URL, headers=config.prefect.HEADERS)
