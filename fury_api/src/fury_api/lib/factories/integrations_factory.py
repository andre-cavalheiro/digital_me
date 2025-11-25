from fury_api.lib.settings import config

from fury_api.lib.integrations import (
    BaseAIClient,
    CommunityArchiveClient,
    OpenAIClient,
    PrefectClient,
    StripeClient,
    XAppClient,
    XUserClient,
)


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
    def get_x_app_client() -> XAppClient:
        """Get a new X API client."""
        token = config.x_app.BEARER_TOKEN.get_secret_value() if config.x_app.BEARER_TOKEN is not None else None
        return XAppClient(bearer_token=token)

    @staticmethod
    def get_x_user_client(
        *,
        access_token: str | None = None,
        refresh_token: str | None = None,
        token_type: str | None = None,
    ) -> XUserClient:
        """
        Get a new X User API client. Auth tokens must be provided per instance.

        If using refresh_token, client credentials will be loaded from config.
        """
        if not access_token and not refresh_token:
            raise ValueError("Provide access_token or refresh_token to create an X User client")

        client_id = config.x_user.OAUTH_CLIENT_ID
        client_secret = (
            config.x_user.OAUTH_CLIENT_SECRET.get_secret_value() if config.x_user.OAUTH_CLIENT_SECRET else None
        )

        return XUserClient(
            base_url=config.x_user.API_URL,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            token_url=config.x_user.OAUTH_TOKEN_URL,
            client_id=client_id,
            client_secret=client_secret,
        )

    @staticmethod
    def get_community_archive_client() -> CommunityArchiveClient:
        """Get a new Community Archive client."""
        token = (
            config.community_archive.BEARER_TOKEN.get_secret_value()
            if config.community_archive.BEARER_TOKEN is not None
            else None
        )
        return CommunityArchiveClient(bearer_token=token)

    @staticmethod
    def get_ai_client() -> BaseAIClient:
        """Get a chat-capable AI client based on configured provider."""
        if config.ai.PROVIDER == "openai":
            api_key = config.ai_openai.API_KEY.get_secret_value() if config.ai_openai.API_KEY else None
            if not api_key:
                raise ValueError("OpenAI API key is not configured")
            model = config.ai_openai.MODEL or config.ai.DEFAULT_MODEL
            return OpenAIClient(
                api_key=api_key,
                base_url=config.ai_openai.BASE_URL,
                default_model=model,
                organization=config.ai_openai.ORGANIZATION,
                timeout=config.ai.REQUEST_TIMEOUT,
            )

        raise ValueError(f"Unsupported AI provider: {config.ai.PROVIDER}")
