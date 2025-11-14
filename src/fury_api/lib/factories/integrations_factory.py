from fury_api.lib.settings import config

from fury_api.lib.integrations import StripeClient, PrefectClient

class IntegrationsFactory:

    @staticmethod
    def get_stripe_client() -> StripeClient:
        """Get a new Stripe API client."""
        return StripeClient(
            api_key=config.stripe.API_KEY.get_secret_value()
        )

    @staticmethod
    def get_prefect_client() -> PrefectClient:
        """Get a new Prefect API client."""
        return PrefectClient(
            base_url=config.prefect.API_URL,
            headers=config.prefect.HEADERS
        )
