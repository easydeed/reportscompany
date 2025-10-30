from fastapi import APIRouter
from ..settings import settings

router = APIRouter()

@router.get("/health")
def health():
    return {"ok": True, "service": settings.APP_NAME}

