import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Literal, Self

from dotenv import load_dotenv
from pydantic import SecretStr, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = [
    "ServerSettings",
    "AppSettings",
    "APISettings",
    "DevExSettings",
    "LoggingSettings",
    "DatabaseSettings",
    "OpenAPISettings",
    "XAppSettings",
    "XUserSettings",
    "SettingsConfig",
    "ExperimentalSettings",
    "CommunityArchiveSettings",
    "AISettings",
    "OpenAISettings",
    "load_settings",
    "config",
    "version",
    "BASE_DIR",
]

module_name, *_ = __package__.split(".", maxsplit=1)
version = importlib.import_module(module_name).__version__
BASE_DIR: Path = Path(importlib.import_module(module_name).__file__).parent


COMMON_SETTINGS_CONFIG: dict[str, Any] = {
    "env_file": ".env",
    "env_file_encoding": "utf-8",
    "validate_default": True,
    "case_sensitive": False,
    "extra": "ignore",
}


def build_settings_config(env_prefix: str) -> SettingsConfigDict:
    return SettingsConfigDict(env_prefix=env_prefix, **COMMON_SETTINGS_CONFIG)


class FuryBaseSettings(BaseSettings):
    """Base settings with shared configuration."""

    model_config = build_settings_config("FURY_API_")


class ServerSettings(FuryBaseSettings):
    """Server configuration."""

    model_config = build_settings_config("FURY_API_SERVER_")

    APP_PATH: str = "fury_api.main:app"
    HOST: str = "localhost"
    PORT: int = 3000
    KEEPALIVE: int = 65
    RELOAD: bool = False
    RELOAD_DIRS: ClassVar[list[str]] = [f"{BASE_DIR}"]
    WORKERS: int = 1
    PROFILING_ENABLED: bool = False


class AppSettings(FuryBaseSettings):
    """Application settings."""

    model_config = build_settings_config("FURY_API_APP_")

    DEBUG: bool = True
    ENVIRONMENT: str = "dev"
    NAME: str = "Digital Me API"
    # Keep this aligned with the actual package name so dynamic imports (e.g. services) work.
    SLUG: str = module_name
    VERSION: str = version

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "prod"

    @property
    def is_testing(self) -> bool:
        return self.ENVIRONMENT == "test"

    @property
    def is_local(self) -> bool:
        return self.ENVIRONMENT == "local"


class APISettings(FuryBaseSettings):
    """API settings."""

    model_config = build_settings_config("FURY_API_")

    CORS_ORIGINS: ClassVar[list[str]] = ["*"]
    CORS_METHODS: ClassVar[list[str]] = ["*"]
    CORS_HEADERS: ClassVar[list[str]] = ["Authorization", "Content-Type"]

    # This must be a Fernet key must be 32 url-safe base64-encoded bytes. Fernet.generate_key()
    SECRET_KEY: str = "V3KihWm1MLiZPpVrbhBXiGtHEitE6fB9gIzxM3VcPaw="

    AUTH_TOKEN_HEADER: str = "API-Key"
    AUTH_TOKEN_SECRET: SecretStr = "example-secret-key"  # TODO: I don't think this is being used for anything? Maybe with the admin domain we no longer need this.

    LONG_LIVED_TOKEN_ALGORITHM: str = "HS256"
    LONG_LIVED_TOKEN_KEY: SecretStr = "suMCrCpbI69GVODCkHvHNA=="  # TODO: On Project Setup this should be generated to avoid using the same key for all projects
    LONG_LIVED_TOKEN_EXPIRY: int = 60 * 60 * 24 * 30 * 12 * 10  # 10 years

    AUTH_HEADER: str = "Authorization"
    AUTH_SCHEME: str = "bearer"

    AUTH_TOKEN_CUSTOM_TRANSLATION: ClassVar[dict[str, str]] = {
        "user_id": "firebase_id",
        "name": "name",
        "email": "email",
    }

    SERVICES_AUTOCOMMIT: bool = True

    AUTH_ALGORITHM: str = "RS256"
    AUTH_ISSUER: str = "local"
    AUTH_DOMAIN: str | None = (
        None  # Not being  used right now, only needed in the future if we want to support multiple issuers.
    )

    ADMIN_TOKEN: SecretStr | None = None


class DevExSettings(FuryBaseSettings):
    """Dev settings."""

    model_config = build_settings_config("FURY_API_DEVEX_")

    ENABLED: bool = False

    ALLOW_ANY_AUTH_TOKEN_FOR_NEW_ORGANIZATION: bool = True

    AUTH_OVERRIDE_ENABLED: bool = True
    AUTH_OVERRIDE_ORGANIZATION_ID: int | None = None
    AUTH_OVERRIDE_USER_ID: int | None = None
    AUTH_OVERRIDE_USER_NAME: str | None = None
    AUTH_OVERRIDE_USER_EMAIL: str | None = None
    AUTH_OVERRIDE_FIREBASE_USER_ID: str | None = None

    TOKEN_GENERATION_FIREBASE_USER_ID: str | None = None

    @model_validator(mode="after")
    def disable_all_if_disabled(self: Self) -> Self:
        if not self.ENABLED:
            for field_name, field_info in self.model_fields.items():
                if field_name == "ENABLED":
                    continue
                value = getattr(self, field_name, None)
                if field_info.annotation is bool or isinstance(value, bool):
                    setattr(self, field_name, False)
                else:
                    setattr(self, field_name, None)
        return self


class LoggingSettings(FuryBaseSettings):
    """Logging settings."""

    model_config = build_settings_config("FURY_API_LOGGING_")

    LEVEL: str = "INFO"
    FORMAT: Literal["json", "console"] = "console"

    FORMAT_EXTERNAL: str = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s | %(message)s"


class DatabaseSettings(FuryBaseSettings):
    """Database settings."""

    model_config = build_settings_config("FURY_DB_")

    ECHO: bool = False
    ECHO_POOL: bool = False

    POOL_DISABLED: bool = False
    POOL_MAX_OVERFLOW: int = 10
    POOL_SIZE: int = 10
    POOL_TIMEOUT: int = 30
    POOL_PRE_PING: bool = True

    CONNECT_ARGS: ClassVar[dict[str, str]] = {}

    URL: str | None = None
    ENGINE: str = "postgresql+psycopg"
    USER: str = "postgres"
    PASSWORD: SecretStr = "postgres"
    HOST: str = "127.0.0.1"
    PORT: int = 5432
    NAME: str = "fury-local"

    SCHEMA: str = "platform"

    READ_ONLY_URL: str | None = None
    FORCE_READ_ONLY: bool = False

    TENANT_ROLE_ENABLED: bool = True
    TENANT_ROLE: str = "tenant_user"
    TENANT_ROLE_RO: str = "tenant_user_ro"
    TENANT_PARAMETER: str = "app.current_organization_id"
    TENANT_QUERY_ROLE_RO: str = "tenant_query_ro"

    NAMING_CONVENTION: ClassVar[dict[str, str]] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    @model_validator(mode="after")
    def assemble_url(self: Self) -> Self:
        if self.URL is not None:
            return self
        password = self.PASSWORD.get_secret_value() if isinstance(self.PASSWORD, SecretStr) else str(self.PASSWORD)
        self.URL = f"{self.ENGINE}://{self.USER}:{password}@{self.HOST}:{self.PORT}/{self.NAME}"
        return self


class OpenAPISettings(FuryBaseSettings):
    """OpenAPI settings."""

    model_config = build_settings_config("FURY_API_OPENAPI_")

    CONTACT_NAME: str = "Andre Cavalheiro"
    CONTACT_EMAIL: str = "andre@cavalheiro.io"
    TITLE: str | None = "Digital Me API"
    VERSION: str = f"v{version}"
    DESCRIPTION: str = "API for Digital Me - AI-assisted writing with content aggregation from curated sources"
    SCHEMA_PATH: str = "/api/schema"


class FirebaseSettings(FuryBaseSettings):
    """Firebase settings."""

    model_config = build_settings_config("FURY_FIREBASE_")

    PROJECT_ID: SecretStr
    PRIVATE_KEY_ID: SecretStr
    PRIVATE_KEY: SecretStr
    CLIENT_EMAIL: SecretStr
    CLIENT_ID: SecretStr
    AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    AUTH_PROVIDER_X509_CERT_URL: str = "https://www.googleapis.com/oauth2/v1/certs"
    CLIENT_X509_CERT_URL: SecretStr
    UNIVERSE_DOMAIN: str = "googleapis.com"
    WEB_API_KEY: SecretStr


class XAppSettings(FuryBaseSettings):
    """X App integration settings."""

    model_config = build_settings_config("FURY_X_APP_")

    BEARER_TOKEN: SecretStr | None = None


class XUserSettings(FuryBaseSettings):
    """X User HTTP integration settings."""

    model_config = build_settings_config("FURY_X_USER_")

    API_URL: str = "https://api.x.com/2"
    OAUTH_TOKEN_URL: str = "https://api.x.com/2/oauth2/token"
    OAUTH_CLIENT_ID: str | None = None
    OAUTH_CLIENT_SECRET: SecretStr | None = None


class CommunityArchiveSettings(FuryBaseSettings):
    """Community Archive integration settings."""

    model_config = build_settings_config("FURY_COMMUNITY_ARCHIVE_")

    BEARER_TOKEN: SecretStr | None = None


class ExperimentalSettings(FuryBaseSettings):
    """Experimental settings."""

    model_config = build_settings_config("FURY_API_EXPERIMENTAL_")


class AISettings(FuryBaseSettings):
    """Generic AI configuration."""

    model_config = build_settings_config("FURY_AI_")

    PROVIDER: Literal["openai"] = "openai"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    TEMPERATURE: float = 0.2
    MAX_OUTPUT_TOKENS: int | None = 512
    HISTORY_MESSAGE_LIMIT: int = 6
    MAX_SECTION_CHARS: int = 800
    MAX_CONTENT_CHARS: int = 500
    REQUEST_TIMEOUT: float = 40.0
    SYSTEM_PROMPT: str = (
        "You are Digital Me, a concise writing partner helping the user draft and refine document content. "
        "Ground answers in the provided document sections, citations, and user selections. "
        "If context is missing, state the gap and ask for a follow-up. "
        "Use clear markdown with short paragraphs or bullet points when helpful."
    )


class OpenAISettings(FuryBaseSettings):
    """OpenAI provider configuration."""

    model_config = build_settings_config("FURY_AI_OPENAI_")

    API_KEY: SecretStr | None = None
    BASE_URL: str = "https://api.openai.com/v1"
    MODEL: str | None = None  # Falls back to AISettings.DEFAULT_MODEL if not set
    EMBEDDING_MODEL: str = "text-embedding-3-small"


@dataclass(frozen=True, kw_only=True, slots=True)
class SettingsConfig:
    server: ServerSettings
    app: AppSettings
    api: APISettings
    dev: DevExSettings
    logging: LoggingSettings
    database: DatabaseSettings
    openapi: OpenAPISettings
    firebase: FirebaseSettings
    x_app: XAppSettings
    x_user: XUserSettings
    community_archive: CommunityArchiveSettings
    experimental: ExperimentalSettings
    ai: AISettings
    ai_openai: OpenAISettings


_loaded_settings: SettingsConfig | None = None


def load_settings(force_reload: bool = False) -> SettingsConfig:
    global _loaded_settings
    if _loaded_settings is not None and not force_reload:
        return _loaded_settings

    load_dotenv()
    try:
        _loaded_settings = SettingsConfig(
            server=ServerSettings(),
            app=AppSettings(),
            api=APISettings(),
            dev=DevExSettings(),
            logging=LoggingSettings(),
            database=DatabaseSettings(),
            openapi=OpenAPISettings(),
            firebase=FirebaseSettings(),
            x_app=XAppSettings(),
            x_user=XUserSettings(),
            community_archive=CommunityArchiveSettings(),
            experimental=ExperimentalSettings(),
            ai=AISettings(),
            ai_openai=OpenAISettings(),
        )
    except ValidationError as exc:
        print(f"Error loading settings: {exc}")
        raise

    return _loaded_settings


config = load_settings()
