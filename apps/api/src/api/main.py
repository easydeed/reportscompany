from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .middleware.rls import RLSContextMiddleware
from .middleware.authn import AuthContextMiddleware, RateLimitMiddleware
from .routes.health import router as health_router
from .routes.reports import router as reports_router
from .routes.report_data import router as report_data_router
from .routes.account import router as account_router
from .routes.usage import router as usage_router
from .routes.auth import router as auth_router
from .routes.apikeys import router as apikeys_router
from .routes.webhooks import router as webhooks_router
from .routes.devfiles import router as devfiles_router
from .routes.billing import router as billing_router
from .routes.stripe_webhook import router as stripe_webhook_router
from .routes.schedules import router as schedules_router
from .routes.unsubscribe import router as unsubscribe_router
from .routes.admin import router as admin_router
from .routes.me import router as me_router
from .routes.affiliates import router as affiliates_router
from .routes.contacts import router as contacts_router
from .routes.contact_groups import router as contact_groups_router
from .routes.dev_stripe_prices import router as dev_stripe_prices_router
from .routes.upload import router as upload_router
from .routes.branding_tools import router as branding_tools_router
from .routes.users import router as users_router

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
app.include_router(report_data_router)
app.include_router(account_router)
app.include_router(usage_router)
app.include_router(schedules_router)
app.include_router(unsubscribe_router)
app.include_router(admin_router)
app.include_router(me_router)
app.include_router(affiliates_router)
app.include_router(contacts_router)
app.include_router(contact_groups_router)
app.include_router(dev_stripe_prices_router)
app.include_router(upload_router)
app.include_router(branding_tools_router)
app.include_router(users_router)

# Root
@app.get("/")
def root():
    return {"message": "Market Reports API"}

