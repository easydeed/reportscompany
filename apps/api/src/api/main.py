from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .middleware.rls import RLSContextMiddleware
from .middleware.authn import AuthContextMiddleware, RateLimitMiddleware
from .routes.health import router as health_router
from .routes.reports import router as reports_router
from .routes.account import router as account_router
from .routes.usage import router as usage_router
from .routes.auth import router as auth_router
from .routes.apikeys import router as apikeys_router
from .routes.webhooks import router as webhooks_router
from .routes.devfiles import router as devfiles_router
from .routes.billing import router as billing_router
from .routes.stripe_webhook import router as stripe_webhook_router

app = FastAPI(
    title="Market Reports API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS or ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth & Rate Limiting (must be after CORS, before routes)
app.add_middleware(AuthContextMiddleware)
app.add_middleware(RateLimitMiddleware)

# RLS placeholder middleware (kept for backward compat)
app.add_middleware(RLSContextMiddleware)

# Routes
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(apikeys_router)
app.include_router(webhooks_router)
app.include_router(devfiles_router)
app.include_router(billing_router)
app.include_router(stripe_webhook_router)
app.include_router(reports_router)
app.include_router(account_router)
app.include_router(usage_router)

# Root
@app.get("/")
def root():
    return {"message": "Market Reports API"}

