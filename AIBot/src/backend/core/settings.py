from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from typing import Dict


class Settings(BaseSettings):
    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore',  # ignore unknown env vars like legacy keys
    )

    PROJECT_NAME: str = "FastAPI Multi-Tenant AI"
    API_V1_STR: str = "/api/v1"

    # JWT settings
    SECRET_KEY: str = "fallback-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"

    # Multi-tenant database settings
    # Support both DEFAULT_DATABASE_URI and legacy SQLALCHEMY_DATABASE_URI from .env
    DEFAULT_DATABASE_URI: str = Field(
        default="sqlite:///./app.db",
        validation_alias=AliasChoices("DEFAULT_DATABASE_URI", "SQLALCHEMY_DATABASE_URI"),
    )
    TENANT_DATABASE_PATH: str = "./tenant_databases/"
    
    # AI Service settings
    AI_PROVIDER: str = "groq"  # "groq" or "gemini"
    GROQ_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    # Feature flags
    # Support both AI_CHAT_ENABLED and legacy AI_CHAT env variables
    AI_CHAT_ENABLED: bool = Field(
        default=True,
        validation_alias=AliasChoices("AI_CHAT_ENABLED", "AI_CHAT"),
    )  # Global default; can be overridden per-tenant

    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None

    # MessageCentral (SMS/OTP) Settings
    MESSAGECENTRAL_BASE_URL: str = "https://cpaas.messagecentral.com"
    MESSAGECENTRAL_CUSTOMER_ID: str | None = None
    # Support both MESSAGECENTRAL_AUTH_TOKEN and MESSAGECENTRAL_BEARER_TOKEN for compatibility
    MESSAGECENTRAL_AUTH_TOKEN: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MESSAGECENTRAL_AUTH_TOKEN", "MESSAGECENTRAL_BEARER_TOKEN"),
    )

    # OTP settings
    OTP_EXPIRY_MINUTES: int = 5
    OTP_RESEND_INTERVAL_SECONDS: int = 30


settings = Settings()

# Debug: Print API key status on startup
print(f"Settings loaded - AI_PROVIDER: {settings.GEMINI_API_KEY}")
print(f"GROQ_API_KEY loaded: {'Yes' if settings.GROQ_API_KEY else 'No'}")
print(f"GEMINI_API_KEY loaded: {'Yes' if settings.GEMINI_API_KEY else 'No'}")


def get_tenant_database_uri(tenant_name: str) -> str:
    """Get database URI for a specific tenant."""
    return f"sqlite:///{settings.TENANT_DATABASE_PATH}{tenant_name}.db"


def get_tenant_database_config(tenant_name: str) -> Dict[str, str]:
    """Get database configuration for a specific tenant."""
    return {
        "database_uri": get_tenant_database_uri(tenant_name),
        "tenant_name": tenant_name,
        "database_path": f"{settings.TENANT_DATABASE_PATH}{tenant_name}.db"
    }
