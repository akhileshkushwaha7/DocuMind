from pydantic_settings import BaseSettings
from pathlib import Path

ENV_FILE = Path(__file__).parent.parent.parent / "backend" / ".env"

class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    REDIS_URL: str
    QDRANT_URL: str
    JWT_SECRET: str
    GROQ_API_KEY: str

    # Add these missing fields
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = {"env_file": str(ENV_FILE)}

settings = Settings()