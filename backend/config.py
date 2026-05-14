from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Base
    secret_key: str = "change-me-in-production"
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    # Base de données
    database_url: str = "postgresql+asyncpg://user:password@localhost/tarot"

    # Groq (free — console.groq.com)
    groq_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""  # ID du prix premium 5€/mois

    # Quota
    daily_free_limit: int = 3

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ignore les variables inconnues du .env parent


@lru_cache()
def get_settings() -> Settings:
    return Settings()
