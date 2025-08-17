
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Project"
    API_V1_STR: str = "/api/v1"

    # JWT settings
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"


    # Database settings
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./test.db"

    # AI Service settings
    AI_PROVIDER: str = "gemini" # "groq" or "gemini"
    GROQ_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
