from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "market-reports-api"
    PORT: int = 10000
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/market_reports"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "dev-secret"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Stripe Configuration
    STRIPE_SECRET_KEY: str = ""
    STARTER_PRICE_ID: str = ""
    PRO_PRICE_ID: str = ""
    ENTERPRISE_PRICE_ID: str = ""
    APP_BASE: str = "http://localhost:3000"
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

