"""
Stripe API integration client.

This client wraps the Stripe Python SDK to provide a cleaner interface
and proper initialization. Unlike HTTP-based integrations, this doesn't
inherit from BaseHTTPClient since it uses the Stripe SDK directly.

Note: The Stripe SDK manages its own HTTP connections internally.
"""

from typing import Any

import stripe

from fury_api.lib.settings import config


class StripeClient:
    """
    Client for interacting with the Stripe API.

    This client configures and wraps the Stripe Python SDK, providing
    a cleaner interface for Stripe operations.

    Unlike HTTP integrations, this doesn't use async context managers
    because the Stripe SDK manages connections internally.

    Usage:
        client = StripeClient()
        customer = client.create_customer(
            email="user@example.com",
            name="Company Name",
            metadata={"internal_id": "123"}
        )
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Stripe client.

        Args:
            api_key: Stripe API key. If not provided, uses config.stripe.API_KEY.
                    Provided as parameter to support testing with different keys.
        """
        self.api_key = api_key or config.stripe.API_KEY.get_secret_value()
        # Configure the Stripe SDK
        stripe.api_key = self.api_key

    def create_customer(
        self,
        *,
        email: str,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> stripe.Customer:
        """
        Create a new Stripe customer.

        Args:
            email: Customer email address
            name: Customer name (typically organization name)
            metadata: Optional metadata to attach to the customer

        Returns:
            The created Stripe Customer object

        Raises:
            stripe.error.StripeError: If the Stripe API request fails
        """
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {},
        )

    def get_customer(self, customer_id: str) -> stripe.Customer:
        """
        Retrieve a Stripe customer by ID.

        Args:
            customer_id: The Stripe customer ID

        Returns:
            The Stripe Customer object

        Raises:
            stripe.error.StripeError: If the customer doesn't exist or API request fails
        """
        return stripe.Customer.retrieve(customer_id)

    def update_customer(
        self,
        customer_id: str,
        *,
        email: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> stripe.Customer:
        """
        Update a Stripe customer.

        Args:
            customer_id: The Stripe customer ID
            email: Optional new email address
            name: Optional new name
            metadata: Optional metadata to update

        Returns:
            The updated Stripe Customer object

        Raises:
            stripe.error.StripeError: If the customer doesn't exist or API request fails
        """
        update_data = {}
        if email is not None:
            update_data["email"] = email
        if name is not None:
            update_data["name"] = name
        if metadata is not None:
            update_data["metadata"] = metadata

        return stripe.Customer.modify(customer_id, **update_data)

    def delete_customer(self, customer_id: str) -> stripe.Customer:
        """
        Delete a Stripe customer.

        Args:
            customer_id: The Stripe customer ID

        Returns:
            The deleted Stripe Customer object

        Raises:
            stripe.error.StripeError: If the customer doesn't exist or API request fails
        """
        return stripe.Customer.delete(customer_id)


def get_stripe_client(api_key: str | None = None) -> StripeClient:
    """
    Create a Stripe client configured for the current environment.

    Args:
        api_key: Optional Stripe API key. If not provided, uses config.

    Returns:
        A configured StripeClient instance

    Example:
        # In a script or service
        stripe_client = get_stripe_client()
        customer = stripe_client.create_customer(
            email="admin@example.com",
            name="Acme Corp",
            metadata={"org_id": "123"}
        )
    """
    return StripeClient(api_key=api_key)
