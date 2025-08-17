from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from typing import Dict


class Settings(BaseSettings):
    # Pydantic v2 settings configuration
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    PROJECT_NAME: str = "FastAPI Multi-Tenant AI"
    API_V1_STR: str = "/api/v1"

    # JWT settings
    SECRET_KEY: str
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
    AI_PROVIDER: str = "gemini"  # "groq" or "gemini"
    GROQ_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None


settings = Settings()


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
