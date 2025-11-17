from typing import TYPE_CHECKING

from fury_api.lib.settings import config
from fury_api.lib.factories.service_factory import ServiceFactory, ServiceType
from fury_api.lib.unit_of_work import UnitOfWork

from fury_api.domain.organizations.models import Organization

if TYPE_CHECKING:
    from fury_api.lib.integrations import StripeClient, PrefectClient

# ####################
# Prefect
# ####################


async def create_prefect_support_user(uow: UnitOfWork, organization_id: int, prefect_client: "PrefectClient") -> None:
    """
    Create a system user for an organization and push credentials to Prefect.

    Args:
        uow: Unit of work for database operations
        organization_id: ID of the organization
        prefect_client: Configured Prefect API client
    """
    users_service = ServiceFactory.create_service(ServiceType.USERS, uow, has_system_access=True)
    system_user = await users_service.create_system_user(organization_id)
    system_token = await users_service.create_long_lived_token_for_user(system_user)
    await _push_prefect_secret(prefect_client, organization_id, system_token)


async def _push_prefect_secret(
    prefect_client: "PrefectClient",
    organization_id: int,
    system_token: str,
) -> None:
    """
    Push system user credentials to Prefect as a secret.

    Args:
        organization_id: ID of the organization
        system_token: Long-lived authentication token
        system_user: The system user
        prefect_client: Configured Prefect API client
    """
    await prefect_client.create_secret(
        secret_name=f"system-user-env-{config.app.ENVIRONMENT}-org-{organization_id}",
        secret_value={
            "value": system_token,
        },
    )


# ####################
# Stripe
# ####################


def create_stripe_customer(
    stripe_client: "StripeClient",
    organization: Organization,
    admin_email: str,
) -> Organization:
    """
    Create a Stripe customer for an organization.

    Args:
        stripe_client: Configured Stripe API client
        organization: The organization to create a customer for
        admin_email: Email address of the organization administrator

    Returns:
        The organization with updated stripe_customer_id

    Raises:
        stripe.error.StripeError: If the Stripe API request fails
    """
    customer = stripe_client.create_customer(
        email=admin_email,
        name=organization.name,
        metadata={"internal_id": str(organization.id)},
    )
    organization.stripe_customer_id = customer.id
    return organization


async def get_organization_by_stripe_customer_id(uow: UnitOfWork, stripe_customer_id: str) -> Organization | None:
    """
    Retrieve an organization by its Stripe customer ID.

    Args:
        uow: Unit of work for database operations
        stripe_customer_id: The Stripe customer ID

    Returns:
        The organization if found, None otherwise
    """
    return await uow.organizations.get_by_stripe_customer_id(uow.session, stripe_customer_id)
