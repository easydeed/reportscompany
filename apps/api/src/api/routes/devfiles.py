from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from ..settings import settings

router = APIRouter()
BASE = "/tmp/mr_reports"

@router.get("/dev-files/reports/{run_id}.pdf")
def dev_pdf(run_id: str):
    """Dev-only route: serves PDFs without auth for easy browser testing.

    S2 — Disabled entirely in production. Returns 404 so production probes
    can't confirm the route exists. The middleware (_PUBLIC_PREFIXES) still
    skips auth for /dev-files/, but this handler will refuse to serve in
    production (defense-in-depth).
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not Found")
    path = os.path.join(BASE, f"{run_id}.pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf", filename=f"report-{run_id}.pdf")
