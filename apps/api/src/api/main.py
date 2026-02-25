import time as _time
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .middleware.authn import AuthContextMiddleware, RateLimitMiddleware
from .routes.health import router as health_router
from .routes.hello import router as hello_router
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
from .routes.onboarding import router as onboarding_router
from .routes.leads import router as leads_router
from .routes.property import router as property_router
from .routes.mobile_reports import router as mobile_reports_router
from .routes.admin_metrics import router as admin_metrics_router
from .routes.lead_pages import router as lead_pages_router

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

# ============================================================================
# MIDDLEWARE REGISTRATION
# 
# CRITICAL: Starlette add_middleware() uses LIFO (stack).
# Last added = first to execute.
# We want: Timing → Auth → RateLimit → Route
# So register in REVERSE order:
# ============================================================================

# 1. Register RateLimit FIRST (executes LAST, after auth sets account_id)
app.add_middleware(RateLimitMiddleware)

# 2. Register Auth SECOND (executes SECOND, sets account_id)
app.add_middleware(AuthContextMiddleware)

# REMOVED: RLSContextMiddleware (L1 — was a no-op, auth handles X-Demo-Account)
# DO NOT add: app.add_middleware(RLSContextMiddleware)

# 3. Timing middleware (executes FIRST via @app.middleware, wraps everything)

@app.middleware("http")
async def timing_middleware(request, call_next):
    start = _time.perf_counter()
    response = await call_next(request)
    elapsed = _time.perf_counter() - start
    
    level = logging.WARNING if elapsed > 1.0 else logging.DEBUG
    logging.getLogger("api.timing").log(
        level,
        f"[TIMING] {request.method} {request.url.path} "
        f"→ {response.status_code} in {elapsed:.3f}s"
    )
    response.headers["Server-Timing"] = f"total;dur={elapsed * 1000:.0f}"
    return response

# Routes
app.include_router(health_router)
app.include_router(hello_router)
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
app.include_router(onboarding_router)
app.include_router(leads_router)
app.include_router(property_router)
app.include_router(mobile_reports_router)
app.include_router(admin_metrics_router)
app.include_router(lead_pages_router)

# Root
@app.get("/")
def root():
    return {"message": "Market Reports API"}
