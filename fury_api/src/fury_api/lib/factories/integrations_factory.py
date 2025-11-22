from fury_api.lib.settings import config

from fury_api.lib.integrations import StripeClient, PrefectClient, XClient, CommunityArchiveClient


class IntegrationsFactory:
    @staticmethod
    def get_stripe_client() -> StripeClient:
        """Get a new Stripe API client."""
        return StripeClient(api_key=config.stripe.API_KEY.get_secret_value())

    @staticmethod
    def get_prefect_client() -> PrefectClient:
        """Get a new Prefect API client."""
        return PrefectClient(base_url=config.prefect.API_URL, headers=config.prefect.HEADERS)

    @staticmethod
    def get_x_client() -> XClient:
        """Get a new X API client."""
        token = config.x.BEARER_TOKEN.get_secret_value() if config.x.BEARER_TOKEN is not None else None
        return XClient(bearer_token=token)

    @staticmethod
    def get_community_archive_client() -> CommunityArchiveClient:
        """Get a new Community Archive client."""
        token = (
            config.community_archive.BEARER_TOKEN.get_secret_value()
            if config.community_archive.BEARER_TOKEN is not None
            else None
        )
        return CommunityArchiveClient(bearer_token=token)
