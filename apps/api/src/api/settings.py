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

    # Email Configuration (Resend)
    RESEND_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "Market Reports <noreply@marketreports.com>"
    EMAIL_REPLY_TO: str = "support@marketreports.com"

    class Config:
        env_file = ".env"


settings = Settings()

# Diagnostic logging for JWT_SECRET
import logging
logger = logging.getLogger(__name__)
jwt_secret_preview = settings.JWT_SECRET[:10] + "..." if len(settings.JWT_SECRET) > 10 else settings.JWT_SECRET
logger.info(f"Settings loaded: JWT_SECRET = {jwt_secret_preview} (length: {len(settings.JWT_SECRET)})")

