"""
Integration client dependency functions for FastAPI.

This module provides dependency injection functions for external API clients.

## HTTP-based integrations (USGS, Prefect)
These use the async context manager pattern for proper lifecycle management:

1. Client creates an httpx.AsyncClient connection on __aenter__
2. Reuses the same connection for all requests (connection pooling)
3. Automatically closes the connection on __aexit__

By using async generators with `yield`, FastAPI automatically:
- Calls __aenter__ before the request handler
- Passes the ready-to-use client to the handler
- Calls __aexit__ after the request completes (even on errors)

Pattern:
    async def get_some_client() -> AsyncGenerator[SomeClient, None]:
        async with SomeClient(...) as client:
            yield client  # Client is ready, connection is open
        # FastAPI ensures cleanup happens here

## SDK-based integrations (Stripe)
These wrap third-party SDKs that manage their own connections.
No async context manager needed since the SDK handles lifecycle internally.

Pattern:
    def get_some_client() -> SomeClient:
        return IntegrationsFactory.get_some_client()

Usage in endpoints:
    @app.post("/example")
    async def handler(
        client: Annotated[SomeClient, Depends(get_some_client)]
    ):
        result = await client.some_method()
        return result
"""

from collections.abc import AsyncGenerator

from fury_api.lib.integrations import StripeClient, PrefectClient, XClient, CommunityArchiveClient

from fury_api.lib.factories import IntegrationsFactory


def get_stripe_client() -> StripeClient:
    """
    Get a Stripe API client.

    The Stripe SDK manages its own HTTP connections internally, so no
    async context manager is needed. The client is configured from settings.

    Returns:
        StripeClient: Ready-to-use Stripe client

    Example:
        @app.post("/organizations/{org_id}/stripe-customer")
        async def create_stripe_customer(
            org_id: int,
            stripe: Annotated[StripeClient, Depends(get_stripe_client)],
        ):
            customer = stripe.create_customer(
                email="admin@example.com",
                name="Organization Name",
                metadata={"org_id": org_id}
            )
            return customer
    """
    return IntegrationsFactory.get_stripe_client()


async def get_prefect_client() -> AsyncGenerator[PrefectClient, None]:
    """
    Get a Prefect API client with automatic lifecycle management.

    The client is configured from settings and manages a long-lived HTTP connection
    that's automatically cleaned up when the request completes.

    Yields:
        PrefectClient: Ready-to-use client with open connection

    Example:
        @app.post("/deployments")
        async def create_deployment(
            prefect: Annotated[PrefectClient, Depends(get_prefect_client)],
            payload: DeploymentPayload,
        ):
            deployment = await prefect.create_deployment(...)
            return deployment
    """
    async with IntegrationsFactory.get_prefect_client() as client:
        yield client


def get_x_client() -> XClient:
    """
    Get an X API client.

    The xdk SDK manages HTTP connections internally, so no async lifecycle
    management is needed. The client is configured from settings.

    Returns:
        XClient: Ready-to-use X client
    """
    return IntegrationsFactory.get_x_client()


def get_community_archive_client() -> CommunityArchiveClient:
    """
    Get a Community Archive client.

    Returns:
        CommunityArchiveClient: Ready-to-use client (currently stubbed).
    """
    return IntegrationsFactory.get_community_archive_client()
