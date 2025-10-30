from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .settings import settings
from .middleware.rls import RLSContextMiddleware
from .routes.health import router as health_router
from .routes.reports import router as reports_router

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

# RLS placeholder middleware
app.add_middleware(RLSContextMiddleware)

# Routes
app.include_router(health_router)
app.include_router(reports_router)

# Root
@app.get("/")
def root():
    return {"message": "Market Reports API"}

