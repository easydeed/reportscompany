from fastapi import APIRouter
from ..settings import settings
from ..schema_guard import REQUIRED_MIGRATION

router = APIRouter()

@router.get("/health")
def health():
    # `schema`: the newest migration this build needs — which code is live,
    # and what the database must have applied for it.
    return {"ok": True, "service": settings.APP_NAME, "schema": REQUIRED_MIGRATION}

