from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "market-reports-api"
    PORT: int = 10000
    # S2 — Environment gate for dev/seed endpoints. Defaults to "production"
    # so any deploy that forgets to set ENVIRONMENT is treated as production
    # (fail-safe). Set ENVIRONMENT=development locally or in staging to
    # enable dev-only routes (/v1/auth/seed-dev, /dev-files/*, etc.).
    ENVIRONMENT: str = "production"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/market_reports"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "dev-secret"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Stripe Configuration
    STRIPE_SECRET_KEY: str = ""
    STARTER_PRICE_ID: str = ""
    PRO_PRICE_ID: str = ""
    ENTERPRISE_PRICE_ID: str = ""
    APP_BASE: str = "https://www.trendyreports.io"
    STRIPE_WEBHOOK_SECRET: str = ""

    # S3 — Internal render token for server-to-server calls from the Next.js
    # print page and social image route to /v1/reports/{id}/data. When set,
    # requests to that endpoint that carry header X-Internal-Render-Token
    # equal to this value are treated as trusted internal renders. When
    # empty (default), the token path is disabled and only authenticated
    # account sessions can read report data.
    INTERNAL_RENDER_TOKEN: str = ""

    # Email Configuration (SendGrid)
    SENDGRID_API_KEY: str = ""
    RESEND_API_KEY: str = ""  # Deprecated — kept for backwards compat, unused
    EMAIL_FROM_ADDRESS: str = "TrendyReports <noreply@trendyreports.io>"
    EMAIL_REPLY_TO: str = "support@trendyreports.io"

    class Config:
        env_file = ".env"


settings = Settings()

# FIX (L2): Log length only, not content — prevents secret leaking in logs
import logging
logger = logging.getLogger(__name__)
logger.info(f"Settings loaded: JWT_SECRET configured ({len(settings.JWT_SECRET)} chars)")

