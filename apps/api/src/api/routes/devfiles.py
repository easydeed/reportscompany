from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

router = APIRouter()
BASE = "/tmp/mr_reports"

@router.get("/dev-files/reports/{run_id}.pdf")
def dev_pdf(run_id: str):
    """Dev-only route: serves PDFs without auth for easy browser testing"""
    path = os.path.join(BASE, f"{run_id}.pdf")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="application/pdf", filename=f"report-{run_id}.pdf")

